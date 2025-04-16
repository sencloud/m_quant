from langchain_openai import ChatOpenAI
from AI.graph.state import AgentState, show_agent_reasoning
from AI.tools.api import get_financial_metrics, get_market_cap, search_line_items
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from AI.utils.progress import progress
from AI.utils.llm import call_llm
from loguru import logger


class BillAckmanSignal(BaseModel):
    """
    Bill Ackman信号模型
    包含信号类型、置信度和推理过程
    """
    signal: Literal["bullish", "bearish", "neutral"]  # 看涨、看跌或中性
    confidence: float  # 置信度
    reasoning: str  # 推理过程


def bill_ackman_agent(state: AgentState):
    """
    使用Bill Ackman的投资原则和LLM推理分析股票。
    获取多个时期的数据以获得更稳健的长期观点。
    结合品牌/竞争优势、激进主义潜力和其他关键因素。
    """
    logger.info("开始Bill Ackman分析")
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    
    logger.info(f"分析股票: {tickers}, 结束日期: {end_date}")
    analysis_data = {}
    ackman_analysis = {}
    
    for ticker in tickers:
        logger.info(f"开始分析股票 {ticker}")
        progress.update_status("bill_ackman_agent", ticker, "获取财务指标")
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)
        
        progress.update_status("bill_ackman_agent", ticker, "收集财务项目")
        # 请求多个时期的数据（年度或TTM）以获得更稳健的长期观点
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "operating_margin",  # 营业利润率
                "debt_to_equity",  # 债务权益比
                "free_cash_flow",  # 自由现金流
                "total_assets",  # 总资产
                "total_liabilities",  # 总负债
                "dividends_and_other_cash_distributions",  # 股息和其他现金分配
                "outstanding_shares",  # 流通股
                # 可选：如果有无形资产数据
                # "intangible_assets"
            ],
            end_date,
            period="annual",
            limit=5
        )
        
        progress.update_status("bill_ackman_agent", ticker, "获取市值")
        market_cap = get_market_cap(ticker, end_date)
        
        progress.update_status("bill_ackman_agent", ticker, "分析业务质量")
        quality_analysis = analyze_business_quality(metrics, financial_line_items)
        
        progress.update_status("bill_ackman_agent", ticker, "分析资产负债表和资本结构")
        balance_sheet_analysis = analyze_financial_discipline(metrics, financial_line_items)
        
        progress.update_status("bill_ackman_agent", ticker, "分析激进主义潜力")
        activism_analysis = analyze_activism_potential(financial_line_items)
        
        progress.update_status("bill_ackman_agent", ticker, "计算内在价值和安全边际")
        valuation_analysis = analyze_valuation(financial_line_items, market_cap)
        
        # 合并部分分数或信号
        total_score = (
            quality_analysis["score"]
            + balance_sheet_analysis["score"]
            + activism_analysis["score"]
            + valuation_analysis["score"]
        )
        max_possible_score = 20  # 根据需要调整权重（例如每个子分析5分）
        
        # 生成简单的买入/持有/卖出（看涨/中性/看跌）信号
        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"  # 看涨
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"  # 看跌
        else:
            signal = "neutral"  # 中性
        
        logger.info(f"{ticker} 总分数: {total_score}/{max_possible_score}, 信号: {signal}")
        
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "quality_analysis": quality_analysis,
            "balance_sheet_analysis": balance_sheet_analysis,
            "activism_analysis": activism_analysis,
            "valuation_analysis": valuation_analysis
        }
        
        progress.update_status("bill_ackman_agent", ticker, "生成Bill Ackman分析")
        ackman_output = generate_ackman_output(
            ticker=ticker, 
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )
        
        ackman_analysis[ticker] = {
            "signal": ackman_output.signal,
            "confidence": ackman_output.confidence,
            "reasoning": ackman_output.reasoning
        }
        
        logger.info(f"{ticker} 分析完成: 信号={ackman_output.signal}, 置信度={ackman_output.confidence}")
        progress.update_status("bill_ackman_agent", ticker, "完成")
    
    # 将结果包装在链的单个消息中
    message = HumanMessage(
        content=json.dumps(ackman_analysis),
        name="bill_ackman_agent"
    )
    
    # 如果请求，显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(ackman_analysis, "Bill Ackman Agent")
    
    # 将信号添加到整体状态
    state["data"]["analyst_signals"]["bill_ackman_agent"] = ackman_analysis

    logger.info("Bill Ackman分析完成")
    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_business_quality(metrics: list, financial_line_items: list) -> dict:
    """
    分析公司是否拥有高质量的业务，具有稳定或增长的现金流，
    持久的竞争优势（护城河）和长期增长潜力。
    如果有无形资产数据，也尝试推断品牌强度（可选）。
    """
    logger.debug("开始分析业务质量")
    score = 0
    details = []
    
    if not metrics or not financial_line_items:
        logger.warning("数据不足，无法分析业务质量")
        return {
            "score": 0,
            "details": "数据不足，无法分析业务质量"
        }
    
    # 1. 多期收入增长分析
    revenues = [item.revenue for item in financial_line_items if item.revenue is not None]
    if len(revenues) >= 2:
        initial, final = revenues[0], revenues[-1]
        if initial and final and final > initial:
            growth_rate = (final - initial) / abs(initial)
            if growth_rate > 0.5:  # 例如，累计增长50%
                score += 2
                details.append(f"收入在整个期间增长了{(growth_rate*100):.1f}%（强劲增长）。")
            else:
                score += 1
                details.append(f"收入增长为正但累计低于50%（{(growth_rate*100):.1f}%）。")
        else:
            details.append("收入没有显著增长或数据不足。")
    else:
        details.append("没有足够的收入数据用于多期趋势分析。")
    
    # 2. 营业利润率和自由现金流一致性
    fcf_vals = [item.free_cash_flow for item in financial_line_items if item.free_cash_flow is not None]
    op_margin_vals = [item.operating_margin for item in financial_line_items if item.operating_margin is not None]
    
    if op_margin_vals:
        above_15 = sum(1 for m in op_margin_vals if m > 0.15)
        if above_15 >= (len(op_margin_vals) // 2 + 1):
            score += 2
            details.append("营业利润率经常超过15%（表明良好的盈利能力）。")
        else:
            details.append("营业利润率不持续高于15%。")
    else:
        details.append("各期没有营业利润率数据。")
    
    if fcf_vals:
        positive_fcf_count = sum(1 for f in fcf_vals if f > 0)
        if positive_fcf_count >= (len(fcf_vals) // 2 + 1):
            score += 1
            details.append("大多数期间显示正自由现金流。")
        else:
            details.append("自由现金流不持续为正。")
    else:
        details.append("各期没有自由现金流数据。")
    
    # 3. 从最新指标检查股本回报率（ROE）
    latest_metrics = metrics[0]
    if latest_metrics.return_on_equity and latest_metrics.return_on_equity > 0.15:
        score += 2
        details.append(f"高ROE为{latest_metrics.return_on_equity:.1%}，表明具有竞争优势。")
    elif latest_metrics.return_on_equity:
        details.append(f"ROE为{latest_metrics.return_on_equity:.1%}，处于中等水平。")
    else:
        details.append("没有ROE数据。")
    
    # 4. （可选）品牌无形资产（如果获取了无形资产）
    # intangible_vals = [item.intangible_assets for item in financial_line_items if item.intangible_assets]
    # if intangible_vals and sum(intangible_vals) > 0:
    #     details.append("显著的无形资产可能表明品牌价值或专有技术。")
    #     score += 1
    
    logger.debug(f"业务质量分析完成，得分: {score}")
    return {
        "score": score,
        "details": "; ".join(details)
    }


def analyze_financial_discipline(metrics: list, financial_line_items: list) -> dict:
    """
    评估公司多个时期的资产负债表：
    - 债务比率趋势
    - 随时间向股东返还资本（股息、回购）
    """
    logger.debug("开始分析财务纪律")
    score = 0
    details = []
    
    if not metrics or not financial_line_items:
        logger.warning("数据不足，无法分析财务纪律")
        return {
            "score": 0,
            "details": "数据不足，无法分析财务纪律"
        }
    
    # 1. 多期债务比率或债务权益比
    debt_to_equity_vals = [item.debt_to_equity for item in financial_line_items if item.debt_to_equity is not None]
    if debt_to_equity_vals:
        below_one_count = sum(1 for d in debt_to_equity_vals if d < 1.0)
        if below_one_count >= (len(debt_to_equity_vals) // 2 + 1):
            score += 2
            details.append("大多数期间的债务权益比<1.0（合理的杠杆）。")
        else:
            details.append("许多期间的债务权益比>=1.0（可能是高杠杆）。")
    else:
        # 回退到总负债/总资产
        liab_to_assets = []
        for item in financial_line_items:
            if item.total_liabilities and item.total_assets and item.total_assets > 0:
                liab_to_assets.append(item.total_liabilities / item.total_assets)
        
        if liab_to_assets:
            below_50pct_count = sum(1 for ratio in liab_to_assets if ratio < 0.5)
            if below_50pct_count >= (len(liab_to_assets) // 2 + 1):
                score += 2
                details.append("大多数期间的负债资产比<50%。")
            else:
                details.append("许多期间的负债资产比>=50%。")
        else:
            details.append("没有一致的杠杆比率数据。")
    
    # 2. 资本配置方法（股息+股数）
    dividends_list = [
        item.dividends_and_other_cash_distributions
        for item in financial_line_items
        if item.dividends_and_other_cash_distributions is not None
    ]
    if dividends_list:
        paying_dividends_count = sum(1 for d in dividends_list if d < 0)
        if paying_dividends_count >= (len(dividends_list) // 2 + 1):
            score += 1
            details.append("公司有向股东返还资本的历史（股息）。")
        else:
            details.append("股息不持续支付或没有分配数据。")
    else:
        details.append("各期没有股息数据。")
    
    # 检查股数减少（简单方法）
    shares = [item.outstanding_shares for item in financial_line_items if item.outstanding_shares is not None]
    if len(shares) >= 2:
        if shares[-1] < shares[0]:
            score += 1
            details.append("流通股随时间减少（可能有回购）。")
        else:
            details.append("流通股在可用期间内没有减少。")
    else:
        details.append("没有多期股数数据来评估回购。")
    
    logger.debug(f"财务纪律分析完成，得分: {score}")
    return {
        "score": score,
        "details": "; ".join(details)
    }


def analyze_activism_potential(financial_line_items: list) -> dict:
    """
    Bill Ackman经常在公司拥有不错的品牌或护城河但运营表现不佳时进行激进主义。
    
    我们将采用简化的方法：
    - 寻找积极的收入趋势但利润率不佳
    - 这可能表明如果运营改进可以释放价值，则存在"激进主义上行空间"。
    """
    logger.debug("开始分析激进主义潜力")
    if not financial_line_items:
        logger.warning("数据不足，无法分析激进主义潜力")
        return {
            "score": 0,
            "details": "数据不足，无法分析激进主义潜力"
        }
    
    # 检查收入增长与营业利润率
    revenues = [item.revenue for item in financial_line_items if item.revenue is not None]
    op_margins = [item.operating_margin for item in financial_line_items if item.operating_margin is not None]
    
    if len(revenues) < 2 or not op_margins:
        logger.warning("数据不足，无法评估激进主义潜力（需要多年收入和利润率）")
        return {
            "score": 0,
            "details": "数据不足，无法评估激进主义潜力（需要多年收入和利润率）。"
        }
    
    initial, final = revenues[0], revenues[-1]
    revenue_growth = (final - initial) / abs(initial) if initial else 0
    avg_margin = sum(op_margins) / len(op_margins)
    
    score = 0
    details = []
    
    # 假设如果有不错的收入增长但利润率低于10%，Ackman可能会看到激进主义潜力
    if revenue_growth > 0.15 and avg_margin < 0.10:
        score += 2
        details.append(
            f"收入增长健康（约{revenue_growth*100:.1f}%），但利润率低（平均{avg_margin*100:.1f}%）。"
            "激进主义可以释放利润率改进。"
        )
    else:
        details.append("没有明显的激进主义机会（要么利润率已经不错，要么增长疲软）。")
    
    logger.debug(f"激进主义潜力分析完成，得分: {score}")
    return {"score": score, "details": "; ".join(details)}


def analyze_valuation(financial_line_items: list, market_cap: float) -> dict:
    """
    Ackman投资于交易价格低于内在价值的公司。
    使用简化的DCF，以FCF为代理，加上安全边际分析。
    """
    logger.debug("开始分析估值")
    if not financial_line_items or market_cap is None:
        logger.warning("数据不足，无法进行估值")
        return {
            "score": 0,
            "details": "数据不足，无法进行估值"
        }
    
    latest = financial_line_items[-1]
    fcf = latest.free_cash_flow if latest.free_cash_flow else 0
    
    if fcf <= 0:
        logger.warning(f"没有正FCF用于估值; FCF = {fcf}")
        return {
            "score": 0,
            "details": f"没有正FCF用于估值; FCF = {fcf}",
            "intrinsic_value": None
        }
    
    # 基本DCF假设
    growth_rate = 0.06
    discount_rate = 0.10
    terminal_multiple = 15
    projection_years = 5
    
    present_value = 0
    for year in range(1, projection_years + 1):
        future_fcf = fcf * (1 + growth_rate) ** year
        pv = future_fcf / ((1 + discount_rate) ** year)
        present_value += pv
    
    # 终值
    terminal_value = (
        fcf * (1 + growth_rate) ** projection_years * terminal_multiple
    ) / ((1 + discount_rate) ** projection_years)
    
    intrinsic_value = present_value + terminal_value
    margin_of_safety = (intrinsic_value - market_cap) / market_cap
    
    score = 0
    # 简单评分
    if margin_of_safety > 0.3:
        score += 3
    elif margin_of_safety > 0.1:
        score += 1
    
    details = [
        f"计算的内在价值: ~{intrinsic_value:,.2f}",
        f"市值: ~{market_cap:,.2f}",
        f"安全边际: {margin_of_safety:.2%}"
    ]
    
    logger.debug(f"估值分析完成，得分: {score}, 安全边际: {margin_of_safety:.2%}")
    return {
        "score": score,
        "details": "; ".join(details),
        "intrinsic_value": intrinsic_value,
        "margin_of_safety": margin_of_safety
    }


def generate_ackman_output(
    ticker: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> BillAckmanSignal:
    """
    以Bill Ackman的风格生成投资决策。
    在系统提示中更明确地引用品牌强度、激进主义潜力、
    催化剂和管理层变动。
    """
    logger.info(f"为 {ticker} 生成Bill Ackman风格输出")
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是Bill Ackman AI代理，使用他的原则做出投资决策：

            1. 寻求具有持久竞争优势（护城河）的高质量企业，通常是知名消费或服务品牌。
            2. 优先考虑长期一致的免费现金流和增长潜力。
            3. 倡导强财务纪律（合理杠杆，高效资本配置）。
            4. 估值很重要：目标是有安全边际的内在价值。
            5. 考虑管理层或运营改进可以释放实质性上行空间的激进主义。
            6. 集中在少数高信念投资上。

            在你的推理中：
            - 强调品牌强度、护城河或独特的市场定位。
            - 将免费现金流生成和利润率趋势作为关键信号。
            - 分析杠杆、股票回购和股息作为资本纪律指标。
            - 提供有数字支持的估值评估（DCF、倍数等）。
            - 识别任何激进主义或价值创造的催化剂（例如，成本削减，更好的资本配置）。
            - 在讨论弱点或机会时使用自信、分析性，有时是对抗性的语气。

            返回你的最终建议（信号：看涨、中性或看跌），置信度为0-100，并附带详细的推理部分。
            """
        ),
        (
            "human",
            """基于以下分析，创建Ackman风格的投资信号。

            {ticker}的分析数据：
            {analysis_data}

            以严格有效的JSON格式返回你的输出：
            {{
              "signal": "bullish" | "bearish" | "neutral",
              "confidence": float (0-100),
              "reasoning": "string"
            }}
            """
        )
    ])

    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    def create_default_bill_ackman_signal():
        logger.warning("创建默认Bill Ackman信号")
        return BillAckmanSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错，默认为中性"
        )

    logger.info(f"调用LLM生成 {ticker} 的Bill Ackman信号")
    return call_llm(
        prompt=prompt, 
        model_name=model_name, 
        model_provider=model_provider, 
        pydantic_model=BillAckmanSignal, 
        agent_name="bill_ackman_agent", 
        default_factory=create_default_bill_ackman_signal,
    )
