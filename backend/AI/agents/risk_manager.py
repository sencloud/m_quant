from langchain_core.messages import HumanMessage
from AI.graph.state import AgentState, show_agent_reasoning
from AI.utils.progress import progress
from AI.tools.api import get_prices, prices_to_df
from loguru import logger
import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel


##### 风险管理代理 #####
def risk_management_agent(state: AgentState):
    """
    基于多个股票的实时风险因素控制仓位大小
    
    主要功能:
    1. 获取股票价格数据
    2. 计算投资组合价值
    3. 确定单个股票的最大仓位限制
    4. 考虑当前持仓和可用现金
    5. 生成风险分析报告
    """
    logger.info("开始风险管理代理")
    portfolio = state["data"]["portfolio"]
    data = state["data"]
    tickers = data["tickers"]
    logger.info(f"处理股票: {tickers}")

    # 初始化每个股票的风险分析
    risk_analysis = {}
    current_prices = {}  # 存储价格以避免重复API调用

    for ticker in tickers:
        progress.update_status("risk_management_agent", ticker, "分析价格数据")
        logger.info(f"开始分析 {ticker} 的风险因素")

        prices = get_prices(
            ticker=ticker,
            start_date=data["start_date"],
            end_date=data["end_date"],
        )
        logger.debug(f"获取到价格数据: {prices}")

        if not prices:
            progress.update_status("risk_management_agent", ticker, "失败：未找到价格数据")
            logger.error(f"无法获取 {ticker} 的价格数据")
            continue

        prices_df = prices_to_df(prices)
        logger.debug(f"价格数据转换为DataFrame: {prices_df}")

        progress.update_status("risk_management_agent", ticker, "计算仓位限制")
        logger.info(f"计算 {ticker} 的仓位限制")

        # 计算投资组合价值
        current_price = prices_df["close"].iloc[-1]
        current_prices[ticker] = current_price  # 存储当前价格
        logger.debug(f"当前价格: {current_price}")

        # 计算该股票的当前仓位价值
        current_position_value = portfolio.get("cost_basis", {}).get(ticker, 0)
        logger.debug(f"当前仓位价值: {current_position_value}")

        # 使用存储的价格计算总投资组合价值
        total_portfolio_value = portfolio.get("cash", 0) + sum(portfolio.get("cost_basis", {}).get(t, 0) for t in portfolio.get("cost_basis", {}))
        logger.debug(f"总投资组合价值: {total_portfolio_value}")

        # 基础限制是任何单个仓位的投资组合的20%
        position_limit = total_portfolio_value * 0.20
        logger.debug(f"单个仓位限制: {position_limit}")

        # 对于现有仓位，从限制中减去当前仓位价值
        remaining_position_limit = position_limit - current_position_value
        logger.debug(f"剩余仓位限制: {remaining_position_limit}")

        # 确保不超过可用现金
        available_cash = portfolio.get("cash", 0)
        max_position_size = min(remaining_position_limit, available_cash)
        logger.debug(f"可用现金: {available_cash}, 最大仓位大小: {max_position_size}")

        risk_analysis[ticker] = {
            "remaining_position_limit": float(max_position_size),
            "current_price": float(current_price),
            "reasoning": {
                "portfolio_value": float(total_portfolio_value),
                "current_position": float(current_position_value),
                "position_limit": float(position_limit),
                "remaining_limit": float(remaining_position_limit),
                "available_cash": float(available_cash),
            },
        }
        logger.info(f"风险分析结果: {risk_analysis[ticker]}")

        progress.update_status("risk_management_agent", ticker, "完成")
        logger.info(f"完成 {ticker} 的风险分析")

    message = HumanMessage(
        content=json.dumps(risk_analysis),
        name="risk_management_agent",
    )

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(risk_analysis, "风险管理代理")

    # 将信号添加到analyst_signals列表
    state["data"]["analyst_signals"]["risk_management_agent"] = risk_analysis
    logger.info("风险管理分析完成，返回结果")

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }
