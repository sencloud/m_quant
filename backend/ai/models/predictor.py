import numpy as np
from datetime import datetime, timedelta
from statistics import mean

class StockPredictor:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.prices = []
        
    def add_price(self, price):
        self.prices.append(float(price))
        
    def predict_next_price(self):
        if len(self.prices) < self.window_size:
            return None
        
        window = self.prices[-self.window_size:]
        prediction = mean(window)
        
        # Add trend analysis
        trend = self._calculate_trend(window)
        prediction *= (1 + trend)
        
        return prediction
    
    def _calculate_trend(self, window):
        if len(window) < 2:
            return 0
        
        changes = [b - a for a, b in zip(window[:-1], window[1:])]
        avg_change = mean(changes)
        return avg_change / window[-1]  # Normalize by current price