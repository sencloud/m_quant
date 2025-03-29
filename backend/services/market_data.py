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

    def _get_futures_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, symbol: str = "M") -> Optional[pd.DataFrame]:
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
                    return None
                
                # 获取小于等于请求结束日期的最后一个交易日
                trade_cal = trade_cal[trade_cal['cal_date'] <= (end_date if end_date else datetime.now().strftime('%Y%m%d'))]
                if trade_cal.empty:
                    logger.warning(f"未找到小于等于{end_date}的交易日")
                    return None
                    
                latest_trade_date = trade_cal.iloc[0]['cal_date']
                logger.info(f"最近的交易日: {latest_trade_date}")
                
                # 获取主力合约
                main_contract = self.pro.fut_mapping(
                    ts_code=symbol+'.DCE',
                    trade_date=latest_trade_date
                )
                logger.info(f"主力合约查询结果: \n{main_contract}")
                
                if main_contract is None or main_contract.empty:
                    logger.warning(f"未找到主力合约 - 品种: {symbol}, 日期: {latest_trade_date}")
                    return None
                symbol = main_contract.iloc[0]['mapping_ts_code']
                logger.info(f"获取到主力合约: {symbol}")
            
            # 获取合约基本信息
            contract_info = self.pro.fut_basic(
                ts_code=symbol,
                exchange='DCE'
            )
            if contract_info is None or contract_info.empty:
                logger.warning(f"未找到合约信息: {symbol}")
                return None
                
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
                return None
            
            logger.info(f"成功获取期货数据，共{len(df)}条记录")
            logger.info(f"数据示例: \n{df.head()}")
            
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
            
            # 处理缺失值和异常值
            df = df.fillna(method='ffill').fillna(method='bfill')
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            logger.info(f"数据处理完成，最终数据示例: \n{df.head()}")
            return df
            
        except Exception as e:
            logger.error(f"获取期货数据失败: {str(e)}", exc_info=True)
            return None

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
            # 获取主力合约数据
            df = self._get_futures_data(start_date, end_date, symbol)
            if df is None or df.empty:
                return []
            
            # 按时间排序
            df = df.sort_values('trade_date')
            
            # 转换为模型格式
            return [
                FuturesData(
                    ts_code=symbol,
                    trade_date=row['trade_date'],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    vol=float(row['vol']),
                    change1=float(row['change1']),
                    amount=float(row['amount'])
                )
                for _, row in df.iterrows()
            ]
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
                    ts_code=row['contract'],
                    trade_date=row['trade_date'],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    vol=float(row['vol']),
                    change1=float(row['change1']),
                    amount=float(row['amount'])
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