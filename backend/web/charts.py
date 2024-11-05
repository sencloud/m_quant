import io
import base64
import matplotlib.pyplot as plt
from ..database.connection import execute_query

def create_stock_chart(code, start_date, end_date):
    """Create stock price chart"""
    data = execute_query('''
        SELECT date, close FROM stocks 
        WHERE code = ? AND date BETWEEN ? AND ?
        ORDER BY date
    ''', (code, start_date, end_date))
    
    if not data:
        return None
    
    dates, prices = zip(*data)
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, prices)
    plt.title(f'{code} Price Chart')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode()