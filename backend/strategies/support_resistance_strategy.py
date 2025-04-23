import pandas as pd
import numpy as np
import talib
from typing import List, Dict, Any
from utils.logger import logger

class SupportResistanceStrategy:
    """支撑阻力策略"""

    def __init__(self):
        self.window = 20
        self.atr_period = 14
        self.atr_multiplier = 2.0

    @staticmethod
    def calculate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """计算交易信号"""
        logger.info("开始计算交易信号")
        
        # 确保数据是按日期排序的
        df = df.sort_values('date')
        
        # 计算支撑位和阻力位
        df['support_level'] = df['low'].rolling(window=20, min_periods=1).min()
        df['resistance_level'] = df['high'].rolling(window=20, min_periods=1).max()
        
        # 计算ATR
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=14, min_periods=1).mean()
        
        # 生成交易信号
        df['signal'] = 0
        
        # 多头信号：价格突破阻力位
        long_condition = (df['close'] > df['resistance_level']) & \
                       (df['close'].shift(1) <= df['resistance_level'].shift(1))
        df.loc[long_condition, 'signal'] = 1
        
        # 空头信号：价格跌破支撑位
        short_condition = (df['close'] < df['support_level']) & \
                        (df['close'].shift(1) >= df['support_level'].shift(1))
        df.loc[short_condition, 'signal'] = -1
        
        # 处理所有可能的None值
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        logger.info("交易信号计算完成")
        return df

    def run_backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """执行回测"""
        logger.info("开始执行回测")
        
        # 初始化回测结果
        position = 0
        trades = []
        equity = []
        initial_capital = 100000.0
        current_capital = initial_capital
        
        # 确保所有需要的列都存在且没有None值
        required_columns = ['date', 'open', 'high', 'low', 'close', 'signal', 'support_level', 'resistance_level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"缺少必要的列: {missing_columns}")
            logger.debug(f"现有的列: {df.columns.tolist()}")
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 处理所有可能的None值和无限值
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 确保日期格式正确
        if not isinstance(df['date'].iloc[0], str):
            df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M')
        
        # 遍历数据进行回测
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 更新持仓
            if position == 0:  # 没有持仓
                if current_row['signal'] == 1:  # 开多
                    position = 1
                    entry_price = float(current_row['close'])
                    trades.append({
                        'date': current_row['date'],
                        'type': 'buy',
                        'price': entry_price,
                        'profit': 0.0
                    })
                elif current_row['signal'] == -1:  # 开空
                    position = -1
                    entry_price = float(current_row['close'])
                    trades.append({
                        'date': current_row['date'],
                        'type': 'sell',
                        'price': entry_price,
                        'profit': 0.0
                    })
            
            elif position == 1:  # 持有多头
                if current_row['signal'] == -1:  # 平多
                    profit = float(current_row['close'] - entry_price)
                    current_capital += profit
                    position = 0
                    trades.append({
                        'date': current_row['date'],
                        'type': 'sell',
                        'price': float(current_row['close']),
                        'profit': profit
                    })
            
            elif position == -1:  # 持有空头
                if current_row['signal'] == 1:  # 平空
                    profit = float(entry_price - current_row['close'])
                    current_capital += profit
                    position = 0
                    trades.append({
                        'date': current_row['date'],
                        'type': 'buy',
                        'price': float(current_row['close']),
                        'profit': profit
                    })
            
            # 记录权益
            equity_point = {
                'date': current_row['date'],
                'equity': float(current_capital)
            }
            equity.append(equity_point)
        
        # 计算回测指标
        total_profit = float(current_capital - initial_capital)
        profit_trades = [t for t in trades if t['profit'] > 0]
        loss_trades = [t for t in trades if t['profit'] < 0]
        
        win_rate = float(len(profit_trades) / len(trades)) if trades else 0.0
        average_profit = float(sum(t['profit'] for t in profit_trades) / len(profit_trades)) if profit_trades else 0.0
        average_loss = float(sum(t['profit'] for t in loss_trades) / len(loss_trades)) if loss_trades else 0.0
        
        # 计算盈亏比，避免除以零和无限值
        if average_loss != 0 and not np.isinf(average_profit) and not np.isinf(average_loss):
            profit_factor = float(abs(average_profit / average_loss))
        else:
            profit_factor = 0.0
        
        logger.info(f"回测完成，总交易次数: {len(trades)}, 总收益率: {total_profit:.2f}")
        
        return {
            'trades': trades,
            'equity_curve': equity,
            'metrics': {
                'total_trades': len(trades),
                'win_rate': win_rate,
                'total_profit': total_profit,
                'average_profit': average_profit,
                'average_loss': average_loss,
                'profit_factor': profit_factor
            }
        } 