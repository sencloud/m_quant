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

class CathieWoodSignal(BaseModel):
    """
    Cathie Wood信号模型
    包含信号类型、置信度和推理过程
    """
    signal: Literal["bullish", "bearish", "neutral"]  # 看涨、看跌或中性
    confidence: float  # 置信度
    reasoning: str  # 推理过程


def cathie_wood_agent(state: AgentState):
    """
    使用Cathie Wood的投资原则和LLM推理分析股票。
    1. 优先考虑具有突破性技术或商业模式的公司
    2. 专注于具有快速采用曲线和巨大TAM（总可寻址市场）的行业
    3. 主要投资于AI、机器人、基因组测序、金融科技和区块链
    4. 愿意承受短期波动以获得长期收益
    """
    logger.info("开始Cathie Wood分析")
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    logger.info(f"分析股票: {tickers}, 结束日期: {end_date}")
    analysis_data = {}
    cw_analysis = {}

    for ticker in tickers:
        logger.info(f"开始分析股票 {ticker}")
        progress.update_status("cathie_wood_agent", ticker, "获取财务指标")
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)

        progress.update_status("cathie_wood_agent", ticker, "收集财务项目")
        # 请求多个时期的数据（年度或TTM）以获得更稳健的观点
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "gross_margin",  # 毛利率
                "operating_margin",  # 营业利润率
                "debt_to_equity",  # 债务权益比
                "free_cash_flow",  # 自由现金流
                "total_assets",  # 总资产
                "total_liabilities",  # 总负债
                "dividends_and_other_cash_distributions",  # 股息和其他现金分配
                "outstanding_shares",  # 流通股
                "research_and_development",  # 研发
                "capital_expenditure",  # 资本支出
                "operating_expense",  # 运营费用
            ],
            end_date,
            period="annual",
            limit=5
        )

        progress.update_status("cathie_wood_agent", ticker, "获取市值")
        market_cap = get_market_cap(ticker, end_date)

        progress.update_status("cathie_wood_agent", ticker, "分析颠覆性潜力")
        disruptive_analysis = analyze_disruptive_potential(metrics, financial_line_items)

        progress.update_status("cathie_wood_agent", ticker, "分析创新驱动增长")
        innovation_analysis = analyze_innovation_growth(metrics, financial_line_items)

        progress.update_status("cathie_wood_agent", ticker, "计算估值和高增长情景")
        valuation_analysis = analyze_cathie_wood_valuation(financial_line_items, market_cap)

        # 合并部分分数或信号
        total_score = disruptive_analysis["score"] + innovation_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 15  # 根据需要调整权重

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
            "disruptive_analysis": disruptive_analysis,
            "innovation_analysis": innovation_analysis,
            "valuation_analysis": valuation_analysis
        }

        progress.update_status("cathie_wood_agent", ticker, "生成Cathie Wood分析")
        cw_output = generate_cathie_wood_output(
            ticker=ticker,
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )

        cw_analysis[ticker] = {
            "signal": cw_output.signal,
            "confidence": cw_output.confidence,
            "reasoning": cw_output.reasoning
        }

        logger.info(f"{ticker} 分析完成: 信号={cw_output.signal}, 置信度={cw_output.confidence}")
        progress.update_status("cathie_wood_agent", ticker, "完成")

    message = HumanMessage(
        content=json.dumps(cw_analysis),
        name="cathie_wood_agent"
    )

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(cw_analysis, "Cathie Wood Agent")

    state["data"]["analyst_signals"]["cathie_wood_agent"] = cw_analysis

    logger.info("Cathie Wood分析完成")
    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_disruptive_potential(metrics: list, financial_line_items: list) -> dict:
    """
    分析公司是否拥有颠覆性产品、技术或商业模式。
    评估颠覆性潜力的多个维度：
    1. 收入增长加速 - 表明市场采用
    2. 研发强度 - 显示创新投资
    3. 毛利率趋势 - 表明定价能力和可扩展性
    4. 运营杠杆 - 展示商业模式效率
    5. 市场份额动态 - 表明竞争地位
    """
    logger.debug("开始分析颠覆性潜力")
    score = 0
    details = []

    if not metrics or not financial_line_items:
        logger.warning("数据不足，无法分析颠覆性潜力")
        return {
            "score": 0,
            "details": "数据不足，无法分析颠覆性潜力"
        }

    # 1. 收入增长分析 - 检查加速增长
    revenues = [item.revenue for item in financial_line_items if item.revenue]
    if len(revenues) >= 3:  # 需要至少3个时期来检查加速
        growth_rates = []
        for i in range(len(revenues)-1):
            if revenues[i] and revenues[i+1]:
                growth_rate = (revenues[i+1] - revenues[i]) / abs(revenues[i]) if revenues[i] != 0 else 0
                growth_rates.append(growth_rate)

        # 检查增长是否在加速
        if len(growth_rates) >= 2 and growth_rates[-1] > growth_rates[0]:
            score += 2
            details.append(f"收入增长正在加速: {(growth_rates[-1]*100):.1f}% vs {(growth_rates[0]*100):.1f}%")

        # 检查绝对增长率
        latest_growth = growth_rates[-1] if growth_rates else 0
        if latest_growth > 1.0:
            score += 3
            details.append(f"卓越的收入增长: {(latest_growth*100):.1f}%")
        elif latest_growth > 0.5:
            score += 2
            details.append(f"强劲的收入增长: {(latest_growth*100):.1f}%")
        elif latest_growth > 0.2:
            score += 1
            details.append(f"中等收入增长: {(latest_growth*100):.1f}%")
    else:
        details.append("收入数据不足，无法进行增长分析")

    # 2. 毛利率分析 - 检查扩大的利润率
    gross_margins = [item.gross_margin for item in financial_line_items if hasattr(item, 'gross_margin') and item.gross_margin is not None]
    if len(gross_margins) >= 2:
        margin_trend = gross_margins[-1] - gross_margins[0]
        if margin_trend > 0.05:  # 5%的改善
            score += 2
            details.append(f"扩大的毛利率: +{(margin_trend*100):.1f}%")
        elif margin_trend > 0:
            score += 1
            details.append(f"略微改善的毛利率: +{(margin_trend*100):.1f}%")

        # 检查绝对利润率水平
        if gross_margins[-1] > 0.50:  # 高利润率业务
            score += 2
            details.append(f"高毛利率: {(gross_margins[-1]*100):.1f}%")
    else:
        details.append("毛利率数据不足")

    # 3. 运营杠杆分析
    revenues = [item.revenue for item in financial_line_items if item.revenue]
    operating_expenses = [
        item.operating_expense
        for item in financial_line_items
        if hasattr(item, "operating_expense") and item.operating_expense
    ]

    if len(revenues) >= 2 and len(operating_expenses) >= 2:
        rev_growth = (revenues[-1] - revenues[0]) / abs(revenues[0])
        opex_growth = (operating_expenses[-1] - operating_expenses[0]) / abs(operating_expenses[0])

        if rev_growth > opex_growth:
            score += 2
            details.append("正运营杠杆: 收入增长快于支出")
    else:
        details.append("运营杠杆分析数据不足")

    # 4. 研发投资分析
    rd_expenses = [item.research_and_development for item in financial_line_items if hasattr(item, 'research_and_development') and item.research_and_development is not None]
    if rd_expenses and revenues:
        rd_intensity = rd_expenses[-1] / revenues[-1]
        if rd_intensity > 0.15:  # 高研发强度
            score += 3
            details.append(f"高研发投资: 收入的{(rd_intensity*100):.1f}%")
        elif rd_intensity > 0.08:
            score += 2
            details.append(f"中等研发投资: 收入的{(rd_intensity*100):.1f}%")
        elif rd_intensity > 0.05:
            score += 1
            details.append(f"一些研发投资: 收入的{(rd_intensity*100):.1f}%")
    else:
        details.append("没有研发数据")

    # 将分数标准化为5分制
    max_possible_score = 12  # 所有可能分数的总和
    normalized_score = (score / max_possible_score) * 5

    logger.debug(f"颠覆性潜力分析完成，得分: {normalized_score}/5")
    return {
        "score": normalized_score,
        "details": "; ".join(details),
        "raw_score": score,
        "max_score": max_possible_score
    }


def analyze_innovation_growth(metrics: list, financial_line_items: list) -> dict:
    """
    评估公司对创新的承诺和指数增长的潜力。
    分析多个维度：
    1. 研发投资趋势 - 衡量对创新的承诺
    2. 自由现金流生成 - 表明资助创新的能力
    3. 运营效率 - 显示创新的可扩展性
    4. 资本配置 - 揭示以创新为中心的管理
    5. 增长再投资 - 展示对未来增长的承诺
    """
    logger.debug("开始分析创新驱动增长")
    score = 0
    details = []

    if not metrics or not financial_line_items:
        logger.warning("数据不足，无法分析创新驱动增长")
        return {
            "score": 0,
            "details": "数据不足，无法分析创新驱动增长"
        }

    # 1. 研发投资趋势
    rd_expenses = [
        item.research_and_development
        for item in financial_line_items
        if hasattr(item, "research_and_development") and item.research_and_development
    ]
    revenues = [item.revenue for item in financial_line_items if item.revenue]

    if rd_expenses and revenues and len(rd_expenses) >= 2:
        # 检查研发增长率
        rd_growth = (rd_expenses[-1] - rd_expenses[0]) / abs(rd_expenses[0]) if rd_expenses[0] != 0 else 0
        if rd_growth > 0.5:  # 研发增长50%
            score += 3
            details.append(f"强劲的研发投资增长: +{(rd_growth*100):.1f}%")
        elif rd_growth > 0.2:
            score += 2
            details.append(f"中等研发投资增长: +{(rd_growth*100):.1f}%")

        # 检查研发强度趋势
        rd_intensity_start = rd_expenses[0] / revenues[0]
        rd_intensity_end = rd_expenses[-1] / revenues[-1]
        if rd_intensity_end > rd_intensity_start:
            score += 2
            details.append(f"增加的研发强度: {(rd_intensity_end*100):.1f}% vs {(rd_intensity_start*100):.1f}%")
    else:
        details.append("研发数据不足，无法进行趋势分析")

    # 2. 自由现金流分析
    fcf_vals = [item.free_cash_flow for item in financial_line_items if item.free_cash_flow]
    if fcf_vals and len(fcf_vals) >= 2:
        # 检查FCF增长和一致性
        fcf_growth = (fcf_vals[-1] - fcf_vals[0]) / abs(fcf_vals[0])
        positive_fcf_count = sum(1 for f in fcf_vals if f > 0)

        if fcf_growth > 0.3 and positive_fcf_count == len(fcf_vals):
            score += 3
            details.append("强劲且一致的FCF增长，优秀的创新资助能力")
        elif positive_fcf_count >= len(fcf_vals) * 0.75:
            score += 2
            details.append("一致的正FCF，良好的创新资助能力")
        elif positive_fcf_count > len(fcf_vals) * 0.5:
            score += 1
            details.append("中等一致的FCF，足够的创新资助能力")
    else:
        details.append("FCF数据不足，无法分析")

    # 3. 运营效率分析
    op_margin_vals = [item.operating_margin for item in financial_line_items if item.operating_margin]
    if op_margin_vals and len(op_margin_vals) >= 2:
        # 检查利润率改善
        margin_trend = op_margin_vals[-1] - op_margin_vals[0]

        if op_margin_vals[-1] > 0.15 and margin_trend > 0:
            score += 3
            details.append(f"强劲且改善的营业利润率: {(op_margin_vals[-1]*100):.1f}%")
        elif op_margin_vals[-1] > 0.10:
            score += 2
            details.append(f"健康的营业利润率: {(op_margin_vals[-1]*100):.1f}%")
        elif margin_trend > 0:
            score += 1
            details.append("改善的运营效率")
    else:
        details.append("营业利润率数据不足")

    # 4. 资本配置分析
    capex = [item.capital_expenditure for item in financial_line_items if hasattr(item, 'capital_expenditure') and item.capital_expenditure]
    if capex and revenues and len(capex) >= 2:
        capex_intensity = abs(capex[-1]) / revenues[-1]
        capex_growth = (abs(capex[-1]) - abs(capex[0])) / abs(capex[0]) if capex[0] != 0 else 0

        if capex_intensity > 0.10 and capex_growth > 0.2:
            score += 2
            details.append("对增长基础设施的强劲投资")
        elif capex_intensity > 0.05:
            score += 1
            details.append("对增长基础设施的中等投资")
    else:
        details.append("资本支出数据不足")

    # 5. 增长再投资分析
    dividends = [item.dividends_and_other_cash_distributions for item in financial_line_items if hasattr(item, 'dividends_and_other_cash_distributions') and item.dividends_and_other_cash_distributions]
    if dividends and fcf_vals:
        # 检查公司是否优先考虑再投资而非股息
        latest_payout_ratio = dividends[-1] / fcf_vals[-1] if fcf_vals[-1] != 0 else 1
        if latest_payout_ratio < 0.2:  # 低股息支付比率表明再投资重点
            score += 2
            details.append("强烈关注再投资而非股息")
        elif latest_payout_ratio < 0.4:
            score += 1
            details.append("中等关注再投资而非股息")
    else:
        details.append("股息数据不足")

    # 将分数标准化为5分制
    max_possible_score = 15  # 所有可能分数的总和
    normalized_score = (score / max_possible_score) * 5

    logger.debug(f"创新驱动增长分析完成，得分: {normalized_score}/5")
    return {
        "score": normalized_score,
        "details": "; ".join(details),
        "raw_score": score,
        "max_score": max_possible_score
    }


def analyze_cathie_wood_valuation(financial_line_items: list, market_cap: float) -> dict:
    """
    Cathie Wood通常关注长期指数增长潜力。我们可以
    采用简化的方法，寻找大的总可寻址市场（TAM）和
    公司捕获可观份额的能力。
    """
    logger.debug("开始Cathie Wood估值分析")
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

    # 不采用标准DCF，而是为创新公司假设更高的增长率。
    # 示例值：
    growth_rate = 0.20  # 20%的年增长率
    discount_rate = 0.15
    terminal_multiple = 25
    projection_years = 5

    present_value = 0
    for year in range(1, projection_years + 1):
        future_fcf = fcf * (1 + growth_rate) ** year
        pv = future_fcf / ((1 + discount_rate) ** year)
        present_value += pv

    # 终值
    terminal_value = (fcf * (1 + growth_rate) ** projection_years * terminal_multiple) \
                     / ((1 + discount_rate) ** projection_years)
    intrinsic_value = present_value + terminal_value

    margin_of_safety = (intrinsic_value - market_cap) / market_cap

    score = 0
    if margin_of_safety > 0.5:
        score += 3
    elif margin_of_safety > 0.2:
        score += 1

    details = [
        f"计算的内在价值: ~{intrinsic_value:,.2f}",
        f"市值: ~{market_cap:,.2f}",
        f"安全边际: {margin_of_safety:.2%}"
    ]

    logger.debug(f"Cathie Wood估值分析完成，得分: {score}, 安全边际: {margin_of_safety:.2%}")
    return {
        "score": score,
        "details": "; ".join(details),
        "intrinsic_value": intrinsic_value,
        "margin_of_safety": margin_of_safety
    }


def generate_cathie_wood_output(
    ticker: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> CathieWoodSignal:
    """
    以Cathie Wood的风格生成投资决策。
    """
    logger.info(f"为 {ticker} 生成Cathie Wood风格输出")
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是Cathie Wood AI代理，使用她的原则做出投资决策：

            1. 寻求利用颠覆性创新的公司。
            2. 强调指数增长潜力，大的TAM。
            3. 专注于技术、医疗保健或其他面向未来的行业。
            4. 考虑潜在突破的多年度时间范围。
            5. 接受追求高回报的更高波动性。
            6. 评估管理层的愿景和投资研发的能力。

            规则：
            - 识别颠覆性或突破性技术。
            - 评估多年收入增长的强劲潜力。
            - 检查公司是否能在大型市场中有效扩展。
            - 使用偏向增长的估值方法。
            - 提供数据驱动的建议（看涨、看跌或中性）。
            
            在提供推理时，通过以下方式做到彻底和具体：
            1. 识别公司利用的具体颠覆性技术/创新
            2. 强调表明指数潜力的增长指标（收入加速，扩大的TAM）
            3. 讨论5年以上时间范围的长期愿景和变革潜力
            4. 解释公司如何颠覆传统行业或创造新市场
            5. 解决可能推动未来增长的研发投资和创新管道
            6. 使用Cathie Wood的乐观、面向未来和信念驱动的语气
            
            例如，如果看涨："该公司的AI驱动平台正在改变5000亿美元的医疗保健分析市场，有证据表明平台采用率从40%加速到65% YoY。他们占收入22%的研发投资正在创造一个技术护城河，使他们能够在这个不断扩大的市场中占据重要份额。当前估值没有反映我们预期的指数增长轨迹，因为..."
            例如，如果看跌："虽然运营在基因组学领域，但公司缺乏真正的颠覆性技术，仅仅是对现有技术的渐进式改进。研发支出仅占收入的8%，表明对突破性创新的投资不足。随着收入增长从45%放缓到20% YoY，缺乏我们在变革性公司中寻找的指数采用曲线的证据..."
            """
        ),
        (
            "human",
            """基于以下分析，创建Cathie Wood风格的投资信号。

            {ticker}的分析数据：
            {analysis_data}

            以这种JSON格式返回交易信号：
            {{
              "signal": "bullish/bearish/neutral",
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

    def create_default_cathie_wood_signal():
        logger.warning("创建默认Cathie Wood信号")
        return CathieWoodSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错，默认为中性"
        )

    logger.info(f"调用LLM生成 {ticker} 的Cathie Wood信号")
    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=CathieWoodSignal,
        agent_name="cathie_wood_agent",
        default_factory=create_default_cathie_wood_signal,
    )

# source: https://ark-invest.com