from langchain_core.messages import HumanMessage
from AI.graph.state import AgentState, show_agent_reasoning
from AI.utils.progress import progress
from loguru import logger
import json

from AI.tools.api import get_financial_metrics, get_market_cap, search_line_items
from langchain_core.prompts import ChatPromptTemplate


##### 估值代理 #####
def valuation_agent(state: AgentState):
    """
    使用多种方法对多个股票进行详细的估值分析
    
    主要功能:
    1. 获取财务数据和指标
    2. 计算所有者收益估值（巴菲特方法）
    3. 计算DCF估值
    4. 比较市值与内在价值
    5. 生成估值信号和置信度
    """
    logger.info("开始估值分析代理")
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    logger.info(f"分析日期: {end_date}, 股票代码: {tickers}")

    # 初始化每个股票的估值分析
    valuation_analysis = {}

    for ticker in tickers:
        progress.update_status("valuation_agent", ticker, "获取财务数据")
        logger.info(f"开始获取 {ticker} 的财务数据")

        # 获取财务指标
        financial_metrics = get_financial_metrics(
            ticker=ticker,
            end_date=end_date,
            period="ttm",
        )
        logger.debug(f"获取到财务指标: {financial_metrics}")

        # 添加财务指标的安全检查
        if not financial_metrics:
            progress.update_status("valuation_agent", ticker, "失败：未找到财务指标")
            logger.error(f"无法获取 {ticker} 的财务指标")
            continue
        
        metrics = financial_metrics[0]
        logger.debug(f"使用财务指标: {metrics}")

        progress.update_status("valuation_agent", ticker, "收集财务项目")
        logger.info(f"开始收集 {ticker} 的财务项目")
        # 获取估值所需的特定财务项目
        financial_line_items = search_line_items(
            ticker=ticker,
            line_items=[
                "free_cash_flow",
                "net_income",
                "depreciation_and_amortization",
                "capital_expenditure",
                "working_capital",
            ],
            end_date=end_date,
            period="ttm",
            limit=2,
        )
        logger.debug(f"获取到财务项目: {financial_line_items}")

        # 添加财务项目的安全检查
        if len(financial_line_items) < 2:
            progress.update_status("valuation_agent", ticker, "失败：财务项目不足")
            logger.error(f"{ticker} 的财务项目数据不足")
            continue

        # 获取当前和之前的财务项目
        current_financial_line_item = financial_line_items[0]
        previous_financial_line_item = financial_line_items[1]
        logger.debug(f"当前财务项目: {current_financial_line_item}")
        logger.debug(f"上一期财务项目: {previous_financial_line_item}")

        progress.update_status("valuation_agent", ticker, "计算所有者收益")
        logger.info(f"开始计算 {ticker} 的所有者收益")
        # 计算营运资金变化
        working_capital_change = current_financial_line_item.working_capital - previous_financial_line_item.working_capital
        logger.debug(f"营运资金变化: {working_capital_change}")

        # 所有者收益估值（巴菲特方法）
        owner_earnings_value = calculate_owner_earnings_value(
            net_income=current_financial_line_item.net_income,
            depreciation=current_financial_line_item.depreciation_and_amortization,
            capex=current_financial_line_item.capital_expenditure,
            working_capital_change=working_capital_change,
            growth_rate=metrics.earnings_growth,
            required_return=0.15,
            margin_of_safety=0.25,
        )
        logger.info(f"所有者收益估值: {owner_earnings_value:,.2f}")

        progress.update_status("valuation_agent", ticker, "计算DCF价值")
        logger.info(f"开始计算 {ticker} 的DCF价值")
        # DCF估值
        dcf_value = calculate_intrinsic_value(
            free_cash_flow=current_financial_line_item.free_cash_flow,
            growth_rate=metrics.earnings_growth,
            discount_rate=0.10,
            terminal_growth_rate=0.03,
            num_years=5,
        )
        logger.info(f"DCF估值: {dcf_value:,.2f}")

        progress.update_status("valuation_agent", ticker, "比较市值")
        logger.info(f"开始比较 {ticker} 的市值")
        # 获取市值
        market_cap = get_market_cap(ticker=ticker, end_date=end_date)
        logger.debug(f"市值: {market_cap:,.2f}")

        # 计算综合估值差距（两种方法的平均值）
        dcf_gap = (dcf_value - market_cap) / market_cap
        owner_earnings_gap = (owner_earnings_value - market_cap) / market_cap
        valuation_gap = (dcf_gap + owner_earnings_gap) / 2
        logger.info(f"估值差距: DCF={dcf_gap:.1%}, 所有者收益={owner_earnings_gap:.1%}, 综合={valuation_gap:.1%}")

        if valuation_gap > 0.15:  # 低估超过15%
            signal = "看多"
        elif valuation_gap < -0.15:  # 高估超过15%
            signal = "看空"
        else:
            signal = "中性"
        logger.info(f"生成的信号: {signal}")

        # 创建分析理由
        reasoning = {}
        reasoning["dcf_analysis"] = {
            "signal": ("bullish" if dcf_gap > 0.15 else "bearish" if dcf_gap < -0.15 else "neutral"),
            "details": f"Intrinsic Value: ${dcf_value:,.2f}, Market Cap: ${market_cap:,.2f}, Gap: {dcf_gap:.1%}",
        }

        reasoning["owner_earnings_analysis"] = {
            "signal": ("bullish" if owner_earnings_gap > 0.15 else "bearish" if owner_earnings_gap < -0.15 else "neutral"),
            "details": f"Owner Earnings Value: ${owner_earnings_value:,.2f}, Market Cap: ${market_cap:,.2f}, Gap: {owner_earnings_gap:.1%}",
        }

        # 计算置信度（0到100的百分比）
        # 估值差距的绝对值越高，置信度越高，但最高为100%
        # 使用0.30（30%）作为对应100%置信度的最大差距
        confidence = min(abs(valuation_gap) / 0.30 * 100, 100)
        confidence = round(confidence)
        logger.info(f"计算得到的置信度: {confidence}%")
        
        valuation_analysis[ticker] = {
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("valuation_agent", ticker, "Done")

    message = HumanMessage(
        content=json.dumps(valuation_analysis),
        name="valuation_agent",
    )

    # 如果设置了标志，打印分析理由
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(valuation_analysis, "估值分析代理")

    # 将信号添加到analyst_signals列表
    state["data"]["analyst_signals"]["valuation_agent"] = valuation_analysis
    logger.info("估值分析完成，返回结果")

    return {
        "messages": [message],
        "data": data,
    }


def calculate_owner_earnings_value(
    net_income: float,
    depreciation: float,
    capex: float,
    working_capital_change: float,
    growth_rate: float = 0.05,
    required_return: float = 0.15,
    margin_of_safety: float = 0.25,
    num_years: int = 5,
) -> float:
    """
    Calculates the intrinsic value using Buffett's Owner Earnings method.

    Owner Earnings = Net Income
                    + Depreciation/Amortization
                    - Capital Expenditures
                    - Working Capital Changes

    Args:
        net_income: Annual net income
        depreciation: Annual depreciation and amortization
        capex: Annual capital expenditures
        working_capital_change: Annual change in working capital
        growth_rate: Expected growth rate
        required_return: Required rate of return (Buffett typically uses 15%)
        margin_of_safety: Margin of safety to apply to final value
        num_years: Number of years to project

    Returns:
        float: Intrinsic value with margin of safety
    """
    logger.debug(f"开始计算所有者收益价值，参数: net_income={net_income}, depreciation={depreciation}, capex={capex}, working_capital_change={working_capital_change}")
    
    if not all([isinstance(x, (int, float)) for x in [net_income, depreciation, capex, working_capital_change]]):
        logger.warning("输入参数类型错误，返回0")
        return 0

    # 计算初始所有者收益
    owner_earnings = net_income + depreciation - capex - working_capital_change
    logger.debug(f"初始所有者收益: {owner_earnings}")

    if owner_earnings <= 0:
        logger.warning("所有者收益为负或零，返回0")
        return 0

    # 预测未来所有者收益
    future_values = []
    for year in range(1, num_years + 1):
        future_value = owner_earnings * (1 + growth_rate) ** year
        discounted_value = future_value / (1 + required_return) ** year
        future_values.append(discounted_value)
        logger.debug(f"第{year}年预测值: {future_value}, 现值: {discounted_value}")

    # 计算终值（使用永续增长公式）
    terminal_growth = min(growth_rate, 0.03)  # 将终值增长率限制在3%
    terminal_value = (future_values[-1] * (1 + terminal_growth)) / (required_return - terminal_growth)
    terminal_value_discounted = terminal_value / (1 + required_return) ** num_years
    logger.debug(f"终值: {terminal_value}, 现值: {terminal_value_discounted}")

    # 求和所有价值并应用安全边际
    intrinsic_value = sum(future_values) + terminal_value_discounted
    value_with_safety_margin = intrinsic_value * (1 - margin_of_safety)
    logger.debug(f"内在价值: {intrinsic_value}, 带安全边际的价值: {value_with_safety_margin}")

    return value_with_safety_margin


def calculate_intrinsic_value(
    free_cash_flow: float,
    growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.02,
    num_years: int = 5,
) -> float:
    """
    基于当前自由现金流计算公司的贴现现金流（DCF）。
    使用此函数计算股票的内在价值。
    
    参数:
        free_cash_flow: 当前自由现金流
        growth_rate: 预期增长率
        discount_rate: 贴现率
        terminal_growth_rate: 终值增长率
        num_years: 预测年数
        
    返回:
        float: 内在价值
    """
    logger.debug(f"开始计算DCF估值，参数: fcf={free_cash_flow}, growth={growth_rate}, discount={discount_rate}")
    
    # 基于增长率估算未来现金流
    cash_flows = [free_cash_flow * (1 + growth_rate) ** i for i in range(num_years)]
    logger.debug(f"预测现金流: {cash_flows}")

    # 计算预测现金流的现值
    present_values = []
    for i in range(num_years):
        present_value = cash_flows[i] / (1 + discount_rate) ** (i + 1)
        present_values.append(present_value)
        logger.debug(f"第{i+1}年现值: {present_value}")

    # 计算终值
    terminal_value = cash_flows[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    terminal_present_value = terminal_value / (1 + discount_rate) ** num_years
    logger.debug(f"终值: {terminal_value}, 现值: {terminal_present_value}")

    # 求和现值和终值
    dcf_value = sum(present_values) + terminal_present_value
    logger.debug(f"DCF估值结果: {dcf_value}")

    return dcf_value


def calculate_working_capital_change(
    current_working_capital: float,
    previous_working_capital: float,
) -> float:
    """
    计算两个期间之间营运资金的绝对变化。
    正变化意味着更多资金被占用在营运资金中（现金流出）。
    负变化意味着更少资金被占用（现金流入）。

    参数:
        current_working_capital: 当前期间的营运资金
        previous_working_capital: 上一期间的营运资金

    返回:
        float: 营运资金变化（当前 - 上一期间）
    """
    logger.debug(f"计算营运资金变化: 当前={current_working_capital}, 上期={previous_working_capital}")
    change = current_working_capital - previous_working_capital
    logger.debug(f"营运资金变化: {change}")
    return change
