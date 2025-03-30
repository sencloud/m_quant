import tushare as ts
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from config import settings
from models.market_data import FuturesData, ETFData, OptionsData
from utils.logger import logger

class MarketDataService:
    def __init__(self):
        logger.info("初始化市场数据服务")
        ts.set_token(settings.TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        self.logger = logger
        logger.debug("Tushare API初始化完成")

    def _get_futures_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, symbol: str = "M") -> List[FuturesData]:
        """获取期货数据"""
        try:
            # 如果是品种代码，先获取主力合约
            if len(symbol) == 1:
                logger.info(f"获取主力合约 - 品种: {symbol}")
                # 获取最近的交易日
                trade_cal = self.pro.trade_cal(
                    exchange='DCE',
                    is_open='1',
                    start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
                    end_date=end_date if end_date else datetime.now().strftime('%Y%m%d')
                )
                if trade_cal is None or trade_cal.empty:
                    logger.warning(f"未找到最近的交易日")
                    return []
                
                # 获取小于等于请求结束日期的最后一个交易日
                trade_cal = trade_cal[trade_cal['cal_date'] <= (end_date if end_date else datetime.now().strftime('%Y%m%d'))]
                if trade_cal.empty:
                    logger.warning(f"未找到小于等于{end_date}的交易日")
                    return []
                    
                latest_trade_date = trade_cal.iloc[0]['cal_date']
                logger.info(f"最近的交易日: {latest_trade_date}")
                
                # 获取主力合约
                main_contract = self.pro.fut_mapping(
                    ts_code=symbol+'.DCE',
                    trade_date=latest_trade_date
                )
                logger.debug(f"主力合约查询结果: \n{main_contract}")
                
                if main_contract is None or main_contract.empty:
                    logger.warning(f"未找到主力合约 - 品种: {symbol}, 日期: {latest_trade_date}")
                    return []
                symbol = main_contract.iloc[0]['mapping_ts_code']
                logger.info(f"获取到主力合约: {symbol}")
            
            # 获取合约基本信息
            contract_info = self.pro.fut_basic(
                ts_code=symbol,
                exchange='DCE'
            )
            if contract_info is None or contract_info.empty:
                logger.warning(f"未找到合约信息: {symbol}")
                return []
            
            # 获取合约的实际交易日期范围
            contract_start_date = contract_info.iloc[0]['list_date']
            contract_end_date = contract_info.iloc[0]['delist_date']
            
            # 对于多合约请求，使用合约的实际交易日期范围
            if len(symbol) > 1:  # 如果是具体合约代码（如M2401）
                start_date = contract_start_date
                end_date = contract_end_date if contract_end_date else datetime.now().strftime('%Y%m%d')
            else:  # 如果是品种代码，使用用户指定的日期范围
                if not start_date:
                    start_date = contract_start_date
                if not end_date:
                    end_date = contract_end_date if contract_end_date else datetime.now().strftime('%Y%m%d')
            
            # 确保日期范围在合约交易期间内
            start_date = max(start_date, contract_start_date)
            if contract_end_date:
                end_date = min(end_date, contract_end_date)
            
            logger.info(f"开始获取期货数据 - 品种: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}")
            
            # 获取合约数据
            df = self.pro.fut_daily(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                logger.warning(f"未找到期货数据 - 合约: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}")
                return []
            
            logger.info(f"成功获取期货数据，共{len(df)}条记录")
            logger.debug(f"数据示例: \n{df.head()}")
            
            # 处理数据
            futures_data = []
            for _, row in df.iterrows():
                # 从ts_code中提取合约代码
                contract = row['ts_code'].split('.')[0]
                
                # 处理可能的无穷大或NaN值
                def safe_float(value):
                    try:
                        if pd.isna(value) or np.isinf(value):
                            return 0.0
                        return float(value)
                    except (ValueError, TypeError):
                        return 0.0
                
                data = {
                    'ts_code': row['ts_code'],
                    'trade_date': row['trade_date'],
                    'pre_close': safe_float(row['pre_close']),
                    'pre_settle': safe_float(row['pre_settle']),
                    'open': safe_float(row['open']),
                    'high': safe_float(row['high']),
                    'low': safe_float(row['low']),
                    'close': safe_float(row['close']),
                    'settle': safe_float(row['settle']),
                    'change1': safe_float(row['change1']),
                    'change2': safe_float(row['change2']),
                    'vol': safe_float(row['vol']),
                    'amount': safe_float(row['amount']),
                    'oi': safe_float(row['oi']),
                    'oi_chg': safe_float(row['oi_chg']),
                    'contract': contract,
                    'price': safe_float(row['close']),  # 使用收盘价作为当前价格
                    'historicalPrices': []  # 这个字段会在API层面处理
                }
                futures_data.append(FuturesData(**data))
            
            return futures_data
        except Exception as e:
            logger.error(f"获取期货数据失败: {str(e)}")
            raise

    def calculate_ma(self, data: pd.DataFrame, window: int) -> pd.Series:
        """计算移动平均线"""
        return data['close'].rolling(window=window).mean()

    def calculate_atr(self, data: pd.DataFrame, window: int = 14) -> pd.Series:
        """计算ATR"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        return atr

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        logger.info("开始生成交易信号")
        
        # 计算金叉/死叉
        data['cross'] = (data['ma5'] > data['ma8']).astype(int)
        data['cross_change'] = data['cross'].diff()
        logger.debug(f"金叉/死叉计算结果: \n{data[['trade_date', 'cross', 'cross_change']].tail()}")
        
        # 生成信号
        data['signal'] = 'hold'
        data.loc[data['cross_change'] == 1, 'signal'] = 'buy'
        data.loc[data['cross_change'] == -1, 'signal'] = 'sell'
        logger.debug(f"信号生成结果: \n{data[['trade_date', 'signal']].tail()}")
        
        # 计算止损止盈价格
        data['stop_loss'] = data.apply(
            lambda x: x['close'] - 1.8 * x['atr'] if x['signal'] == 'buy' else None, 
            axis=1
        )
        data['take_profit'] = data.apply(
            lambda x: x['close'] + 2.6 * x['atr'] if x['signal'] == 'buy' else None, 
            axis=1
        )
        logger.debug(f"止损止盈计算结果: \n{data[['trade_date', 'stop_loss', 'take_profit']].tail()}")
        
        # 计算历史信号信息
        last_signal = None
        last_signal_date = None
        last_signal_price = None
        last_stop_loss = None
        last_take_profit = None
        
        # 从后向前遍历，找到最近的金叉信号
        logger.info("开始查找最近的金叉信号")
        for idx in reversed(data.index):
            if data.loc[idx, 'signal'] == 'buy':  # 只找金叉信号
                last_signal = data.loc[idx, 'signal']
                last_signal_date = data.loc[idx, 'trade_date']
                last_signal_price = data.loc[idx, 'close']
                last_stop_loss = data.loc[idx, 'stop_loss']
                last_take_profit = data.loc[idx, 'take_profit']
                logger.info(f"找到最近的金叉信号: 日期={last_signal_date}, 价格={last_signal_price}")
                break
        
        # 将找到的最近信号信息填充到所有行
        data['last_signal'] = last_signal
        data['last_signal_date'] = last_signal_date
        data['last_signal_price'] = last_signal_price
        data['last_stop_loss'] = last_stop_loss
        data['last_take_profit'] = last_take_profit
        
        logger.debug(f"历史信号信息填充结果: \n{data[['trade_date', 'last_signal', 'last_signal_date', 'last_signal_price']].tail()}")
        logger.info("交易信号生成完成")
        
        return data

    def get_futures_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, symbol: str = "M") -> List[FuturesData]:
        """获取豆粕期货数据"""
        try:
            # 获取数据
            futures_data = self._get_futures_data(start_date, end_date, symbol)
            if not futures_data:
                return []
            
            # 按合约分组
            contract_groups = {}
            for data in futures_data:
                if data.contract not in contract_groups:
                    contract_groups[data.contract] = {
                        'ts_code': data.ts_code,
                        'trade_date': data.trade_date,
                        'pre_close': data.pre_close,
                        'pre_settle': data.pre_settle,
                        'open': data.open,
                        'high': data.high,
                        'low': data.low,
                        'close': data.close,
                        'settle': data.settle,
                        'change1': data.change1,
                        'change2': data.change2,
                        'vol': data.vol,
                        'amount': data.amount,
                        'oi': data.oi,
                        'oi_chg': data.oi_chg,
                        'contract': data.contract,
                        'price': data.price,
                        'historicalPrices': []
                    }
                contract_groups[data.contract]['historicalPrices'].append({
                    'date': data.trade_date,
                    'open': data.open,
                    'high': data.high,
                    'low': data.low,
                    'close': data.close,
                    'volume': data.vol,
                    'contract': data.contract
                })
            
            # 转换为FuturesData列表
            result = []
            for contract_data in contract_groups.values():
                # 按日期排序
                contract_data['historicalPrices'].sort(key=lambda x: x['date'])
                result.append(FuturesData(**contract_data))
            
            return result
        except Exception as e:
            logger.error(f"获取期货数据失败: {str(e)}")
            return []

    def get_etf_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: str = "159985.SZ"
    ) -> List[ETFData]:
        """获取ETF数据并计算技术指标"""
        logger.info(f"获取ETF数据 - 代码: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}")
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 获取ETF日线数据
            df = self.pro.fund_daily(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # 重命名列以匹配我们的模型
            df = df.rename(columns={
                'trade_date': 'trade_date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'vol',
                'amount': 'amount'
            })
            
            # 按时间正序排序
            df = df.sort_values('trade_date')
            
            # 处理缺失值和异常值
            df = df.fillna(method='ffill').fillna(method='bfill')
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # 计算技术指标
            df['ma5'] = self.calculate_ma(df, 5)
            df['ma8'] = self.calculate_ma(df, 8)
            df['atr'] = self.calculate_atr(df)
            
            # 处理技术指标的缺失值和异常值
            df['ma5'] = df['ma5'].fillna(method='ffill').fillna(method='bfill')
            df['ma8'] = df['ma8'].fillna(method='ffill').fillna(method='bfill')
            df['atr'] = df['atr'].fillna(method='ffill').fillna(method='bfill')
            
            # 生成交易信号
            df = self.generate_signals(df)
            
            # 转换为模型格式
            return [
                ETFData(
                    ts_code=symbol,
                    trade_date=row['trade_date'],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    vol=float(row['vol']),
                    amount=float(row['amount']),
                    ma5=float(row['ma5']),
                    ma8=float(row['ma8']),
                    atr=float(row['atr']),
                    signal=row['signal'],
                    stop_loss=float(row['stop_loss']) if pd.notnull(row['stop_loss']) else None,
                    take_profit=float(row['take_profit']) if pd.notnull(row['take_profit']) else None,
                    last_signal=row['last_signal'],
                    last_signal_date=row['last_signal_date'],
                    last_signal_price=float(row['last_signal_price']) if pd.notnull(row['last_signal_price']) else None,
                    last_stop_loss=float(row['last_stop_loss']) if pd.notnull(row['last_stop_loss']) else None,
                    last_take_profit=float(row['last_take_profit']) if pd.notnull(row['last_take_profit']) else None
                )
                for _, row in df.iterrows()
            ]
            
        except Exception as e:
            self.logger.error(f"获取ETF数据失败: {str(e)}")
            raise

    def get_options_data(
        self,
        underlying: str = "M",
        exchange: str = "DCE"
    ) -> List[OptionsData]:
        logger.info(f"获取期权数据 - 标的: {underlying}, 交易所: {exchange}")
        try:
            df = self.pro.opt_basic(
                underlying=underlying,
                exchange=exchange
            )
            logger.debug(f"成功获取期权数据，共{len(df)}条记录")
            return [OptionsData(**row) for row in df.to_dict('records')]
        except Exception as e:
            logger.error(f"获取期权数据失败: {str(e)}")
            raise

    def get_futures_contracts_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, contracts: List[str] = ["M2401", "M2405", "M2409"]) -> List[FuturesData]:
        """获取多个豆粕期货合约数据"""
        try:
            # 获取每个合约的数据
            all_data = []
            for contract in contracts:
                df = self._get_futures_data(start_date, end_date, contract)
                if df is not None and not df.empty:
                    # 添加合约信息
                    df['contract'] = contract
                    all_data.append(df)
            
            if not all_data:
                return []
            
            # 合并所有合约数据
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # 转换为模型格式
            return [
                FuturesData(
                    ts_code=row['ts_code'],
                    trade_date=row['trade_date'],
                    pre_close=row['pre_close'],
                    pre_settle=row['pre_settle'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    settle=row['settle'],
                    change1=row['change1'],
                    change2=row['change2'],
                    vol=row['vol'],
                    amount=row['amount'],
                    oi=row['oi'],
                    oi_chg=row['oi_chg'],
                    contract=row['contract'],
                    price=row['price'],
                    historicalPrices=row['historicalPrices']
                )
                for _, row in combined_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"获取多合约数据失败: {str(e)}")
            return []

    def get_futures_inventory(self) -> Dict:
        """获取豆粕库存数据"""
        try:
            logger.info("开始获取豆粕库存数据")
            # 使用akshare获取豆粕库存数据
            df = ak.futures_inventory_em(symbol='豆粕')
            
            if df is None or df.empty:
                logger.warning("未获取到豆粕库存数据")
                return {}
            
            # 获取最新一条数据
            latest_data = df.iloc[-1]
            
            # 处理历史数据
            history_data = []
            for _, row in df.tail(10).iterrows():  # 只取最近10条数据
                history_data.append({
                    "date": row['日期'],
                    "inventory": int(row['库存'])
                })
            
            result = {
                "total_inventory": int(latest_data['库存']),
                "warehouse_inventory": int(latest_data['库存'] * 0.6),  # 假设仓库库存占总库存60%
                "port_inventory": int(latest_data['库存'] * 0.4),  # 假设港口库存占总库存40%
                "update_date": latest_data['日期'],
                "history_data": history_data
            }
            
            logger.info(f"成功获取豆粕库存数据: {result}")
            return result
            
        except Exception as e:
            logger.error(f"获取库存数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}

    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """计算技术分析指标"""
        try:
            # 处理可能的无穷大或NaN值
            def safe_float(value):
                try:
                    if pd.isna(value) or np.isinf(value):
                        return 0.0
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            # 计算EMA
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            
            # 计算MACD
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            bar = 2 * (dif - dea)
            
            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 计算KDJ
            low_9 = df['low'].rolling(window=9).min()
            high_9 = df['high'].rolling(window=9).max()
            rsv = (df['close'] - low_9) / (high_9 - low_9) * 100
            k = rsv.rolling(window=3).mean()
            d = k.rolling(window=3).mean()
            j = 3 * k - 2 * d
            
            # 计算布林带
            ma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            
            # 获取最新值
            latest_price = df['close'].iloc[-1]
            latest_volume = df['vol'].iloc[-1]
            volume_change = (df['vol'].iloc[-1] - df['vol'].iloc[-2]) / df['vol'].iloc[-2] * 100
            
            # 确定趋势
            def get_trend(current, previous):
                if current > previous:
                    return "up"
                elif current < previous:
                    return "down"
                else:
                    return "neutral"
            
            return {
                "contract": df['ts_code'].iloc[-1],
                "last_updated": df['trade_date'].iloc[-1],
                "current_price": safe_float(latest_price),
                "price_targets": {
                    "support_levels": {
                        "s1": safe_float(latest_price * 0.98),
                        "s2": safe_float(latest_price * 0.95)
                    },
                    "resistance_levels": {
                        "r1": safe_float(latest_price * 1.02),
                        "r2": safe_float(latest_price * 1.05)
                    },
                    "trend": get_trend(latest_price, df['close'].iloc[-2])
                },
                "ema": {
                    "ema12": safe_float(ema12.iloc[-1]),
                    "ema26": safe_float(ema26.iloc[-1]),
                    "trend": get_trend(ema12.iloc[-1], ema26.iloc[-1])
                },
                "macd": {
                    "diff": safe_float(dif.iloc[-1]),
                    "dea": safe_float(dea.iloc[-1]),
                    "bar": safe_float(bar.iloc[-1]),
                    "trend": get_trend(dif.iloc[-1], dea.iloc[-1])
                },
                "rsi": {
                    "value": safe_float(rsi.iloc[-1]),
                    "trend": get_trend(rsi.iloc[-1], rsi.iloc[-2])
                },
                "kdj": {
                    "k": safe_float(k.iloc[-1]),
                    "d": safe_float(d.iloc[-1]),
                    "j": safe_float(j.iloc[-1]),
                    "trend": get_trend(k.iloc[-1], d.iloc[-1])
                },
                "bollinger_bands": {
                    "upper": safe_float(upper.iloc[-1]),
                    "middle": safe_float(ma20.iloc[-1]),
                    "lower": safe_float(lower.iloc[-1]),
                    "trend": get_trend(latest_price, ma20.iloc[-1])
                },
                "volume": {
                    "current": safe_float(latest_volume),
                    "change_percent": safe_float(volume_change),
                    "trend": get_trend(latest_volume, df['vol'].iloc[-2])
                }
            }
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return {}

    def get_technical_indicators(self, symbol: str = "M") -> Dict:
        """获取技术分析指标"""
        try:
            logger.info(f"开始获取技术分析指标 - 品种: {symbol}")
            # 获取最近30天的数据用于计算技术指标
            futures_data = self._get_futures_data(
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                symbol=symbol
            )
            
            if not futures_data:
                logger.warning("未获取到期货数据")
                return {}
            
            # 将列表转换为DataFrame
            df = pd.DataFrame([{
                'ts_code': item.ts_code,
                'trade_date': item.trade_date,
                'open': item.open,
                'high': item.high,
                'low': item.low,
                'close': item.close,
                'vol': item.vol
            } for item in futures_data])
            
            # 按日期排序
            df = df.sort_values('trade_date')
            
            # 计算技术指标
            indicators = self.calculate_technical_indicators(df)
            logger.info(f"成功计算技术分析指标: {indicators}")
            return indicators
            
        except Exception as e:
            logger.error(f"获取技术分析指标失败: {str(e)}")
            return {} 