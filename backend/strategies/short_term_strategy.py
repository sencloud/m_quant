from .base_strategy import BaseStrategy
import backtrader as bt
import pandas as pd
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class ShortTermStrategy(BaseStrategy):
    params = (
        ('code', None),           # 股票代码
        ('start_date', None),     # 回测开始日期
        ('end_date', None),       # 回测结束日期
        # Position Settings
        ('position_size_type', 'fixed'),  # 'fixed' or 'percentage'
        ('position_size', 100),    # 固定数量或资金比例
        # Risk Management
        ('stop_loss', 0.05),      # 止损比例
        ('take_profit', 0.10),    # 止盈比例
        ('trailing_stop', 0.0),    # 追踪止损比例
        
        ('rsi_period', 14),         # RSI周期
        ('rsi_overbought', 70),     # RSI超买阈值
        ('rsi_oversold', 30),       # RSI超卖阈值
    )

    def __init__(self):
        logger.info("Initializing ShortTermStrategy")
        super().__init__()
        
        # 初始化指标
        self.ma5 = bt.indicators.SMA(self.data.close, period=5)
        self.ma10 = bt.indicators.SMA(self.data.close, period=10)
        self.ma20 = bt.indicators.SMA(self.data.close, period=20)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        
        self.ma5_cross_ma10 = bt.indicators.CrossOver(self.ma5, self.ma10)
        self.ma10_cross_ma20 = bt.indicators.CrossOver(self.ma10, self.ma20)
        
        # 设置最小周期
        self._minperiod = max(5, 10, 14, 20)
        
        # 交易相关变量
        self.signal = False
        self.order = None
        self.entry_price = None
        self.highest_price = None  # 用于追踪止损
        
        # 交易记录
        self.trades = []
        self.current_trade = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        try:
            if order.status in [order.Completed]:
                if order.isbuy():
                    self.current_trade = {
                        'entry': len(self.data) - 1,  # 使用当前数据长度作为索引
                        'entry_price': order.executed.price,
                        'size': order.executed.size,
                        'type': 'LONG',
                        'exit': None,
                        'exit_price': None,
                        'pnl': None,
                        'exit_reason': None
                    }
                    self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                            f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                else:
                    if self.current_trade:
                        self.current_trade['exit'] = len(self.data) - 1
                        self.current_trade['exit_price'] = order.executed.price
                        self.current_trade['pnl'] = order.executed.pnl
                        
                        self.trades.append(self.current_trade)
                        self.current_trade = None
                    
                    self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                            f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            else:
                logger.warning('Order Canceled/Margin/Rejected')
        except Exception as e:
            logger.error(f"Error in notify_order: {str(e)}")

        self.order = None

    def get_position_size(self):
        if self.params.position_size_type == 'fixed':
            # 确保固定数量至少为100股
            return 1
        else:  # percentage
            available_cash = self.broker.getcash()
            current_price = self.data.close[0]
            # 计算按比例可以买入的股数
            shares = int((available_cash * self.params.position_size / 1) / current_price)
            # 向下取整到最接近的1的倍数，并确保至少为1股
            return max(1, (shares // 100) * 100)

    def should_stop_loss(self):
        if not self.position or not self.entry_price:
            return False
        current_price = self.data.close[0]
        return current_price <= self.entry_price * (1 - self.params.stop_loss)

    def should_take_profit(self):
        if not self.position or not self.entry_price:
            return False
        current_price = self.data.close[0]
        return current_price >= self.entry_price * (1 + self.params.take_profit)

    def should_trailing_stop(self):
        if not self.position or not self.highest_price:
            return False
        if self.params.trailing_stop <= 0:
            return False
        current_price = self.data.close[0]
        return current_price <= self.highest_price * (1 - self.params.trailing_stop)

    def next(self):
        if len(self) < self._minperiod:
            return

        # 记录每日数据
        self.log(f"Close: {self.data.close[0]:.2f}, MA5: {self.ma5[0]:.2f}, "
                f"MA10: {self.ma10[0]:.2f}, MA20: {self.ma20[0]:.2f}")
        
        # 更新最高价
        if self.position:
            if self.highest_price is None or self.data.close[0] > self.highest_price:
                self.highest_price = self.data.close[0]

        # 如果有未完成订单，等待
        if self.order:
            return

        # 检查是否需要退出仓位
        if self.position:
            exit_signal = False
            exit_reason = None
            
            if self.should_stop_loss():
                exit_signal = True
                exit_reason = 'Stop Loss'
            elif self.should_take_profit():
                exit_signal = True
                exit_reason = 'Take Profit'
            elif self.should_trailing_stop():
                exit_signal = True
                exit_reason = 'Trailing Stop'
            
            if exit_signal:
                self.order = self.close()
                self.log(f"EXIT SIGNAL ({exit_reason}) at {self.data.close[0]:.2f}")
                self.highest_price = None
                return

        # 入场信号
        if self.ma5_cross_ma10 > 0:
            # and \
            #     self.rsi < self.params.rsi_overbought:
            self.signal = True

        # 如果有信号且MA10上穿MA20，则做多 and self.ma10_cross_ma20 > 0
        if self.signal and not self.position:
            size = self.get_position_size()
            self.order = self.buy(size=size)
            self.entry_price = self.data.close[0]
            self.highest_price = self.entry_price
            self.log(f"BUY CREATE at {self.data.close[0]:.2f}, size: {size}")

    def stop(self):
        # 计算策略统计信息
        self.stats = {
            'total_trades': len(self.trades),
            'won_trades': len([t for t in self.trades if t['pnl'] > 0]),
            'lost_trades': len([t for t in self.trades if t['pnl'] <= 0]),
            'total_pnl': sum(t['pnl'] for t in self.trades if t['pnl'] is not None),
            'win_rate': len([t for t in self.trades if t['pnl'] > 0]) / len(self.trades) if self.trades else 0,
        }
        
        self.log(f'(MA5_MA10_MA20) Ending Value {self.broker.getvalue():.2f}')
        self.log(f'Total Trades: {self.stats["total_trades"]}, '
                f'Win Rate: {self.stats["win_rate"]:.2%}')

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
