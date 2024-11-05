import sys
import os
import logging
from datetime import datetime
import tushare as ts
import time

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend.database.connection import execute_many, execute_query

logger = logging.getLogger(__name__)

# Initialize Tushare with your token
ts.set_token('')
pro = ts.pro_api()

def create_daily_basic_table():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS daily_basic (
                ts_code TEXT,
                trade_date TEXT,
                close REAL,
                turnover_rate REAL,
                turnover_rate_f REAL,
                volume_ratio REAL,
                pe REAL,
                pe_ttm REAL,
                pb REAL,
                ps REAL,
                ps_ttm REAL,
                dv_ratio REAL,
                dv_ttm REAL,
                total_share REAL,
                float_share REAL,
                free_share REAL,
                total_mv REAL,
                circ_mv REAL,
                PRIMARY KEY (ts_code, trade_date)
            )
        ''')
        logger.info("Created daily_basic table")
    except Exception as e:
        logger.error(f"Error creating daily_basic table: {str(e)}")
        raise

def get_daily_basic_data(trade_date):
    try:
        df = pro.daily_basic(
            ts_code='', 
            trade_date=trade_date,
            fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
        )
        # Convert DataFrame to list of tuples
        data = [tuple(row) for row in df.values]
        return data
    except Exception as e:
        logger.error(f"Error fetching data from Tushare: {str(e)}")
        raise

def save_daily_basic_data(data):
    try:
        execute_many('''
            INSERT OR REPLACE INTO daily_basic (
                ts_code, trade_date, close, turnover_rate, turnover_rate_f,
                volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
                total_share, float_share, free_share, total_mv, circ_mv
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to daily_basic table")
    except Exception as e:
        logger.error(f"Error saving daily basic data: {str(e)}")
        raise

def create_fut_basic_table():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS fut_basic (
                ts_code TEXT PRIMARY KEY,
                symbol TEXT,
                exchange TEXT,
                name TEXT,
                fut_code TEXT,
                multiplier REAL,
                trade_unit TEXT,
                per_unit REAL,
                quote_unit TEXT,
                quote_unit_desc TEXT,
                d_mode_desc TEXT,
                list_date TEXT,
                delist_date TEXT,
                d_month TEXT,
                last_ddate TEXT,
                trade_time_desc TEXT
            )
        ''')
        logger.info("Created fut_basic table")
    except Exception as e:
        logger.error(f"Error creating fut_basic table: {str(e)}")
        raise

def get_fut_basic_data(exchange, fut_type=None, fut_code=None):
    try:
        df = pro.fut_basic(
            exchange=exchange,
            fut_type=fut_type,
            fut_code=fut_code,
            fields='ts_code,symbol,exchange,name,fut_code,multiplier,trade_unit,per_unit,quote_unit,quote_unit_desc,d_mode_desc,list_date,delist_date,d_month,last_ddate,trade_time_desc'
        )
        # Convert DataFrame to list of tuples
        data = [tuple(row) for row in df.values]
        return data
    except Exception as e:
        logger.error(f"Error fetching futures data from Tushare: {str(e)}")
        raise

def save_fut_basic_data(data):
    try:
        execute_many('''
            INSERT OR REPLACE INTO fut_basic (
                ts_code, symbol, exchange, name, fut_code, multiplier,
                trade_unit, per_unit, quote_unit, quote_unit_desc,
                d_mode_desc, list_date, delist_date, d_month,
                last_ddate, trade_time_desc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to fut_basic table")
    except Exception as e:
        logger.error(f"Error saving futures basic data: {str(e)}")
        raise

def create_fut_daily_table():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS fut_daily (
                ts_code TEXT,
                trade_date TEXT,
                pre_close REAL,
                pre_settle REAL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                settle REAL,
                change1 REAL,
                change2 REAL,
                vol REAL,
                amount REAL,
                oi REAL,
                oi_chg REAL,
                delv_settle REAL,
                PRIMARY KEY (ts_code, trade_date)
            )
        ''')
        logger.info("Created fut_daily table")
    except Exception as e:
        logger.error(f"Error creating fut_daily table: {str(e)}")
        raise

def get_fut_daily_data(ts_code, start_date=None, end_date=None, trade_date=None):
    try:
        # 设置每次获取的数据量
        limit = 2000
        data = []
        
        # 明确指定需要获取的字段
        fields = 'ts_code,trade_date,pre_close,pre_settle,open,high,low,close,settle,change1,change2,vol,amount,oi,oi_chg,delv_settle'
        
        if trade_date:
            # 获取单个交易日的数据
            df = pro.fut_daily(
                ts_code=ts_code, 
                trade_date=trade_date,
                fields=fields
            )
            return [tuple(row) for row in df.values]
        else:
            # 分批获取历史数据
            while True:
                df = pro.fut_daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=len(data),
                    fields=fields
                )
                
                if df is None or df.empty:
                    break
                
                current_batch = [tuple(row) for row in df.values]
                data.extend(current_batch)
                
                if len(current_batch) < limit:
                    break
                    
                # 休息1分钟避免超过频率限制
                logger.info(f"Retrieved {len(current_batch)} records, sleeping for 1 minute...")
                time.sleep(60)
                
        return data
    except Exception as e:
        logger.error(f"Error fetching futures daily data from Tushare: {str(e)}")
        raise

def save_fut_daily_data(data):
    try:
        execute_many('''
            INSERT OR REPLACE INTO fut_daily (
                ts_code, trade_date, pre_close, pre_settle, open,
                high, low, close, settle, change1, change2,
                vol, amount, oi, oi_chg, delv_settle
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to fut_daily table")
    except Exception as e:
        logger.error(f"Error saving futures daily data: {str(e)}")
        raise

def create_fut_mins_table():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS fut_mins (
                ts_code TEXT,
                trade_time TEXT,
                open REAL,
                close REAL,
                high REAL,
                low REAL,
                vol INTEGER,
                amount REAL,
                oi REAL,
                PRIMARY KEY (ts_code, trade_time)
            )
        ''')
        logger.info("Created fut_mins table")
    except Exception as e:
        logger.error(f"Error creating fut_mins table: {str(e)}")
        raise

def get_fut_mins_data(ts_code, freq, start_date=None, end_date=None):
    try:
        # 设置每次获取的数据量
        limit = 8000
        data = []
        
        # 明确指定需要获取的字段
        fields = 'ts_code,trade_time,open,close,high,low,vol,amount,oi'
        
        # 分批获取历史数据
        while True:
            df = pro.ft_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=len(data),
                fields=fields
            )
            
            if df is None or df.empty:
                break
            
            current_batch = [tuple(row) for row in df.values]
            data.extend(current_batch)
            
            if len(current_batch) < limit:
                break
                
            # 休息1分钟避免超过频率限制
            logger.info(f"Retrieved {len(current_batch)} records, sleeping for 1 minute...")
            time.sleep(60)
            
        return data
    except Exception as e:
        logger.error(f"Error fetching futures minute data from Tushare: {str(e)}")
        raise

def save_fut_mins_data(data):
    try:
        execute_many('''
            INSERT OR REPLACE INTO fut_15mins (
                ts_code, trade_time, open, close, high,
                low, vol, amount, oi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to fut_15mins table")
    except Exception as e:
        logger.error(f"Error saving futures minute data: {str(e)}")
        raise

def create_fut_mapping_table():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS fut_mapping (
                ts_code TEXT,
                trade_date TEXT,
                mapping_ts_code TEXT,
                PRIMARY KEY (ts_code, trade_date)
            )
        ''')
        logger.info("Created fut_mapping table")
    except Exception as e:
        logger.error(f"Error creating fut_mapping table: {str(e)}")
        raise

def get_fut_mapping_data(ts_code=None, start_date=None, end_date=None, trade_date=None):
    try:
        # 设置每次获取的数据量
        limit = 2000
        data = []
        
        # 明确指定需要获取的字段
        fields = 'ts_code,trade_date,mapping_ts_code'
        
        if trade_date:
            # 获取单个交易日的数据
            df = pro.fut_mapping(
                ts_code=ts_code, 
                trade_date=trade_date,
                fields=fields
            )
            return [tuple(row) for row in df.values]
        else:
            # 分批获取历史数据
            while True:
                df = pro.fut_mapping(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=len(data),
                    fields=fields
                )
                
                if df is None or df.empty:
                    break
                
                current_batch = [tuple(row) for row in df.values]
                data.extend(current_batch)
                
                if len(current_batch) < limit:
                    break
                    
                # 休息1分钟避免超过频率限制
                logger.info(f"Retrieved {len(current_batch)} records, sleeping for 1 minute...")
                time.sleep(60)
                
        return data
    except Exception as e:
        logger.error(f"Error fetching futures mapping data from Tushare: {str(e)}")
        raise

def save_fut_mapping_data(data):
    try:
        execute_many('''
            INSERT OR REPLACE INTO fut_mapping (
                ts_code, trade_date, mapping_ts_code
            ) VALUES (?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to fut_mapping table")
    except Exception as e:
        logger.error(f"Error saving futures mapping data: {str(e)}")
        raise

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create tables
    # create_daily_basic_table()
    # create_fut_basic_table()
    # create_fut_daily_table()
    # create_fut_mins_table()
    # create_fut_mapping_table()
    # create_fut_daily_table()
    
    # Get and save daily basic data
    # trade_date = '20241031'
    # data = get_daily_basic_data(trade_date)
    # save_daily_basic_data(data)
    
    # Get and save futures data for each exchange
    # exchanges = ['CFFEX', 'DCE', 'CZCE', 'SHFE', 'INE', 'GFEX']
    # for exchange in exchanges:
    #     futures_data = get_fut_basic_data(exchange, fut_type='1')
    #     save_fut_basic_data(futures_data)
    
    # Get and save futures mapping data
    # ts_code = 'RB.SHF'  # 连续合约代码
    # start_date = '20000101'
    # end_date = '20251231'
    
    # # 1. 先获取映射数据
    # logger.info(f"Getting mapping data for {ts_code}")
    # futures_mapping_data = get_fut_mapping_data(
    #     ts_code=ts_code,
    #     start_date=start_date,
    #     end_date=end_date
    # )
    # save_fut_mapping_data(futures_mapping_data)
    
    # # 2. 对每个映射的合约获取日线数据
    # processed_contracts = set()  # 用于跟踪已处理的合约
    # request_count = 0  # 用于跟踪请求次数
    
    # for mapping in futures_mapping_data:
    #     mapping_ts_code = mapping[2]  # 映射的合约代码
    #     trade_date = mapping[1]       # 对应的交易日期
        
    #     # 如果这个合约已经处理过，跳过
    #     if mapping_ts_code in processed_contracts:
    #         continue
        
    #     # 检查请求次数，每19次请求后休息一分钟
    #     if request_count >= 19:
    #         logger.info("Reached API rate limit, sleeping for 1 minute...")
    #         time.sleep(60)
    #         request_count = 0
            
    #     logger.info(f"Getting daily data for contract: {mapping_ts_code}")
        
    #     try:
    #         # 获取该合约的日线数据
    #         futures_daily_data = get_fut_daily_data(
    #             ts_code=mapping_ts_code,
    #             start_date=start_date,
    #             end_date=end_date
    #         )
            
    #         if futures_daily_data:
    #             save_fut_daily_data(futures_daily_data)
    #             processed_contracts.add(mapping_ts_code)
    #             logger.info(f"Saved daily data for contract: {mapping_ts_code}")
            
    #         request_count += 1
            
    #     except Exception as e:
    #         logger.error(f"Error processing contract {mapping_ts_code}: {str(e)}")
    #         # 如果是频率限制错误，休息一分钟后继续
    #         if "每分钟最多访问该接口20次" in str(e):
    #             logger.info("Hit rate limit, sleeping for 1 minute...")
    #             time.sleep(60)
    #             request_count = 0
    #             # 重试当前合约
    #             continue
    #         else:
    #             raise
    
    # Get and save futures minute data for a specific contract
    ts_code = 'RB2501.SHF'  # 示例合约代码
    freq = '15min'  # 1min/5min/15min/30min/60min
    start_date = '2024-09-02 09:00:00'
    end_date = '2024-10-31 23:00:00'
    
    futures_mins_data = get_fut_mins_data(
        ts_code=ts_code,
        freq=freq,
        start_date=start_date,
        end_date=end_date
    )
    save_fut_mins_data(futures_mins_data)
    
    print("Successfully processed all data")
