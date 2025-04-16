from AI.graph.state import AgentState, show_agent_reasoning
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from AI.tools.api import get_financial_metrics, get_market_cap, search_line_items
from AI.utils.llm import call_llm
from AI.utils.progress import progress
from loguru import logger


class WarrenBuffettSignal(BaseModel):
    """
    沃伦·巴菲特的投资信号模型
    
    属性:
    - signal: 投资信号类型 ("bullish" | "bearish" | "neutral")
    - confidence: 信号置信度 (0-100)
    - reasoning: 投资理由说明
    """
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def warren_buffett_agent(state: AgentState):
    """
    基于巴菲特的投资原则和LLM推理分析股票
    
    主要功能:
    1. 获取财务指标数据
    2. 分析基本面
    3. 评估业务一致性
    4. 分析护城河
    5. 评估管理层质量
    6. 计算内在价值
    7. 生成投资信号
    """
    logger.info("开始巴菲特投资分析")
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    logger.info(f"分析股票: {tickers}")

    # 收集所有分析数据用于LLM推理
    analysis_data = {}
    buffett_analysis = {}

    for ticker in tickers:
        logger.info(f"开始分析 {ticker}")
        progress.update_status("warren_buffett_agent", ticker, "获取财务指标")
        # 获取所需数据
        metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=5)
        logger.debug(f"获取到财务指标: {metrics}")

        progress.update_status("warren_buffett_agent", ticker, "收集财务项目")
        financial_line_items = search_line_items(
            ticker,
            [
                "capital_expenditure",
                "depreciation_and_amortization",
                "net_income",
                "outstanding_shares",
                "total_assets",
                "total_liabilities",
                "dividends_and_other_cash_distributions",
                "issuance_or_purchase_of_equity_shares",
            ],
            end_date,
        )
        logger.debug(f"获取到财务项目: {financial_line_items}")

        progress.update_status("warren_buffett_agent", ticker, "获取市值")
        # 获取当前市值
        market_cap = get_market_cap(ticker, end_date)
        logger.debug(f"当前市值: {market_cap}")

        progress.update_status("warren_buffett_agent", ticker, "分析基本面")
        # 分析基本面
        fundamental_analysis = analyze_fundamentals(metrics)
        logger.debug(f"基本面分析结果: {fundamental_analysis}")

        progress.update_status("warren_buffett_agent", ticker, "分析一致性")
        consistency_analysis = analyze_consistency(financial_line_items)
        logger.debug(f"一致性分析结果: {consistency_analysis}")

        progress.update_status("warren_buffett_agent", ticker, "分析护城河")
        moat_analysis = analyze_moat(metrics)
        logger.debug(f"护城河分析结果: {moat_analysis}")

        progress.update_status("warren_buffett_agent", ticker, "分析管理层质量")
        mgmt_analysis = analyze_management_quality(financial_line_items)
        logger.debug(f"管理层分析结果: {mgmt_analysis}")

        progress.update_status("warren_buffett_agent", ticker, "计算内在价值")
        intrinsic_value_analysis = calculate_intrinsic_value(financial_line_items)
        logger.debug(f"内在价值分析结果: {intrinsic_value_analysis}")

        # 计算总分
        total_score = fundamental_analysis["score"] + consistency_analysis["score"] + moat_analysis["score"] + mgmt_analysis["score"]
        max_possible_score = 10 + moat_analysis["max_score"] + mgmt_analysis["max_score"]
        logger.debug(f"总分: {total_score}, 最高可能分数: {max_possible_score}")

        # 如果有内在价值和当前价格，添加安全边际分析
        margin_of_safety = None
        intrinsic_value = intrinsic_value_analysis["intrinsic_value"]
        if intrinsic_value and market_cap:
            margin_of_safety = (intrinsic_value - market_cap) / market_cap
            logger.debug(f"安全边际: {margin_of_safety:.2%}")

        # 使用更严格的安全边际要求生成交易信号
        # 如果基本面+护城河+管理层都很强但安全边际<0.3，则为中性
        # 如果基本面很弱或安全边际严重为负 -> 看跌
        # 否则看涨
        if (total_score >= 0.7 * max_possible_score) and margin_of_safety and (margin_of_safety >= 0.3):
            signal = "bullish"
            logger.info(f"{ticker} 生成看涨信号")
        elif total_score <= 0.3 * max_possible_score or (margin_of_safety is not None and margin_of_safety < -0.3):
            signal = "bearish"
            logger.info(f"{ticker} 生成看跌信号")
        else:
            signal = "neutral"
            logger.info(f"{ticker} 生成中性信号")

        # 合并所有分析结果
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "fundamental_analysis": fundamental_analysis,
            "consistency_analysis": consistency_analysis,
            "moat_analysis": moat_analysis,
            "management_analysis": mgmt_analysis,
            "intrinsic_value_analysis": intrinsic_value_analysis,
            "market_cap": market_cap,
            "margin_of_safety": margin_of_safety,
        }
        logger.debug(f"分析数据: {analysis_data[ticker]}")

        progress.update_status("warren_buffett_agent", ticker, "生成巴菲特分析")
        buffett_output = generate_buffett_output(
            ticker=ticker,
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )
        logger.debug(f"巴菲特分析输出: {buffett_output}")

        # 以与其他代理一致的格式存储分析
        buffett_analysis[ticker] = {
            "signal": buffett_output.signal,
            "confidence": buffett_output.confidence,
            "reasoning": buffett_output.reasoning,
        }
        logger.info(f"{ticker} 分析完成")

        progress.update_status("warren_buffett_agent", ticker, "完成")

    # 创建消息
    message = HumanMessage(content=json.dumps(buffett_analysis), name="warren_buffett_agent")

    # 如果请求，显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(buffett_analysis, "Warren Buffett Agent")

    # 将信号添加到analyst_signals列表
    state["data"]["analyst_signals"]["warren_buffett_agent"] = buffett_analysis
    logger.info("巴菲特分析完成")

    return {"messages": [message], "data": state["data"]}


def analyze_fundamentals(metrics: list) -> dict[str, any]:
    """
    基于巴菲特的 criteria 分析公司基本面
    
    分析指标:
    1. ROE (股本回报率)
    2. 资产负债率
    3. 营业利润率
    4. 流动比率
    """
    if not metrics:
        logger.warning("没有足够的财务指标数据")
        return {"score": 0, "details": "基本面数据不足"}

    latest_metrics = metrics[0]
    logger.debug(f"分析最新财务指标: {latest_metrics}")

    score = 0
    reasoning = []

    # 检查ROE (股本回报率)
    if latest_metrics.return_on_equity and latest_metrics.return_on_equity > 0.15:  # 15% ROE阈值
        score += 2
        reasoning.append(f"强劲的ROE {latest_metrics.return_on_equity:.1%}")
    elif latest_metrics.return_on_equity:
        reasoning.append(f"较弱的ROE {latest_metrics.return_on_equity:.1%}")
    else:
        reasoning.append("无ROE数据")

    # 检查资产负债率
    if latest_metrics.debt_to_equity and latest_metrics.debt_to_equity < 0.5:
        score += 2
        reasoning.append("保守的债务水平")
    elif latest_metrics.debt_to_equity:
        reasoning.append(f"较高的资产负债率 {latest_metrics.debt_to_equity:.1f}")
    else:
        reasoning.append("无资产负债率数据")

    # 检查营业利润率
    if latest_metrics.operating_margin and latest_metrics.operating_margin > 0.15:
        score += 2
        reasoning.append("强劲的营业利润率")
    elif latest_metrics.operating_margin:
        reasoning.append(f"较弱的营业利润率 {latest_metrics.operating_margin:.1%}")
    else:
        reasoning.append("无营业利润率数据")

    # 检查流动比率
    if latest_metrics.current_ratio and latest_metrics.current_ratio > 1.5:
        score += 1
        reasoning.append("良好的流动性状况")
    elif latest_metrics.current_ratio:
        reasoning.append(f"较弱的流动性，流动比率 {latest_metrics.current_ratio:.1f}")
    else:
        reasoning.append("无流动比率数据")

    logger.debug(f"基本面分析得分: {score}, 理由: {reasoning}")
    return {"score": score, "details": "; ".join(reasoning), "metrics": latest_metrics.model_dump()}


def analyze_consistency(financial_line_items: list) -> dict[str, any]:
    """
    分析收益一致性和增长
    
    分析内容:
    1. 收益增长趋势
    2. 总增长率
    """
    if len(financial_line_items) < 4:  # 需要至少4个期间进行趋势分析
        logger.warning("历史数据不足")
        return {"score": 0, "details": "历史数据不足"}

    score = 0
    reasoning = []

    # 检查收益增长趋势
    earnings_values = [item.net_income for item in financial_line_items if item.net_income]
    logger.debug(f"收益值: {earnings_values}")
    
    if len(earnings_values) >= 4:
        # 简单检查：每个期间的收益是否大于下一个期间
        earnings_growth = all(earnings_values[i] > earnings_values[i + 1] for i in range(len(earnings_values) - 1))

        if earnings_growth:
            score += 3
            reasoning.append("过去期间收益持续增长")
        else:
            reasoning.append("收益增长模式不一致")

        # 计算从最早到最新的总增长率
        if len(earnings_values) >= 2 and earnings_values[-1] != 0:
            growth_rate = (earnings_values[0] - earnings_values[-1]) / abs(earnings_values[-1])
            reasoning.append(f"过去{len(earnings_values)}个期间总收益增长 {growth_rate:.1%}")
    else:
        reasoning.append("收益数据不足以进行趋势分析")

    logger.debug(f"一致性分析得分: {score}, 理由: {reasoning}")
    return {
        "score": score,
        "details": "; ".join(reasoning),
    }


def analyze_moat(metrics: list) -> dict[str, any]:
    """
    评估公司是否具有持久的竞争优势（护城河）
    
    分析内容:
    1. ROE稳定性
    2. 营业利润率稳定性
    3. 综合评分
    """
    if not metrics or len(metrics) < 3:
        logger.warning("数据不足以进行护城河分析")
        return {"score": 0, "max_score": 3, "details": "数据不足以进行护城河分析"}

    reasoning = []
    moat_score = 0
    historical_roes = []
    historical_margins = []

    for m in metrics:
        if m.return_on_equity is not None:
            historical_roes.append(m.return_on_equity)
        if m.operating_margin is not None:
            historical_margins.append(m.operating_margin)

    logger.debug(f"历史ROE: {historical_roes}")
    logger.debug(f"历史利润率: {historical_margins}")

    # 检查ROE稳定性
    if len(historical_roes) >= 3:
        stable_roe = all(r > 0.15 for r in historical_roes)
        if stable_roe:
            moat_score += 1
            reasoning.append("ROE持续高于15%（表明存在护城河）")
        else:
            reasoning.append("ROE未持续高于15%")

    # 检查营业利润率稳定性
    if len(historical_margins) >= 3:
        stable_margin = all(m > 0.15 for m in historical_margins)
        if stable_margin:
            moat_score += 1
            reasoning.append("营业利润率持续高于15%（护城河指标）")
        else:
            reasoning.append("营业利润率未持续高于15%")

    # 如果两者都稳定/改善，额外加1分
    if moat_score == 2:
        moat_score += 1
        reasoning.append("ROE和利润率稳定性都表明存在坚实的护城河")

    logger.debug(f"护城河分析得分: {moat_score}, 理由: {reasoning}")
    return {
        "score": moat_score,
        "max_score": 3,
        "details": "; ".join(reasoning),
    }


def analyze_management_quality(financial_line_items: list) -> dict[str, any]:
    """
    检查股票稀释或持续回购，以及股息记录
    
    分析内容:
    1. 股票回购情况
    2. 新股发行情况
    3. 股息支付记录
    """
    if not financial_line_items:
        logger.warning("数据不足以进行管理层分析")
        return {"score": 0, "max_score": 2, "details": "数据不足以进行管理层分析"}

    reasoning = []
    mgmt_score = 0

    latest = financial_line_items[0]
    logger.debug(f"最新财务数据: {latest}")

    if hasattr(latest, "issuance_or_purchase_of_equity_shares") and latest.issuance_or_purchase_of_equity_shares and latest.issuance_or_purchase_of_equity_shares < 0:
        # 负值表示公司在回购股票
        mgmt_score += 1
        reasoning.append("公司一直在回购股票（对股东友好）")

    if hasattr(latest, "issuance_or_purchase_of_equity_shares") and latest.issuance_or_purchase_of_equity_shares and latest.issuance_or_purchase_of_equity_shares > 0:
        # 正发行意味着新股 => 可能的稀释
        reasoning.append("最近发行普通股（可能稀释）")
    else:
        reasoning.append("未检测到显著的新股发行")

    # 检查是否有股息
    if hasattr(latest, "dividends_and_other_cash_distributions") and latest.dividends_and_other_cash_distributions and latest.dividends_and_other_cash_distributions < 0:
        mgmt_score += 1
        reasoning.append("公司有支付股息的记录")
    else:
        reasoning.append("没有或很少支付股息")

    logger.debug(f"管理层分析得分: {mgmt_score}, 理由: {reasoning}")
    return {
        "score": mgmt_score,
        "max_score": 2,
        "details": "; ".join(reasoning),
    }


def calculate_owner_earnings(financial_line_items: list) -> dict[str, any]:
    """
    计算所有者收益（巴菲特偏好的真实收益能力指标）
    所有者收益 = 净利润 + 折旧 - 维护性资本支出
    """
    if not financial_line_items or len(financial_line_items) < 1:
        logger.warning("数据不足以计算所有者收益")
        return {"owner_earnings": None, "details": ["数据不足以计算所有者收益"]}

    latest = financial_line_items[0]
    logger.debug(f"最新财务数据: {latest}")

    net_income = latest.net_income
    depreciation = latest.depreciation_and_amortization
    capex = latest.capital_expenditure

    if not all([net_income, depreciation, capex]):
        logger.warning("缺少所有者收益计算的组成部分")
        return {"owner_earnings": None, "details": ["缺少所有者收益计算的组成部分"]}

    # 估算维护性资本支出（通常是总资本支出的70-80%）
    maintenance_capex = capex * 0.75
    owner_earnings = net_income + depreciation - maintenance_capex

    logger.debug(f"所有者收益计算结果: {owner_earnings}")
    return {
        "owner_earnings": owner_earnings,
        "components": {"net_income": net_income, "depreciation": depreciation, "maintenance_capex": maintenance_capex},
        "details": ["所有者收益计算成功"],
    }


def calculate_intrinsic_value(financial_line_items: list) -> dict[str, any]:
    """
    使用DCF模型和所有者收益计算内在价值
    
    假设:
    1. 增长率: 5%（保守估计）
    2. 折现率: 9%（典型折现率）
    3. 终值倍数: 12
    4. 预测年数: 10年
    """
    if not financial_line_items:
        logger.warning("数据不足以进行估值")
        return {"intrinsic_value": None, "details": ["数据不足以进行估值"]}

    # 计算所有者收益
    earnings_data = calculate_owner_earnings(financial_line_items)
    if not earnings_data["owner_earnings"]:
        logger.warning("无法计算所有者收益")
        return {"intrinsic_value": None, "details": earnings_data["details"]}

    owner_earnings = earnings_data["owner_earnings"]
    logger.debug(f"所有者收益: {owner_earnings}")

    # 获取当前市场数据
    latest_financial_line_items = financial_line_items[0]
    shares_outstanding = latest_financial_line_items.outstanding_shares

    if not shares_outstanding:
        logger.warning("缺少流通股数据")
        return {"intrinsic_value": None, "details": ["缺少流通股数据"]}

    # 巴菲特的DCF假设（保守方法）
    growth_rate = 0.05  # 保守的5%增长率
    discount_rate = 0.09  # 典型的~9%折现率
    terminal_multiple = 12
    projection_years = 10

    logger.debug(f"DCF假设: 增长率={growth_rate}, 折现率={discount_rate}, 终值倍数={terminal_multiple}, 预测年数={projection_years}")

    # 未来所有者收益的折现值之和
    future_value = 0
    for year in range(1, projection_years + 1):
        future_earnings = owner_earnings * (1 + growth_rate) ** year
        present_value = future_earnings / (1 + discount_rate) ** year
        future_value += present_value

    # 终值
    terminal_value = (owner_earnings * (1 + growth_rate) ** projection_years * terminal_multiple) / ((1 + discount_rate) ** projection_years)

    intrinsic_value = future_value + terminal_value
    logger.debug(f"内在价值: {intrinsic_value}")

    return {
        "intrinsic_value": intrinsic_value,
        "owner_earnings": owner_earnings,
        "assumptions": {
            "growth_rate": growth_rate,
            "discount_rate": discount_rate,
            "terminal_multiple": terminal_multiple,
            "projection_years": projection_years,
        },
        "details": ["使用DCF模型和所有者收益计算内在价值"],
    }


def generate_buffett_output(
    ticker: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> WarrenBuffettSignal:
    """
    基于巴菲特的投资原则从LLM获取投资决策
    
    原则:
    1. 能力圈：只投资于你了解的业务
    2. 安全边际 (> 30%)：以显著低于内在价值的价格买入
    3. 经济护城河：寻找持久的竞争优势
    4. 优质管理层：寻找保守、以股东为导向的团队
    5. 财务实力：偏好低债务、高股本回报率
    6. 长期视角：投资于企业，而不仅仅是股票
    7. 仅在基本面恶化或估值远超过内在价值时卖出
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Warren Buffett AI agent. Decide on investment signals based on Warren Buffett's principles:
                - Circle of Competence: Only invest in businesses you understand
                - Margin of Safety (> 30%): Buy at a significant discount to intrinsic value
                - Economic Moat: Look for durable competitive advantages
                - Quality Management: Seek conservative, shareholder-oriented teams
                - Financial Strength: Favor low debt, strong returns on equity
                - Long-term Horizon: Invest in businesses, not just stocks
                - Sell only if fundamentals deteriorate or valuation far exceeds intrinsic value

                When providing your reasoning, be thorough and specific by:
                1. Explaining the key factors that influenced your decision the most (both positive and negative)
                2. Highlighting how the company aligns with or violates specific Buffett principles
                3. Providing quantitative evidence where relevant (e.g., specific margins, ROE values, debt levels)
                4. Concluding with a Buffett-style assessment of the investment opportunity
                5. Using Warren Buffett's voice and conversational style in your explanation

                For example, if bullish: "I'm particularly impressed with [specific strength], reminiscent of our early investment in See's Candies where we saw [similar attribute]..."
                For example, if bearish: "The declining returns on capital remind me of the textile operations at Berkshire that we eventually exited because..."

                Follow these guidelines strictly.
                """,
            ),
            (
                "human",
                """Based on the following data, create the investment signal as Warren Buffett would:

                Analysis Data for {ticker}:
                {analysis_data}

                Return the trading signal in the following JSON format exactly:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
                  "confidence": float between 0 and 100,
                  "reasoning": "string"
                }}
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})
    logger.debug(f"生成LLM提示: {prompt}")

    # 解析失败时的默认信号
    def create_default_warren_buffett_signal():
        logger.warning("分析出错，返回默认中性信号")
        return WarrenBuffettSignal(signal="neutral", confidence=0.0, reasoning="分析出错，默认返回中性信号")

    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=WarrenBuffettSignal,
        agent_name="warren_buffett_agent",
        default_factory=create_default_warren_buffett_signal,
    )
