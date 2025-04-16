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
import math
from loguru import logger


class BenGrahamSignal(BaseModel):
    """
    本杰明·格雷厄姆信号模型
    包含信号类型、置信度和推理过程
    """
    signal: Literal["bullish", "bearish", "neutral"]  # 信号类型：看涨、看跌或中性
    confidence: float  # 置信度
    reasoning: str  # 推理过程


def ben_graham_agent(state: AgentState):
    """
    使用本杰明·格雷厄姆的经典价值投资原则分析股票:
    1. 多年稳定的盈利
    2. 稳健的财务实力（低负债、充足的流动性）
    3. 相对于内在价值的折价（如格雷厄姆数字或净流动资产）
    4. 充足的安全边际
    
    Analyzes stocks using Benjamin Graham's classic value-investing principles:
    1. Earnings stability over multiple years.
    2. Solid financial strength (low debt, adequate liquidity).
    3. Discount to intrinsic value (e.g. Graham Number or net-net).
    4. Adequate margin of safety.
    """
    logger.info("开始本杰明·格雷厄姆分析")
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    logger.info(f"分析日期: {end_date}, 股票代码: {tickers}")

    analysis_data = {}
    graham_analysis = {}

    for ticker in tickers:
        logger.info(f"开始分析股票 {ticker}")
        
        progress.update_status("ben_graham_agent", ticker, "获取财务指标")
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=10)
        logger.debug(f"获取到财务指标: {metrics}")

        progress.update_status("ben_graham_agent", ticker, "收集财务项目")
        financial_line_items = search_line_items(ticker, ["earnings_per_share", "revenue", "net_income", "book_value_per_share", "total_assets", "total_liabilities", "current_assets", "current_liabilities", "dividends_and_other_cash_distributions", "outstanding_shares"], end_date, period="annual", limit=10)
        logger.debug(f"获取到财务项目: {financial_line_items}")

        progress.update_status("ben_graham_agent", ticker, "获取市值")
        market_cap = get_market_cap(ticker, end_date)
        logger.debug(f"获取到市值: {market_cap}")

        # 执行子分析
        progress.update_status("ben_graham_agent", ticker, "分析盈利稳定性")
        earnings_analysis = analyze_earnings_stability(metrics, financial_line_items)
        logger.info(f"盈利稳定性分析结果: {earnings_analysis}")

        progress.update_status("ben_graham_agent", ticker, "分析财务实力")
        strength_analysis = analyze_financial_strength(metrics, financial_line_items)
        logger.info(f"财务实力分析结果: {strength_analysis}")

        progress.update_status("ben_graham_agent", ticker, "分析格雷厄姆估值")
        valuation_analysis = analyze_valuation_graham(metrics, financial_line_items, market_cap)
        logger.info(f"格雷厄姆估值分析结果: {valuation_analysis}")

        # 汇总评分
        total_score = earnings_analysis["score"] + strength_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 15  # 三个分析函数的总可能分数
        logger.info(f"总分: {total_score}/{max_possible_score}")

        # 将总分映射到信号
        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"
        logger.info(f"生成的信号: {signal}")

        analysis_data[ticker] = {"signal": signal, "score": total_score, "max_score": max_possible_score, "earnings_analysis": earnings_analysis, "strength_analysis": strength_analysis, "valuation_analysis": valuation_analysis}

        progress.update_status("ben_graham_agent", ticker, "生成格雷厄姆分析")
        graham_output = generate_graham_output(
            ticker=ticker,
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )
        logger.info(f"格雷厄姆分析输出: {graham_output}")

        graham_analysis[ticker] = {"signal": graham_output.signal, "confidence": graham_output.confidence, "reasoning": graham_output.reasoning}

        progress.update_status("ben_graham_agent", ticker, "完成")
        logger.info(f"完成股票 {ticker} 的分析")

    # 将结果包装在单个消息中
    message = HumanMessage(content=json.dumps(graham_analysis), name="ben_graham_agent")

    # 可选显示推理过程
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(graham_analysis, "Ben Graham Agent")

    # 将信号存储在整体状态中
    state["data"]["analyst_signals"]["ben_graham_agent"] = graham_analysis
    logger.info("分析完成，返回结果")

    return {"messages": [message], "data": state["data"]}


def analyze_earnings_stability(metrics: list, financial_line_items: list) -> dict:
    """
    格雷厄姆要求至少几年的稳定正收益（理想情况下5年以上）。
    我们将检查:
    1. 正EPS的年数
    2. 从第一个到最后一个期间的EPS增长
    
    Graham wants at least several years of consistently positive earnings (ideally 5+).
    We'll check:
    1. Number of years with positive EPS.
    2. Growth in EPS from first to last period.
    """
    logger.info("开始分析盈利稳定性")
    score = 0
    details = []

    if not metrics or not financial_line_items:
        logger.warning("数据不足，无法进行盈利稳定性分析")
        return {"score": score, "details": "Insufficient data for earnings stability analysis"}

    eps_vals = []
    for item in financial_line_items:
        if item.earnings_per_share is not None:
            eps_vals.append(item.earnings_per_share)

    if len(eps_vals) < 2:
        logger.warning("没有足够的多年EPS数据")
        details.append("Not enough multi-year EPS data.")
        return {"score": score, "details": "; ".join(details)}

    # 1. 持续的正EPS
    positive_eps_years = sum(1 for e in eps_vals if e > 0)
    total_eps_years = len(eps_vals)
    logger.info(f"正EPS年数: {positive_eps_years}/{total_eps_years}")
    
    if positive_eps_years == total_eps_years:
        score += 3
        details.append("EPS was positive in all available periods.")
    elif positive_eps_years >= (total_eps_years * 0.8):
        score += 2
        details.append("EPS was positive in most periods.")
    else:
        details.append("EPS was negative in multiple periods.")

    # 2. 从最早到最新的EPS增长
    if eps_vals[-1] > eps_vals[0]:
        score += 1
        details.append("EPS grew from earliest to latest period.")
    else:
        details.append("EPS did not grow from earliest to latest period.")

    logger.info(f"盈利稳定性分析完成，得分: {score}")
    return {"score": score, "details": "; ".join(details)}


def analyze_financial_strength(metrics: list, financial_line_items: list) -> dict:
    """
    格雷厄姆检查流动性（流动比率 >= 2）、可管理的债务
    和股息记录（最好有一些股息历史）。
    
    Graham checks liquidity (current ratio >= 2), manageable debt,
    and dividend record (preferably some history of dividends).
    """
    logger.info("开始分析财务实力")
    score = 0
    details = []

    if not financial_line_items:
        logger.warning("没有数据用于财务实力分析")
        return {"score": score, "details": "No data for financial strength analysis"}

    latest_item = financial_line_items[-1]
    total_assets = latest_item.total_assets or 0
    total_liabilities = latest_item.total_liabilities or 0
    current_assets = latest_item.current_assets or 0
    current_liabilities = latest_item.current_liabilities or 0

    # 1. 流动比率
    if current_liabilities > 0:
        current_ratio = current_assets / current_liabilities
        logger.info(f"流动比率: {current_ratio:.2f}")
        if current_ratio >= 2.0:
            score += 2
            details.append(f"Current ratio = {current_ratio:.2f} (>=2.0: solid).")
        elif current_ratio >= 1.5:
            score += 1
            details.append(f"Current ratio = {current_ratio:.2f} (moderately strong).")
        else:
            details.append(f"Current ratio = {current_ratio:.2f} (<1.5: weaker liquidity).")
    else:
        details.append("Cannot compute current ratio (missing or zero current_liabilities).")

    # 2. 债务与资产比率
    if total_assets > 0:
        debt_ratio = total_liabilities / total_assets
        logger.info(f"债务比率: {debt_ratio:.2f}")
        if debt_ratio < 0.5:
            score += 2
            details.append(f"Debt ratio = {debt_ratio:.2f}, under 0.50 (conservative).")
        elif debt_ratio < 0.8:
            score += 1
            details.append(f"Debt ratio = {debt_ratio:.2f}, somewhat high but could be acceptable.")
        else:
            details.append(f"Debt ratio = {debt_ratio:.2f}, quite high by Graham standards.")
    else:
        details.append("Cannot compute debt ratio (missing total_assets).")

    # 3. 股息记录
    div_periods = [item.dividends_and_other_cash_distributions for item in financial_line_items if item.dividends_and_other_cash_distributions is not None]
    if div_periods:
        # 在许多数据源中，股息流出显示为负数
        # （支付给股东的钱）。我们将任何负数视为"支付了股息"
        div_paid_years = sum(1 for d in div_periods if d < 0)
        logger.info(f"支付股息的年数: {div_paid_years}/{len(div_periods)}")
        if div_paid_years > 0:
            # 例如，如果至少一半的期间有股息
            if div_paid_years >= (len(div_periods) // 2 + 1):
                score += 1
                details.append("Company paid dividends in the majority of the reported years.")
            else:
                details.append("Company has some dividend payments, but not most years.")
        else:
            details.append("Company did not pay dividends in these periods.")
    else:
        details.append("No dividend data available to assess payout consistency.")

    logger.info(f"财务实力分析完成，得分: {score}")
    return {"score": score, "details": "; ".join(details)}


def analyze_valuation_graham(metrics: list, financial_line_items: list, market_cap: float) -> dict:
    """
    格雷厄姆估值的核心方法:
    1. 净流动资产检查：(流动资产 - 总负债) vs 市值
    2. 格雷厄姆数字：sqrt(22.5 * EPS * 每股账面价值)
    3. 比较每股价格与格雷厄姆数字 => 安全边际
    
    Core Graham approach to valuation:
    1. Net-Net Check: (Current Assets - Total Liabilities) vs. Market Cap
    2. Graham Number: sqrt(22.5 * EPS * Book Value per Share)
    3. Compare per-share price to Graham Number => margin of safety
    """
    logger.info("开始格雷厄姆估值分析")
    if not financial_line_items or not market_cap or market_cap <= 0:
        logger.warning("数据不足，无法进行估值")
        return {"score": 0, "details": "Insufficient data to perform valuation"}

    latest = financial_line_items[-1]
    current_assets = latest.current_assets or 0
    total_liabilities = latest.total_liabilities or 0
    book_value_ps = latest.book_value_per_share or 0
    eps = latest.earnings_per_share or 0
    shares_outstanding = latest.outstanding_shares or 0

    details = []
    score = 0

    # 1. 净流动资产检查
    #   NCAV = 流动资产 - 总负债
    #   如果 NCAV > 市值 => 历史上是一个强烈的买入信号
    net_current_asset_value = current_assets - total_liabilities
    logger.info(f"净流动资产价值: {net_current_asset_value:,.2f}")
    
    if net_current_asset_value > 0 and shares_outstanding > 0:
        net_current_asset_value_per_share = net_current_asset_value / shares_outstanding
        price_per_share = market_cap / shares_outstanding if shares_outstanding else 0

        details.append(f"Net Current Asset Value = {net_current_asset_value:,.2f}")
        details.append(f"NCAV Per Share = {net_current_asset_value_per_share:,.2f}")
        details.append(f"Price Per Share = {price_per_share:,.2f}")

        if net_current_asset_value > market_cap:
            score += 4  # 非常强烈的格雷厄姆信号
            details.append("Net-Net: NCAV > Market Cap (classic Graham deep value).")
        else:
            # 部分净流动资产折价
            if net_current_asset_value_per_share >= (price_per_share * 0.67):
                score += 2
                details.append("NCAV Per Share >= 2/3 of Price Per Share (moderate net-net discount).")
    else:
        details.append("NCAV not exceeding market cap or insufficient data for net-net approach.")

    # 2. 格雷厄姆数字
    #   GrahamNumber = sqrt(22.5 * EPS * BVPS).
    #   将结果与当前每股价格比较
    #   如果 GrahamNumber >> 价格，表示低估
    graham_number = None
    if eps > 0 and book_value_ps > 0:
        graham_number = math.sqrt(22.5 * eps * book_value_ps)
        details.append(f"Graham Number = {graham_number:.2f}")
        logger.info(f"格雷厄姆数字: {graham_number:.2f}")
    else:
        details.append("Unable to compute Graham Number (EPS or Book Value missing/<=0).")

    # 3. 相对于格雷厄姆数字的安全边际
    if graham_number and shares_outstanding > 0:
        current_price = market_cap / shares_outstanding
        if current_price > 0:
            margin_of_safety = (graham_number - current_price) / current_price
            details.append(f"Margin of Safety (Graham Number) = {margin_of_safety:.2%}")
            logger.info(f"安全边际: {margin_of_safety:.2%}")
            if margin_of_safety > 0.5:
                score += 3
                details.append("Price is well below Graham Number (>=50% margin).")
            elif margin_of_safety > 0.2:
                score += 1
                details.append("Some margin of safety relative to Graham Number.")
            else:
                details.append("Price close to or above Graham Number, low margin of safety.")
        else:
            details.append("Current price is zero or invalid; can't compute margin of safety.")
    # else: already appended details for missing graham_number

    logger.info(f"格雷厄姆估值分析完成，得分: {score}")
    return {"score": score, "details": "; ".join(details)}


def generate_graham_output(
    ticker: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> BenGrahamSignal:
    """
    以本杰明·格雷厄姆的风格生成投资决策:
    - 价值强调，安全边际，净流动资产，保守的资产负债表，稳定的盈利
    - 返回JSON结构的结果: { signal, confidence, reasoning }
    
    Generates an investment decision in the style of Benjamin Graham:
    - Value emphasis, margin of safety, net-nets, conservative balance sheet, stable earnings.
    - Return the result in a JSON structure: { signal, confidence, reasoning }.
    """
    logger.info(f"开始为 {ticker} 生成格雷厄姆分析输出")

    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a Benjamin Graham AI agent, making investment decisions using his principles:
            1. Insist on a margin of safety by buying below intrinsic value (e.g., using Graham Number, net-net).
            2. Emphasize the company's financial strength (low leverage, ample current assets).
            3. Prefer stable earnings over multiple years.
            4. Consider dividend record for extra safety.
            5. Avoid speculative or high-growth assumptions; focus on proven metrics.
            
            When providing your reasoning, be thorough and specific by:
            1. Explaining the key valuation metrics that influenced your decision the most (Graham Number, NCAV, P/E, etc.)
            2. Highlighting the specific financial strength indicators (current ratio, debt levels, etc.)
            3. Referencing the stability or instability of earnings over time
            4. Providing quantitative evidence with precise numbers
            5. Comparing current metrics to Graham's specific thresholds (e.g., "Current ratio of 2.5 exceeds Graham's minimum of 2.0")
            6. Using Benjamin Graham's conservative, analytical voice and style in your explanation
            
            For example, if bullish: "The stock trades at a 35% discount to net current asset value, providing an ample margin of safety. The current ratio of 2.5 and debt-to-equity of 0.3 indicate strong financial position..."
            For example, if bearish: "Despite consistent earnings, the current price of $50 exceeds our calculated Graham Number of $35, offering no margin of safety. Additionally, the current ratio of only 1.2 falls below Graham's preferred 2.0 threshold..."
                        
            Return a rational recommendation: bullish, bearish, or neutral, with a confidence level (0-100) and thorough reasoning.
            """
        ),
        (
            "human",
            """Based on the following analysis, create a Graham-style investment signal:

            Analysis Data for {ticker}:
            {analysis_data}

            Return JSON exactly in this format:
            {{
              "signal": "bullish" or "bearish" or "neutral",
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

    def create_default_ben_graham_signal():
        logger.warning("生成分析时出错，返回默认中性信号")
        return BenGrahamSignal(signal="neutral", confidence=0.0, reasoning="Error in generating analysis; defaulting to neutral.")

    result = call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=BenGrahamSignal,
        agent_name="ben_graham_agent",
        default_factory=create_default_ben_graham_signal,
    )
    
    logger.info(f"生成的分析结果: {result}")
    return result
