import tushare as ts
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from config import settings
from models.market_data import FuturesData, ETFData, OptionsData, PriceRangeAnalysis, KlineData, HistoricalBottom, ContractStats
from utils.logger import logger
import time
import threading
import os

class RateLimiter:
    """令牌桶算法实现的限流器"""
    def __init__(self, rate, capacity):
        self.rate = rate  # 令牌产生速率
        self.capacity = capacity  # 桶的容量
        self.tokens = capacity  # 当前令牌数
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self):
        """获取一个令牌，如果没有令牌则等待"""
        with self.lock:
            now = time.time()
            # 计算从上次更新到现在产生的令牌数
            elapsed = now - self.last_update
            new_tokens = elapsed * self.rate
            
            # 更新令牌数和上次更新时间
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now
            
            if self.tokens < 1:
                # 计算需要等待的时间
                wait_time = (1 - self.tokens) / self.rate
                logger.warning(f"API限流: 需要等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
                # 重新计算令牌数
                now = time.time()
                elapsed = now - self.last_update
                new_tokens = elapsed * self.rate
                self.tokens = min(self.capacity, self.tokens + new_tokens)
                self.last_update = now
            
            # 消耗一个令牌
            self.tokens -= 1
            return True

class MarketDataService:
    def __init__(self):
        logger.info("初始化市场数据服务")
        try:
            token = settings.TUSHARE_TOKEN
            if not token:
                logger.error("未找到 TUSHARE_TOKEN，请在 .env 文件中设置")
                self.pro = None
            else:
                ts.set_token(token)
                self.pro = ts.pro_api()
                self.logger = logger
                logger.debug("Tushare API初始化完成")
                
                # 初始化限流器: 每分钟最多280次调用(留有余地)
                self.rate_limiter = RateLimiter(rate=280/60, capacity=280)
        except Exception as e:
            logger.error(f"市场数据服务初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.pro = None
            self.logger = logger
            self.rate_limiter = None

    def _call_tushare_api(self, func, *args, **kwargs):
        """包装Tushare API调用，添加限流保护"""
        if self.rate_limiter:
            self.rate_limiter.acquire()
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "每分钟最多访问该接口300次" in str(e):
                logger.error(f"Tushare API限流: {str(e)}")
                # 如果是限流错误，等待一段时间后重试
                time.sleep(2)
                # 重试时也要使用限流保护
                if self.rate_limiter:
                    self.rate_limiter.acquire()
                return self._call_tushare_api(func, *args, **kwargs)
            raise

    def _get_futures_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, symbol: str = "M") -> List[FuturesData]:
        """获取期货数据"""
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取期货数据")
                return []
                
            # 如果是品种代码，先获取主力合约
            if len(symbol) == 1:
                logger.info(f"获取主力合约 - 品种: {symbol}")
                # 获取最近的交易日
                trade_cal = self._call_tushare_api(
                    self.pro.trade_cal,
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
                
                # 按日期降序排序，从最近的交易日开始查找
                trade_cal = trade_cal.sort_values('cal_date', ascending=False)
                
                # 尝试查找最近5个交易日的主力合约
                main_contract = None
                latest_trade_date = None
                
                for _, row in trade_cal.head(5).iterrows():
                    current_date = row['cal_date']
                    logger.info(f"尝试获取{current_date}的主力合约")
                    
                    temp_main_contract = self._call_tushare_api(
                        self.pro.fut_mapping,
                        ts_code=symbol+'.DCE',
                        trade_date=current_date
                    )
                    
                    if temp_main_contract is not None and not temp_main_contract.empty:
                        main_contract = temp_main_contract
                        latest_trade_date = current_date
                        logger.info(f"在{current_date}找到主力合约")
                        break
                    else:
                        logger.warning(f"在{current_date}未找到主力合约")
                
                if main_contract is None or main_contract.empty:
                    logger.warning(f"在最近5个交易日未找到主力合约 - 品种: {symbol}")
                    return []
                
                symbol = main_contract.iloc[0]['mapping_ts_code']
                logger.info(f"获取到主力合约: {symbol}, 日期: {latest_trade_date}")
            
            # 获取合约基本信息
            contract_info = self._call_tushare_api(
                self.pro.fut_basic,
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
            df = self._call_tushare_api(
                self.pro.fut_daily,
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
            df = self._call_tushare_api(
                self.pro.fund_daily,
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
            df = self._call_tushare_api(
                self.pro.opt_basic,
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

    def get_options_hedge_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        hedge_type: str = "delta"
    ) -> List[dict]:
        """获取期权对冲数据
        
        Args:
            start_date: 开始日期，格式为YYYYMMDD
            end_date: 结束日期，格式为YYYYMMDD
            hedge_type: 对冲类型，可选值为'delta'或'delta_gamma'
            
        Returns:
            期权对冲数据列表
        """
        logger.info(f"获取期权对冲数据 - 开始日期: {start_date}, 结束日期: {end_date}, 对冲类型: {hedge_type}")
        try:
            # 如果未指定日期，则默认获取最近3个月数据
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
                
            # 获取期货数据作为基础
            futures_data = self._get_futures_data(start_date, end_date, "M")
            if not futures_data:
                logger.warning("未获取到期货数据")
                return []
                
            # 将期货数据转换为DataFrame
            df_futures = pd.DataFrame([{
                'ts_code': item.ts_code,
                'trade_date': item.trade_date,
                'futures_price': item.close
            } for item in futures_data])
            
            # 模拟期权价格和希腊字母数据
            df_futures['options_price'] = df_futures['futures_price'] * 0.05  # 模拟期权价格
            
            # 根据对冲类型生成不同的希腊字母值
            if hedge_type == "delta":
                df_futures['delta'] = 0.5 + (np.random.random(len(df_futures)) - 0.5) * 0.2
                df_futures['gamma'] = 0.05 + np.random.random(len(df_futures)) * 0.05
                df_futures['theta'] = -0.02 - np.random.random(len(df_futures)) * 0.01
                df_futures['vega'] = 0.1 + np.random.random(len(df_futures)) * 0.05
                
                # 仅使用delta进行对冲
                df_futures['hedge_ratio'] = df_futures['delta']
            else:  # delta-gamma对冲
                df_futures['delta'] = 0.5 + (np.random.random(len(df_futures)) - 0.5) * 0.2
                df_futures['gamma'] = 0.05 + np.random.random(len(df_futures)) * 0.05
                df_futures['theta'] = -0.02 - np.random.random(len(df_futures)) * 0.01
                df_futures['vega'] = 0.1 + np.random.random(len(df_futures)) * 0.05
                
                # Delta-Gamma对冲考虑gamma因素
                df_futures['hedge_ratio'] = df_futures['delta'] + 0.5 * df_futures['gamma'] * df_futures['futures_price'] * 0.01
            
            # 计算P&L
            df_futures['pl'] = np.random.normal(0, 1, len(df_futures)) * 100  # 随机生成每日P&L
            
            # 计算累计P&L
            df_futures['cumulative_pl'] = df_futures['pl'].cumsum()
            
            # 生成波动率
            df_futures['volatility'] = 0.2 + np.random.random(len(df_futures)) * 0.1
            
            # 生成风险敞口
            df_futures['risk_exposure'] = df_futures['futures_price'] * (1 - df_futures['hedge_ratio']) * 0.1
            
            # 生成信号
            conditions = [
                (df_futures['delta'] > 0.6),
                (df_futures['delta'] < 0.4),
                (df_futures['delta'] >= 0.4) & (df_futures['delta'] <= 0.6)
            ]
            choices = ['increase_hedge', 'decrease_hedge', 'maintain']
            df_futures['signal'] = np.select(conditions, choices, default='maintain')
            
            # 按日期排序
            df_futures = df_futures.sort_values('trade_date')
            
            # 转换为字典列表返回
            result = df_futures.to_dict('records')
            logger.info(f"成功生成期权对冲数据，共{len(result)}条记录")
            return result
            
        except Exception as e:
            logger.error(f"获取期权对冲数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_historical_comparison_data(self, symbol: str = "M") -> List[FuturesData]:
        """获取历史同期数据"""
        try:
            logger.info(f"开始获取历史同期数据 - 品种: {symbol}")
            
            # 处理可能的无穷大或NaN值
            def safe_float(value):
                try:
                    if pd.isna(value) or np.isinf(value):
                        return 0.0
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            
            # 获取当前主力合约
            # 获取最近的交易日
            trade_cal = self._call_tushare_api(
                self.pro.trade_cal,
                exchange='DCE',
                is_open='1',
                start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d')
            )
            if trade_cal is None or trade_cal.empty:
                logger.warning(f"未找到最近的交易日")
                return []
            
            # 按日期降序排序，从最近的交易日开始查找
            trade_cal = trade_cal.sort_values('cal_date', ascending=False)
            
            # 尝试查找最近5个交易日的主力合约
            main_contract = None
            latest_trade_date = None
            
            for _, row in trade_cal.head(5).iterrows():
                current_date = row['cal_date']
                logger.info(f"尝试获取{current_date}的主力合约")
                
                temp_main_contract = self._call_tushare_api(
                    self.pro.fut_mapping,
                    ts_code=symbol+'.DCE',
                    trade_date=current_date
                )
                
                if temp_main_contract is not None and not temp_main_contract.empty:
                    main_contract = temp_main_contract
                    latest_trade_date = current_date
                    logger.info(f"在{current_date}找到主力合约")
                    break
                else:
                    logger.warning(f"在{current_date}未找到主力合约")
            
            if main_contract is None or main_contract.empty:
                logger.warning(f"在最近5个交易日未找到主力合约 - 品种: {symbol}")
                return []
            
            current_contract = main_contract.iloc[0]['mapping_ts_code'].split('.')[0]  # 去掉.DCE后缀
            logger.info(f"当前主力合约: {current_contract}")
            
            # 从合约代码中提取年份和月份部分（例如从M2509提取25和09）
            contract_year = current_contract[-4:-2]  # 提取年份，如"25"
            contract_month = current_contract[-2:]   # 提取月份，如"09"
            
            # 获取过去10年的同期合约数据
            historical_data = []
            current_year = int(contract_year)  # 使用当前合约的年份作为基准
            
            # 获取当前合约的数据作为参考
            current_contract_info = self._call_tushare_api(
                self.pro.fut_basic,
                ts_code=f"{current_contract}.DCE",
                exchange='DCE'
            )
            
            if current_contract_info is None or current_contract_info.empty:
                logger.warning(f"未找到当前合约信息: {current_contract}")
                return []
                
            # 计算当前合约已上市的天数
            current_list_date = current_contract_info.iloc[0]['list_date']
            days_listed = (datetime.strptime(latest_trade_date, '%Y%m%d') - 
                         datetime.strptime(current_list_date, '%Y%m%d')).days
            
            for year in range(current_year - 10, current_year + 1):
                # 构建历史合约代码（例如M2409、M2309等）
                year_str = str(year)[-2:]  # 取年份的后两位
                historical_contract = f"{symbol}{year_str}{contract_month}"
                logger.info(f"获取历史合约数据: {historical_contract}")
                
                try:
                    # 获取合约基本信息
                    contract_info = self._call_tushare_api(
                        self.pro.fut_basic,
                        ts_code=f"{historical_contract}.DCE",
                        exchange='DCE'
                    )
                    
                    if contract_info is not None and not contract_info.empty:
                        # 获取合约的实际交易日期范围
                        start_date = contract_info.iloc[0]['list_date']
                        end_date = contract_info.iloc[0]['delist_date']
                        if not end_date:  # 如果是当前合约
                            end_date = latest_trade_date
                            
                        # 计算开始日期：从退市日期往前推days_listed天
                        if end_date:
                            start_date = (datetime.strptime(end_date, '%Y%m%d') - 
                                        timedelta(days=365)).strftime('%Y%m%d')
                            
                        logger.info(f"合约 {historical_contract} 交易期间: {start_date} - {end_date}")
                        
                        # 获取该合约的历史数据
                        df = self._call_tushare_api(
                            self.pro.fut_daily,
                            ts_code=f"{historical_contract}.DCE",
                            start_date=start_date,
                            end_date=end_date
                        )
                        
                        if df is not None and not df.empty:
                            # 过滤掉无效数据（价格为0的数据点）
                            df = df[df['close'] > 0]
                            
                            if not df.empty:
                                # 获取最新的价格数据
                                latest_data = df.iloc[-1]
                                
                                # 构建合约数据
                                contract_data = {
                                    'ts_code': f"{historical_contract}.DCE",
                                    'trade_date': latest_data['trade_date'],
                                    'pre_close': safe_float(latest_data['pre_close']),
                                    'pre_settle': safe_float(latest_data['pre_settle']),
                                    'open': safe_float(latest_data['open']),
                                    'high': safe_float(latest_data['high']),
                                    'low': safe_float(latest_data['low']),
                                    'close': safe_float(latest_data['close']),
                                    'settle': safe_float(latest_data['settle']),
                                    'change1': safe_float(latest_data['change1']),
                                    'change2': safe_float(latest_data['change2']),
                                    'vol': safe_float(latest_data['vol']),
                                    'amount': safe_float(latest_data['amount']),
                                    'oi': safe_float(latest_data['oi']),
                                    'oi_chg': safe_float(latest_data['oi_chg']),
                                    'contract': historical_contract,
                                    'price': safe_float(latest_data['close']),
                                    'historicalPrices': []
                                }
                                
                                # 添加历史价格数据
                                for _, row in df.iterrows():
                                    # 过滤日期：只保留10月到8月的数据
                                    trade_month = int(row['trade_date'][4:6])  # 获取月份
                                    if 1 <= trade_month <= 8 or trade_month >= 10:  # 只保留1-8月和10-12月的数据
                                        price_data = {
                                            'date': row['trade_date'],
                                            'open': safe_float(row['open']),
                                            'high': safe_float(row['high']),
                                            'low': safe_float(row['low']),
                                            'close': safe_float(row['close']),
                                            'volume': safe_float(row['vol']),
                                            'contract': historical_contract
                                        }
                                        contract_data['historicalPrices'].append(price_data)
                                
                                # 只有当有历史价格数据时才添加到结果中
                                if contract_data['historicalPrices']:
                                    historical_data.append(FuturesData(**contract_data))
                    else:
                        logger.warning(f"未找到合约信息: {historical_contract}")
                        
                except Exception as e:
                    logger.error(f"获取合约 {historical_contract} 数据失败: {str(e)}")
                    continue
            
            logger.info(f"成功获取历史同期数据，共{len(historical_data)}个合约")
            return historical_data
            
        except Exception as e:
            logger.error(f"获取历史同期数据失败: {str(e)}")
            raise

    def get_monthly_probability_data(self, symbol: str = "M") -> dict:
        """获取历史月度涨跌概率数据，按01、05、09三个月度合约分别计算"""
        try:
            logger.info(f"开始获取历史月度涨跌概率数据 - 品种: {symbol}")
            
            # 定义要分析的月度合约
            monthly_contracts = ['01', '05', '09']
            result = {}
            
            # 获取当前文件的绝对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            daily_data_dir = os.path.join(current_dir, '..', 'daily_data')
            
            # 确保目录存在
            if not os.path.exists(daily_data_dir):
                logger.error(f"目录不存在: {daily_data_dir}")
                return {}
                
            logger.info(f"查找目录: {daily_data_dir}")
            
            # 获取所有合约文件
            all_files = os.listdir(daily_data_dir)
            logger.info(f"目录内容: {all_files}")
            
            # 按月份分组处理文件
            for month in monthly_contracts:
                # 存储该月份合约的结果，使用 M01、M05、M09 格式
                contract_key = f'{symbol}{month}'  # 例如：M01、M05、M09
                logger.info(f"处理{month}月合约数据， contract_key: {contract_key}")
                
                # 筛选该月份的合约文件
                contract_files = []
                for file in all_files:
                    if (file.startswith(f'{symbol}') and 
                        file.endswith('.DCE_future_daily_20100101_20251231.csv')):
                        # 从文件名中提取月份（例如从M2401.DCE_future_daily_20100101_20251231.csv中提取01）
                        file_month = file[3:5]
                        logger.info(f"检查文件: {file}, 提取的月份: {file_month}, 目标月份: {month}")
                        if file_month == month:
                            contract_files.append(file)
                
                logger.info(f"找到的{month}月合约文件: {contract_files}")
                
                if not contract_files:
                    logger.warning(f"未找到{month}月合约数据")
                    continue
                
                # 读取并合并所有合约数据
                all_data = []
                for file in contract_files:
                    try:
                        file_path = os.path.join(daily_data_dir, file)
                        logger.info(f"读取文件: {file_path}")
                        df = pd.read_csv(file_path)
                        logger.info(f"文件 {file} 数据形状: {df.shape}")
                        logger.info(f"文件 {file} 列名: {df.columns.tolist()}")
                        
                        # 添加合约信息
                        contract = file.split('.')[0]  # 例如：M2401
                        df['contract'] = contract
                        
                        # 转换日期格式
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                        df['year'] = df['date'].dt.year
                        df['month'] = df['date'].dt.month
                        
                        # 根据合约月份过滤数据
                        contract_year = int(contract[1:3])  # 例如从M2401提取24
                        contract_month = int(contract[3:])  # 例如从M2401提取01
                        
                        # 将两位数年份转换为四位数
                        if contract_year < 50:  # 假设20xx年
                            full_year = 2000 + contract_year
                        else:  # 假设19xx年
                            full_year = 1900 + contract_year
                            
                        # 计算合约的开始和结束月份
                        if contract_month == 1:  # 01合约
                            # 保留前一年2月到12月的数据
                            mask = (df['year'] == full_year - 1) & (df['month'] >= 2)
                        elif contract_month == 5:  # 05合约
                            # 保留前一年6月到12月，以及当年1月到4月的数据
                            mask = ((df['year'] == full_year - 1) & (df['month'] >= 6)) | \
                                   ((df['year'] == full_year) & (df['month'] <= 4))
                        else:  # 09合约
                            # 保留前一年10月到12月，以及当年1月到8月的数据
                            mask = ((df['year'] == full_year - 1) & (df['month'] >= 10)) | \
                                   ((df['year'] == full_year) & (df['month'] <= 8))
                        
                        # 添加调试日志
                        logger.info(f"合约 {contract} 年份: {contract_year}, 完整年份: {full_year}, 月份: {contract_month}")
                        logger.info(f"数据年份范围: {df['year'].min()} - {df['year'].max()}")
                        logger.info(f"数据月份范围: {df['month'].min()} - {df['month'].max()}")
                        logger.info(f"过滤条件: {mask.sum()} 条数据符合条件")
                        
                        # 打印每个月份的数据数量
                        month_counts = df.groupby(['year', 'month']).size()
                        logger.info(f"每月数据数量:\n{month_counts}")
                        
                        df = df[mask]
                        logger.info(f"过滤后的数据形状: {df.shape}")
                        logger.info(f"过滤后的数据示例:\n{df[['date', 'year', 'month']].head()}")
                        
                        if not df.empty:
                            all_data.append(df)
                            logger.info(f"成功添加合约 {contract} 的数据，形状: {df.shape}")
                        else:
                            logger.warning(f"合约 {contract} 过滤后没有数据")
                            
                    except Exception as e:
                        logger.error(f"读取文件{file}失败: {str(e)}")
                        continue
                
                if not all_data:
                    logger.warning(f"未能读取任何{month}月合约数据")
                    continue
                
                # 合并所有合约数据
                combined_df = pd.concat(all_data, ignore_index=True)
                logger.info(f"合并后的数据形状: {combined_df.shape}")
                
                if combined_df.empty:
                    logger.warning(f"合并后的数据为空")
                    continue
                
                # 计算每日涨跌标志
                combined_df['daily_change'] = np.where(combined_df['close'] > combined_df['open'], 1, 0)
                
                # 计算月内波动率
                combined_df['volatility'] = (combined_df['high'] - combined_df['low']) / combined_df['close']
                
                # 创建热力图数据 - 按合约名称和月份组织
                heatmap_data = {}
                
                # 获取所有合约
                contracts = combined_df['contract'].unique()
                logger.info(f"找到的合约: {contracts}")
                
                # 对每个合约计算月度统计
                for contract in contracts:
                    contract_data = combined_df[combined_df['contract'] == contract]
                    logger.info(f"处理合约 {contract} 的数据，形状: {contract_data.shape}")
                    
                    # 计算该合约每个月的统计
                    monthly_stats = contract_data.groupby('month').agg({
                        'daily_change': ['sum', 'count'],
                        'volatility': 'mean'
                    }).reset_index()
                    
                    # 重命名列
                    monthly_stats.columns = ['month', 'up_days', 'total_days', 'avg_volatility']
                    
                    # 计算上涨概率和标准差
                    monthly_stats['up_prob'] = monthly_stats['up_days'] / monthly_stats['total_days']
                    monthly_stats['std'] = np.sqrt(monthly_stats['up_prob'] * (1 - monthly_stats['up_prob']) / monthly_stats['total_days'])
                    
                    # 存储到热力图数据中
                    heatmap_data[contract] = {}
                    for _, row in monthly_stats.iterrows():
                        month = int(row['month'])
                        stats = {
                            'up_days': int(row['up_days']),
                            'total_days': int(row['total_days']),
                            'up_prob': float(row['up_prob']),
                            'std': float(row['std']),
                            'avg_volatility': float(row['avg_volatility'])
                        }
                        heatmap_data[contract][month] = stats
                        logger.info(f"添加热力图数据: 合约={contract}, 月份={month}, 统计={stats}")
                
                # 计算每个月份的平均统计
                monthly_avg_stats = []
                for m in range(1, 13):
                    month_data = combined_df[combined_df['month'] == m]
                    if not month_data.empty:
                        up_days = int(month_data['daily_change'].sum())
                        total_days = int(len(month_data))
                        up_prob = float(up_days / total_days)
                        std = float(np.sqrt(up_prob * (1 - up_prob) / total_days))
                        avg_volatility = float(month_data['volatility'].mean())
                        
                        monthly_avg_stats.append({
                            'month': m,
                            'up_days': up_days,
                            'total_days': total_days,
                            'up_prob': up_prob,
                            'std': std,
                            'avg_volatility': avg_volatility
                        })
                        logger.info(f"月份{m}统计: 上涨天数={up_days}, 总天数={total_days}, 上涨概率={up_prob:.2f}, 标准差={std:.4f}, 平均波动率={avg_volatility:.4f}")
                
                result[contract_key] = {
                    "heatmap_data": heatmap_data,
                    "monthly_avg_stats": monthly_avg_stats
                }
                # logger.info(f"存储{contract_key}合约结果: {result[contract_key]}")
            
            # 添加关键事件标注
            key_events = [
                {
                    "date": "2025-04-01",
                    "event": "中国对美关税反制",
                    "impact": "大豆进口成本上升，豆粕价格上涨"
                },
                {
                    "date": "2025-03-15",
                    "event": "USDA种植意向报告",
                    "impact": "美豆种植面积下调，远期合约价格上涨"
                },
                {
                    "date": "2024-12-01",
                    "event": "巴西大豆出口政策调整",
                    "impact": "南美大豆出口节奏变化，影响全球供应"
                },
                {
                    "date": "2024-09-01",
                    "event": "美国中西部干旱",
                    "impact": "美豆减产预期，价格大幅上涨"
                },
                {
                    "date": "2024-06-01",
                    "event": "阿根廷大豆产量恢复",
                    "impact": "南美供应增加，全球价格承压"
                },
                {
                    "date": "2024-03-01",
                    "event": "中国生猪存栏回升",
                    "impact": "豆粕需求增加，价格支撑"
                },
                {
                    "date": "2023-07-01",
                    "event": "厄尔尼诺现象",
                    "impact": "全球气候异常，影响大豆种植和产量预期"
                },
                {
                    "date": "2022-03-01",
                    "event": "俄乌冲突",
                    "impact": "全球粮食供应链中断，豆粕价格大幅上涨"
                },
                {
                    "date": "2021-05-01",
                    "event": "巴西干旱",
                    "impact": "南美大豆减产，全球供应紧张"
                },
                {
                    "date": "2020-01-01",
                    "event": "新冠疫情",
                    "impact": "全球供应链中断，豆粕价格波动加剧"
                },
                {
                    "date": "2019-08-01",
                    "event": "非洲猪瘟",
                    "impact": "中国生猪存栏大幅下降，豆粕需求减少"
                },
                {
                    "date": "2018-06-01",
                    "event": "中美贸易战",
                    "impact": "大豆进口受限，豆粕价格波动加大"
                },
                {
                    "date": "2017-03-01",
                    "event": "巴西腐败案",
                    "impact": "巴西政治动荡，影响大豆出口"
                },
                {
                    "date": "2016-06-01",
                    "event": "英国脱欧",
                    "impact": "全球金融市场动荡，大宗商品价格波动"
                },
                {
                    "date": "2015-08-01",
                    "event": "人民币贬值",
                    "impact": "进口成本上升，豆粕价格上涨"
                },
                {
                    "date": "2014-03-01",
                    "event": "克里米亚危机",
                    "impact": "地缘政治风险上升，农产品价格波动"
                },
                {
                    "date": "2013-05-01",
                    "event": "美国干旱",
                    "impact": "美豆减产，全球供应紧张"
                },
                {
                    "date": "2012-07-01",
                    "event": "美国中西部干旱",
                    "impact": "美豆产量大幅下降，价格创历史新高"
                },
                {
                    "date": "2011-03-01",
                    "event": "日本福岛核事故",
                    "impact": "全球食品安全担忧，农产品价格波动"
                },
                {
                    "date": "2010-06-01",
                    "event": "俄罗斯小麦出口禁令",
                    "impact": "全球粮食供应紧张，豆粕替代需求增加"
                },
                {
                    "date": "2009-04-01",
                    "event": "甲型H1N1流感",
                    "impact": "全球食品安全担忧，农产品价格波动"
                },
                {
                    "date": "2008-09-01",
                    "event": "全球金融危机",
                    "impact": "大宗商品价格暴跌，豆粕需求下降"
                },
                {
                    "date": "2007-08-01",
                    "event": "美国次贷危机",
                    "impact": "金融市场动荡，大宗商品价格波动"
                },
                {
                    "date": "2006-03-01",
                    "event": "禽流感疫情",
                    "impact": "养殖业受损，豆粕需求下降"
                },
                {
                    "date": "2005-08-01",
                    "event": "卡特里娜飓风",
                    "impact": "美国港口受损，影响大豆出口"
                },
                {
                    "date": "2004-12-01",
                    "event": "印度洋海啸",
                    "impact": "东南亚地区受灾，影响农产品贸易"
                }
            ]
            
            # 添加关键事件到结果中
            result['key_events'] = key_events
            
            # logger.info(f"最终返回结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"获取历史月度涨跌概率数据失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
            
    def get_event_price_data(self, event_date: str, contract: str = "M01", days_before: int = 30, days_after: int = 30) -> List[FuturesData]:
        """获取事件前后的价格走势数据
        
        Args:
            event_date: 事件日期，格式为YYYY-MM-DD
            contract: 合约代码，如M01、M05、M09
            days_before: 事件前的天数
            days_after: 事件后的天数
            
        Returns:
            事件前后的价格数据列表
        """
        try:
            logger.info(f"开始获取事件价格数据 - 事件日期: {event_date}, 合约: {contract}, 前后天数: {days_before}/{days_after}")
            
            # 获取当前文件的绝对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            daily_data_dir = os.path.join(current_dir, '..', 'daily_data')
            
            # 确保目录存在
            if not os.path.exists(daily_data_dir):
                logger.error(f"目录不存在: {daily_data_dir}")
                return []
            
            # 将事件日期转换为datetime对象
            event_date_obj = datetime.strptime(event_date, '%Y-%m-%d')
            
            # 计算日期范围
            start_date = event_date_obj - timedelta(days=days_before)
            end_date = event_date_obj + timedelta(days=days_after)
            
            # 格式化日期为YYYYMMDD格式
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            # 计算事件发生时的合约代码
            event_year = event_date_obj.year
            event_month = event_date_obj.month
            contract_month = int(contract[1:])  # 从M01中提取01
            
            # 根据事件日期和合约月份计算实际的合约代码
            # 例如：2016年6月的事件，对于M01合约，应该查找M1701
            # 合约规则：01合约在每年2月上市，05合约在每年6月上市，09合约在每年10月上市
            if contract_month == 1:  # 01合约
                if event_month >= 2:  # 2月及以后的事件，使用下一年的01合约
                    contract_year = event_year + 1
                else:  # 1月的事件，使用当年的01合约
                    contract_year = event_year
            elif contract_month == 5:  # 05合约
                if event_month >= 6:  # 6月及以后的事件，使用下一年的05合约
                    contract_year = event_year + 1
                else:  # 5月及以前的事件，使用当年的05合约
                    contract_year = event_year
            else:  # 09合约
                if event_month >= 10:  # 10月及以后的事件，使用下一年的09合约
                    contract_year = event_year + 1
                else:  # 9月及以前的事件，使用当年的09合约
                    contract_year = event_year
            
            # 构建完整的合约代码，例如M1701
            full_contract = f"{contract[0]}{str(contract_year)[-2:]}{contract[1:]}"
            logger.info(f"计算得到的合约代码: {full_contract}")
            
            # 查找匹配的合约文件
            contract_files = []
            for file in os.listdir(daily_data_dir):
                if (file.startswith(full_contract) and 
                    file.endswith('.DCE_future_daily_20100101_20251231.csv')):
                    contract_files.append(file)
            
            if not contract_files:
                logger.warning(f"未找到合约 {full_contract} 的数据文件")
                return []
            
            # 读取并合并所有合约数据
            all_data = []
            for file in contract_files:
                try:
                    file_path = os.path.join(daily_data_dir, file)
                    df = pd.read_csv(file_path)
                    
                    # 转换日期格式
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                    
                    # 过滤日期范围
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df = df[mask]
                    
                    if not df.empty:
                        all_data.append(df)
                        
                except Exception as e:
                    logger.error(f"读取文件{file}失败: {str(e)}")
                    continue
            
            if not all_data:
                logger.warning(f"未找到事件日期 {event_date} 前后的数据")
                return []
            
            # 合并所有合约数据
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # 按日期排序
            combined_df = combined_df.sort_values('date')
            
            # 转换为FuturesData列表
            result = []
            for _, row in combined_df.iterrows():
                # 处理可能的无穷大或NaN值
                def safe_float(value):
                    try:
                        if pd.isna(value) or np.isinf(value):
                            return 0.0
                        return float(value)
                    except (ValueError, TypeError):
                        return 0.0
                
                data = {
                    'ts_code': f"{full_contract}.DCE",
                    'trade_date': row['date'].strftime('%Y%m%d'),
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
                    'contract': full_contract,
                    'price': safe_float(row['close']),  # 使用收盘价作为当前价格
                    'historicalPrices': []  # 这个字段会在API层面处理
                }
                result.append(FuturesData(**data))
            
            logger.info(f"成功获取事件价格数据，共{len(result)}条记录")
            return result
            
        except Exception as e:
            logger.error(f"获取事件价格数据失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return []

    def get_realtime_arbitrage_data(self) -> dict:
        """获取实时套利数据"""
        try:
            # 获取三个品种的5分钟数据
            soybean_df = ak.futures_zh_minute_sina(symbol="B2509", period="5")  # 豆二
            meal_df = ak.futures_zh_minute_sina(symbol="M2509", period="5")     # 豆粕
            oil_df = ak.futures_zh_minute_sina(symbol="Y2509", period="5")      # 豆油

            # 重置索引，将datetime列变成普通列
            soybean_df = soybean_df.reset_index()
            meal_df = meal_df.reset_index()
            oil_df = oil_df.reset_index()

            # 确保时间对齐
            timestamps = sorted(set(soybean_df['datetime']) & set(meal_df['datetime']) & set(oil_df['datetime']))
            
            # 过滤数据
            soybean_df = soybean_df[soybean_df['datetime'].isin(timestamps)]
            meal_df = meal_df[meal_df['datetime'].isin(timestamps)]
            oil_df = oil_df[oil_df['datetime'].isin(timestamps)]
            
            # 计算油粕比
            oil_prices = oil_df['close'].values
            meal_prices = meal_df['close'].values
            oil_meal_ratio = oil_prices / meal_prices
            
            # 计算压榨利润
            soybean_prices = soybean_df['close'].values
            crushing_margin = (oil_prices * 0.18 + meal_prices * 0.8) - soybean_prices
            
            # 计算历史均值（这里用最近20个周期的均值）
            historical_average = np.mean(crushing_margin[-20:])

            return {
                "timestamps": timestamps,
                "oil_meal_ratio": {
                    "current_ratio": float(oil_meal_ratio[-1]),
                    "values": oil_meal_ratio.tolist()
                },
                "crushing_margin": {
                    "current_margin": float(crushing_margin[-1]),
                    "historical_average": float(historical_average),
                    "values": crushing_margin.tolist()
                },
                "raw_data": {
                    "soybean": soybean_prices.tolist(),
                    "meal": meal_prices.tolist(),
                    "oil": oil_prices.tolist()
                }
            }
        except Exception as e:
            logger.error(f"获取实时套利数据失败: {str(e)}")
            raise

    def get_cost_comparison_data(self) -> List[dict]:
        """获取豆粕成本和主力合约价格比较数据"""
        try:
            # 获取豆粕成本数据
            cost_df = ak.futures_hog_cost(symbol="豆粕")
            if cost_df is None or cost_df.empty:
                logger.warning("未找到豆粕成本数据")
                return []
            
            # 打印列名以便调试
            logger.info(f"成本数据数量: {len(cost_df)}")
            
            # 重命名列以匹配我们的模型
            column_mapping = {
                '日期': 'date',
                '价格': 'value'  # 假设价格列是成本价
            }
            cost_df = cost_df.rename(columns=column_mapping)
            
            # 获取主力合约数据
            futures_data = self.get_futures_data(symbol="M")
            
            if not futures_data:
                logger.warning("未找到豆粕期货数据")
                return []
            
            # 将期货数据转换为DataFrame
            futures_rows = []
            for contract_data in futures_data:
                # 遍历每个合约的历史价格数据
                if hasattr(contract_data, 'historicalPrices') and contract_data.historicalPrices:
                    for price_data in contract_data.historicalPrices:
                        futures_rows.append({
                            'date': price_data['date'],
                            'futures_price': price_data['close']
                        })
            
            futures_df = pd.DataFrame(futures_rows)
            logger.info(f"期货数据数量: {len(futures_df)}")
            
            # 统一日期格式：先转换成datetime，再转换成相同的字符串格式
            # 成本数据：yyyy-MM-dd -> datetime -> yyyyMMdd
            cost_df['date'] = pd.to_datetime(cost_df['date']).dt.strftime('%Y%m%d')
            
            # 期货数据已经是yyyyMMdd格式，但为了保证一致性，也做同样的处理
            futures_df['date'] = pd.to_datetime(futures_df['date'], format='%Y%m%d').dt.strftime('%Y%m%d')
            
            # 打印合并前的数据行数
            logger.info(f"合并前 - 成本数据行数: {len(cost_df)}, 期货数据行数: {len(futures_df)}")
            logger.info(f"成本数据日期范围: {cost_df['date'].min()} - {cost_df['date'].max()}")
            logger.info(f"期货数据日期范围: {futures_df['date'].min()} - {futures_df['date'].max()}")
            
            # 合并数据
            merged_df = pd.merge(cost_df, futures_df, on='date', how='inner')
            
            # 打印合并后的数据行数和示例
            logger.info(f"合并后数据行数: {len(merged_df)}")
            logger.info(f"合并后数据示例:\n{merged_df.head()}")
            
            # 计算价差和价格比
            merged_df['price_diff'] = merged_df['value'] - merged_df['futures_price']
            merged_df['price_ratio'] = merged_df['value'] / merged_df['futures_price']
            
            # 按日期排序
            merged_df = merged_df.sort_values('date')
            
            # 转换为列表
            result = []
            for _, row in merged_df.iterrows():
                result.append({
                    'date': row['date'],
                    'cost': float(row['value']),
                    'futures_price': float(row['futures_price']),
                    'price_diff': float(row['price_diff']),
                    'price_ratio': float(row['price_ratio'])
                })
            
            logger.info(f"最终结果数量: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取成本比较数据失败: {str(e)}")
            # 打印完整的错误堆栈以便调试
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return [] 

    def get_price_range_analysis(self, contract: str) -> PriceRangeAnalysis:
        try:
            # 获取当前日期
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            # 根据合约类型生成实际合约代码列表
            contract_type = contract[-2:]  # 获取月份部分 (01/05/09)
            contract_codes = []
            
            # 根据当前月份确定是否需要使用下一年的合约
            next_year = False
            if (contract_type == "01" and current_month > 1) or \
               (contract_type == "05" and current_month > 5) or \
               (contract_type == "09" and current_month > 9):
                next_year = True
            
            # 从当前年份往前推15年
            start_year = current_year + (1 if next_year else 0)
            for year in range(start_year, start_year - 15, -1):
                contract_code = f"M{str(year)[-2:]}{contract_type}.DCE"  # 添加.DCE后缀
                contract_codes.append(contract_code)
            
            # 获取所有合约的数据
            all_data = []
            for code in contract_codes:
                try:
                    data = self._get_futures_data(symbol=code)
                    if data:
                        all_data.extend(data)
                except Exception as e:
                    logger.error(f"获取{code}数据失败: {str(e)}")
                    continue
            
            if not all_data:
                raise ValueError("未获取到任何期货数据")
            
            # 转换为DataFrame
            df = pd.DataFrame([d.dict() for d in all_data])
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date')
            
            # 计算历史底部区域
            historical_bottoms = []
            
            # 按合约分组处理数据
            contract_groups = df.groupby('ts_code')
            
            for contract_code, contract_df in contract_groups:
                # 确保数据按日期排序
                contract_df = contract_df.sort_values('trade_date').reset_index(drop=True)
                
                # 只处理有足够数据的合约（至少有60个交易日的数据）
                if len(contract_df) < 60:
                    continue
                
                # 过滤掉价格为0或异常的数据
                valid_df = contract_df[contract_df['low'] > 0]
                if len(valid_df) < 60:  # 确保过滤后仍有足够数据
                    continue
                
                # 根据合约类型剔除特定月份的数据
                contract_month = contract_code.split('.')[0][-2:]  # 获取合约月份部分
                if contract_month == "01":
                    # 剔除1月份的数据
                    valid_df = valid_df[valid_df['trade_date'].dt.month != 1]
                elif contract_month == "05":
                    # 剔除5月份的数据
                    valid_df = valid_df[valid_df['trade_date'].dt.month != 5]
                elif contract_month == "09":
                    # 剔除9月份的数据
                    valid_df = valid_df[valid_df['trade_date'].dt.month != 9]
                
                # 再次检查数据量是否足够
                if len(valid_df) < 60:
                    continue
                
                # 重置索引，确保索引连续
                valid_df = valid_df.reset_index(drop=True)
                
                # 找出合约周期内的最低价格
                min_price_idx = valid_df['low'].idxmin()
                min_price = valid_df['low'].iloc[min_price_idx]
                min_price_date = valid_df['trade_date'].iloc[min_price_idx]
                
                # 确定底部区域的开始和结束日期（最低价前后30个交易日）
                start_idx = max(0, min_price_idx - 30)
                end_idx = min(len(valid_df) - 1, min_price_idx + 30)
                
                # 计算底部区域的持续时间
                duration = int(end_idx - start_idx + 1)  # 确保是int类型
                
                # 计算反弹幅度（使用底部区域之后的20个交易日的最高价）
                bounce_amplitude = 0
                if end_idx + 20 < len(valid_df):
                    max_price_after = valid_df['high'].iloc[end_idx+1:end_idx+21].max()
                    bounce_amplitude = (max_price_after - min_price) / min_price * 100
                else:
                    # 如果后续数据不足20个交易日，则使用所有可用的后续数据
                    if end_idx + 1 < len(valid_df):
                        max_price_after = valid_df['high'].iloc[end_idx+1:].max()
                        bounce_amplitude = (max_price_after - min_price) / min_price * 100
                    # 如果没有后续数据，则使用底部区域内的最高价作为反弹目标
                    else:
                        max_price_in_bottom = valid_df['high'].iloc[start_idx:end_idx+1].max()
                        if max_price_in_bottom > min_price:  # 确保底部区域内有高于最低价的价格
                            bounce_amplitude = (max_price_in_bottom - min_price) / min_price * 100
                
                # 获取完整的K线数据
                kline_data = []
                for _, row in valid_df.iterrows():
                    kline_data.append(KlineData(
                        trade_date=row['trade_date'].strftime('%Y%m%d'),
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        vol=float(row['vol'])
                    ))
                
                # 使用HistoricalBottom模型创建底部记录
                historical_bottom = HistoricalBottom(
                    start_date=valid_df['trade_date'].iloc[start_idx].strftime("%Y%m%d"),
                    end_date=valid_df['trade_date'].iloc[end_idx].strftime("%Y%m%d"),
                    duration=int(duration),
                    bounce_amplitude=float(bounce_amplitude),
                    lowest_price=float(min_price),
                    contract=str(contract_code.split('.')[0]),
                    kline_data=kline_data
                )
                
                historical_bottoms.append(historical_bottom)
                logger.info(f"找到合约 {contract_code} 的底部区域: 最低价 {min_price} 出现在 {min_price_date.strftime('%Y-%m-%d')}")
            
            if not historical_bottoms:
                raise ValueError("未找到历史底部区域")
            
            # 计算统计数据 - 历史底部最低价是所有合约的最低价
            bottom_price = min([b.lowest_price for b in historical_bottoms])
            bottom_range_end = bottom_price * 1.2
            
            # 计算反弹成功率
            successful_bounces = sum(1 for b in historical_bottoms if b.bounce_amplitude > 5)  # 反弹超过5%视为成功
            bounce_success_rate = (successful_bounces / len(historical_bottoms)) * 100 if historical_bottoms else 0
            
            # 计算平均反弹幅度和平均持续时间
            avg_bounce_amplitude = sum(b.bounce_amplitude for b in historical_bottoms) / len(historical_bottoms) if historical_bottoms else 0
            avg_bottom_duration = sum(b.duration for b in historical_bottoms) / len(historical_bottoms) if historical_bottoms else 0
            
            # 获取当前价格 (使用最新合约的收盘价)
            # 确保数据有效且排序正确
            valid_price_df = df[df['close'] > 0].sort_values('trade_date')
            if len(valid_price_df) == 0:
                raise ValueError("没有有效的价格数据")
                
            latest_contract_data = valid_price_df.iloc[-1]
            current_price = float(latest_contract_data['close'])
            
            # 计算每个合约的价格统计
            contract_stats = []
            all_prices = []  # 收集所有价格用于计算分位数
            all_volatilities = []  # 收集所有波动率用于计算分位数
            
            for contract_code, contract_df in contract_groups:
                # 确保数据按日期排序
                contract_df = contract_df.sort_values('trade_date').reset_index(drop=True)
                
                # 只处理有足够数据的合约（至少有60个交易日的数据）
                if len(contract_df) < 60:
                    continue
                
                # 过滤掉价格为0或异常的数据
                valid_df = contract_df[contract_df['low'] > 0]
                if len(valid_df) < 60:  # 确保过滤后仍有足够数据
                    continue

                # 计算30日波动率
                returns = valid_df['close'].pct_change()
                volatility_series = returns.rolling(window=30).std()
                volatility_30d = float(volatility_series.iloc[-1] if not volatility_series.empty else 0) * np.sqrt(252) * 100
                
                # 收集所有价格和波动率数据
                all_prices.extend([float(x) for x in valid_df['close'].values])
                all_volatilities.extend([float(x) for x in volatility_series.dropna().values])

                # 计算统计数据
                contract_stat = ContractStats(
                    contract=str(contract_code.split('.')[0]),  # 去掉.DCE后缀
                    lowest_price=float(valid_df['low'].min()),
                    highest_price=float(valid_df['high'].max()),
                    price_range=float(valid_df['high'].max() - valid_df['low'].min()),
                    start_price=float(valid_df['open'].iloc[0]),
                    end_price=float(valid_df['close'].iloc[-1]),
                    volatility_30d=volatility_30d,
                    quantile_coef=float(valid_df['low'].min()) / float(valid_df['open'].iloc[0]),  # 分位系数计算
                    standardized_value=0.0  # 初始化为0，后面会更新
                )
                contract_stats.append(contract_stat)

            # 按合约代码排序
            contract_stats.sort(key=lambda x: x.contract)
            
            # 计算价格分位数
            price_quartiles = {
                'q1': float(np.percentile(all_prices, 25)),
                'q2': float(np.percentile(all_prices, 50)),
                'q3': float(np.percentile(all_prices, 75))
            }
            
            # 计算波动率分位数
            volatility_quartiles = {
                'q1': float(np.percentile(all_volatilities, 25)),
                'q2': float(np.percentile(all_volatilities, 50)),
                'q3': float(np.percentile(all_volatilities, 75))
            }

            # 计算标准化指标
            historical_min = min(stat.lowest_price for stat in contract_stats)
            historical_max = max(stat.highest_price for stat in contract_stats)
            
            self.logger.info(f"历史最低价: {historical_min}, 历史最高价: {historical_max}")
            
            for stat in contract_stats:
                if historical_max != historical_min:  # 避免除以零
                    stat.standardized_value = (stat.end_price - historical_min) / (historical_max - historical_min)
                    self.logger.debug(f"合约 {stat.contract} 标准化值: {stat.standardized_value:.4f}, 结束价: {stat.end_price}")
                else:
                    stat.standardized_value = 0.0
                    self.logger.warning(f"历史最高价等于最低价，合约 {stat.contract} 标准化值设为0")

            # 计算低点预测
            if not contract_stats:
                self.logger.warning(f"没有找到任何合约统计数据")
                return PriceRangeAnalysis(
                    bottom_price=0.0,
                    current_price=0.0,
                    bottom_range_start=0.0,
                    bottom_range_end=0.0,
                    bounce_success_rate=0.0,
                    avg_bounce_amplitude=0.0,
                    avg_bottom_duration=0.0,
                    historical_bottoms=[],
                    contract_stats=[],
                    price_quartiles={'q1': 0.0, 'q2': 0.0, 'q3': 0.0},
                    volatility_quartiles={'q1': 0.0, 'q2': 0.0, 'q3': 0.0},
                    predicted_low={
                        'base': 0.0,
                        'lower': 0.0,
                        'upper': 0.0,
                        'confidence': 0.0,
                        'factors': {
                            'supply_pressure': 0.0,
                            'policy_risk': 0.0,
                            'basis_impact': 0.0
                        }
                    }
                )

            # 修改合约匹配逻辑
            month = contract[1:3]  # 获取月份部分 (01, 05, 09)
            matching_stats = [s for s in contract_stats if s.contract.endswith(month)]
            self.logger.info(f"为合约 {contract} 查找匹配的月份 {month}, 找到 {len(matching_stats)} 个匹配合约")
            
            if not matching_stats:
                self.logger.warning(f"没有找到匹配的合约统计数据: {contract}")
                current_stat = contract_stats[0]  # 使用第一个合约的数据
                self.logger.info(f"使用默认合约 {current_stat.contract} 的数据进行预测")
            else:
                current_stat = matching_stats[-1]  # 使用最新的匹配合约
                self.logger.info(f"使用匹配合约 {current_stat.contract} 的数据进行预测")

            # 计算平均分位系数作为基础系数
            base_coef = sum(stat.quantile_coef for stat in matching_stats) / len(matching_stats) if matching_stats else 0.8
            self.logger.info(f"计算得到的平均分位系数: {base_coef:.2f}")
            
            base_prediction = current_stat.start_price * base_coef
            self.logger.info(f"基础预测: {base_prediction:.2f}, 开始价格: {current_stat.start_price}, 基础系数: {base_coef:.2f}")
            
            # 根据合约类型调整修正因子
            supply_pressure = -0.05 if contract[1:3] == '05' else (-0.1 if contract[1:3] == '01' else 0)  # 5月合约供应压力，1月合约设为0.1
            policy_risk = 0.03 if contract[1:3] == '09' else 0  # 9月合约政策风险
            self.logger.info(f"合约调整因子 - 供应压力: {supply_pressure:.2f}, 政策风险: {policy_risk:.2f}")
            
            predicted_low = {
                'base': round(base_prediction, 0),
                'lower': round(base_prediction * (1 + supply_pressure), 0),
                'upper': round(base_prediction * (1 + policy_risk), 0),
                'confidence': round(0.8 - abs(supply_pressure) - abs(policy_risk), 2),  # 置信度随修正幅度降低
                'factors': {
                    'supply_pressure': round(abs(supply_pressure) if supply_pressure < 0 else 0, 2),  # 转换为正值表示压力
                    'policy_risk': round(abs(policy_risk) if policy_risk > 0 else 0, 2),  # 保持正值表示风险
                    'basis_impact': round(abs(1 - base_coef) if base_coef < 1 else 0, 2)  # 基差影响用分位系数偏离度表示
                }
            }
            self.logger.info(f"预测低点 - 基础: {predicted_low['base']}, 下限: {predicted_low['lower']}, 上限: {predicted_low['upper']}, 置信度: {predicted_low['confidence']}")

            return PriceRangeAnalysis(
                bottom_price=float(bottom_price),
                current_price=float(current_price),
                bottom_range_start=float(bottom_price),
                bottom_range_end=float(bottom_range_end),
                bounce_success_rate=float(bounce_success_rate),
                avg_bounce_amplitude=float(avg_bounce_amplitude),
                avg_bottom_duration=int(avg_bottom_duration),
                historical_bottoms=historical_bottoms,
                contract_stats=contract_stats,
                price_quartiles=price_quartiles,
                volatility_quartiles=volatility_quartiles,
                predicted_low=predicted_low
            )
            
        except Exception as e:
            logger.error(f"计算价格区间分析失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise