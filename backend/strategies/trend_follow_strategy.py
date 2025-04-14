import pandas as pd
import numpy as np
import talib
from typing import List, Dict
from utils.logger import logger

class TrendFollowStrategy:
    """豆粕均线趋势跟随策略"""

    @staticmethod
    def calculate_signals(df_15min: pd.DataFrame, df_60min: pd.DataFrame) -> pd.DataFrame:
        """计算交易信号"""
        logger.info("开始计算交易信号")
        
        # 确保时间索引对齐
        df_15min = df_15min.set_index('date')
        df_60min = df_60min.set_index('date')
        
        # 使用talib计算ATR
        df_15min['atr'] = talib.ATR(df_15min['high'], df_15min['low'], df_15min['close'], timeperiod=70)
        
        # 在60分钟数据中计算趋势方向
        df_60min['above_ema60'] = df_60min['close'] > df_60min['ema60']
        df_60min['prev_above_ema60'] = df_60min['above_ema60'].shift(1)
        df_60min['trend'] = 0
        # 多头趋势：当前和前一根K线都在EMA60上方
        df_60min.loc[(df_60min['above_ema60'] == True) & (df_60min['prev_above_ema60'] == True), 'trend'] = 1
        # 空头趋势：当前和前一根K线都在EMA60下方
        df_60min.loc[(df_60min['above_ema60'] == False) & (df_60min['prev_above_ema60'] == False), 'trend'] = -1
        
        # 使用talib计算15分钟EMA
        df_15min['ema12'] = talib.EMA(df_15min['close'], timeperiod=12)
        df_15min['ema26'] = talib.EMA(df_15min['close'], timeperiod=26)
        
        # 计算EMA斜率
        df_15min['ema12_slope'] = df_15min['ema12'].diff()
        df_15min['ema26_slope'] = df_15min['ema26'].diff()
        
        # 将60分钟趋势信息合并到15分钟数据中
        df_15min['trend'] = df_60min['trend'].reindex(df_15min.index, method='ffill')
        
        # 生成交易信号
        df_15min['trade_signal'] = 0
        
        # 多头条件：60分钟在EMA60上方，且15分钟EMA12和EMA26都向上
        long_condition = (
            (df_15min['trend'] == 1) & 
            (df_15min['ema12'] > df_15min['ema26']) &
            (df_15min['ema12_slope'] > 0) &
            (df_15min['ema26_slope'] > 0)
        )
        
        # 空头条件：60分钟在EMA60下方，且15分钟EMA12和EMA26都向下
        short_condition = (
            (df_15min['trend'] == -1) & 
            (df_15min['ema12'] < df_15min['ema26']) &
            (df_15min['ema12_slope'] < 0) &
            (df_15min['ema26_slope'] < 0)
        )
        
        # 生成交易信号
        df_15min.loc[long_condition, 'trade_signal'] = 1
        df_15min.loc[short_condition, 'trade_signal'] = -1
        
        # 只在信号变化时开仓
        df_15min['signal_change'] = df_15min['trade_signal'].diff()
        df_15min.loc[df_15min['signal_change'] == 0, 'trade_signal'] = 0
        
        logger.info("交易信号计算完成")
        return df_15min

    @staticmethod
    def run_backtest(df_15min: pd.DataFrame) -> Dict:
        """执行回测"""
        logger.info("开始执行回测")
        
        TAKE_PROFIT_MULTIPLE = 3.6  # ATR止盈倍数
        STOP_LOSS_MULTIPLE = 1.8    # ATR止损倍数
        
        trades: List[Dict] = []
        position = 0
        entry_price = 0
        entry_date = None
        entry_atr = 0
        total_pnl = 0
        returns = []
        monthly_profits = {}  # 用于存储月度盈亏
        
        last_trend = 0  # 记录上次交易的趋势
        trend_trade_count = 0  # 当前趋势下的交易次数
        
        for date, row in df_15min.iterrows():
            # 检查趋势是否改变
            if last_trend != row['trend']:
                trend_trade_count = 0  # 趋势改变，重置交易次数
                
            if position == 0:  # 没有持仓
                # 检查是否允许开仓：当前趋势下未交易
                if trend_trade_count >= 1:
                    continue  # 不满足开仓条件，跳过
                    
                if row['trade_signal'] != 0:
                    position = row['trade_signal']
                    entry_price = row['close']
                    entry_date = date
                    entry_atr = row['atr']
                    last_trend = row['trend']  # 记录开仓时的趋势
                    trend_trade_count += 1  # 增加当前趋势下的交易次数
                
            else:  # 有持仓
                # 计算止盈止损价位
                if position == 1:
                    take_profit = entry_price + (entry_atr * TAKE_PROFIT_MULTIPLE)
                    stop_loss = entry_price - (entry_atr * STOP_LOSS_MULTIPLE)
                    # 检查是否触及止盈止损
                    if row['high'] >= take_profit or row['low'] <= stop_loss or row['trade_signal'] == -1:
                        exit_price = round(take_profit) if row['high'] >= take_profit else (
                            round(stop_loss) if row['low'] <= stop_loss else round(row['close'])
                        )
                        pnl = position * (exit_price - entry_price)
                        total_pnl += pnl
                        returns.append(pnl / entry_price)
                        
                        trades.append({
                            'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                            'entry_price': float(entry_price),
                            'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                            'exit_price': float(exit_price),
                            'position': 'long',
                            'pnl': float(pnl) * 10,  # 每手10吨
                            'exit_type': 'take_profit' if row['high'] >= take_profit else (
                                'stop_loss' if row['low'] <= stop_loss else 'signal'
                            )
                        })
                        
                        position = 0  # 平仓
                        last_trend = row['trend']
                        
                else:  # position == -1
                    take_profit = entry_price - (entry_atr * TAKE_PROFIT_MULTIPLE)
                    stop_loss = entry_price + (entry_atr * STOP_LOSS_MULTIPLE)
                    # 检查是否触及止盈止损
                    if row['low'] <= take_profit or row['high'] >= stop_loss or row['trade_signal'] == 1:
                        exit_price = round(take_profit) if row['low'] <= take_profit else (
                            round(stop_loss) if row['high'] >= stop_loss else round(row['close'])
                        )
                        pnl = position * (exit_price - entry_price)
                        total_pnl += pnl
                        returns.append(pnl / entry_price)
                        
                        trades.append({
                            'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                            'entry_price': float(entry_price),
                            'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                            'exit_price': float(exit_price),
                            'position': 'short',
                            'pnl': float(pnl) * 10,  # 每手10吨
                            'exit_type': 'take_profit' if row['low'] <= take_profit else (
                                'stop_loss' if row['high'] >= stop_loss else 'signal'
                            )
                        })
                        
                        position = 0  # 平仓
                        last_trend = row['trend']
        
        # 计算月度盈亏
        for trade in trades:
            month_key = pd.to_datetime(trade['exit_date']).strftime('%Y-%m')
            if month_key not in monthly_profits:
                monthly_profits[month_key] = 0
            monthly_profits[month_key] += trade['pnl']
        
        # 计算回测指标
        returns = np.array(returns)
        total_returns = float(np.sum(returns))
        annual_returns = float(total_returns * (252 / len(df_15min)) * (24 / 4))  # 假设每天交易6小时，4个15分钟
        sharpe_ratio = float(np.mean(returns) / np.std(returns) * np.sqrt(252 * 24 / 4)) if len(returns) > 0 else 0
        max_drawdown = float(np.min(np.minimum.accumulate(np.cumprod(1 + returns)) - 1)) if len(returns) > 0 else 0
        win_rate = float(np.sum(returns > 0) / len(returns)) if len(returns) > 0 else 0
        
        # 计算总收益和手续费
        total_profit = sum(trade['pnl'] for trade in trades)  # 总收益（元）
        commission = len(trades) * 1.51  # 总手续费
        net_profit = total_profit - commission  # 净收益
        
        logger.info(f"回测完成，总交易次数: {len(trades)}, 总收益率: {total_returns:.2%}")
        
        return {
            'total_returns': total_returns,
            'annual_returns': annual_returns,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_profit': float(total_profit),  # 总收益（元）
            'commission': float(commission),      # 手续费（元）
            'net_profit': float(net_profit),      # 净收益（元）
            'monthly_profits': monthly_profits,   # 月度盈亏统计
            'trades': trades
        } 