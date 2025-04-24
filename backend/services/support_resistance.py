import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SRInfo:
    start_time: datetime
    price: float
    sr_type: str  # "Support" or "Resistance"
    strength: int
    timeframe_str: str
    ephemeral: bool = False
    break_time: Optional[datetime] = None
    retest_times: List[datetime] = None

    def __post_init__(self):
        if self.retest_times is None:
            self.retest_times = []

class SupportResistanceService:
    def __init__(self):
        self.SR_PIVOT_LENGTH = 15
        self.MAX_SR_INFO_LIST_SIZE = 10
        self.ATR_LENGTH = 20
        self.TOO_CLOSE_ATR = 1.0 / 8.0
        self.MIN_SR_SIZE = 5

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, length: int = None) -> pd.Series:
        """Calculate Average True Range"""
        if length is None:
            length = self.ATR_LENGTH
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=length).mean()

    def find_pivot_points(self, data: pd.DataFrame, length: int = None) -> Tuple[pd.Series, pd.Series]:
        """Find pivot high and low points"""
        if length is None:
            length = self.SR_PIVOT_LENGTH

        pivot_high = pd.Series(index=data.index, dtype=float)
        pivot_low = pd.Series(index=data.index, dtype=float)

        for i in range(length, len(data) - length):
            if all(data['high'].iloc[i] > data['high'].iloc[i-length:i]) and \
               all(data['high'].iloc[i] > data['high'].iloc[i+1:i+length+1]):
                pivot_high.iloc[i] = data['high'].iloc[i]

            if all(data['low'].iloc[i] < data['low'].iloc[i-length:i]) and \
               all(data['low'].iloc[i] < data['low'].iloc[i+1:i+length+1]):
                pivot_low.iloc[i] = data['low'].iloc[i]

        return pivot_high, pivot_low

    def get_support_resistance_levels(self, data: pd.DataFrame, timeframe: str = '1h') -> List[SRInfo]:
        """Calculate support and resistance levels"""
        # Calculate ATR
        atr = self.calculate_atr(data['high'], data['low'], data['close'])
        
        # Find pivot points
        pivot_high, pivot_low = self.find_pivot_points(data)
        
        sr_levels: List[SRInfo] = []
        
        # Process pivot lows (Support levels)
        for idx in pivot_low.dropna().index:
            price = pivot_low[idx]
            
            # Check if price is too close to existing levels
            too_close = False
            for sr in sr_levels:
                if abs(sr.price - price) < atr[idx] * self.TOO_CLOSE_ATR:
                    too_close = True
                    break
            
            if not too_close:
                sr_levels.append(SRInfo(
                    start_time=data['date'].iloc[idx],
                    price=price,
                    sr_type="Support",
                    strength=1,
                    timeframe_str=timeframe
                ))
        
        # Process pivot highs (Resistance levels)
        for idx in pivot_high.dropna().index:
            price = pivot_high[idx]
            
            # Check if price is too close to existing levels
            too_close = False
            for sr in sr_levels:
                if abs(sr.price - price) < atr[idx] * self.TOO_CLOSE_ATR:
                    too_close = True
                    break
            
            if not too_close:
                sr_levels.append(SRInfo(
                    start_time=data['date'].iloc[idx],
                    price=price,
                    sr_type="Resistance",
                    strength=1,
                    timeframe_str=timeframe
                ))

        # Sort levels by price
        sr_levels.sort(key=lambda x: x.price)
        
        return sr_levels

    def check_breaks_and_retests(self, data: pd.DataFrame, sr_levels: List[SRInfo]) -> List[SRInfo]:
        """Check for breaks and retests of support/resistance levels"""
        for sr in sr_levels:
            for idx, row in data.iterrows():
                current_time = row['date']
                if current_time <= sr.start_time:
                    continue
                    
                if sr.break_time is None:
                    # Check for breaks
                    if sr.sr_type == "Resistance" and row['high'] > sr.price:
                        sr.break_time = current_time
                    elif sr.sr_type == "Support" and row['low'] < sr.price:
                        sr.break_time = current_time
                
                # Check for retests
                if sr.break_time is None:
                    if sr.sr_type == "Resistance" and \
                       row['high'] >= sr.price and row['close'] <= sr.price:
                        if not sr.retest_times or sr.retest_times[-1] != current_time:
                            sr.retest_times.append(current_time)
                            sr.strength += 1
                    
                    elif sr.sr_type == "Support" and \
                         row['low'] <= sr.price and row['close'] >= sr.price:
                        if not sr.retest_times or sr.retest_times[-1] != current_time:
                            sr.retest_times.append(current_time)
                            sr.strength += 1
        
        return sr_levels

    def get_sr_levels(self, data: pd.DataFrame, timeframe: str = '1h') -> List[Dict]:
        """Main function to get support and resistance levels with breaks and retests"""
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data['date']):
            data['date'] = pd.to_datetime(data['date'])
            
        sr_levels = self.get_support_resistance_levels(data, timeframe)
        sr_levels = self.check_breaks_and_retests(data, sr_levels)
        
        # Convert to dict format for API response
        result = []
        for sr in sr_levels:
            # 确保所有时间都是有效的datetime对象
            if isinstance(sr.start_time, pd.Timestamp):
                start_time = sr.start_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_time = pd.to_datetime(sr.start_time).strftime('%Y-%m-%d %H:%M:%S')
                
            if sr.break_time is not None:
                if isinstance(sr.break_time, pd.Timestamp):
                    break_time = sr.break_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    break_time = pd.to_datetime(sr.break_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                break_time = None
                
            retest_times = []
            for rt in sr.retest_times:
                if isinstance(rt, pd.Timestamp):
                    retest_times.append(rt.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    retest_times.append(pd.to_datetime(rt).strftime('%Y-%m-%d %H:%M:%S'))
            
            result.append({
                'price': float(sr.price),
                'type': sr.sr_type,
                'strength': sr.strength,
                'start_time': start_time,
                'break_time': break_time,
                'retest_times': retest_times,
                'timeframe': sr.timeframe_str
            })

        return result