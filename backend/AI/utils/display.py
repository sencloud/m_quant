from colorama import Fore, Style
from tabulate import tabulate
from .analysts import ANALYST_ORDER
import os
import json
from loguru import logger


def sort_agent_signals(signals):
    """按预定义顺序对代理信号进行排序"""
    # 从ANALYST_ORDER创建顺序映射
    analyst_order = {display: idx for idx, (display, _) in enumerate(ANALYST_ORDER)}
    analyst_order["风险管理"] = len(ANALYST_ORDER)  # 将风险管理放在最后

    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def print_trading_output(result: dict) -> None:
    """
    打印格式化的交易结果，包含多个股票的彩色表格。

    参数:
        result (dict): 包含决策和分析师信号的字典
    """
    decisions = result.get("decisions")
    if not decisions:
        logger.error("没有可用的交易决策")
        return

    # 打印每个股票的决策
    for ticker, decision in decisions.items():
        logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}分析 {Fore.CYAN}{ticker}{Style.RESET_ALL}")
        logger.info(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 50}{Style.RESET_ALL}")

        # 准备该股票的分析师信号表格
        table_data = []
        for agent, signals in result.get("analyst_signals", {}).items():
            if ticker not in signals:
                continue
                
            # 在信号部分跳过风险管理代理
            if agent == "risk_management_agent":
                continue

            signal = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            signal_type = signal.get("signal", "").upper()
            confidence = signal.get("confidence", 0)

            signal_color = {
                "BULLISH": Fore.GREEN,
                "BEARISH": Fore.RED,
                "NEUTRAL": Fore.YELLOW,
            }.get(signal_type, Fore.WHITE)
            
            # 获取推理（如果可用）
            reasoning_str = ""
            if "reasoning" in signal and signal["reasoning"]:
                reasoning = signal["reasoning"]
                
                # 处理不同类型的推理（字符串、字典等）
                if isinstance(reasoning, str):
                    reasoning_str = reasoning
                elif isinstance(reasoning, dict):
                    # 将字典转换为字符串表示
                    reasoning_str = json.dumps(reasoning, indent=2)
                else:
                    # 将任何其他类型转换为字符串
                    reasoning_str = str(reasoning)
                
                # 包装长推理文本以提高可读性
                wrapped_reasoning = ""
                current_line = ""
                # 使用60个字符的固定宽度以匹配表格列宽
                max_line_length = 60
                for word in reasoning_str.split():
                    if len(current_line) + len(word) + 1 > max_line_length:
                        wrapped_reasoning += current_line + "\n"
                        current_line = word
                    else:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                if current_line:
                    wrapped_reasoning += current_line
                
                reasoning_str = wrapped_reasoning

            table_data.append(
                [
                    f"{Fore.CYAN}{agent_name}{Style.RESET_ALL}",
                    f"{signal_color}{signal_type}{Style.RESET_ALL}",
                    f"{Fore.WHITE}{confidence}%{Style.RESET_ALL}",
                    f"{Fore.WHITE}{reasoning_str}{Style.RESET_ALL}",
                ]
            )

        # 按预定义顺序对信号进行排序
        table_data = sort_agent_signals(table_data)

        logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}代理分析:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        logger.info(
            tabulate(
                table_data,
                headers=[f"{Fore.WHITE}代理", "信号", "置信度", "推理"],
                tablefmt="grid",
                colalign=("left", "center", "right", "left"),
            )
        )

        # 打印交易决策表格
        action = decision.get("action", "").upper()
        action_color = {
            "BUY": Fore.GREEN,
            "SELL": Fore.RED,
            "HOLD": Fore.YELLOW,
            "COVER": Fore.GREEN,
            "SHORT": Fore.RED,
        }.get(action, Fore.WHITE)

        # 获取推理并格式化
        reasoning = decision.get("reasoning", "")
        # 包装长推理文本以提高可读性
        wrapped_reasoning = ""
        if reasoning:
            current_line = ""
            # 使用60个字符的固定宽度以匹配表格列宽
            max_line_length = 60
            for word in reasoning.split():
                if len(current_line) + len(word) + 1 > max_line_length:
                    wrapped_reasoning += current_line + "\n"
                    current_line = word
                else:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            if current_line:
                wrapped_reasoning += current_line

        decision_data = [
            ["操作", f"{action_color}{action}{Style.RESET_ALL}"],
            ["数量", f"{action_color}{decision.get('quantity')}{Style.RESET_ALL}"],
            [
                "置信度",
                f"{Fore.WHITE}{decision.get('confidence'):.1f}%{Style.RESET_ALL}",
            ],
            ["推理", f"{Fore.WHITE}{wrapped_reasoning}{Style.RESET_ALL}"],
        ]
        
        logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}交易决策:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        logger.info(tabulate(decision_data, tablefmt="grid", colalign=("left", "left")))

    # 打印投资组合摘要
    logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}投资组合摘要:{Style.RESET_ALL}")
    portfolio_data = []
    
    # 提取投资组合经理推理（对所有股票通用）
    portfolio_manager_reasoning = None
    for ticker, decision in decisions.items():
        if decision.get("reasoning"):
            portfolio_manager_reasoning = decision.get("reasoning")
            break
            
    for ticker, decision in decisions.items():
        action = decision.get("action", "").upper()
        action_color = {
            "BUY": Fore.GREEN,
            "SELL": Fore.RED,
            "HOLD": Fore.YELLOW,
            "COVER": Fore.GREEN,
            "SHORT": Fore.RED,
        }.get(action, Fore.WHITE)
        portfolio_data.append(
            [
                f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
                f"{action_color}{action}{Style.RESET_ALL}",
                f"{action_color}{decision.get('quantity')}{Style.RESET_ALL}",
                f"{Fore.WHITE}{decision.get('confidence'):.1f}%{Style.RESET_ALL}",
            ]
        )

    headers = [f"{Fore.WHITE}股票", "操作", "数量", "置信度"]
    
    # 打印投资组合摘要表格
    logger.info(
        tabulate(
            portfolio_data,
            headers=headers,
            tablefmt="grid",
            colalign=("left", "center", "right", "right"),
        )
    )
    
    # 如果可用，打印投资组合经理的推理
    if portfolio_manager_reasoning:
        # 处理不同类型的推理（字符串、字典等）
        reasoning_str = ""
        if isinstance(portfolio_manager_reasoning, str):
            reasoning_str = portfolio_manager_reasoning
        elif isinstance(portfolio_manager_reasoning, dict):
            # 将字典转换为字符串表示
            reasoning_str = json.dumps(portfolio_manager_reasoning, indent=2)
        else:
            # 将任何其他类型转换为字符串
            reasoning_str = str(portfolio_manager_reasoning)
            
        # 包装长推理文本以提高可读性
        wrapped_reasoning = ""
        current_line = ""
        # 使用60个字符的固定宽度以匹配表格列宽
        max_line_length = 60
        for word in reasoning_str.split():
            if len(current_line) + len(word) + 1 > max_line_length:
                wrapped_reasoning += current_line + "\n"
                current_line = word
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        if current_line:
            wrapped_reasoning += current_line
            
        logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}投资组合策略:{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}{wrapped_reasoning}{Style.RESET_ALL}")


def print_backtest_results(table_rows: list) -> None:
    """以格式化的表格打印回测结果"""
    # 清屏
    os.system("cls" if os.name == "nt" else "clear")

    # 将行分为股票行和摘要行
    ticker_rows = []
    summary_rows = []

    for row in table_rows:
        if isinstance(row[1], str) and "投资组合摘要" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)

    
    # 显示最新的投资组合摘要
    if summary_rows:
        latest_summary = summary_rows[-1]
        logger.info(f"\n{Fore.WHITE}{Style.BRIGHT}投资组合摘要:{Style.RESET_ALL}")

        # 提取值并在转换为浮点数之前移除逗号
        cash_str = latest_summary[7].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        position_str = latest_summary[6].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        total_str = latest_summary[8].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")

        logger.info(f"现金余额: {Fore.CYAN}${float(cash_str):,.2f}{Style.RESET_ALL}")
        logger.info(f"总持仓价值: {Fore.YELLOW}${float(position_str):,.2f}{Style.RESET_ALL}")
        logger.info(f"总价值: {Fore.WHITE}${float(total_str):,.2f}{Style.RESET_ALL}")
        logger.info(f"回报: {latest_summary[9]}")
        
        # 如果可用，显示性能指标
        if latest_summary[10]:  # 夏普比率
            logger.info(f"夏普比率: {latest_summary[10]}")
        if latest_summary[11]:  # 索提诺比率
            logger.info(f"索提诺比率: {latest_summary[11]}")
        if latest_summary[12]:  # 最大回撤
            logger.info(f"最大回撤: {latest_summary[12]}")

    # 添加垂直间距
    logger.info("\n" * 2)

    # 打印仅包含股票行的表格
    logger.info(
        tabulate(
            ticker_rows,
            headers=[
                "日期",
                "股票",
                "操作",
                "数量",
                "价格",
                "持仓",
                "持仓价值",
                "看涨",
                "看跌",
                "中性",
            ],
            tablefmt="grid",
            colalign=(
                "left",  # 日期
                "left",  # 股票
                "center",  # 操作
                "right",  # 数量
                "right",  # 价格
                "right",  # 持仓
                "right",  # 持仓价值
                "right",  # 看涨
                "right",  # 看跌
                "right",  # 中性
            ),
        )
    )

    # 添加垂直间距
    logger.info("\n" * 4)


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    shares_owned: float,
    position_value: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    is_summary: bool = False,
    total_value: float = None,
    return_pct: float = None,
    cash_balance: float = None,
    total_position_value: float = None,
    sharpe_ratio: float = None,
    sortino_ratio: float = None,
    max_drawdown: float = None,
) -> list[any]:
    """Format a row for the backtest results table"""
    # Color the action
    action_color = {
        "BUY": Fore.GREEN,
        "COVER": Fore.GREEN,
        "SELL": Fore.RED,
        "SHORT": Fore.RED,
        "HOLD": Fore.WHITE,
    }.get(action.upper(), Fore.WHITE)

    if is_summary:
        return_color = Fore.GREEN if return_pct >= 0 else Fore.RED
        return [
            date,
            f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
            "",  # Action
            "",  # Quantity
            "",  # Price
            "",  # Shares
            f"{Fore.YELLOW}${total_position_value:,.2f}{Style.RESET_ALL}",  # Total Position Value
            f"{Fore.CYAN}${cash_balance:,.2f}{Style.RESET_ALL}",  # Cash Balance
            f"{Fore.WHITE}${total_value:,.2f}{Style.RESET_ALL}",  # Total Value
            f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",  # Return
            f"{Fore.YELLOW}{sharpe_ratio:.2f}{Style.RESET_ALL}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{Fore.YELLOW}{sortino_ratio:.2f}{Style.RESET_ALL}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{Fore.RED}{abs(max_drawdown):.2f}%{Style.RESET_ALL}" if max_drawdown is not None else "",  # Max Drawdown
        ]
    else:
        return [
            date,
            f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
            f"{action_color}{action.upper()}{Style.RESET_ALL}",
            f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{shares_owned:,.0f}{Style.RESET_ALL}",
            f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",
            f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",
            f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",
            f"{Fore.BLUE}{neutral_count}{Style.RESET_ALL}",
        ]
