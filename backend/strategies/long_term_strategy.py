from .base_strategy import BaseStrategy
from datetime import datetime, timedelta

class LongTermStrategy(BaseStrategy):
    """Long-term strategy: Quarterly trend following"""
    def __init__(self, code, start_date, end_date):
        super().__init__()

    def next(self):
        pass