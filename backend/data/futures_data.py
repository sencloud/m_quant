import backtrader as bt

class FuturesData(bt.feeds.PandasData):
    """期货数据源"""
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'vol'),
        ('openinterest', 'oi'),
    ) 