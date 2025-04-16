from AI.graph.state import AgentState, show_agent_reasoning
from AI.tools.api import get_financial_metrics, get_market_cap, search_line_items, get_insider_trades, get_company_news
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from AI.utils.progress import progress
from AI.utils.llm import call_llm
from loguru import logger

class CharlieMungerSignal(BaseModel):
    """
    Charlie Munger信号模型
    包含信号类型、置信度和推理过程
    """
    signal: Literal["bullish", "bearish", "neutral"]  # 看涨、看跌或中性
    confidence: float  # 置信度
    reasoning: str  # 推理过程


def charlie_munger_agent(state: AgentState):
    """
    使用Charlie Munger的投资原则和心智模型分析股票。
    重点关注护城河强度、管理层质量、可预测性和估值。
    """
    logger.info("开始Charlie Munger分析")
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    
    logger.info(f"分析股票: {tickers}, 结束日期: {end_date}")
    analysis_data = {}
    munger_analysis = {}
    
    for ticker in tickers:
        logger.info(f"开始分析股票 {ticker}")
        progress.update_status("charlie_munger_agent", ticker, "获取财务指标")
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=10)  # Munger看更长的时期
        
        progress.update_status("charlie_munger_agent", ticker, "收集财务项目")
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "net_income",  # 净利润
                "operating_income",  # 营业利润
                "return_on_invested_capital",  # 投资回报率
                "gross_margin",  # 毛利率
                "operating_margin",  # 营业利润率
                "free_cash_flow",  # 自由现金流
                "capital_expenditure",  # 资本支出
                "cash_and_equivalents",  # 现金及等价物
                "total_debt",  # 总债务
                "shareholders_equity",  # 股东权益
                "outstanding_shares",  # 流通股
                "research_and_development",  # 研发
                "goodwill_and_intangible_assets",  # 商誉和无形资产
            ],
            end_date,
            period="annual",
            limit=10  # Munger检查长期趋势
        )
        
        progress.update_status("charlie_munger_agent", ticker, "获取市值")
        market_cap = get_market_cap(ticker, end_date)
        
        progress.update_status("charlie_munger_agent", ticker, "获取内幕交易")
        # Munger重视管理层持股
        insider_trades = get_insider_trades(
            ticker,
            end_date,
            # 回溯2年看内幕交易模式
            start_date=None,
            limit=100
        )
        
        progress.update_status("charlie_munger_agent", ticker, "获取公司新闻")
        # Munger避免频繁负面新闻的企业
        company_news = get_company_news(
            ticker,
            end_date,
            # 回溯1年看新闻
            start_date=None,
            limit=100
        )
        
        progress.update_status("charlie_munger_agent", ticker, "分析护城河强度")
        moat_analysis = analyze_moat_strength(metrics, financial_line_items)
        
        progress.update_status("charlie_munger_agent", ticker, "分析管理层质量")
        management_analysis = analyze_management_quality(financial_line_items, insider_trades)
        
        progress.update_status("charlie_munger_agent", ticker, "分析业务可预测性")
        predictability_analysis = analyze_predictability(financial_line_items)
        
        progress.update_status("charlie_munger_agent", ticker, "计算Munger风格估值")
        valuation_analysis = calculate_munger_valuation(financial_line_items, market_cap)
        
        # 用Munger的权重偏好合并部分分数
        # Munger更重视质量和可预测性而不是当前估值
        total_score = (
            moat_analysis["score"] * 0.35 +
            management_analysis["score"] * 0.25 +
            predictability_analysis["score"] * 0.25 +
            valuation_analysis["score"] * 0.15
        )
        
        max_possible_score = 10  # 缩放到0-10
        
        # 生成简单的买入/持有/卖出信号
        if total_score >= 7.5:  # Munger标准很高
            signal = "bullish"  # 看涨
        elif total_score <= 4.5:
            signal = "bearish"  # 看跌
        else:
            signal = "neutral"  # 中性
        
        logger.info(f"{ticker} 总分数: {total_score}/{max_possible_score}, 信号: {signal}")
        
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "moat_analysis": moat_analysis,
            "management_analysis": management_analysis,
            "predictability_analysis": predictability_analysis,
            "valuation_analysis": valuation_analysis,
            # 包含一些来自新闻的定性评估
            "news_sentiment": analyze_news_sentiment(company_news) if company_news else "没有新闻数据"
        }
        
        progress.update_status("charlie_munger_agent", ticker, "生成Charlie Munger分析")
        munger_output = generate_munger_output(
            ticker=ticker, 
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )
        
        munger_analysis[ticker] = {
            "signal": munger_output.signal,
            "confidence": munger_output.confidence,
            "reasoning": munger_output.reasoning
        }
        
        logger.info(f"{ticker} 分析完成: 信号={munger_output.signal}, 置信度={munger_output.confidence}")
        progress.update_status("charlie_munger_agent", ticker, "完成")
    
    # 将结果包装在单个消息中
    message = HumanMessage(
        content=json.dumps(munger_analysis),
        name="charlie_munger_agent"
    )
    
    # 如果请求则显示推理
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(munger_analysis, "Charlie Munger Agent")
    
    # 将信号添加到整体状态
    state["data"]["analyst_signals"]["charlie_munger_agent"] = munger_analysis

    logger.info("Charlie Munger分析完成")
    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_moat_strength(metrics: list, financial_line_items: list) -> dict:
    """
    使用Munger的方法分析企业的竞争优势：
    - 持续的高资本回报率(ROIC)
    - 定价能力(稳定/改善的毛利率)
    - 低资本需求
    - 网络效应和无形资产(研发投资、商誉)
    """
    logger.debug("开始分析护城河强度")
    score = 0
    details = []
    
    if not metrics or not financial_line_items:
        logger.warning("数据不足，无法分析护城河强度")
        return {
            "score": 0,
            "details": "数据不足，无法分析护城河强度"
        }
    
    # 1. 投资回报率(ROIC)分析 - Munger最喜欢的指标
    roic_values = [item.return_on_invested_capital for item in financial_line_items 
                   if hasattr(item, 'return_on_invested_capital') and item.return_on_invested_capital is not None]
    
    if roic_values:
        # 检查ROIC是否持续高于15%(Munger的阈值)
        high_roic_count = sum(1 for r in roic_values if r > 0.15)
        if high_roic_count >= len(roic_values) * 0.8:  # 80%的时期显示高ROIC
            score += 3
            details.append(f"优秀的ROIC: {high_roic_count}/{len(roic_values)}个时期>15%")
        elif high_roic_count >= len(roic_values) * 0.5:  # 50%的时期
            score += 2
            details.append(f"良好的ROIC: {high_roic_count}/{len(roic_values)}个时期>15%")
        elif high_roic_count > 0:
            score += 1
            details.append(f"混合的ROIC: 仅{high_roic_count}/{len(roic_values)}个时期>15%")
        else:
            details.append("差的ROIC: 从未超过15%阈值")
    else:
        details.append("没有ROIC数据")
    
    # 2. 定价能力 - 检查毛利率稳定性和趋势
    gross_margins = [item.gross_margin for item in financial_line_items 
                    if hasattr(item, 'gross_margin') and item.gross_margin is not None]
    
    if gross_margins and len(gross_margins) >= 3:
        # 计算平均毛利率和波动性
        avg_margin = sum(gross_margins) / len(gross_margins)
        margin_volatility = sum(abs(m - avg_margin) for m in gross_margins) / len(gross_margins)
        
        if avg_margin > 0.4:  # 高毛利率业务
            score += 3
            details.append(f"强大的定价能力: 平均毛利率{(avg_margin*100):.1f}%")
        elif avg_margin > 0.25:  # 中等毛利率
            score += 2
            details.append(f"良好的定价能力: 平均毛利率{(avg_margin*100):.1f}%")
        elif avg_margin > 0.15:  # 较低但可接受的毛利率
            score += 1
            details.append(f"适中的定价能力: 平均毛利率{(avg_margin*100):.1f}%")
        else:
            details.append(f"有限的定价能力: 平均毛利率仅{(avg_margin*100):.1f}%")
            
        # 检查毛利率稳定性
        if margin_volatility < 0.03:  # 非常稳定的利润率
            score += 2
            details.append(f"高度稳定的利润率: 平均{(avg_margin*100):.1f}%，波动最小")
        elif margin_volatility < 0.07:  # 中等稳定的利润率
            score += 1
            details.append(f"中等稳定的利润率: 平均{(avg_margin*100):.1f}%，有一些波动")
        else:
            details.append(f"不稳定的利润率: 平均{(avg_margin*100):.1f}%，波动较大({margin_volatility:.1%})")
    else:
        details.append("利润率历史数据不足")
    
    # 3. 资本需求分析
    capex_values = [item.capital_expenditure for item in financial_line_items 
                   if hasattr(item, 'capital_expenditure') and item.capital_expenditure is not None]
    revenue_values = [item.revenue for item in financial_line_items 
                     if hasattr(item, 'revenue') and item.revenue is not None]
    
    if capex_values and revenue_values and len(capex_values) == len(revenue_values):
        # 计算资本支出占收入的比例
        capex_to_revenue = [abs(c) / r for c, r in zip(capex_values, revenue_values) if r > 0]
        if capex_to_revenue:
            avg_capex_ratio = sum(capex_to_revenue) / len(capex_to_revenue)
            
            if avg_capex_ratio < 0.05:  # 非常低的资本需求
                score += 3
                details.append(f"极低的资本需求: 平均{(avg_capex_ratio*100):.1f}%的收入用于资本支出")
            elif avg_capex_ratio < 0.10:  # 低资本需求
                score += 2
                details.append(f"低资本需求: 平均{(avg_capex_ratio*100):.1f}%的收入用于资本支出")
            elif avg_capex_ratio < 0.15:  # 中等资本需求
                score += 1
                details.append(f"中等资本需求: 平均{(avg_capex_ratio*100):.1f}%的收入用于资本支出")
            else:
                details.append(f"高资本需求: 平均{(avg_capex_ratio*100):.1f}%的收入用于资本支出")
    else:
        details.append("资本支出数据不足")
    
    # 4. 无形资产分析
    goodwill_and_intangible_assets = [item.goodwill_and_intangible_assets for item in financial_line_items 
                                    if hasattr(item, 'goodwill_and_intangible_assets') and item.goodwill_and_intangible_assets is not None]
    
    if (goodwill_and_intangible_assets and len(goodwill_and_intangible_assets) > 0):
        score += 1
        details.append("显著的商誉/无形资产，表明品牌价值或知识产权")
    
    # 将分数缩放到0-10范围
    final_score = min(10, score * 10 / 9)  # 最大可能原始分数为9
    
    logger.debug(f"护城河强度分析完成，得分: {final_score}/10")
    return {
        "score": final_score,
        "details": "; ".join(details)
    }


def analyze_management_quality(financial_line_items: list, insider_trades: list) -> dict:
    """
    使用Munger的标准评估管理层质量：
    - 资本配置智慧
    - 内幕持股和交易
    - 现金管理效率
    - 坦诚和透明度
    - 长期关注
    """
    logger.debug("开始分析管理层质量")
    score = 0
    details = []
    
    if not financial_line_items:
        logger.warning("数据不足，无法分析管理层质量")
        return {
            "score": 0,
            "details": "数据不足，无法分析管理层质量"
        }
    
    # 1. 资本配置 - 检查FCF与净利润比率
    # Munger重视将利润转化为现金的公司
    fcf_values = [item.free_cash_flow for item in financial_line_items 
                 if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    
    net_income_values = [item.net_income for item in financial_line_items 
                        if hasattr(item, 'net_income') and item.net_income is not None]
    
    if fcf_values and net_income_values and len(fcf_values) == len(net_income_values):
        # 计算每个时期的FCF与净利润比率
        fcf_to_ni_ratios = []
        for i in range(len(fcf_values)):
            if net_income_values[i] and net_income_values[i] > 0:
                fcf_to_ni_ratios.append(fcf_values[i] / net_income_values[i])
        
        if fcf_to_ni_ratios:
            avg_ratio = sum(fcf_to_ni_ratios) / len(fcf_to_ni_ratios)
            if avg_ratio > 1.1:  # FCF > 净利润表明良好的会计
                score += 3
                details.append(f"优秀的现金转化: FCF/净利润比率为{avg_ratio:.2f}")
            elif avg_ratio > 0.9:  # FCF大致等于净利润
                score += 2
                details.append(f"良好的现金转化: FCF/净利润比率为{avg_ratio:.2f}")
            elif avg_ratio > 0.7:  # FCF略低于净利润
                score += 1
                details.append(f"中等的现金转化: FCF/净利润比率为{avg_ratio:.2f}")
            else:
                details.append(f"差的现金转化: FCF/净利润比率仅为{avg_ratio:.2f}")
        else:
            details.append("无法计算FCF与净利润比率")
    else:
        details.append("缺少FCF或净利润数据")
    
    # 2. 债务管理 - Munger对债务谨慎
    debt_values = [item.total_debt for item in financial_line_items 
                  if hasattr(item, 'total_debt') and item.total_debt is not None]
    
    equity_values = [item.shareholders_equity for item in financial_line_items 
                    if hasattr(item, 'shareholders_equity') and item.shareholders_equity is not None]
    
    if debt_values and equity_values and len(debt_values) == len(equity_values):
        # 计算最近时期的债务权益比
        recent_de_ratio = debt_values[0] / equity_values[0] if equity_values[0] > 0 else float('inf')
        
        if recent_de_ratio < 0.3:  # 非常低的债务
            score += 3
            details.append(f"保守的债务管理: 债务权益比为{recent_de_ratio:.2f}")
        elif recent_de_ratio < 0.7:  # 中等债务
            score += 2
            details.append(f"谨慎的债务管理: 债务权益比为{recent_de_ratio:.2f}")
        elif recent_de_ratio < 1.5:  # 较高但仍合理的债务
            score += 1
            details.append(f"中等债务水平: 债务权益比为{recent_de_ratio:.2f}")
        else:
            details.append(f"高债务水平: 债务权益比为{recent_de_ratio:.2f}")
    else:
        details.append("缺少债务或权益数据")
    
    # 3. 现金管理效率 - Munger重视适当的现金水平
    cash_values = [item.cash_and_equivalents for item in financial_line_items
                  if hasattr(item, 'cash_and_equivalents') and item.cash_and_equivalents is not None]
    revenue_values = [item.revenue for item in financial_line_items
                     if hasattr(item, 'revenue') and item.revenue is not None]
    
    if cash_values and revenue_values and len(cash_values) > 0 and len(revenue_values) > 0:
        # 计算现金收入比(Munger喜欢大多数企业保持在10-20%)
        cash_to_revenue = cash_values[0] / revenue_values[0] if revenue_values[0] > 0 else 0
        
        if 0.1 <= cash_to_revenue <= 0.25:
            # 黄金区间 - 不多不少
            score += 2
            details.append(f"谨慎的现金管理: 现金/收入比率为{cash_to_revenue:.2f}")
        elif 0.05 <= cash_to_revenue < 0.1 or 0.25 < cash_to_revenue <= 0.4:
            # 合理但不理想
            score += 1
            details.append(f"可接受的现金状况: 现金/收入比率为{cash_to_revenue:.2f}")
        elif cash_to_revenue > 0.4:
            # 现金过多 - 可能资本配置效率低下
            details.append(f"现金储备过多: 现金/收入比率为{cash_to_revenue:.2f}")
        else:
            # 现金过少 - 可能有风险
            details.append(f"现金储备低: 现金/收入比率为{cash_to_revenue:.2f}")
    else:
        details.append("现金或收入数据不足")
    
    # 4. 内幕活动 - Munger重视管理层持股
    if insider_trades and len(insider_trades) > 0:
        # 统计买入vs卖出
        buys = sum(1 for trade in insider_trades if hasattr(trade, 'transaction_type') and 
                   trade.transaction_type and trade.transaction_type.lower() in ['buy', 'purchase'])
        sells = sum(1 for trade in insider_trades if hasattr(trade, 'transaction_type') and 
                    trade.transaction_type and trade.transaction_type.lower() in ['sell', 'sale'])
        
        # 计算买入比率
        total_trades = buys + sells
        if total_trades > 0:
            buy_ratio = buys / total_trades
            if buy_ratio > 0.7:  # 强劲的内幕买入
                score += 2
                details.append(f"强劲的内幕买入: {buys}/{total_trades}笔交易是买入")
            elif buy_ratio > 0.4:  # 平衡的内幕活动
                score += 1
                details.append(f"平衡的内幕交易: {buys}/{total_trades}笔交易是买入")
            elif buy_ratio < 0.1 and sells > 5:  # 大量卖出
                score -= 1  # 过度卖出的惩罚
                details.append(f"令人担忧的内幕卖出: {sells}/{total_trades}笔交易是卖出")
            else:
                details.append(f"混合的内幕活动: {buys}/{total_trades}笔交易是买入")
        else:
            details.append("没有记录的内幕交易")
    else:
        details.append("没有内幕交易数据")
    
    # 5. 股份数量一致性 - Munger偏好稳定/减少的股份
    share_counts = [item.outstanding_shares for item in financial_line_items
                   if hasattr(item, 'outstanding_shares') and item.outstanding_shares is not None]
    
    if share_counts and len(share_counts) >= 3:
        if share_counts[0] < share_counts[-1] * 0.95:  # 股份减少5%+
            score += 2
            details.append("股东友好: 随时间减少股份数量")
        elif share_counts[0] < share_counts[-1] * 1.05:  # 稳定的股份数量
            score += 1
            details.append("稳定的股份数量: 有限的稀释")
        elif share_counts[0] > share_counts[-1] * 1.2:  # >20%稀释
            score -= 1  # 过度稀释的惩罚
            details.append("令人担忧的稀释: 股份数量显著增加")
        else:
            details.append("随时间适度增加股份数量")
    else:
        details.append("股份数量数据不足")
    
    # 将分数缩放到0-10范围
    # 最大可能原始分数为12 (3+3+2+2+2)
    final_score = max(0, min(10, score * 10 / 12))
    
    logger.debug(f"管理层质量分析完成，得分: {final_score}/10")
    return {
        "score": final_score,
        "details": "; ".join(details)
    }


def analyze_predictability(financial_line_items: list) -> dict:
    """
    评估业务的可预测性 - Munger强烈偏好那些未来运营和现金流
    相对容易预测的企业。
    """
    logger.debug("开始分析业务可预测性")
    score = 0
    details = []
    
    if not financial_line_items or len(financial_line_items) < 5:
        logger.warning("数据不足，无法分析业务可预测性(需要5年以上)")
        return {
            "score": 0,
            "details": "数据不足，无法分析业务可预测性(需要5年以上)"
        }
    
    # 1. 收入稳定性和增长
    revenues = [item.revenue for item in financial_line_items 
               if hasattr(item, 'revenue') and item.revenue is not None]
    
    if revenues and len(revenues) >= 5:
        # 计算同比增长率
        growth_rates = [(revenues[i] / revenues[i+1] - 1) for i in range(len(revenues)-1)]
        
        avg_growth = sum(growth_rates) / len(growth_rates)
        growth_volatility = sum(abs(r - avg_growth) for r in growth_rates) / len(growth_rates)
        
        if avg_growth > 0.05 and growth_volatility < 0.1:
            score += 3
            details.append(f"稳定且强劲的增长: 平均{(avg_growth*100):.1f}%，低波动性")
        elif avg_growth > 0 and growth_volatility < 0.15:
            score += 2
            details.append(f"稳定但温和的增长: 平均{(avg_growth*100):.1f}%，中等波动性")
        elif avg_growth > 0:
            score += 1
            details.append(f"正增长但波动: 平均{(avg_growth*100):.1f}%，高波动性")
        else:
            details.append(f"收入下降: 平均{(avg_growth*100):.1f}%")
    else:
        details.append("收入历史数据不足")
    
    # 2. 利润率稳定性
    operating_margins = [item.operating_margin for item in financial_line_items 
                       if hasattr(item, 'operating_margin') and item.operating_margin is not None]
    
    if operating_margins and len(operating_margins) >= 5:
        avg_margin = sum(operating_margins) / len(operating_margins)
        margin_volatility = sum(abs(m - avg_margin) for m in operating_margins) / len(operating_margins)
        
        if margin_volatility < 0.03:  # 非常稳定的利润率
            score += 2
            details.append(f"高度可预测的利润率: 平均{(avg_margin*100):.1f}%，波动最小")
        elif margin_volatility < 0.07:  # 中等稳定的利润率
            score += 1
            details.append(f"中等可预测的利润率: 平均{(avg_margin*100):.1f}%，有一些波动")
        else:
            details.append(f"不可预测的利润率: 平均{(avg_margin*100):.1f}%，波动较大({margin_volatility:.1%})")
    else:
        details.append("利润率历史数据不足")
    
    # 3. 现金生成可靠性
    fcf_values = [item.free_cash_flow for item in financial_line_items 
                 if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    
    if fcf_values and len(fcf_values) >= 5:
        # 统计正FCF时期
        positive_fcf_periods = sum(1 for fcf in fcf_values if fcf > 0)
        
        if positive_fcf_periods == len(fcf_values):
            # 持续正FCF
            score += 2
            details.append("高度可预测的现金生成: 所有时期都是正FCF")
        elif positive_fcf_periods >= len(fcf_values) * 0.8:
            # 主要是正FCF
            score += 1
            details.append(f"可预测的现金生成: {positive_fcf_periods}/{len(fcf_values)}个时期是正FCF")
        else:
            details.append(f"不可预测的现金生成: 仅{positive_fcf_periods}/{len(fcf_values)}个时期是正FCF")
    else:
        details.append("自由现金流历史数据不足")
    
    # 将分数缩放到0-10范围
    # 最大可能原始分数为10 (3+3+2+2)
    final_score = min(10, score * 10 / 10)
    
    logger.debug(f"业务可预测性分析完成，得分: {final_score}/10")
    return {
        "score": final_score,
        "details": "; ".join(details)
    }


def calculate_munger_valuation(financial_line_items: list, market_cap: float) -> dict:
    """
    使用Munger的方法计算内在价值：
    - 关注所有者收益(用FCF近似)
    - 对标准化收益使用简单倍数
    - 偏好为优秀企业支付合理价格
    """
    logger.debug("开始Munger风格估值分析")
    score = 0
    details = []
    
    if not financial_line_items or market_cap is None:
        logger.warning("数据不足，无法进行估值")
        return {
            "score": 0,
            "details": "数据不足，无法进行估值"
        }
    
    # 获取FCF值(Munger偏好的"所有者收益"指标)
    fcf_values = [item.free_cash_flow for item in financial_line_items 
                 if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    
    if not fcf_values or len(fcf_values) < 3:
        logger.warning("FCF数据不足，无法进行估值")
        return {
            "score": 0,
            "details": "FCF数据不足，无法进行估值"
        }
    
    # 1. 通过取最近3-5年的平均值来标准化收益
    # (Munger偏好标准化收益以避免基于周期性因素的过高/过低估值)
    normalized_fcf = sum(fcf_values[:min(5, len(fcf_values))]) / min(5, len(fcf_values))
    
    if normalized_fcf <= 0:
        logger.warning(f"负或零标准化FCF ({normalized_fcf})，无法估值")
        return {
            "score": 0,
            "details": f"负或零标准化FCF ({normalized_fcf})，无法估值",
            "intrinsic_value": None
        }
    
    # 2. 计算FCF收益率(P/FCF倍数的倒数)
    fcf_yield = normalized_fcf / market_cap
    
    # 3. 根据业务质量应用Munger的FCF倍数
    # Munger愿意为优秀企业支付更高倍数
    # 使用滑动比例，更高的FCF收益率更有吸引力
    if fcf_yield > 0.08:  # >8% FCF收益率(P/FCF < 12.5倍)
        score += 4
        details.append(f"优秀价值: {fcf_yield:.1%} FCF收益率")
    elif fcf_yield > 0.05:  # >5% FCF收益率(P/FCF < 20倍)
        score += 3
        details.append(f"良好价值: {fcf_yield:.1%} FCF收益率")
    elif fcf_yield > 0.03:  # >3% FCF收益率(P/FCF < 33倍)
        score += 1
        details.append(f"合理价值: {fcf_yield:.1%} FCF收益率")
    else:
        details.append(f"昂贵: 仅{fcf_yield:.1%} FCF收益率")
    
    # 4. 计算简单内在价值范围
    # Munger倾向于使用直接的估值，避免复杂的DCF模型
    conservative_value = normalized_fcf * 10  # 10倍FCF = 10%收益率
    reasonable_value = normalized_fcf * 15    # 15倍FCF ≈ 6.7%收益率
    optimistic_value = normalized_fcf * 20    # 20倍FCF = 5%收益率
    
    # 5. 计算安全边际
    current_to_reasonable = (reasonable_value - market_cap) / market_cap
    
    if current_to_reasonable > 0.3:  # >30%上涨空间
        score += 3
        details.append(f"大的安全边际: 相对合理价值有{current_to_reasonable:.1%}上涨空间")
    elif current_to_reasonable > 0.1:  # >10%上涨空间
        score += 2
        details.append(f"中等安全边际: 相对合理价值有{current_to_reasonable:.1%}上涨空间")
    elif current_to_reasonable > -0.1:  # 在合理价值10%以内
        score += 1
        details.append(f"合理价格: 在合理价值10%以内({current_to_reasonable:.1%})")
    else:
        details.append(f"昂贵: 相对合理价值溢价{-current_to_reasonable:.1%}")
    
    # 6. 检查收益轨迹以获取额外背景
    # Munger喜欢增长的所有者收益
    if len(fcf_values) >= 3:
        recent_avg = sum(fcf_values[:3]) / 3
        older_avg = sum(fcf_values[-3:]) / 3 if len(fcf_values) >= 6 else fcf_values[-1]
        
        if recent_avg > older_avg * 1.2:  # FCF增长>20%
            score += 3
            details.append("FCF增长趋势增加了内在价值")
        elif recent_avg > older_avg:
            score += 2
            details.append("稳定到增长的FCF支持估值")
        else:
            details.append("FCF下降趋势令人担忧")
    
    # 将分数缩放到0-10范围
    # 最大可能原始分数为10 (4+3+3)
    final_score = min(10, score * 10 / 10) 
    
    logger.debug(f"Munger风格估值分析完成，得分: {final_score}/10, 安全边际: {current_to_reasonable:.2%}")
    return {
        "score": final_score,
        "details": "; ".join(details),
        "intrinsic_value_range": {
            "conservative": conservative_value,
            "reasonable": reasonable_value,
            "optimistic": optimistic_value
        },
        "fcf_yield": fcf_yield,
        "normalized_fcf": normalized_fcf
    }


def analyze_news_sentiment(news_items: list) -> str:
    """
    对最近新闻的简单定性分析。
    Munger关注重要新闻但不过度反应短期故事。
    """
    if not news_items or len(news_items) == 0:
        return "没有新闻数据"
    
    # 目前只返回简单计数 - 在实际实现中，这将使用NLP
    return f"需要定性审查{len(news_items)}条最近新闻"


def generate_munger_output(
    ticker: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> CharlieMungerSignal:
    """
    以Charlie Munger的风格生成投资决策。
    """
    logger.info(f"为 {ticker} 生成Charlie Munger风格输出")
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是Charlie Munger AI代理，使用他的原则做出投资决策：

            1. 关注业务的质量和可预测性。
            2. 依靠来自多个学科的心智模型来分析投资。
            3. 寻找强大、持久的竞争优势(护城河)。
            4. 强调长期思考和耐心。
            5. 重视管理层的诚信和能力。
            6. 优先考虑高投资回报率的业务。
            7. 为优秀企业支付合理价格。
            8. 永远不要支付过高价格，始终要求安全边际。
            9. 避免复杂性和你不理解的业务。
            10. "反转，总是反转" - 关注避免愚蠢而不是寻求卓越。
            
            规则：
            - 赞扬具有可预测、稳定运营和现金流的业务。
            - 重视具有高ROIC和定价能力的业务。
            - 偏好具有可理解经济学的简单业务。
            - 欣赏管理层持股和股东友好的资本配置。
            - 关注长期经济学而不是短期指标。
            - 对具有快速变化动态或过度股份稀释的业务持怀疑态度。
            - 避免过度杠杆或金融工程。
            - 提供理性、数据驱动的建议(看涨、看跌或中性)。
            
            在提供推理时，通过以下方式做到彻底和具体：
            1. 解释影响你决策的最关键因素(正面和负面)
            2. 应用至少2-3个具体的心智模型或学科来解释你的思考
            3. 讨论业务的长期经济特征和可持续性
            4. 评估管理层的历史表现和资本配置决策
            5. 解释为什么这个价格提供了足够的安全边际(或没有)
            6. 使用Charlie Munger的直率、智慧和幽默的语气
            
            例如，如果看涨："这家公司拥有我们在优秀企业中寻找的所有特征。他们的护城河来自强大的品牌和网络效应，这反映在持续高于20%的ROIC上。管理层通过减少股份数量和保持保守的资产负债表展示了股东友好的资本配置。当前的估值提供了30%的安全边际，考虑到业务的稳定性和可预测性，这是一个有吸引力的价格..."
            
            例如，如果看跌："虽然这家公司有一些积极的方面，但几个关键问题令人担忧。首先，业务缺乏真正的护城河，这反映在ROIC从15%下降到8%上。其次，管理层通过频繁的股份发行和激进的收购展示了糟糕的资本配置。最后，当前的估值几乎没有提供安全边际，考虑到业务的周期性..."
            """
        ),
        (
            "human",
            """基于以下分析，创建Charlie Munger风格的投资信号。

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

    def create_default_charlie_munger_signal():
        logger.warning("创建默认Charlie Munger信号")
        return CharlieMungerSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="分析出错，默认为中性"
        )

    logger.info(f"调用LLM生成 {ticker} 的Charlie Munger信号")
    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=CharlieMungerSignal,
        agent_name="charlie_munger_agent",
        default_factory=create_default_charlie_munger_signal,
    )