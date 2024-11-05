import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'stocks.db'

def init_db():
    """Initialize database schema"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            date TEXT,
            code TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (date, code)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS strategy_results (
            strategy_name TEXT,
            code TEXT,
            entry_date TEXT,
            entry_price REAL,
            exit_date TEXT,
            exit_price REAL,
            profit_loss REAL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tracked_stocks (
            ts_code TEXT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()