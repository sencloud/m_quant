import pandas as pd
import numpy as np
import talib
from typing import List, Dict
from utils.logger import logger

class GridStrategy:
    """豆粕网格交易策略"""

    @staticmethod
    def calculate_signals(df: pd.DataFrame, grid_levels: int = 10, atr_period: int = 14) -> pd.DataFrame:
        """计算网格交易信号
        Args:
            df: 行情数据
            grid_levels: 网格数量
            atr_period: ATR周期
        """
        try:
            logger.info("开始计算网格交易信号")
            
            # 计算ATR用于动态调整网格范围
            df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=atr_period)
            
            # 计算布林带作为网格范围的参考
            df['sma20'] = talib.SMA(df['close'].values, timeperiod=20)
            df['std20'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['sma20'] + 2 * df['std20']
            df['bb_lower'] = df['sma20'] - 2 * df['std20']
            
            # 处理初始的NaN值
            df = df.fillna(method='bfill').fillna(method='ffill')
            
            # 计算网格
            df['grid_height'] = (df['bb_upper'] - df['bb_lower']) / grid_levels
            
            # 生成网格价位
            df['grids'] = df.apply(
                lambda x: [float(x['bb_lower'] + i * x['grid_height']) for i in range(grid_levels + 1)],
                axis=1
            )
            
            # 计算当前价格所在的网格位置
            df['current_grid'] = df.apply(
                lambda x: min(max(0, int(np.digitize(x['close'], x['grids']) - 1)), grid_levels - 1),
                axis=1
            )
            
            # 生成交易信号
            df['trade_signal'] = 0
            
            # 计算价格相对于当前网格的位置
            df['grid_position'] = df.apply(
                lambda x: (x['close'] - x['grids'][x['current_grid']]) / x['grid_height']
                if not pd.isna(x['grid_height']) and x['grid_height'] != 0
                else 0.5,
                axis=1
            )
            
            # 当价格接近上方网格时做空，接近下方网格时做多
            df.loc[df['grid_position'] > 0.8, 'trade_signal'] = -1  # 接近上方网格，做空
            df.loc[df['grid_position'] < 0.2, 'trade_signal'] = 1   # 接近下方网格，做多
            
            # 计算趋势强度，用于调整仓位
            df['trend_strength'] = (df['close'] - df['sma20']) / df['std20']
            
            logger.info("网格交易信号计算完成")
            return df
            
        except Exception as e:
            error_msg = f"计算网格交易信号失败: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def run_backtest(df: pd.DataFrame, grid_levels: int = 10) -> Dict:
        """执行回测
        Args:
            df: 行情数据
            grid_levels: 网格数量
        """
        logger.info("开始执行网格策略回测")
        
        initial_capital = 100000  # 初始资金10万元
        current_assets = initial_capital  # 当前资产总额
        position_size = current_assets * 0.95 / grid_levels  # 每个网格使用的资金
        
        trades: List[Dict] = []
        positions = {}  # 记录每个网格的持仓情况
        total_pnl = 0
        returns = []
        monthly_profits = {}
        
        for _, row in df.iterrows():
            # 获取当前网格价位
            current_grid = row['current_grid']
            grid_prices = row['grids']
            
            # 检查是否需要在当前网格位置开仓
            if row['trade_signal'] != 0:
                # 计算开仓数量（基于资金管理和趋势强度）
                position_multiplier = min(abs(row['trend_strength']), 2.0)  # 最大加倍2倍
                shares_per_lot = 100  # ETF每手100股
                max_lots = int(position_size * position_multiplier / (row['close'] * shares_per_lot))
                num_shares = max_lots * shares_per_lot
                
                if num_shares > 0:
                    grid_key = f"grid_{current_grid}"
                    
                    # 开仓
                    if row['trade_signal'] == 1 and grid_key not in positions:  # 做多
                        entry_price = row['close']
                        positions[grid_key] = {
                            'type': 'long',
                            'price': entry_price,
                            'shares': num_shares,
                            'date': row['date']
                        }
                        
                    elif row['trade_signal'] == -1 and grid_key not in positions:  # 做空
                        entry_price = row['close']
                        positions[grid_key] = {
                            'type': 'short',
                            'price': entry_price,
                            'shares': num_shares,
                            'date': row['date']
                        }
            
            # 检查是否需要平仓
            grids_to_remove = []
            for grid_key, position in positions.items():
                grid_num = int(grid_key.split('_')[1])
                
                # 计算止盈价位
                if position['type'] == 'long':
                    take_profit = grid_prices[grid_num + 1] if grid_num < len(grid_prices) - 1 else None
                    if take_profit and row['high'] >= take_profit:
                        # 平多仓
                        exit_price = take_profit
                        pnl = (exit_price - position['price']) * position['shares']
                        total_pnl += pnl
                        current_assets += pnl
                        returns.append(pnl / position_size)
                        
                        trades.append({
                            'entry_date': position['date'].strftime('%Y-%m-%d %H:%M'),
                            'entry_price': float(position['price']),
                            'exit_date': row['date'].strftime('%Y-%m-%d %H:%M'),
                            'exit_price': float(exit_price),
                            'position': 'long',
                            'shares': position['shares'],
                            'pnl': float(pnl),
                            'grid': grid_num
                        })
                        
                        grids_to_remove.append(grid_key)
                        
                else:  # short position
                    take_profit = grid_prices[grid_num - 1] if grid_num > 0 else None
                    if take_profit and row['low'] <= take_profit:
                        # 平空仓
                        exit_price = take_profit
                        pnl = (position['price'] - exit_price) * position['shares']
                        total_pnl += pnl
                        current_assets += pnl
                        returns.append(pnl / position_size)
                        
                        trades.append({
                            'entry_date': position['date'].strftime('%Y-%m-%d %H:%M'),
                            'entry_price': float(position['price']),
                            'exit_date': row['date'].strftime('%Y-%m-%d %H:%M'),
                            'exit_price': float(exit_price),
                            'position': 'short',
                            'shares': position['shares'],
                            'pnl': float(pnl),
                            'grid': grid_num
                        })
                        
                        grids_to_remove.append(grid_key)
            
            # 移除已平仓的网格
            for grid_key in grids_to_remove:
                del positions[grid_key]
        
        # 处理未平仓的持仓
        last_row = df.iloc[-1]
        for grid_key, position in positions.items():
            exit_price = last_row['close']
            if position['type'] == 'long':
                pnl = (exit_price - position['price']) * position['shares']
            else:
                pnl = (position['price'] - exit_price) * position['shares']
            
            total_pnl += pnl
            current_assets += pnl
            returns.append(pnl / position_size)
            
            trades.append({
                'entry_date': position['date'].strftime('%Y-%m-%d %H:%M'),
                'entry_price': float(position['price']),
                'exit_date': last_row['date'].strftime('%Y-%m-%d %H:%M'),
                'exit_price': float(exit_price),
                'position': position['type'],
                'shares': position['shares'],
                'pnl': float(pnl),
                'grid': int(grid_key.split('_')[1])
            })
        
        # 计算月度盈亏
        for trade in trades:
            month_key = pd.to_datetime(trade['exit_date']).strftime('%Y-%m')
            if month_key not in monthly_profits:
                monthly_profits[month_key] = 0
            monthly_profits[month_key] += trade['pnl']
        
        # 计算回测指标
        returns = np.array(returns)
        total_returns = float(np.prod(1 + returns) - 1)  # 使用几何平均计算总收益
        
        # 计算年化收益率
        if len(df) > 0:
            time_span = (df['date'].max() - df['date'].min()).days / 365.0
            annual_returns = float((1 + total_returns) ** (1 / time_span) - 1) if time_span > 0 else 0.0
        else:
            annual_returns = 0.0
        
        # 计算夏普比率
        risk_free_rate = 0.0
        if len(returns) > 0:
            excess_returns = returns - risk_free_rate
            sharpe_ratio = float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
        else:
            sharpe_ratio = 0.0
        
        # 计算最大回撤
        portfolio_values = np.array([initial_capital] + [initial_capital * (1 + ret) for ret in returns])
        peak = np.maximum.accumulate(portfolio_values)
        drawdowns = (peak - portfolio_values) / peak
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        logger.info(f"回测完成，总交易次数: {len(trades)}, 总收益率: {total_returns:.2%}")
        
        return {
            'total_returns': total_returns,
            'annual_returns': annual_returns,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': float(np.sum(returns > 0) / len(returns)) if len(returns) > 0 else 0.0,
            'total_profit': float(total_pnl),
            'final_assets': float(current_assets),
            'monthly_profits': {k: float(v) for k, v in monthly_profits.items()},
            'trades': trades
        } 