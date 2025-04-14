import pandas as pd
import numpy as np
import talib
from typing import List, Dict
from utils.logger import logger

class OBVADXEMAStrategy:
    """基于OBV、ADX与EMA均线的组合策略"""

    @staticmethod
    def calculate_signals(df_60min: pd.DataFrame) -> pd.DataFrame:
        """计算交易信号"""
        logger.info("开始计算OBV、ADX与EMA组合策略信号")
        
        # 确保时间索引对齐
        df_60min = df_60min.set_index('date')
        
        # 计算EMA指标
        df_60min['ema20'] = talib.EMA(df_60min['close'], timeperiod=20)
        df_60min['ema60'] = talib.EMA(df_60min['close'], timeperiod=60)
        
        # 计算EMA斜率
        df_60min['ema20_slope'] = df_60min['ema20'].diff()
        df_60min['ema60_slope'] = df_60min['ema60'].diff()
        
        # 计算ADX指标
        df_60min['adx'] = talib.ADX(df_60min['high'], df_60min['low'], df_60min['close'], timeperiod=14)
        df_60min['plus_di'] = talib.PLUS_DI(df_60min['high'], df_60min['low'], df_60min['close'], timeperiod=14)
        df_60min['minus_di'] = talib.MINUS_DI(df_60min['high'], df_60min['low'], df_60min['close'], timeperiod=14)
        
        # 计算OBV指标
        df_60min['obv'] = talib.OBV(df_60min['close'], df_60min['volume'])
        df_60min['obv_ma30'] = talib.SMA(df_60min['obv'], timeperiod=30)
        
        # 计算OBV变化率
        df_60min['obv_change'] = df_60min['obv'].diff()
        df_60min['obv_change_ma5'] = df_60min['obv_change'].rolling(5).mean()
        
        # 计算ATR用于止损
        df_60min['atr'] = talib.ATR(df_60min['high'], df_60min['low'], df_60min['close'], timeperiod=14)
        
        # 计算布林带
        df_60min['bb_upper'], df_60min['bb_middle'], df_60min['bb_lower'] = talib.BBANDS(
            df_60min['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        
        # 计算EMA5用于跟踪止盈
        df_60min['ema5'] = talib.EMA(df_60min['close'], timeperiod=5)
        
        # 计算前15分钟震荡区间
        df_60min['high_15'] = df_60min['high'].rolling(15).max()
        df_60min['low_15'] = df_60min['low'].rolling(15).min()
        
        # 计算连续阳线/阴线
        df_60min['is_red'] = df_60min['close'] > df_60min['open']
        df_60min['is_green'] = df_60min['close'] < df_60min['open']
        
        # 计算连续3根阳线/阴线
        df_60min['red_count'] = df_60min['is_red'].rolling(3).sum()
        df_60min['green_count'] = df_60min['is_green'].rolling(3).sum()
        
        # 计算成交量均量
        df_60min['volume_ma5'] = df_60min['volume'].rolling(5).mean()
        
        # 生成交易信号
        df_60min['trade_signal'] = 0
        
        # 多头条件
        long_condition = (
            (df_60min['ema20'] > df_60min['ema60']) &  # EMA20在EMA60上方
            (df_60min['ema20_slope'] > 0) &  # EMA20斜率向上
            (df_60min['adx'] >= 25) &  # ADX大于等于25
            (df_60min['adx'] > df_60min['adx'].shift(1)) &  # ADX上升
            (df_60min['obv'] > df_60min['obv_ma30']) &  # OBV上穿30周期均线
            (df_60min['volume'] > df_60min['volume_ma5'] * 1.5) &  # 成交量放大
            (
                (df_60min['close'] > df_60min['high_15'].shift(1)) |  # 突破前15分钟震荡区间上沿
                (df_60min['red_count'] >= 3)  # 连续3根阳线
            )
        )
        
        # 空头条件
        short_condition = (
            (df_60min['ema20'] < df_60min['ema60']) &  # EMA20在EMA60下方
            (df_60min['ema20_slope'] < 0) &  # EMA20斜率向下
            (df_60min['adx'] >= 25) &  # ADX大于等于25
            (df_60min['adx'] > df_60min['adx'].shift(1)) &  # ADX上升
            (df_60min['obv'] < df_60min['obv_ma30']) &  # OBV下穿30周期均线
            (df_60min['volume'] < df_60min['volume_ma5'] * 0.8) &  # 成交量萎缩
            (
                (df_60min['close'] < df_60min['low_15'].shift(1)) |  # 跌破前15分钟震荡区间下沿
                (df_60min['green_count'] >= 3)  # 连续3根阴线
            )
        )
        
        # 生成交易信号
        df_60min.loc[long_condition, 'trade_signal'] = 1
        df_60min.loc[short_condition, 'trade_signal'] = -1
        
        # 只在信号变化时开仓
        df_60min['signal_change'] = df_60min['trade_signal'].diff()
        df_60min.loc[df_60min['signal_change'] == 0, 'trade_signal'] = 0
        
        logger.info("OBV、ADX与EMA组合策略信号计算完成")
        return df_60min

    @staticmethod
    def run_backtest(df_60min: pd.DataFrame) -> Dict:
        """执行回测"""
        logger.info("开始执行OBV、ADX与EMA组合策略回测")
        
        STOP_LOSS_MULTIPLE = 1.5  # ATR止损倍数
        ADX_THRESHOLD = 25  # ADX强趋势阈值
        
        trades: List[Dict] = []
        position = 0
        entry_price = 0
        entry_date = None
        entry_atr = 0
        total_pnl = 0
        returns = []
        monthly_profits = {}  # 用于存储月度盈亏
        
        # 用于跟踪止盈
        trailing_stop_price = 0
        profit_target_reached = False
        
        for date, row in df_60min.iterrows():
            if position == 0:  # 没有持仓
                if row['trade_signal'] != 0:
                    position = row['trade_signal']
                    entry_price = row['close']
                    entry_date = date
                    entry_atr = row['atr']
                    trailing_stop_price = 0
                    profit_target_reached = False
                
            else:  # 有持仓
                if position == 1:  # 多头
                    # 计算止损价
                    stop_loss = entry_price - (entry_atr * STOP_LOSS_MULTIPLE)
                    
                    # 计算止盈价
                    take_profit = entry_price + (entry_atr * STOP_LOSS_MULTIPLE)  # 1:1风险回报比
                    
                    # 检查是否达到止盈目标
                    if not profit_target_reached and row['high'] >= take_profit:
                        profit_target_reached = True
                        trailing_stop_price = entry_price  # 移动止损到成本价
                    
                    # 如果已经达到止盈目标，使用EMA5作为跟踪止损
                    if profit_target_reached:
                        trailing_stop_price = max(trailing_stop_price, row['ema5'])
                    
                    # 检查是否触及止损或反向信号
                    if (row['low'] <= stop_loss) or (row['trade_signal'] == -1) or (profit_target_reached and row['low'] <= trailing_stop_price):
                        exit_price = row['close']
                        if row['low'] <= stop_loss:
                            exit_price = stop_loss
                        elif profit_target_reached and row['low'] <= trailing_stop_price:
                            exit_price = trailing_stop_price
                            
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
                            'exit_type': 'stop_loss' if row['low'] <= stop_loss else 
                                        'trailing_stop' if profit_target_reached and row['low'] <= trailing_stop_price else 'signal'
                        })
                        
                        position = 0
                        
                else:  # 空头
                    # 计算止损价
                    stop_loss = entry_price + (entry_atr * STOP_LOSS_MULTIPLE)
                    
                    # 计算止盈价
                    take_profit = entry_price - (entry_atr * STOP_LOSS_MULTIPLE)  # 1:1风险回报比
                    
                    # 检查是否达到止盈目标
                    if not profit_target_reached and row['low'] <= take_profit:
                        profit_target_reached = True
                        trailing_stop_price = entry_price  # 移动止损到成本价
                    
                    # 如果已经达到止盈目标，使用EMA5作为跟踪止损
                    if profit_target_reached:
                        trailing_stop_price = min(trailing_stop_price, row['ema5'])
                    
                    # 检查是否触及止损或反向信号
                    if (row['high'] >= stop_loss) or (row['trade_signal'] == 1) or (profit_target_reached and row['high'] >= trailing_stop_price):
                        exit_price = row['close']
                        if row['high'] >= stop_loss:
                            exit_price = stop_loss
                        elif profit_target_reached and row['high'] >= trailing_stop_price:
                            exit_price = trailing_stop_price
                            
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
                            'exit_type': 'stop_loss' if row['high'] >= stop_loss else 
                                        'trailing_stop' if profit_target_reached and row['high'] >= trailing_stop_price else 'signal'
                        })
                        
                        position = 0
        
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
        
        logger.info(f"OBV、ADX与EMA组合策略回测完成，总交易次数: {len(trades)}, 总收益率: {total_returns:.2%}")
        
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