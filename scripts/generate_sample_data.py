import sys
import os
import logging
from datetime import datetime, timedelta
import tushare as ts
import yfinance as yf

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend.database.connection import execute_many, execute_query
from backend.data.process_data import ProcessData

logger = logging.getLogger(__name__)

# Initialize Tushare with your token
ts.set_token('')
pro = ts.pro_api()

def get_sample_data(stock_code, start_date, end_date):
    try:
        # Get data from Tushare
        df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        
        # Convert DataFrame to list of tuples
        data = [
            (row['trade_date'], stock_code, row['open'], row['high'], row['low'], row['close'], row['vol'])
            for _, row in df.iterrows()
        ]
        
        return data
    except Exception as e:
        logger.error(f"Error fetching data from Tushare: {str(e)}")
        raise

def get_stock_basic():
    try:
        # Get stock basic info from Tushare
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        
        # Convert DataFrame to list of tuples
        data = [
            (row['ts_code'], row['symbol'], row['name'], row['area'], row['industry'], row['list_date'])
            for _, row in df.iterrows()
        ]
        
        return data
    except Exception as e:
        logger.error(f"Error fetching stock basic data from Tushare: {str(e)}")
        raise

def save_stock_basic(data):
    try:
        execute_many('''
            INSERT INTO stock_basic (ts_code, symbol, name, area, industry, list_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to stock_basic table")
    except Exception as e:
        logger.error(f"Error saving stock basic data: {str(e)}")
        raise

def create_stock_basic_table():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS stock_basic (
                ts_code TEXT PRIMARY KEY,
                symbol TEXT,
                name TEXT,
                area TEXT,
                industry TEXT,
                list_date TEXT
            )
        ''')
        logger.info("Created stock_basic table")
    except Exception as e:
        logger.error(f"Error creating stock_basic table: {str(e)}")
        raise

def create_minute_hour_tables():
    try:
        # Create minute data table
        execute_query('''
            CREATE TABLE IF NOT EXISTS stock_minute_data (
                datetime TEXT,
                stock_code TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (datetime, stock_code)
            )
        ''')
        
        # Create hourly data table
        execute_query('''
            CREATE TABLE IF NOT EXISTS stock_hour_data (
                datetime TEXT,
                stock_code TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (datetime, stock_code)
            )
        ''')
        logger.info("Created minute and hour data tables")
    except Exception as e:
        logger.error(f"Error creating minute/hour tables: {str(e)}")
        raise

def get_minute_hour_data(symbol, period='7d', interval='1m'):
    try:
        # Convert Tushare stock code to Yahoo Finance format
        yahoo_symbol = symbol.split('.')[0]
        if symbol.endswith('SZ'):
            yahoo_symbol += '.SZ'
        elif symbol.endswith('SH'):
            yahoo_symbol += '.SS'
            
        # Get data from yfinance
        stock = yf.Ticker(yahoo_symbol)
        df = stock.history(period=period, interval=interval)
        
        # Convert DataFrame to list of tuples
        data = [
            (index.strftime('%Y-%m-%d %H:%M:%S'), 
             symbol,
             row['Open'], 
             row['High'], 
             row['Low'], 
             row['Close'], 
             row['Volume'])
            for index, row in df.iterrows()
        ]
        print(data)
                
        return data
    except Exception as e:
        logger.error(f"Error fetching data from yfinance: {str(e)}")
        raise

def save_minute_hour_data(data, interval='1m'):
    try:
        table_name = 'stock_minute_data' if interval == '1m' else 'stock_hour_data'
        execute_many(f'''
            INSERT OR REPLACE INTO {table_name}
            (datetime, stock_code, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
        logger.info(f"Saved {len(data)} records to {table_name}")
    except Exception as e:
        logger.error(f"Error saving {interval} data: {str(e)}")
        raise

if __name__ == '__main__':
    # Create stock_basic table
    # create_stock_basic_table()

    # Get and save stock basic data
    # stock_basic_data = get_stock_basic()
    # save_stock_basic(stock_basic_data)
    # print(f"Retrieved and saved stock basic data for {len(stock_basic_data)} stocks")

    sample_stocks = ['000333.SZ', '600276.SH']
    start_date = '20200101'
    end_date = datetime.now().strftime('%Y%m%d')
    
    # for stock_code in sample_stocks:
    #     data = get_sample_data(stock_code, start_date, end_date)
    #     ProcessData.save_stock_data(stock_code, data)
    #     print(f"Retrieved and saved data for {stock_code}")

    # Add new code for minute/hour data
    create_minute_hour_tables()
    
    for stock_code in sample_stocks:
        # Get and save minute data
        minute_data = get_minute_hour_data(stock_code, period='7d', interval='1m')
        save_minute_hour_data(minute_data, interval='1m')
        print(f"Retrieved and saved minute data for {stock_code}")
        
        # Get and save hourly data
        hour_data = get_minute_hour_data(stock_code, period='7d', interval='1h')
        save_minute_hour_data(hour_data, interval='1h')
        print(f"Retrieved and saved hourly data for {stock_code}")
