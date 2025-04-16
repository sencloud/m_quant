import sys

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import questionary

import matplotlib.pyplot as plt
import pandas as pd
from colorama import Fore, Style, init
import numpy as np
import itertools
import os

from AI.llm.models import LLM_ORDER, OLLAMA_LLM_ORDER, get_model_info, ModelProvider
from AI.utils.analysts import ANALYST_ORDER
from AI.AIService import run_hedge_fund
from AI.tools.api import (
    get_company_news,
    get_price_data,
    get_prices,
    get_financial_metrics,
    get_insider_trades,
)
from AI.utils.display import print_backtest_results, format_backtest_row
from typing_extensions import Callable
from AI.utils.ollama import ensure_ollama_and_model
from utils.logger import logger

init(autoreset=True)


class Backtester:
    def __init__(
        self,
        agent: Callable,
        tickers: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
        model_name: str = "gpt-4o",
        model_provider: str = "OpenAI",
        selected_analysts: list[str] = [],
        initial_margin_requirement: float = 0.0,
    ):
        """
        :param agent: 交易代理 (Callable)
        :param tickers: 要回测的股票代码列表
        :param start_date: 开始日期字符串 (YYYY-MM-DD)
        :param end_date: 结束日期字符串 (YYYY-MM-DD)
        :param initial_capital: 初始投资组合现金
        :param model_name: 使用的LLM模型名称 (gpt-4等)
        :param model_provider: LLM提供商 (OpenAI等)
        :param selected_analysts: 要纳入的分析师名称或ID列表
        :param initial_margin_requirement: 保证金比率 (例如 0.5 = 50%)
        """
        self.agent = agent
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.model_name = model_name
        self.model_provider = model_provider
        self.selected_analysts = selected_analysts

        # 初始化投资组合，支持做多/做空头寸
        self.portfolio_values = []
        self.portfolio = {
            "cash": initial_capital,
            "margin_used": 0.0,  # 所有做空头寸的总保证金使用量
            "margin_requirement": initial_margin_requirement,  # 做空所需的保证金比率
            "positions": {
                ticker: {
                    "long": 0,               # 持有的做多股数
                    "short": 0,              # 持有的做空股数
                    "long_cost_basis": 0.0,  # 每股平均成本基础(做多)
                    "short_cost_basis": 0.0, # 每股平均成本基础(做空)
                    "short_margin_used": 0.0 # 该股票做空使用的保证金金额
                } for ticker in tickers
            },
            "realized_gains": {
                ticker: {
                    "long": 0.0,   # 做多头寸的已实现收益
                    "short": 0.0,  # 做空头寸的已实现收益
                } for ticker in tickers
            }
        }

    def execute_trade(self, ticker: str, action: str, quantity: float, current_price: float):
        """
        执行交易，支持做多和做空头寸
        `quantity` 是代理想要买入/卖出/做空/平仓的股数
        我们只交易整数股以保持简单
        """
        if quantity <= 0:
            return 0

        quantity = int(quantity)  # 强制整数股
        position = self.portfolio["positions"][ticker]

        if action == "buy":
            cost = quantity * current_price
            if cost <= self.portfolio["cash"]:
                # 新总数的加权平均成本基础
                old_shares = position["long"]
                old_cost_basis = position["long_cost_basis"]
                new_shares = quantity
                total_shares = old_shares + new_shares

                if total_shares > 0:
                    total_old_cost = old_cost_basis * old_shares
                    total_new_cost = cost
                    position["long_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                position["long"] += quantity
                self.portfolio["cash"] -= cost
                return quantity
            else:
                # 计算最大可负担数量
                max_quantity = int(self.portfolio["cash"] / current_price)
                if max_quantity > 0:
                    cost = max_quantity * current_price
                    old_shares = position["long"]
                    old_cost_basis = position["long_cost_basis"]
                    total_shares = old_shares + max_quantity

                    if total_shares > 0:
                        total_old_cost = old_cost_basis * old_shares
                        total_new_cost = cost
                        position["long_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                    position["long"] += max_quantity
                    self.portfolio["cash"] -= cost
                    return max_quantity
                return 0

        elif action == "sell":
            # 你只能卖出你拥有的数量
            quantity = min(quantity, position["long"])
            if quantity > 0:
                # 使用平均成本基础计算已实现收益/损失
                avg_cost_per_share = position["long_cost_basis"] if position["long"] > 0 else 0
                realized_gain = (current_price - avg_cost_per_share) * quantity
                self.portfolio["realized_gains"][ticker]["long"] += realized_gain

                position["long"] -= quantity
                self.portfolio["cash"] += quantity * current_price

                if position["long"] == 0:
                    position["long_cost_basis"] = 0.0

                return quantity

        elif action == "short":
            """
            典型的做空流程:
              1) 收到收益 = current_price * quantity
              2) 存入保证金 = 收益 * margin_ratio
              3) 现金净效应 = +收益 - 保证金
            """
            proceeds = current_price * quantity
            margin_required = proceeds * self.portfolio["margin_requirement"]
            if margin_required <= self.portfolio["cash"]:
                # 加权平均做空成本基础
                old_short_shares = position["short"]
                old_cost_basis = position["short_cost_basis"]
                new_shares = quantity
                total_shares = old_short_shares + new_shares

                if total_shares > 0:
                    total_old_cost = old_cost_basis * old_short_shares
                    total_new_cost = current_price * new_shares
                    position["short_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                position["short"] += quantity

                # 更新保证金使用
                position["short_margin_used"] += margin_required
                self.portfolio["margin_used"] += margin_required

                # 增加现金收益，然后减去所需保证金
                self.portfolio["cash"] += proceeds
                self.portfolio["cash"] -= margin_required
                return quantity
            else:
                # 计算最大可做空数量
                margin_ratio = self.portfolio["margin_requirement"]
                if margin_ratio > 0:
                    max_quantity = int(self.portfolio["cash"] / (current_price * margin_ratio))
                else:
                    max_quantity = 0

                if max_quantity > 0:
                    proceeds = current_price * max_quantity
                    margin_required = proceeds * margin_ratio

                    old_short_shares = position["short"]
                    old_cost_basis = position["short_cost_basis"]
                    total_shares = old_short_shares + max_quantity

                    if total_shares > 0:
                        total_old_cost = old_cost_basis * old_short_shares
                        total_new_cost = current_price * max_quantity
                        position["short_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                    position["short"] += max_quantity
                    position["short_margin_used"] += margin_required
                    self.portfolio["margin_used"] += margin_required

                    self.portfolio["cash"] += proceeds
                    self.portfolio["cash"] -= margin_required
                    return max_quantity
                return 0

        elif action == "cover":
            """
            平仓时:
              1) 支付平仓成本 = current_price * quantity
              2) 释放相应比例的保证金
              3) 现金净效应 = -平仓成本 + 释放的保证金
            """
            quantity = min(quantity, position["short"])
            if quantity > 0:
                cover_cost = quantity * current_price
                avg_short_price = position["short_cost_basis"] if position["short"] > 0 else 0
                realized_gain = (avg_short_price - current_price) * quantity

                if position["short"] > 0:
                    portion = quantity / position["short"]
                else:
                    portion = 1.0

                margin_to_release = portion * position["short_margin_used"]

                position["short"] -= quantity
                position["short_margin_used"] -= margin_to_release
                self.portfolio["margin_used"] -= margin_to_release

                # 支付平仓成本，但收回释放的保证金
                self.portfolio["cash"] += margin_to_release
                self.portfolio["cash"] -= cover_cost

                self.portfolio["realized_gains"][ticker]["short"] += realized_gain

                if position["short"] == 0:
                    position["short_cost_basis"] = 0.0
                    position["short_margin_used"] = 0.0

                return quantity

        return 0

    def calculate_portfolio_value(self, current_prices):
        """
        计算总投资组合价值，包括:
          - 现金
          - 做多头寸的市场价值
          - 做空头寸的未实现收益/损失
        """
        total_value = self.portfolio["cash"]

        for ticker in self.tickers:
            position = self.portfolio["positions"][ticker]
            price = current_prices[ticker]

            # 做多头寸价值
            long_value = position["long"] * price
            total_value += long_value

            # 做空头寸未实现盈亏 = short_shares * (short_cost_basis - current_price)
            if position["short"] > 0:
                total_value += position["short"] * (position["short_cost_basis"] - price)

        return total_value

    def prefetch_data(self):
        """预取回测期间所需的所有数据"""
        logger.info("预取整个回测期间的数据...")

        # 将结束日期字符串转换为datetime，获取前一年的数据
        end_date_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        start_date_dt = end_date_dt - relativedelta(years=1)
        start_date_str = start_date_dt.strftime("%Y-%m-%d")

        for ticker in self.tickers:
            # 获取整个期间的价格数据，加上1年
            get_prices(ticker, start_date_str, self.end_date)

            # 获取财务指标
            get_financial_metrics(ticker, self.end_date, limit=10)

            # 获取内幕交易
            get_insider_trades(ticker, self.end_date, start_date=self.start_date, limit=1000)

            # 获取公司新闻
            get_company_news(ticker, self.end_date, start_date=self.start_date, limit=1000)

        logger.info("数据预取完成")

    def parse_agent_response(self, agent_output):
        """解析代理的JSON输出(如果无效则默认为'hold')"""
        import json

        try:
            decision = json.loads(agent_output)
            return decision
        except Exception:
            logger.error(f"解析操作出错: {agent_output}")
            return {"action": "hold", "quantity": 0}

    def run_backtest(self):
        # 在开始时预取所有数据
        self.prefetch_data()

        dates = pd.date_range(self.start_date, self.end_date, freq="B")
        table_rows = []
        performance_metrics = {
            'sharpe_ratio': None,
            'sortino_ratio': None,
            'max_drawdown': None,
            'long_short_ratio': None,
            'gross_exposure': None,
            'net_exposure': None
        }

        logger.info("开始回测...")

        # 用初始资金初始化投资组合价值列表
        if len(dates) > 0:
            self.portfolio_values = [{"Date": dates[0], "Portfolio Value": self.initial_capital}]
        else:
            self.portfolio_values = []

        for current_date in dates:
            lookback_start = (current_date - timedelta(days=30)).strftime("%Y-%m-%d")
            current_date_str = current_date.strftime("%Y-%m-%d")
            previous_date_str = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")

            # 如果没有前一天可以回看(即范围内的第一个日期)，则跳过
            if lookback_start == current_date_str:
                continue

            # 获取所有股票的当前价格
            try:
                current_prices = {}
                missing_data = False
                
                for ticker in self.tickers:
                    try:
                        price_data = get_price_data(ticker, previous_date_str, current_date_str)
                        if price_data.empty:
                            logger.warning(f"警告: {current_date_str}没有{ticker}的价格数据")
                            missing_data = True
                            break
                        current_prices[ticker] = price_data.iloc[-1]["close"]
                    except Exception as e:
                        logger.error(f"获取{ticker}在{previous_date_str}和{current_date_str}之间的价格时出错: {e}")
                        missing_data = True
                        break
                
                if missing_data:
                    logger.warning(f"由于缺少价格数据，跳过交易日{current_date_str}")
                    continue
                
            except Exception as e:
                # 如果有一般API错误，记录并跳过这一天
                logger.error(f"获取{current_date_str}的价格时出错: {e}")
                continue

            # ---------------------------------------------------------------
            # 1) 执行代理的交易
            # ---------------------------------------------------------------
            output = self.agent(
                tickers=self.tickers,
                start_date=lookback_start,
                end_date=current_date_str,
                portfolio=self.portfolio,
                model_name=self.model_name,
                model_provider=self.model_provider,
                selected_analysts=self.selected_analysts,
            )
            decisions = output["decisions"]
            analyst_signals = output["analyst_signals"]

            # 为每个股票执行交易
            executed_trades = {}
            for ticker in self.tickers:
                decision = decisions.get(ticker, {"action": "hold", "quantity": 0})
                action, quantity = decision.get("action", "hold"), decision.get("quantity", 0)

                executed_quantity = self.execute_trade(ticker, action, quantity, current_prices[ticker])
                executed_trades[ticker] = executed_quantity

            # ---------------------------------------------------------------
            # 2) 现在交易已执行，重新计算这一天的最终投资组合价值
            # ---------------------------------------------------------------
            total_value = self.calculate_portfolio_value(current_prices)

            # 同时计算最终交易后状态的做多/做空敞口
            long_exposure = sum(
                self.portfolio["positions"][t]["long"] * current_prices[t]
                for t in self.tickers
            )
            short_exposure = sum(
                self.portfolio["positions"][t]["short"] * current_prices[t]
                for t in self.tickers
            )

            # 计算总敞口和净敞口
            gross_exposure = long_exposure + short_exposure
            net_exposure = long_exposure - short_exposure
            long_short_ratio = (
                long_exposure / short_exposure if short_exposure > 1e-9 else float('inf')
            )

            # 在self.portfolio_values中跟踪每天的投资组合价值
            self.portfolio_values.append({
                "Date": current_date,
                "Portfolio Value": total_value,
                "Long Exposure": long_exposure,
                "Short Exposure": short_exposure,
                "Gross Exposure": gross_exposure,
                "Net Exposure": net_exposure,
                "Long/Short Ratio": long_short_ratio
            })

            # ---------------------------------------------------------------
            # 3) 构建要显示的表行
            # ---------------------------------------------------------------
            date_rows = []

            # 对于每个股票，记录信号/交易
            for ticker in self.tickers:
                ticker_signals = {}
                for agent_name, signals in analyst_signals.items():
                    if ticker in signals:
                        ticker_signals[agent_name] = signals[ticker]

                bullish_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "bullish"])
                bearish_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "bearish"])
                neutral_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "neutral"])

                # 计算净头寸价值
                pos = self.portfolio["positions"][ticker]
                long_val = pos["long"] * current_prices[ticker]
                short_val = pos["short"] * current_prices[ticker]
                net_position_value = long_val - short_val

                # 从决策中获取操作和数量
                action = decisions.get(ticker, {}).get("action", "hold")
                quantity = executed_trades.get(ticker, 0)
                
                # 将代理操作添加到表行
                date_rows.append(
                    format_backtest_row(
                        date=current_date_str,
                        ticker=ticker,
                        action=action,
                        quantity=quantity,
                        price=current_prices[ticker],
                        shares_owned=pos["long"] - pos["short"],  # 净股数
                        position_value=net_position_value,
                        bullish_count=bullish_count,
                        bearish_count=bearish_count,
                        neutral_count=neutral_count,
                    )
                )
            # ---------------------------------------------------------------
            # 4) 计算性能摘要指标
            # ---------------------------------------------------------------
            # 计算投资组合回报与初始资金
            # 已实现收益已反映在现金余额中，所以我们不再单独添加
            portfolio_return = (total_value / self.initial_capital - 1) * 100

            # 为这一天添加摘要行
            date_rows.append(
                format_backtest_row(
                    date=current_date_str,
                    ticker="",
                    action="",
                    quantity=0,
                    price=0,
                    shares_owned=0,
                    position_value=0,
                    bullish_count=0,
                    bearish_count=0,
                    neutral_count=0,
                    is_summary=True,
                    total_value=total_value,
                    return_pct=portfolio_return,
                    cash_balance=self.portfolio["cash"],
                    total_position_value=total_value - self.portfolio["cash"],
                    sharpe_ratio=performance_metrics["sharpe_ratio"],
                    sortino_ratio=performance_metrics["sortino_ratio"],
                    max_drawdown=performance_metrics["max_drawdown"],
                ),
            )

            table_rows.extend(date_rows)
            print_backtest_results(table_rows)

            # 如果我们有足够的数据，更新性能指标
            if len(self.portfolio_values) > 3:
                self._update_performance_metrics(performance_metrics)

        # 存储最终性能指标以供analyze_performance参考
        self.performance_metrics = performance_metrics
        return performance_metrics

    def _update_performance_metrics(self, performance_metrics):
        """使用每日回报更新性能指标的辅助方法"""
        values_df = pd.DataFrame(self.portfolio_values).set_index("Date")
        values_df["Daily Return"] = values_df["Portfolio Value"].pct_change()
        clean_returns = values_df["Daily Return"].dropna()

        if len(clean_returns) < 2:
            return  # 数据点不足

        # 假设每年252个交易日
        daily_risk_free_rate = 0.0434 / 252
        excess_returns = clean_returns - daily_risk_free_rate
        mean_excess_return = excess_returns.mean()
        std_excess_return = excess_returns.std()

        # 夏普比率
        if std_excess_return > 1e-12:
            performance_metrics["sharpe_ratio"] = np.sqrt(252) * (mean_excess_return / std_excess_return)
        else:
            performance_metrics["sharpe_ratio"] = 0.0

        # 索提诺比率
        negative_returns = excess_returns[excess_returns < 0]
        if len(negative_returns) > 0:
            downside_std = negative_returns.std()
            if downside_std > 1e-12:
                performance_metrics["sortino_ratio"] = np.sqrt(252) * (mean_excess_return / downside_std)
            else:
                performance_metrics["sortino_ratio"] = float('inf') if mean_excess_return > 0 else 0
        else:
            performance_metrics["sortino_ratio"] = float('inf') if mean_excess_return > 0 else 0

        # 最大回撤(确保存储为负百分比)
        rolling_max = values_df["Portfolio Value"].cummax()
        drawdown = (values_df["Portfolio Value"] - rolling_max) / rolling_max
        
        if len(drawdown) > 0:
            min_drawdown = drawdown.min()
            # 存储为负百分比
            performance_metrics["max_drawdown"] = min_drawdown * 100
            
            # 存储最大回撤的日期以供参考
            if min_drawdown < 0:
                performance_metrics["max_drawdown_date"] = drawdown.idxmin().strftime('%Y-%m-%d')
            else:
                performance_metrics["max_drawdown_date"] = None
        else:
            performance_metrics["max_drawdown"] = 0.0
            performance_metrics["max_drawdown_date"] = None

    def analyze_performance(self):
        """创建性能DataFrame，打印摘要统计，并绘制权益曲线"""
        if not self.portfolio_values:
            logger.warning("未找到投资组合数据。请先运行回测。")
            return pd.DataFrame()

        performance_df = pd.DataFrame(self.portfolio_values).set_index("Date")
        if performance_df.empty:
            logger.warning("没有有效的性能数据可分析。")
            return performance_df

        final_portfolio_value = performance_df["Portfolio Value"].iloc[-1]
        total_return = ((final_portfolio_value - self.initial_capital) / self.initial_capital) * 100

        logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}投资组合性能摘要:{Style.RESET_ALL}")
        logger.info(f"总回报: {Fore.GREEN if total_return >= 0 else Fore.RED}{total_return:.2f}%{Style.RESET_ALL}")
        
        # 仅用于信息目的打印已实现盈亏
        total_realized_gains = sum(
            self.portfolio["realized_gains"][ticker]["long"] + 
            self.portfolio["realized_gains"][ticker]["short"] 
            for ticker in self.tickers
        )
        logger.info(f"总已实现收益/损失: {Fore.GREEN if total_realized_gains >= 0 else Fore.RED}${total_realized_gains:,.2f}{Style.RESET_ALL}")

        # 绘制投资组合价值随时间的变化
        plt.figure(figsize=(12, 6))
        plt.plot(performance_df.index, performance_df["Portfolio Value"], color="blue")
        plt.title("投资组合价值随时间变化")
        plt.ylabel("投资组合价值 ($)")
        plt.xlabel("日期")
        plt.grid(True)
        plt.show()

        # 计算每日回报
        performance_df["Daily Return"] = performance_df["Portfolio Value"].pct_change().fillna(0)
        daily_rf = 0.0434 / 252  # 每日无风险利率
        mean_daily_return = performance_df["Daily Return"].mean()
        std_daily_return = performance_df["Daily Return"].std()

        # 年化夏普比率
        if std_daily_return != 0:
            annualized_sharpe = np.sqrt(252) * ((mean_daily_return - daily_rf) / std_daily_return)
        else:
            annualized_sharpe = 0
        logger.info(f"\n夏普比率: {Fore.YELLOW}{annualized_sharpe:.2f}{Style.RESET_ALL}")

        # 使用回测期间计算的最大回撤值(如果可用)
        max_drawdown = getattr(self, 'performance_metrics', {}).get('max_drawdown')
        max_drawdown_date = getattr(self, 'performance_metrics', {}).get('max_drawdown_date')
        
        # 如果尚不存在值，则计算它
        if max_drawdown is None:
            rolling_max = performance_df["Portfolio Value"].cummax()
            drawdown = (performance_df["Portfolio Value"] - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            max_drawdown_date = drawdown.idxmin().strftime('%Y-%m-%d') if pd.notnull(drawdown.idxmin()) else None

        if max_drawdown_date:
            logger.info(f"最大回撤: {Fore.RED}{abs(max_drawdown):.2f}%{Style.RESET_ALL} (在{max_drawdown_date})")
        else:
            logger.info(f"最大回撤: {Fore.RED}{abs(max_drawdown):.2f}%{Style.RESET_ALL}")

        # 胜率
        winning_days = len(performance_df[performance_df["Daily Return"] > 0])
        total_days = max(len(performance_df) - 1, 1)
        win_rate = (winning_days / total_days) * 100
        logger.info(f"胜率: {Fore.GREEN}{win_rate:.2f}%{Style.RESET_ALL}")

        # 平均盈亏比
        positive_returns = performance_df[performance_df["Daily Return"] > 0]["Daily Return"]
        negative_returns = performance_df[performance_df["Daily Return"] < 0]["Daily Return"]
        avg_win = positive_returns.mean() if not positive_returns.empty else 0
        avg_loss = abs(negative_returns.mean()) if not negative_returns.empty else 0
        if avg_loss != 0:
            win_loss_ratio = avg_win / avg_loss
        else:
            win_loss_ratio = float('inf') if avg_win > 0 else 0
        logger.info(f"盈亏比: {Fore.GREEN}{win_loss_ratio:.2f}{Style.RESET_ALL}")

        # 最大连续盈利/亏损
        returns_binary = (performance_df["Daily Return"] > 0).astype(int)
        if len(returns_binary) > 0:
            max_consecutive_wins = max((len(list(g)) for k, g in itertools.groupby(returns_binary) if k == 1), default=0)
            max_consecutive_losses = max((len(list(g)) for k, g in itertools.groupby(returns_binary) if k == 0), default=0)
        else:
            max_consecutive_wins = 0
            max_consecutive_losses = 0

        logger.info(f"最大连续盈利: {Fore.GREEN}{max_consecutive_wins}{Style.RESET_ALL}")
        logger.info(f"最大连续亏损: {Fore.RED}{max_consecutive_losses}{Style.RESET_ALL}")

        return performance_df


### 4. 运行回测 #####
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="运行回测模拟")
    parser.add_argument(
        "--tickers",
        type=str,
        required=False,
        help="逗号分隔的股票代码列表 (例如, AAPL,MSFT,GOOGL)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="YYYY-MM-DD格式的结束日期",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=(datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d"),
        help="YYYY-MM-DD格式的开始日期",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=100000,
        help="初始资金金额 (默认: 100000)",
    )
    parser.add_argument(
        "--margin-requirement",
        type=float,
        default=0.0,
        help="做空头寸的保证金比率，例如0.5表示50% (默认: 0.0)",
    )
    parser.add_argument(
        "--ollama", action="store_true", help="使用Ollama进行本地LLM推理"
    )

    args = parser.parse_args()

    # 从逗号分隔的字符串解析股票代码
    tickers = [ticker.strip() for ticker in args.tickers.split(",")] if args.tickers else []

    # 选择分析师
    selected_analysts = None
    choices = questionary.checkbox(
        "使用空格键选择/取消选择分析师。",
        choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
        instruction="\n\n按'a'切换全部。\n\n按Enter完成以运行对冲基金。",
        validate=lambda x: len(x) > 0 or "您必须至少选择一个分析师。",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        logger.info("\n\n收到中断。退出...")
        sys.exit(0)
    else:
        selected_analysts = choices
        logger.info(
            f"\n选择的分析师: "
            f"{', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}"
        )

    # 根据是否使用Ollama选择LLM模型
    model_choice = None
    model_provider = None
    
    if args.ollama:
        logger.info(f"{Fore.CYAN}使用Ollama进行本地LLM推理。{Style.RESET_ALL}")
        
        # 从Ollama特定模型中选择
        model_choice = questionary.select(
            "选择您的Ollama模型:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in OLLAMA_LLM_ORDER],
            style=questionary.Style([
                ("selected", "fg:green bold"),
                ("pointer", "fg:green bold"),
                ("highlighted", "fg:green"),
                ("answer", "fg:green bold"),
            ])
        ).ask()
        
        if not model_choice:
            logger.info("\n\n收到中断。退出...")
            sys.exit(0)
        
        # 确保Ollama已安装、运行，并且模型可用
        if not ensure_ollama_and_model(model_choice):
            logger.error(f"{Fore.RED}没有Ollama和所选模型无法继续。{Style.RESET_ALL}")
            sys.exit(1)
        
        model_provider = ModelProvider.OLLAMA.value
        logger.info(f"\n选择{Fore.CYAN}Ollama{Style.RESET_ALL}模型: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
    else:
        # 使用标准基于云的LLM选择
        model_choice = questionary.select(
            "选择您的LLM模型:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in LLM_ORDER],
            style=questionary.Style([
                ("selected", "fg:green bold"),
                ("pointer", "fg:green bold"),
                ("highlighted", "fg:green"),
                ("answer", "fg:green bold"),
            ])
        ).ask()

        if not model_choice:
            logger.info("\n\n收到中断。退出...")
            sys.exit(0)
        else:
            model_info = get_model_info(model_choice)
            if model_info:
                model_provider = model_info.provider.value
                logger.info(f"\n选择{Fore.CYAN}{model_provider}{Style.RESET_ALL}模型: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
            else:
                model_provider = "Unknown"
                logger.info(f"\n选择模型: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")

    # 创建并运行回测器
    backtester = Backtester(
        agent=run_hedge_fund,
        tickers=tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        model_name=model_choice,
        model_provider=model_provider,
        selected_analysts=selected_analysts,
        initial_margin_requirement=args.margin_requirement,
    )

    performance_metrics = backtester.run_backtest()
    performance_df = backtester.analyze_performance()
