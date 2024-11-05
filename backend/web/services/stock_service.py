from datetime import datetime
from backend.database.connection import execute_query
import logging
import tushare as ts
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StockService:
    @staticmethod
    def parse_date(date_str: str) -> str:
        """解析各种格式的日期字符串"""
        try:
            # 处理 URL 编码的日期格式（例如：2023-10-30+20:55）
            date_str = date_str.replace('+', ' ')
            
            # 尝试不同的日期格式
            for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y%m%d')
                except ValueError:
                    continue
            
            raise ValueError(f"Unable to parse date: {date_str}")
            
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            raise

    @staticmethod
    def get_daily_data(code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取每日股票数据"""
        try:
            start_date_formatted = StockService.parse_date(start_date)
            end_date_formatted = StockService.parse_date(end_date)

            query = '''
                SELECT date, open, high, low, close, volume
                FROM stocks
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date
            '''
            
            result = execute_query(query, (code, start_date_formatted, end_date_formatted))
            
            if not result:
                return []
                
            return StockService.format_stock_data(result)

        except Exception as e:
            logger.error(f"Error in get_daily_data: {e}")
            raise

    @staticmethod
    def get_intraday_data(code, granularity, start_date, end_date):
        """获取日内数据"""
        table = f'stocks_{granularity}'
        query = f'''
            SELECT datetime as date, open, high, low, close, volume
            FROM {table}
            WHERE code = ? AND datetime BETWEEN ? AND ?
            ORDER BY datetime
        '''
        
        return StockService.format_stock_data(
            execute_query(query, (code, start_date, end_date))
        )

    @staticmethod
    def get_available_stocks():
        """获取可用股票列表"""
        stocks = execute_query('''
            SELECT ts_code, name, area, industry
            FROM stock_basic
        ''')
        
        return [{
            'ts_code': stock[0],
            'name': stock[1],
            'area': stock[2],
            'industry': stock[3]
        } for stock in stocks]

    @staticmethod
    def format_stock_data(data: List[Tuple]) -> List[Dict]:
        """格式化股票数据"""
        if not data:
            return []

        result = []
        prev_close = None
        
        for row in data:
            date = row[0]  # 假设日期格式为 YYYYMMDD
            current_close = float(row[4])
            
            # 计算涨跌幅
            change = ((current_close - prev_close) / prev_close * 100) if prev_close else 0
            
            # 格式化日期
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            
            result.append({
                'date': formatted_date,
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': current_close,
                'volume': int(row[5]),
                'change': round(change, 2)
            })
            
            prev_close = current_close

        return result

    @staticmethod
    def get_grouped_stocks():
        """获取按交易所和行业分组的股票列表"""
        try:
            stocks = execute_query('''
                SELECT DISTINCT s.code, sb.name, sb.industry
                FROM stocks s
                JOIN stock_basic sb ON s.code = sb.ts_code
                ORDER BY s.code, sb.industry, sb.name
            ''')

            # Group stocks by exchange and industry
            grouped_stocks = {}
            for stock in stocks:
                code, name, industry = stock
                # 根据股票代码后缀判断交易所
                exchange = 'SH' if code.endswith('.SH') else 'SZ' if code.endswith('.SZ') else 'BJ'

                # 初始化交易所分组
                if exchange not in grouped_stocks:
                    grouped_stocks[exchange] = {}

                # 处理空行业情况
                industry = industry or 'Unknown'

                # 初始化行业分组
                if industry not in grouped_stocks[exchange]:
                    grouped_stocks[exchange][industry] = []

                # 添加股票信息
                grouped_stocks[exchange][industry].append({
                    'code': code,
                    'name': name
                })

            return grouped_stocks

        except Exception as e:
            logger.error(f"Error in get_grouped_stocks: {e}")
            raise

    @staticmethod
    def calculate_technical_factors(df: pd.DataFrame) -> pd.DataFrame:
        """计算技术面因子"""
        # 计算移动平均
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # 计算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 计算波动率
        df['volatility'] = df['close'].rolling(window=20).std()
        
        return df

    @staticmethod
    def apply_factor_filter(factors: Dict, weights: Dict) -> List[Dict]:
        """应用因子筛选"""
        try:
            # 获取最新交易日期
            latest_date = execute_query(
                "SELECT MAX(trade_date) FROM daily_basic"
            )[0][0]
            
            final_df = None
            
            # 获取基本面和成交量因子
            fundamental_volume_factors = factors.get('fundamental', []) + factors.get('volume', [])
            if fundamental_volume_factors:
                factor_columns = ', '.join(fundamental_volume_factors)
                basic_query = f'''
                    SELECT ts_code, {factor_columns}
                    FROM daily_basic
                    WHERE trade_date = ?
                '''
                basic_data = execute_query(basic_query, (latest_date,))
                final_df = pd.DataFrame(
                    basic_data, 
                    columns=['ts_code'] + fundamental_volume_factors
                )
            
            # 获取技术面因子
            if factors.get('technical'):
                # 优化：只获取需要计算的股票的数据
                stock_filter = ''
                if final_df is not None:
                    stock_list = tuple(final_df['ts_code'].tolist())
                    stock_filter = f'AND code IN {stock_list}' if stock_list else ''
                
                # 优化：减少获取的历史数据时间范围
                days_needed = 60  # 根据实际需要的技术指标调整天数
                start_date = (datetime.strptime(latest_date, '%Y%m%d') - timedelta(days=days_needed)).strftime('%Y%m%d')
                
                tech_query = f'''
                    SELECT date, code as ts_code, open, high, low, close, volume
                    FROM stocks
                    WHERE date >= ? AND date <= ? {stock_filter}
                    ORDER BY code, date
                '''
                tech_data = execute_query(tech_query, (start_date, latest_date))
                
                if not tech_data:
                    return []
                    
                tech_df = pd.DataFrame(
                    tech_data, 
                    columns=['date', 'ts_code', 'open', 'high', 'low', 'close', 'volume']
                )
                
                # 优化：使用向量化操作替代 groupby
                tech_df.set_index(['date', 'ts_code'], inplace=True)
                tech_df.sort_index(inplace=True)
                
                # 计算技术因子
                grouped = tech_df.groupby('ts_code')
                
                # 优化：只计算需要的技术因子
                needed_factors = set(factors['technical'])
                tech_results = {}
                
                if 'ma5' in needed_factors:
                    tech_results['ma5'] = grouped['close'].transform(lambda x: x.rolling(5).mean())
                if 'ma10' in needed_factors:
                    tech_results['ma10'] = grouped['close'].transform(lambda x: x.rolling(10).mean())
                if 'ma20' in needed_factors:
                    tech_results['ma20'] = grouped['close'].transform(lambda x: x.rolling(20).mean())
                
                if 'macd' in needed_factors:
                    exp1 = grouped['close'].transform(lambda x: x.ewm(span=12, adjust=False).mean())
                    exp2 = grouped['close'].transform(lambda x: x.ewm(span=26, adjust=False).mean())
                    tech_results['macd'] = exp1 - exp2
                    tech_results['signal'] = tech_results['macd'].groupby('ts_code').transform(lambda x: x.ewm(span=9, adjust=False).mean())
                
                if 'rsi' in needed_factors:
                    delta = grouped['close'].transform('diff')
                    gain = delta.where(delta > 0, 0).groupby('ts_code').transform(lambda x: x.rolling(14).mean())
                    loss = (-delta.where(delta < 0, 0)).groupby('ts_code').transform(lambda x: x.rolling(14).mean())
                    rs = gain / loss
                    tech_results['rsi'] = 100 - (100 / (1 + rs))
                
                if 'volatility' in needed_factors:
                    tech_results['volatility'] = grouped['close'].transform(lambda x: x.rolling(20).std() / x.rolling(20).mean() * 100)
                
                # 合并计算结果
                for factor, values in tech_results.items():
                    tech_df[factor] = values
                
                # 只保留最新日期的数据
                tech_df = tech_df.groupby('ts_code').last()
                tech_df.reset_index(inplace=True)
                
                # 只选择需要的技术因子列
                tech_columns = ['ts_code'] + [col for col in factors['technical'] if col in tech_df.columns]
                tech_df = tech_df[tech_columns]
                
                # 合并技术因子数据
                if final_df is None:
                    final_df = tech_df
                else:
                    final_df = final_df.merge(tech_df, on='ts_code', how='inner')
            
            if final_df is None or final_df.empty:
                return []
                
            # 在标准化之前保存原始数据
            original_data = final_df.copy()
            
            # 标准化因子值并计算得分
            for factor in weights.keys():
                if factor in final_df.columns:
                    final_df[factor] = (final_df[factor] - final_df[factor].mean()) / final_df[factor].std()
            
            # 计算综合得分
            total_weight = sum(weights.values())
            final_df['score'] = 0
            
            # 定义需要取负的因子（值越小越好）
            negative_factors = {'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'volatility'}
            
            for factor, weight in weights.items():
                if factor in final_df.columns:
                    if factor in negative_factors:
                        final_df['score'] -= final_df[factor] * (weight / total_weight)
                    else:
                        final_df['score'] += final_df[factor] * (weight / total_weight)
            
            # 将得分转换为0-100的范围
            final_df['score'] = (final_df['score'] - final_df['score'].min()) / (final_df['score'].max() - final_df['score'].min()) * 100
            
            # 获取股票基本信息
            stocks_info = execute_query('''
                SELECT ts_code, name, industry 
                FROM stock_basic
            ''')
            stocks_df = pd.DataFrame(
                stocks_info, 
                columns=['ts_code', 'name', 'industry']
            )
            
            # 合并基本信息
            final_df = final_df.merge(stocks_df, on='ts_code', how='inner')
            
            # 排序并只取前10条数据
            final_df = final_df.sort_values('score', ascending=False).head(10)
            
            # 修改结果格式化部分，使用 original_data 获取因子的原始值
            result = []
            for _, row in final_df.iterrows():
                # 获取该股票的原始数据
                original_row = original_data[original_data['ts_code'] == row['ts_code']].iloc[0]
                
                # 创建因子字典，使用原始值
                factor_values = {}
                for factor in weights.keys():
                    if factor in original_row and pd.notna(original_row[factor]):
                        factor_values[factor] = float(original_row[factor])
                    else:
                        factor_values[factor] = None

                # 添加股票信息
                stock_info = {
                    'ts_code': row['ts_code'],
                    'name': row['name'],
                    'industry': row['industry'],
                    'score': float(row['score']),
                    'factors': factor_values
                }
                result.append(stock_info)

            return result

        except Exception as e:
            logger.error(f"Error in apply_factor_filter: {e}")
            raise

    @staticmethod
    def get_available_factors() -> Dict:
        """获取可用的因子列表"""
        try:
            # 基本面因子 - 确保这些字段在 daily_basic 表中存在
            fundamental_factors = [
                {'code': 'pe', 'name': '市盈率', 'is_higher_better': False},
                {'code': 'pe_ttm', 'name': '市盈率(TTM)', 'is_higher_better': False},
                {'code': 'pb', 'name': '市净率', 'is_higher_better': False},
                {'code': 'ps_ttm', 'name': '市销率(TTM)', 'is_higher_better': False},
                {'code': 'dv_ttm', 'name': '股息率(TTM)', 'is_higher_better': True},
                {'code': 'total_mv', 'name': '总市值', 'is_higher_better': None},
            ]
            
            # 技术面因子
            technical_factors = [
                {'code': 'ma5', 'name': '5日均线', 'is_higher_better': None},
                {'code': 'ma10', 'name': '10日均线', 'is_higher_better': None},
                {'code': 'ma20', 'name': '20日均线', 'is_higher_better': None},
                {'code': 'macd', 'name': 'MACD', 'is_higher_better': True},
                {'code': 'rsi', 'name': 'RSI', 'is_higher_better': None},
                {'code': 'volatility', 'name': '波动率', 'is_higher_better': False},
            ]
            
            # 成交量因子
            volume_factors = [
                {'code': 'turnover_rate', 'name': '换手率', 'is_higher_better': None},
                {'code': 'volume_ratio', 'name': '量比', 'is_higher_better': True},
            ]
            
            return {
                'fundamental': fundamental_factors,
                'technical': technical_factors,
                'volume': volume_factors
            }
            
        except Exception as e:
            logger.error(f"Error in get_available_factors: {e}")
            raise