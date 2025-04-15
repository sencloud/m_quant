import pandas as pd
import numpy as np
import talib
from typing import List, Dict
from utils.logger import logger

class OBVADXEMAStrategy:
    """基于OBV与EMA的组合策略"""

    @staticmethod
    def calculate_signals(df_60min: pd.DataFrame) -> pd.DataFrame:
        """计算交易信号"""
        logger.info("开始计算OBV与EMA组合策略信号")
        
        # 确保时间索引对齐
        df_60min = df_60min.set_index('date')
        
        # 计算EMA指标
        df_60min['ema20'] = talib.EMA(df_60min['close'], timeperiod=20)
        
        # 计算OBV指标
        df_60min['obv'] = talib.OBV(df_60min['close'], df_60min['volume'])
        
        # 计算OBV变化率
        df_60min['obv_change'] = df_60min['obv'].diff()
        
        # 生成交易信号
        df_60min['trade_signal'] = 0
        
        # 计算K线实体
        df_60min['body_high'] = df_60min[['open', 'close']].max(axis=1)
        df_60min['body_low'] = df_60min[['open', 'close']].min(axis=1)
        
        # 多头条件
        long_condition = (
            (df_60min['body_low'] > df_60min['ema20']) &  # K线实体在EMA20上方
            (df_60min['obv_change'] > 0)  # OBV上升
        )
        
        # 空头条件
        short_condition = (
            (df_60min['body_high'] < df_60min['ema20']) &  # K线实体在EMA20下方
            (df_60min['obv_change'] < 0)  # OBV下降
        )
        
        # 生成交易信号
        df_60min.loc[long_condition, 'trade_signal'] = 1
        df_60min.loc[short_condition, 'trade_signal'] = -1
        
        # 只在信号变化时开仓
        df_60min['signal_change'] = df_60min['trade_signal'].diff()
        df_60min.loc[df_60min['signal_change'] == 0, 'trade_signal'] = 0
        
        logger.info("OBV与EMA组合策略信号计算完成")
        return df_60min

    @staticmethod
    def run_backtest(df_60min: pd.DataFrame) -> Dict:
        """执行回测"""
        logger.info("开始执行OBV与EMA组合策略回测")
        
        FIXED_POINTS = 15  # 固定止盈止损点数
        
        trades: List[Dict] = []
        position = 0
        entry_price = 0
        entry_date = None
        total_pnl = 0
        returns = []
        monthly_profits = {}  # 用于存储月度盈亏
        trailing_profit = 0  # 用于记录跟踪止盈金额
        
        for date, row in df_60min.iterrows():
            if position == 0:  # 没有持仓
                if row['trade_signal'] != 0:
                    position = row['trade_signal']
                    entry_price = row['close']
                    entry_date = date
                    trailing_profit = 0  # 重置跟踪止盈金额
                
            else:  # 有持仓
                if position == 1:  # 多头
                    # 计算止损价和止盈价
                    stop_loss = entry_price - FIXED_POINTS + 5
                    take_profit = entry_price + FIXED_POINTS
                    
                    # 检查是否触及止损
                    if row['close'] <= stop_loss:
                        exit_price = row['close']
                        exit_price = int(round(exit_price))
                        pnl = position * (exit_price - entry_price)
                        total_pnl += pnl
                        returns.append(pnl / entry_price)
                        
                        trades.append({
                            'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                            'entry_price': float(entry_price),
                            'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                            'exit_price': exit_price,
                            'position': 'long',
                            'pnl': float(pnl) * 10,  # 每手10吨
                            'exit_type': 'stop_loss'
                        })
                        
                        position = 0
                        trailing_profit = 0
                    
                    # 检查是否触及止盈条件
                    elif row['close'] >= take_profit:
                        # 如果OBV继续上升，记录当前止盈金额并继续持有
                        if row['obv_change'] > 0:
                            current_profit = (row['close'] - entry_price) * 10
                            trailing_profit = max(trailing_profit, current_profit)
                        # 如果OBV开始下降，立即止盈
                        else:
                            exit_price = row['close']
                            exit_price = int(round(exit_price))
                            pnl = position * (exit_price - entry_price)
                            total_pnl += pnl
                            returns.append(pnl / entry_price)
                            
                            trades.append({
                                'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                                'entry_price': float(entry_price),
                                'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                                'exit_price': exit_price,
                                'position': 'long',
                                'pnl': float(pnl) * 10,  # 每手10吨
                                'exit_type': 'take_profit'
                            })
                            
                            position = 0
                            trailing_profit = 0
                        
                else:  # 空头
                    # 计算止损价和止盈价
                    stop_loss = entry_price + FIXED_POINTS - 5
                    take_profit = entry_price - FIXED_POINTS
                    
                    # 检查是否触及止损
                    if row['close'] >= stop_loss:
                        exit_price = row['close']
                        exit_price = int(round(exit_price))
                        pnl = position * (exit_price - entry_price)
                        total_pnl += pnl
                        returns.append(pnl / entry_price)
                        
                        trades.append({
                            'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                            'entry_price': float(entry_price),
                            'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                            'exit_price': exit_price,
                            'position': 'short',
                            'pnl': float(pnl) * 10,  # 每手10吨
                            'exit_type': 'stop_loss'
                        })
                        
                        position = 0
                        trailing_profit = 0
                    
                    # 检查是否触及止盈条件
                    elif row['close'] <= take_profit:
                        # 如果OBV继续下降，记录当前止盈金额并继续持有
                        if row['obv_change'] < 0:
                            current_profit = (entry_price - row['close']) * 10
                            trailing_profit = max(trailing_profit, current_profit)
                        # 如果OBV开始上升，立即止盈
                        else:
                            exit_price = row['close']
                            exit_price = int(round(exit_price))
                            pnl = position * (exit_price - entry_price)
                            total_pnl += pnl
                            returns.append(pnl / entry_price)
                            
                            trades.append({
                                'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                                'entry_price': float(entry_price),
                                'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                                'exit_price': exit_price,
                                'position': 'short',
                                'pnl': float(pnl) * 10,  # 每手10吨
                                'exit_type': 'take_profit'
                            })
                            
                            position = 0
                            trailing_profit = 0
        
        # 计算月度盈亏
        for trade in trades:
            month_key = pd.to_datetime(trade['exit_date']).strftime('%Y-%m')
            if month_key not in monthly_profits:
                monthly_profits[month_key] = 0
            monthly_profits[month_key] += trade['pnl']
        
        # 计算回测指标
        returns = np.array(returns)
        total_returns = float(np.sum(returns))
        annual_returns = float(total_returns * (252 / len(df_60min)))  # 假设每天交易4小时
        sharpe_ratio = float(np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 0 else 0
        max_drawdown = float(np.min(np.minimum.accumulate(np.cumprod(1 + returns)) - 1)) if len(returns) > 0 else 0
        win_rate = float(np.sum(returns > 0) / len(returns)) if len(returns) > 0 else 0
        
        # 计算总收益和手续费
        total_profit = sum(trade['pnl'] for trade in trades)  # 总收益（元）
        commission = len(trades) * 1.51  # 总手续费
        net_profit = total_profit - commission  # 净收益
        
        logger.info(f"OBV与EMA组合策略回测完成，总交易次数: {len(trades)}, 总收益率: {total_returns:.2%}")
        
        return {
            'total_returns': total_returns * 100,
            'annual_returns': annual_returns * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'total_profit': float(total_profit),  # 总收益（元）
            'commission': float(commission),      # 手续费（元）
            'net_profit': float(net_profit),      # 净收益（元）
            'monthly_profits': monthly_profits,   # 月度盈亏统计
            'trades': trades
        } 