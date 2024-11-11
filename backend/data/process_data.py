import logging
from datetime import datetime, timedelta
from ..database.connection import execute_many, execute_query
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class ProcessData:
    @staticmethod
    def calculate_technical_indicators(df, is_training=False):
        """计算技术指标"""
        # 确保数据按日期排序
        df = df.sort_index()
        
        # 检查并标准化列名
        column_mapping = {
            'close': 'Close',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'volume': 'Volume',
            'trade_date': 'date'
        }
        
        # 将列名转换为小写以进行统一比较
        df.columns = df.columns.str.lower()
        
        # 应用列名映射
        df = df.rename(columns=column_mapping)
        
        # 打印列名以进行调试
        print("Columns after mapping:", df.columns.tolist())
        
        # 简单移动平均线 (SMA)
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        
        # 指数移动平均线 (EMA)
        df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # 收益率
        df['Returns'] = df['Close'].pct_change()
        
        # 动量 (10日)
        df['Momentum'] = df['Close'] - df['Close'].shift(10)
        
        # 波动率 (20日)
        df['Volatility'] = df['Returns'].rolling(window=20).std() * np.sqrt(20)
        
        # 成交量移动平均
        df['Volume_MA_5'] = df['Volume'].rolling(window=5).mean()
        df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
        
        # 添加预测目标（5天后的收盘价）
        # df['Target_5d'] = df['Close'].shift(-5)
        # 只在训练时添加目标值
        if is_training:
            df['Target_5d'] = df['Close'].shift(-5)
            # 训练时需要删除没有目标值的行
            df = df.dropna(subset=['Target_5d'])
        else:
            # 预测时填充任何缺失值
            df = df.fillna(method='ffill').fillna(0)
        
        # 删除包含NaN的行
        df = df.dropna()
        
        return df

    @staticmethod
    def get_stock_data(symbol, start_date, end_date, is_training=False):
        """Get stock data with validation and error handling"""
        try:
            # Validate dates
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if start > end:
                raise ValueError("Start date must be before end date")
            
            # Convert dates to yyyyMMdd format for database query
            start_date_db = start.strftime('%Y%m%d')
            end_date_db = end.strftime('%Y%m%d')
            
            data = execute_query('''
                SELECT date, open, high, low, close, volume
                FROM stocks
                WHERE code = ? AND date BETWEEN ? AND ?
                ORDER BY date
            ''', (symbol, start_date_db, end_date_db))  # 这里改用 symbol
            
            if not data:
                logger.warning(f"No data found for {symbol} between {start_date} and {end_date}")
                return None
            
            # Convert data to pandas DataFrame
            df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert date to datetime and set it as index
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df.set_index('date', inplace=True)
            
            # Convert numeric columns to appropriate types
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
            df['volume'] = df['volume'].astype(int)
            
            # 计算技术指标
            df = ProcessData.calculate_technical_indicators(df, is_training=is_training)
            
            # 记录获取到的数据范围
            logger.info(f"Retrieved data: from {df.index.min()} to {df.index.max()}, total points: {len(df)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing stock data: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def save_stock_data(code, data):
        """Save stock data with validation and error handling"""
        try:
            logger.info(f"Attempting to save data for {code}, received {len(data)} rows")
            
            # Convert DataFrame to list of tuples
            records = []
            for _, row in data.iterrows():
                try:
                    record = (
                        row['trade_date'],
                        code,
                        float(row['open']),
                        float(row['high']),
                        float(row['low']),
                        float(row['close']),
                        int(row['vol'])
                    )
                    records.append(record)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping row due to conversion error: {row.to_dict()}, Error: {str(e)}")
                    continue
            
            if not records:
                raise ValueError("No valid records to save")
                
            execute_many(
                'INSERT OR REPLACE INTO stocks VALUES (?,?,?,?,?,?,?)',
                records
            )
            logger.info(f"Successfully saved {len(records)} rows for {code}")
            
        except Exception as e:
            logger.error(f"Error saving stock data: {str(e)}")
            logger.error(f"First few rows of input data:\n{data.head()}")
            raise

    @staticmethod
    def get_futures_data(symbol, start_date, end_date):
        """获取期货数据"""
        try:
            query = '''
                SELECT trade_date as date, open, high, low, close, vol, oi
                FROM fut_daily
                WHERE ts_code = ? AND trade_date BETWEEN ? AND ?
                ORDER BY trade_date
            '''
            
            # 转换日期格式
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            
            # 执行查询
            data = execute_query(query, [symbol, start_date, end_date])
            
            # 转换为DataFrame
            df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'vol', 'oi'])
            
            # 处理日期列
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting futures data: {str(e)}", exc_info=True)
            raise
