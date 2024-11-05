import backtrader as bt
from datetime import datetime
import logging
from ..models.trade_strategy import SimpleTradeStrategy
from ...strategies.short_term_strategy import ShortTermStrategy
from ...strategies.medium_term_strategy import MediumTermStrategy
from ...strategies.long_term_strategy import LongTermStrategy
from ...data.stock_data import StockData
from ...data.process_data import ProcessData

logger = logging.getLogger(__name__)

class BacktestService:
    STRATEGY_MAP = {
        'short_term': ShortTermStrategy,
        'medium_term': MediumTermStrategy,
        'long_term': LongTermStrategy
    }

    @staticmethod
    def run_backtest(params):
        """运行回测"""
        try:
            # 创建Cerebro引擎
            cerebro = bt.Cerebro()
            
            # 设置初始资金
            initial_capital = float(params.get('initialCapital', 100000))
            cerebro.broker.setcash(initial_capital)
            
            # 设置手续费
            commission = float(params.get('commission', 0.003))
            cerebro.broker.setcommission(commission=commission)
            
            # 准备数据
            start_date = datetime.strptime(params['startDate'], '%Y-%m-%d')
            end_date = datetime.strptime(params['endDate'], '%Y-%m-%d')
            
            stock_data = ProcessData.get_stock_data(
                params['stock'],
                params['startDate'],
                params['endDate']
            )
            data_feed = StockData(
                dataname=stock_data,
                fromdate=start_date,
                todate=end_date
            )
            cerebro.adddata(data_feed)
            
            # 添加策略
            strategy_class = BacktestService.STRATEGY_MAP.get(params['strategy'])
            if not strategy_class:
                raise ValueError(f"Invalid strategy: {params['strategy']}")
                
            strategy_params = BacktestService._prepare_strategy_params(params)
            cerebro.addstrategy(strategy_class, **strategy_params)
            
            # 添加分析器
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            
            # 运行回测
            results = cerebro.run()
            
            # 处理结果
            return BacktestService._process_results(results)
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _prepare_strategy_params(params):
        """准备策略参数"""
        return {
            'code': params['stock'],
            'start_date': datetime.strptime(params['startDate'], '%Y-%m-%d'),
            'end_date': datetime.strptime(params['endDate'], '%Y-%m-%d'),
            'position_size_type': params.get('positionSizeType', 'fixed'),
            'position_size': float(params.get('positionSize', 100)),
            'stop_loss': float(params.get('stopLoss', 5)) / 100,
            'take_profit': float(params.get('takeProfit', 10)) / 100,
            'trailing_stop': float(params.get('trailingStop', 0)) / 100,
        }

    @staticmethod
    def _process_results(results):
        """处理回测结果"""
        if not results:
            logger.warning("No results returned from backtest")
            return None
            
        strategy = results[0]
        logger.debug(f"Processing results for strategy: {strategy}")
        
        # 检查交易数据
        if not hasattr(strategy, 'trades'):
            logger.error("Strategy does not have trades attribute")
            return None
            
        trades_analyzer = strategy.analyzers.trades.get_analysis()
        sharpe_analyzer = strategy.analyzers.sharpe.get_analysis()
        drawdown_analyzer = strategy.analyzers.drawdown.get_analysis()
        
        logger.debug(f"Found {len(strategy.trades)} trades")
        logger.debug(f"Trades analyzer data: {trades_analyzer}")
        
        # 计算基础指标
        total_trades = len(strategy.trades)
        won_trades = len([t for t in strategy.trades if t.get('pnl', 0) > 0])
        
        # 计算收益率
        initial_value = strategy.broker.startingcash
        final_value = strategy.broker.getvalue()
        total_return = final_value - initial_value
        
        logger.debug(f"Basic metrics - total_trades: {total_trades}, won_trades: {won_trades}, total_return: {total_return}")
        
        return {
            'metrics': BacktestService._calculate_metrics(
                strategy, trades_analyzer, sharpe_analyzer, drawdown_analyzer,
                total_trades, won_trades, total_return
            ),
            'chartData': BacktestService._prepare_chart_data(strategy),
            'trades': BacktestService._prepare_trades_list(strategy)
        }

    @staticmethod
    def _calculate_metrics(strategy, trades_analyzer, sharpe_analyzer, 
                         drawdown_analyzer, total_trades, won_trades, total_return):
        """计算回测指标"""
        try:
            logger.debug(f"Starting metrics calculation with: total_trades={total_trades}, won_trades={won_trades}")
            
            # 从嵌套的 AutoOrderedDict 中正确获取 PNL 值
            won_pnl = trades_analyzer.get('won', {}).get('pnl', {}).get('total', 0)
            lost_pnl = abs(trades_analyzer.get('lost', {}).get('pnl', {}).get('total', 1))  # 默认值为1避免除以0
            
            logger.debug(f"Raw PNL values - won_pnl: {won_pnl}, lost_pnl: {lost_pnl}")

            # 计算盈利因子
            profit_factor = abs(won_pnl / lost_pnl) if lost_pnl != 0 else 0
            logger.debug(f"Calculated profit factor: {profit_factor}")

            # 安全地获取夏普比率
            sharpe = sharpe_analyzer.get('sharperatio', 0)
            if sharpe is None or isinstance(sharpe, (list, tuple)) and not sharpe:
                sharpe = 0
            elif isinstance(sharpe, (list, tuple)):
                sharpe = sharpe[0] if sharpe[0] is not None else 0
            logger.debug(f"Processed Sharpe ratio: {sharpe}")

            # 安全地获取最大回撤
            max_drawdown = drawdown_analyzer.get('max', {}).get('drawdown', 0)
            if max_drawdown is None:
                max_drawdown = 0
            elif isinstance(max_drawdown, (list, tuple)):
                max_drawdown = max_drawdown[0] if max_drawdown[0] is not None else 0
            logger.debug(f"Processed max drawdown: {max_drawdown}")

            # 计算胜率
            win_rate = (won_trades / total_trades) if total_trades > 0 else 0
            logger.debug(f"Calculated win rate: {win_rate}")

            # 安全地从交易分析器获取更多指标
            avg_trade = trades_analyzer.get('pnl', {}).get('net', {}).get('average', 0) or 0
            max_win = trades_analyzer.get('won', {}).get('pnl', {}).get('max', 0) or 0
            max_loss = abs(trades_analyzer.get('lost', {}).get('pnl', {}).get('max', 0) or 0)
            
            metrics = {
                'totalReturn': round(float(total_return or 0), 2),
                'winRate': round(float(win_rate * 100 or 0), 2),  # 转换为百分比
                'sharpeRatio': round(float(sharpe or 0), 2),
                'profitFactor': round(float(profit_factor or 0), 2),
                'totalTrades': int(total_trades or 0),
                'wonTrades': int(won_trades or 0),
                'lostTrades': int((total_trades - won_trades) if total_trades and won_trades else 0),
                'maxDrawdown': round(float(max_drawdown * 100 or 0), 2),  # 转换为百分比
                'averageTrade': round(float(avg_trade or 0), 2),
                'maxWin': round(float(max_win or 0), 2),
                'maxLoss': round(float(max_loss or 0), 2)
            }
            
            logger.debug(f"Final metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}", exc_info=True)
            logger.error(f"Trades analyzer data: {trades_analyzer}")
            logger.error(f"Sharpe analyzer data: {sharpe_analyzer}")
            logger.error(f"Drawdown analyzer data: {drawdown_analyzer}")
            
            # 返回默认值
            return {
                'totalReturn': 0,
                'winRate': 0,
                'sharpeRatio': 0,
                'profitFactor': 0,
                'totalTrades': 0,
                'wonTrades': 0,
                'lostTrades': 0,
                'maxDrawdown': 0,
                'averageTrade': 0,
                'maxWin': 0,
                'maxLoss': 0
            }

    @staticmethod
    def _prepare_chart_data(strategy):
        """准备图表数据"""
        try:
            # 获取有效数据长度
            valid_length = len(strategy.data)
            logger.debug(f"Starting chart data preparation with {valid_length} data points")
            
            chart_data = []
            
            for i in range(valid_length):
                try:
                    # 计算当前索引
                    current_index = 0 - (valid_length - 1 - i)
                    
                    # 创建基础数据点
                    data_point = {
                        'date': strategy.data.datetime.datetime(current_index).date().isoformat(),
                        'close': float(strategy.data.close[current_index])
                    }
                    
                    # 添加移动平均线数据
                    if hasattr(strategy, 'ma5'):
                        data_point['ma5'] = float(strategy.ma5[current_index])
                    if hasattr(strategy, 'ma10'):
                        data_point['ma10'] = float(strategy.ma10[current_index])
                    if hasattr(strategy, 'ma20'):
                        data_point['ma20'] = float(strategy.ma20[current_index])
                    
                    # 添加账户价值
                    try:
                        data_point['equity'] = float(strategy.broker.get_value())
                    except Exception as e:
                        logger.warning(f"Could not get equity value for data point {i}: {str(e)}")
                        data_point['equity'] = None
                    
                    chart_data.append(data_point)
                    
                    # 每100个点记录一次日志
                    if i % 100 == 0:
                        logger.debug(f"Processed {i} data points")
                    
                except Exception as e:
                    logger.error(f"Error processing data point {i}: {str(e)}", exc_info=True)
                    continue
            
            logger.debug(f"Completed chart data preparation, total points: {len(chart_data)}")
            return chart_data
            
        except Exception as e:
            logger.error(f"Error in _prepare_chart_data: {e}", exc_info=True)
            return []

    @staticmethod
    def _prepare_trades_list(strategy):
        """准备交易列表"""
        try:
            logger.debug(f"Starting trades list preparation with {len(strategy.trades)} trades")
            trades_list = []
            processed_trades = set()  # 用于跟踪已处理的交易
            
            valid_length = len(strategy.data)
            
            for trade in strategy.trades:
                if trade.get('entry') is not None:
                    try:
                        # 创建唯一标识
                        trade_key = (
                            trade['entry'],
                            trade.get('exit'),
                            trade.get('pnl'),
                            trade.get('size')
                        )
                        
                        # 跳过重复交易
                        if trade_key in processed_trades:
                            continue
                            
                        # 跳过size为0的交易
                        if trade.get('size', 0) == 0:
                            continue
                        
                        # 计算日期
                        entry_index = valid_length - 1 - trade['entry']
                        entry_date = strategy.data.datetime.datetime(0 - entry_index).date().isoformat()
                        
                        exit_date = None
                        if trade.get('exit') is not None:
                            exit_index = valid_length - 1 - trade['exit']
                            exit_date = strategy.data.datetime.datetime(0 - exit_index).date().isoformat()
                        
                        trade_data = {
                            'entryDate': entry_date,
                            'exitDate': exit_date,
                            'entryPrice': float(trade['entry_price']),
                            'exitPrice': float(trade['exit_price']) if trade.get('exit_price') is not None else None,
                            'type': trade['type'],
                            'quantity': trade['size'],
                            'profit': float(trade['pnl']) if trade.get('pnl') is not None else None,
                            'status': 'CLOSED' if trade.get('exit') is not None else 'OPEN',
                            'exitReason': trade.get('exit_reason', '')
                        }
                        
                        trades_list.append(trade_data)
                        processed_trades.add(trade_key)
                        
                    except Exception as e:
                        logger.error(f"Error processing trade: {str(e)}", exc_info=True)
                        continue
            
            logger.debug(f"Completed trades list preparation, total entries: {len(trades_list)}")
            return trades_list
            
        except Exception as e:
            logger.error(f"Error in _prepare_trades_list: {e}", exc_info=True)
            return []