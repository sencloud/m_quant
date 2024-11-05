import backtrader as bt

class SimpleTradeStrategy(bt.Strategy):
    """用于执行单次交易的简单策略"""
    
    params = (
        ('action', None),  # 'buy' 或 'sell'
        ('quantity', 0),
        ('store', None),
    )

    def __init__(self):
        if not self.p.action or not self.p.quantity:
            raise ValueError("Action and quantity must be specified for SimpleTradeStrategy")

    def next(self):
        if self.p.action == 'buy':
            self.buy(size=self.p.quantity)
        elif self.p.action == 'sell':
            self.sell(size=self.p.quantity)
        else:
            raise ValueError("Invalid action specified. Use 'buy' or 'sell'.")
        # 执行订单后停止
        self.env.runstop()

class BaseStrategy(bt.Strategy):
    """基础策略类，包含通用功能"""
    
    params = (
        ('position_size_type', 'fixed'),  # 'fixed' 或 'percentage'
        ('position_size', 100),
        ('stop_loss', 0.05),
        ('take_profit', 0.10),
        ('trailing_stop', 0),
    )

    def __init__(self):
        self.order = None
        self.stop_order = None
        self.profit_order = None
        self.position_size = self.p.position_size
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.on_buy_order_completed(order)
            else:
                self.on_sell_order_completed(order)
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.on_order_failed(order)
            
    def on_buy_order_completed(self, order):
        """买入订单完成时的处理"""
        self.order = None
        # 设置止损和止盈订单
        self.set_stop_orders(order.executed.price)
        
    def on_sell_order_completed(self, order):
        """卖出订单完成时的处理"""
        self.order = None
        self.stop_order = None
        self.profit_order = None
        
    def on_order_failed(self, order):
        """订单失败时的处理"""
        self.order = None
        
    def set_stop_orders(self, entry_price):
        """设置止损和止盈订单"""
        if self.p.stop_loss > 0:
            stop_price = entry_price * (1 - self.p.stop_loss)
            self.stop_order = self.sell(
                exectype=bt.Order.Stop,
                price=stop_price,
                size=self.position_size
            )
            
        if self.p.take_profit > 0:
            profit_price = entry_price * (1 + self.p.take_profit)
            self.profit_order = self.sell(
                exectype=bt.Order.Limit,
                price=profit_price,
                size=self.position_size
            ) 