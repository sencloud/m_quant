import pandas as pd
import numpy as np
import talib
from typing import List, Dict
from utils.logger import logger

class DualMAStrategy:
    """双均线策略 - EMA8和EMA21"""

    @staticmethod
    def calculate_signals(df: pd.DataFrame, use_atr_tp: bool = False) -> pd.DataFrame:
        """计算交易信号
        Args:
            df: 行情数据
            use_atr_tp: 是否使用ATR止盈
        """
        logger.info("开始计算交易信号")
        
        # 确保时间索引对齐
        df = df.set_index('date')
        
        # 计算EMA8和EMA21
        df['ema8'] = talib.EMA(df['close'], timeperiod=8)
        df['ema21'] = talib.EMA(df['close'], timeperiod=21)
        
        # 计算金叉死叉
        df['cross_over'] = (df['ema8'] > df['ema21']) & (df['ema8'].shift(1) <= df['ema21'].shift(1))
        df['cross_under'] = (df['ema8'] < df['ema21']) & (df['ema8'].shift(1) >= df['ema21'].shift(1))
        
        # 如果开启ATR止盈，计算ATR
        if use_atr_tp:
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=10)
            df['tp_price'] = df['close'] + df['atr'] * 1.1  # 1.1倍ATR止盈价可以达到100%胜率
        
        # 生成交易信号
        df['trade_signal'] = 0
        df.loc[df['cross_over'], 'trade_signal'] = 1  # 金叉做多
        df.loc[df['cross_under'], 'trade_signal'] = -1  # 死叉平仓
        
        logger.info("交易信号计算完成")
        return df

    @staticmethod
    def run_backtest(df: pd.DataFrame, use_atr_tp: bool = False) -> Dict:
        """执行回测
        Args:
            df: 行情数据
            use_atr_tp: 是否使用ATR止盈
        """
        logger.info("开始执行回测")
        
        initial_capital = 100000  # 初始资金10万元
        current_assets = initial_capital  # 当前资产总额
        position_size = current_assets * 0.95  # 每次使用95%的当前资产
        
        trades: List[Dict] = []
        position = 0
        entry_price = 0
        entry_date = None
        total_pnl = 0
        returns = []
        monthly_profits = {}
        
        for date, row in df.iterrows():
            if position == 0:  # 没有持仓
                if row['trade_signal'] == 1:  # 金叉开多
                    position = 1
                    entry_price = row['close']
                    entry_date = date
                    # 计算可以开的手数（每手100股）
                    shares_per_lot = 100  # ETF每手100股
                    max_lots = int(position_size / (entry_price * shares_per_lot))  # 可以开的手数
                    num_shares = max_lots * shares_per_lot  # 实际交易股数
                    
            elif position == 1:  # 持有多仓
                should_exit = False
                exit_type = 'signal'
                
                # 检查是否触发ATR止盈
                if use_atr_tp and row['high'] >= row['tp_price']:
                    should_exit = True
                    exit_type = 'atr_tp'
                
                # 检查是否触发死叉平仓
                if row['trade_signal'] == -1:
                    should_exit = True
                    exit_type = 'signal'
                
                if should_exit:
                    exit_price = row['close']
                    # 计算盈亏
                    pnl = (exit_price - entry_price) * num_shares
                    total_pnl += pnl
                    current_assets += pnl  # 更新当前资产总额
                    position_size = current_assets * 0.95  # 更新下次可用的资金
                    returns.append(pnl / position_size)  # 使用实际使用的资金计算收益率
                    
                    # 计算开平仓手续费
                    entry_commission = entry_price * num_shares * 0.0025 / 100  # 开仓手续费
                    exit_commission = exit_price * num_shares * 0.0025 / 100   # 平仓手续费
                    total_commission = entry_commission + exit_commission
                    
                    trades.append({
                        'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                        'entry_price': float(entry_price),
                        'exit_date': date.strftime('%Y-%m-%d %H:%M'),
                        'exit_price': float(exit_price),
                        'position': 'long',
                        'shares': num_shares,
                        'pnl': float(pnl),
                        'commission': float(total_commission),
                        'exit_type': exit_type
                    })
                    
                    position = 0
        
        # 计算月度盈亏
        for trade in trades:
            month_key = pd.to_datetime(trade['exit_date']).strftime('%Y-%m')
            if month_key not in monthly_profits:
                monthly_profits[month_key] = 0
            monthly_profits[month_key] += trade['pnl']
        
        # 处理最后一个未平仓的持仓
        if position == 1:
            last_row = df.iloc[-1]
            exit_price = last_row['close']
            pnl = (exit_price - entry_price) * num_shares
            total_pnl += pnl
            current_assets += pnl
            returns.append(pnl / position_size)
            
            entry_commission = entry_price * num_shares * 0.0025 / 100
            exit_commission = exit_price * num_shares * 0.0025 / 100
            total_commission = entry_commission + exit_commission
            
            trades.append({
                'entry_date': entry_date.strftime('%Y-%m-%d %H:%M'),
                'entry_price': float(entry_price),
                'exit_date': df.index[-1].strftime('%Y-%m-%d %H:%M'),
                'exit_price': float(exit_price),
                'position': 'long',
                'shares': num_shares,
                'pnl': float(pnl),
                'commission': float(total_commission),
                'exit_type': 'last_position'
            })
        
        # 计算回测指标
        returns = np.array(returns)
        total_returns = float(np.prod(1 + returns) - 1)  # 使用几何平均计算总收益
        
        # 根据数据周期确定年化因子
        if len(df) > 0:
            # 计算数据的时间跨度（年）
            time_span = (df.index[-1] - df.index[0]).days / 365.0
            
            # 计算年化收益率
            if time_span > 0:
                annual_returns = float((1 + total_returns) ** (1 / time_span) - 1)
            else:
                annual_returns = 0.0
        else:
            annual_returns = 0.0

        # 计算夏普比率 (假设无风险利率为0)
        risk_free_rate = 0.0
        excess_returns = returns - risk_free_rate

        # 根据数据周期确定年化因子
        if len(df) > 0:
            # 计算数据的时间跨度（年）
            time_span = (df.index[-1] - df.index[0]).days / 365.0
            
            # 计算年化因子
            if time_span > 0:
                # 计算平均每个交易日的收益率数量
                daily_returns_count = len(returns) / (time_span * 252)  # 252是每年的交易日数
                annualization_factor = np.sqrt(daily_returns_count * 252)
            else:
                annualization_factor = 1.0
        else:
            annualization_factor = 1.0

        # 计算夏普比率
        if len(returns) > 0:
            sharpe_ratio = float(np.mean(excess_returns) / np.std(excess_returns) * annualization_factor)
        else:
            sharpe_ratio = 0.0
        
        # 计算最大回撤
        portfolio_values = [initial_capital]
        for ret in returns:
            portfolio_values.append(portfolio_values[-1] * (1 + ret))
        portfolio_values = np.array(portfolio_values)
        peak = np.maximum.accumulate(portfolio_values)
        drawdowns = (peak - portfolio_values) / peak
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        # 计算总收益和手续费
        total_profit = float(sum(trade['pnl'] for trade in trades))
        commission = float(sum(trade['commission'] for trade in trades))
        net_profit = float(total_profit - commission)
        
        # 确保月度盈亏中的值都是float类型
        monthly_profits = {k: float(v) for k, v in monthly_profits.items()}
        
        # 确保trades中的数值都是float类型
        for trade in trades:
            trade['entry_price'] = float(trade['entry_price'])
            trade['exit_price'] = float(trade['exit_price'])
            trade['pnl'] = float(trade['pnl'])
            trade['commission'] = float(trade['commission'])
            trade['shares'] = int(trade['shares'])  # 股数保持为整数
        
        logger.info(f"回测完成，总交易次数: {len(trades)}, 总收益率: {total_returns:.2%}")
        
        return {
            'total_returns': total_returns,
            'annual_returns': annual_returns,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': float(np.sum(returns > 0) / len(returns)) if len(returns) > 0 else 0.0,
            'total_profit': total_profit,
            'commission': commission,
            'net_profit': net_profit,
            'monthly_profits': monthly_profits,
            'trades': trades
        } 