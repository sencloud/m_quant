from datetime import datetime
import numpy as np
import logging
from ..database.connection import execute_query, execute_many
import backtrader as bt

class BaseStrategy(bt.Strategy):
    """Base class for all trading strategies"""
    
    def __init__(self):
        super().__init__()
        self.trades = []
        self.entry_bar = None
        self.exit_reason = ''
        self.current_trade = None  # 用于跟踪当前交易
    
    def next(self):
        raise NotImplementedError("Strategy must implement the next method")
    
    def get_data(self, code, start_date, end_date):
        """Get stock data with error handling"""
        try:
            data = execute_query('''
                SELECT date, open, high, low, close, volume 
                FROM stocks 
                WHERE code = ? AND date BETWEEN ? AND ?
                ORDER BY date
            ''', (code, start_date, end_date))
            
            if not data:
                self.logger.warning(f"No data found for {code} between {start_date} and {end_date}")
                return []
                
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            raise
    
    def save_result(self, result):
        """Save strategy result with error handling"""
        try:
            execute_many('''
                INSERT INTO strategy_results 
                (strategy_name, code, entry_date, entry_price, exit_date, exit_price, profit_loss)
                VALUES (?,?,?,?,?,?,?)
            ''', [result])
            self.logger.info(f"Saved trade result: {result}")
        except Exception as e:
            self.logger.error(f"Error saving result: {str(e)}")
            raise
    
    def notify_trade(self, trade):
        """交易通知"""
        if trade.isclosed:  # 交易关闭时
            try:
                # 获取当前位置
                current_position = len(self.data) - 1
                
                # 只记录实际的交易（size > 0）
                if trade.size > 0:
                    trade_info = {
                        'entry': self.entry_bar,
                        'exit': current_position,
                        'entry_price': trade.price,
                        'exit_price': trade.price + (trade.pnl / trade.size),
                        'type': 'LONG' if trade.long else 'SHORT',
                        'size': trade.size,
                        'pnl': trade.pnl,
                        'exit_reason': self.exit_reason
                    }
                    
                    # 检查是否是重复交易
                    is_duplicate = False
                    if self.trades:
                        last_trade = self.trades[-1]
                        if (last_trade['entry'] == trade_info['entry'] and 
                            last_trade['exit'] == trade_info['exit'] and
                            last_trade['pnl'] == trade_info['pnl']):
                            is_duplicate = True
                    
                    if not is_duplicate:
                        self.trades.append(trade_info)
                        self.log(f'TRADE COMPLETED - PnL: {trade.pnl:.2f}')
                
            except Exception as e:
                self.log(f'Error in notify_trade: {str(e)}')
    
    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_bar = len(self.data) - 1
            elif order.issell():
                self.exit_reason = getattr(self, 'exit_reason', '')
    
    def buy(self, *args, **kwargs):
        self.entry_bar = len(self.data) - 1  # 记录入场位置
        super().buy(*args, **kwargs)
        
    def sell(self, *args, **kwargs):
        self.entry_bar = len(self.data) - 1  # 记录入场位置
        super().sell(*args, **kwargs)