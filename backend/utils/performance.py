import numpy as np
from datetime import datetime

class PerformanceMetrics:
    @staticmethod
    def calculate_returns(prices):
        """Calculate return series"""
        return np.diff(prices) / prices[:-1]
    
    @staticmethod
    def calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252):
        """Calculate annualized Sharpe ratio"""
        if len(returns) < 2:
            return 0
        
        excess_returns = returns - risk_free_rate/periods_per_year
        return np.sqrt(periods_per_year) * np.mean(excess_returns) / np.std(excess_returns)
    
    @staticmethod
    def calculate_sortino_ratio(returns, risk_free_rate=0.0, periods_per_year=252):
        """Calculate Sortino ratio using downside deviation"""
        if len(returns) < 2:
            return 0
        
        excess_returns = returns - risk_free_rate/periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        
        return np.sqrt(periods_per_year) * np.mean(excess_returns) / downside_std if downside_std != 0 else 0
    
    @staticmethod
    def calculate_max_drawdown(prices):
        """Calculate maximum drawdown and duration"""
        peak = prices[0]
        max_dd = 0
        max_dd_duration = 0
        current_dd_duration = 0
        peak_idx = 0
        
        for i, price in enumerate(prices):
            if price > peak:
                peak = price
                peak_idx = i
                current_dd_duration = 0
            else:
                current_dd = (peak - price) / peak
                current_dd_duration = i - peak_idx
                
                if current_dd > max_dd:
                    max_dd = current_dd
                    max_dd_duration = current_dd_duration
        
        return max_dd, max_dd_duration
    
    @staticmethod
    def calculate_strategy_metrics(trades):
        """Calculate comprehensive strategy performance metrics"""
        if not trades:
            return {}
        
        # Extract trade data
        returns = [t['profitLoss'] for t in trades]
        durations = [(datetime.strptime(t['exitDate'], '%Y-%m-%d') - 
                     datetime.strptime(t['entryDate'], '%Y-%m-%d')).days 
                    for t in trades]
        
        # Calculate metrics
        total_return = sum(returns)
        win_rate = len([r for r in returns if r > 0]) / len(returns)
        avg_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
        avg_loss = np.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_trade_duration': np.mean(durations),
            'sharpe_ratio': PerformanceMetrics.calculate_sharpe_ratio(np.array(returns)),
            'sortino_ratio': PerformanceMetrics.calculate_sortino_ratio(np.array(returns))
        }