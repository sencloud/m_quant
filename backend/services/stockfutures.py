import time
import tushare as ts
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np
from config import settings
from utils.logger import logger
from services.support_resistance import SupportResistanceService
import akshare as ak

class StockFuturesService:
    """股票期货联动服务"""
    
    def __init__(self):
        """初始化服务"""
        try:
            self.token = settings.TUSHARE_TOKEN
            if not self.token:
                logger.error("未找到 TUSHARE_TOKEN，请在 .env 文件中设置")
                self.pro = None
            else:
                ts.set_token(self.token)
                try:
                    self.pro = ts.pro_api()
                    # 测试连接
                    self.pro.query('stock_basic', limit=1)
                    logger.info("股票期货联动服务初始化完成")
                except Exception as e:
                    logger.error(f"Tushare API 连接失败: {e}")
                    self.pro = None
            # 初始化支撑阻力服务
            self.sr_service = SupportResistanceService()
        except Exception as e:
            logger.error(f"股票期货联动服务初始化失败: {e}")
            self.pro = None

    def get_hs300_stocks(self) -> List[Dict[str, Any]]:
        """
        获取沪深300成分股列表
        
        Returns:
            成分股列表，包含股票代码、名称等信息
        """
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取沪深300成分股")
                return []
            
            # 获取沪深300成分股
            df = self.pro.index_weight(
                index_code='399300.SZ'
            )
            
            if df is None or df.empty:
                logger.warning("获取沪深300成分股为空")
                return []
            
            # 获取成分股的基本信息
            stocks_info = []
            # 批量获取股票代码列表
            stock_codes = list(set(df['con_code'].tolist()))
            logger.info(f"沪深300成分股股票代码个数: {len(stock_codes)}")
            
            # 分批处理，每批次最多处理20个股票，避免超过API访问限制
            batch_size = 20
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i+batch_size]
                
                # 使用逗号分隔的字符串传递多个股票代码
                codes_str = ','.join(batch_codes)
                try:
                    stock_info_batch = self.pro.stock_basic(
                        ts_code=codes_str,
                        fields='ts_code,symbol,name,area,industry,market,list_date'
                    )
                    
                    if not stock_info_batch.empty:
                        for _, stock in stock_info_batch.iterrows():
                            stocks_info.append(stock.to_dict())
                    
                    # 添加延时，避免触发频率限制
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"批量获取股票基本信息失败: {e}")
                
            # 如果stocks_info为空，记录警告
            if not stocks_info:
                logger.warning("未能获取任何沪深300成分股的基本信息")
            
            logger.info(f"成功获取沪深300成分股信息，共{len(stocks_info)}条记录")
            return stocks_info
        except Exception as e:
            logger.error(f"获取沪深300成分股失败: {e}")
            return []

    def get_stock_daily(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期，默认为前60个交易日
            end_date: 结束日期，默认为当前日期
            
        Returns:
            股票日线数据DataFrame
        """
        try:
            if self.pro is None:
                logger.error("Tushare API 未初始化，无法获取股票日线数据")
                return pd.DataFrame()
            
            # 设置默认日期范围
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
            
            # 获取日线数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                logger.warning(f"获取股票{ts_code}日线数据为空")
                return pd.DataFrame()
            
            # 按日期升序排序
            df = df.sort_values('trade_date')
            
            return df
        except Exception as e:
            logger.error(f"获取股票{ts_code}日线数据失败: {e}")
            return pd.DataFrame()

    def get_hourly_data(self, symbol: str) -> pd.DataFrame:
        """
        获取股票小时级别行情数据
        
        Args:
            symbol: 股票代码（不带市场标识）
            
        Returns:
            小时级别行情数据DataFrame
        """
        try:
            # 将tushare格式的代码转换为akshare格式
            market = 'sh' if symbol.startswith('6') else 'sz'
            ak_symbol = f"{market}{symbol}"
            
            # 获取小时行情数据
            try:
                df = ak.stock_zh_a_minute(symbol=ak_symbol, period='60')
                logger.info(f"获取股票{ak_symbol}小时行情数据成功")
                if df is None or df.empty:
                    logger.warning(f"获取股票{ak_symbol}小时行情数据为空")
                    return pd.DataFrame()
            except IndexError:
                logger.warning(f"获取股票{ak_symbol}小时行情数据时发生索引错误，可能是接口返回格式变更")
                import traceback
                traceback.print_exc()
                return pd.DataFrame()
            
            # 确保价格字段为数值类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
            
            # 重命名列以匹配support_resistance服务的要求
            df = df.rename(columns={
                'day': 'date'
            })
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            
            # 确保所有必需的列都存在
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"小时行情数据缺少必需的列: {missing_columns}")
                return pd.DataFrame()
            
            # 删除任何包含NaN的行
            df = df.dropna(subset=['open', 'high', 'low', 'close'])
            
            if df.empty:
                logger.warning(f"处理后的小时行情数据为空")
                return pd.DataFrame()
            
            logger.info(f"成功处理小时行情数据，数据形状: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"获取股票{symbol}小时行情数据失败: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def find_stocks_near_support(self, threshold_percent: float = 0.03) -> List[Dict[str, Any]]:
        """
        找出最新价格在支撑位附近的股票
        
        Args:
            threshold_percent: 价格与支撑位的阈值百分比，默认3%
            
        Returns:
            符合条件的股票列表
        """
        try:
            # 获取沪深300成分股
            stocks = self.get_hs300_stocks()
            if not stocks:
                return []
            
            # 第一次筛选 - 日线级别
            daily_results = []
            for stock in stocks:
                try:
                    # 获取股票日线数据
                    logger.info(f"获取股票{stock['ts_code']}日线数据")
                    df = self.get_stock_daily(stock['ts_code'])
                    if df.empty:
                        continue
                    
                    # 将trade_date列重命名为date，以匹配support_resistance服务的要求
                    df = df.rename(columns={'trade_date': 'date'})
                    
                    # 计算支撑位和压力位
                    logger.info(f"计算支撑位和压力位")
                    sr_levels = self.sr_service.get_sr_levels(df)
                    if not sr_levels:
                        continue
                    
                    # 获取最新收盘价和涨跌幅
                    logger.info(f"获取最新收盘价")
                    latest_price = df.iloc[-1]['close']
                    latest_pct_chg = df.iloc[-1]['pct_chg']
                    
                    # 找到最近的支撑位
                    logger.info(f"找到最近的支撑位")
                    support_levels = [level['price'] for level in sr_levels if level['type'] == 'Support']
                    if not support_levels:
                        continue
                    nearest_support = min(support_levels, key=lambda x: abs(x - latest_price))
                    logger.info(f"最近支撑位: {nearest_support}")
                    # 计算价格与支撑位的距离百分比
                    distance_percent = abs(latest_price - nearest_support) / latest_price
                    
                    # 如果价格在支撑位附近
                    if distance_percent <= threshold_percent:
                        daily_results.append({
                            **stock,
                            'latest_price': latest_price,
                            'pct_chg': latest_pct_chg,
                            'nearest_support': nearest_support,
                            'distance_percent': distance_percent,
                            'sr_levels': sr_levels
                        })
                except Exception as e:
                    logger.error(f"处理股票{stock['ts_code']}日线数据时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            logger.info(f"日线级别筛选找到{len(daily_results)}只股票")
            
            # 第二次筛选 - 小时级别
            hourly_results = []
            for stock in daily_results:
                try:
                    # 从ts_code中提取纯数字代码
                    symbol = stock['ts_code'].split('.')[0]
                    
                    # 获取小时行情数据
                    logger.info(f"获取股票{symbol}小时行情数据")
                    hourly_df = self.get_hourly_data(symbol)
                    if hourly_df.empty:
                        continue
                    
                    # 计算小时级别支撑位和压力位
                    logger.info(f"计算小时级别支撑位和压力位")
                    hourly_sr_levels = self.sr_service.get_sr_levels(hourly_df, timeframe='1h')
                    if not hourly_sr_levels:
                        continue
                    
                    # 获取最新价格
                    latest_hourly_price = hourly_df.iloc[-1]['close']
                    
                    # 找到最近的支撑位
                    hourly_support_levels = [level['price'] for level in hourly_sr_levels if level['type'] == 'Support']
                    if not hourly_support_levels:
                        continue
                    nearest_hourly_support = min(hourly_support_levels, key=lambda x: abs(x - latest_hourly_price))
                    
                    # 计算价格与支撑位的距离百分比
                    hourly_distance_percent = abs(latest_hourly_price - nearest_hourly_support) / latest_hourly_price
                    
                    # 添加小时级别的信息
                    hourly_results.append({
                        **stock,
                        'hourly_latest_price': latest_hourly_price,
                        'hourly_nearest_support': nearest_hourly_support,
                        'hourly_distance_percent': hourly_distance_percent,
                        'hourly_sr_levels': hourly_sr_levels
                    })
                except Exception as e:
                    logger.error(f"处理股票{stock['ts_code']}小时数据时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # 按小时级别的距离百分比排序，取前10只
            hourly_results.sort(key=lambda x: x['hourly_distance_percent'])
            final_results = hourly_results[:10] if len(hourly_results) > 10 else hourly_results
            
            logger.info(f"小时级别筛选后找到{len(final_results)}只股票")
            return final_results
        except Exception as e:
            logger.error(f"查找支撑位附近的股票失败: {e}")
            return [] 