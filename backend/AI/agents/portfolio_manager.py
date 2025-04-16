import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from AI.graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from AI.utils.progress import progress
from AI.utils.llm import call_llm


class PortfolioDecision(BaseModel):
    """
    投资组合决策模型
    包含交易动作、数量、置信度和理由
    """
    action: Literal["buy", "sell", "short", "cover", "hold"]  # 交易动作：买入、卖出、做空、平仓或持有
    quantity: int = Field(description="交易股数")  # 交易数量
    confidence: float = Field(description="决策置信度，介于0.0和100.0之间")  # 决策置信度
    reasoning: str = Field(description="决策理由")  # 决策理由


class PortfolioManagerOutput(BaseModel):
    """
    投资组合管理器输出模型
    包含所有股票的决策字典
    """
    decisions: dict[str, PortfolioDecision] = Field(description="股票代码到交易决策的字典")


##### 投资组合管理代理 #####
def portfolio_management_agent(state: AgentState):
    """
    为多个股票做出最终交易决策并生成订单
    
    主要功能:
    1. 分析各个分析师的信号
    2. 考虑仓位限制和风险因素
    3. 生成最终的交易决策
    4. 返回交易指令
    """
    logger.info("开始投资组合管理代理")
    
    # 获取投资组合和分析师信号
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    tickers = state["data"]["tickers"]
    logger.info(f"处理股票: {tickers}")

    progress.update_status("portfolio_management_agent", None, "分析信号")
    logger.info("开始分析交易信号")

    # 获取每个股票的仓位限制、当前价格和信号
    position_limits = {}
    current_prices = {}
    max_shares = {}
    signals_by_ticker = {}
    
    for ticker in tickers:
        progress.update_status("portfolio_management_agent", ticker, "处理分析师信号")
        logger.info(f"处理 {ticker} 的分析师信号")

        # 获取股票的仓位限制和当前价格
        risk_data = analyst_signals.get("risk_management_agent", {}).get(ticker, {})
        position_limits[ticker] = risk_data.get("remaining_position_limit", 0)
        current_prices[ticker] = risk_data.get("current_price", 0)
        logger.debug(f"{ticker} 仓位限制: {position_limits[ticker]}, 当前价格: {current_prices[ticker]}")

        # 根据仓位限制和价格计算最大允许股数
        if current_prices[ticker] > 0:
            max_shares[ticker] = int(position_limits[ticker] / current_prices[ticker])
        else:
            max_shares[ticker] = 0
        logger.debug(f"{ticker} 最大允许股数: {max_shares[ticker]}")

        # 获取股票的信号
        ticker_signals = {}
        for agent, signals in analyst_signals.items():
            if agent != "risk_management_agent" and ticker in signals:
                ticker_signals[agent] = {"signal": signals[ticker]["signal"], "confidence": signals[ticker]["confidence"]}
        signals_by_ticker[ticker] = ticker_signals
        logger.debug(f"{ticker} 分析师信号: {ticker_signals}")

    progress.update_status("portfolio_management_agent", None, "制定交易决策")
    logger.info("开始制定交易决策")

    # 生成交易决策
    result = generate_trading_decision(
        tickers=tickers,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
        model_name=state["metadata"]["model_name"],
        model_provider=state["metadata"]["model_provider"],
    )
    logger.info(f"生成的交易决策: {result}")

    # 创建投资组合管理消息
    message = HumanMessage(
        content=json.dumps({ticker: decision.model_dump() for ticker, decision in result.decisions.items()}),
        name="portfolio_management",
    )

    # 如果设置了标志，打印决策
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning({ticker: decision.model_dump() for ticker, decision in result.decisions.items()}, "投资组合管理代理")

    progress.update_status("portfolio_management_agent", None, "完成")
    logger.info("完成交易决策制定")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }


def generate_trading_decision(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict[str, float],
    model_name: str,
    model_provider: str,
) -> PortfolioManagerOutput:
    """
    尝试从LLM获取决策，带有重试逻辑
    
    参数:
    - tickers: 股票代码列表
    - signals_by_ticker: 每个股票的分析师信号
    - current_prices: 当前价格
    - max_shares: 最大允许股数
    - portfolio: 投资组合信息
    - model_name: 模型名称
    - model_provider: 模型提供商
    
    返回:
    - PortfolioManagerOutput: 包含所有股票交易决策的输出
    """
    logger.info("开始生成交易决策")
    
    # 创建提示模板
    template = ChatPromptTemplate.from_messages(
        [
            (
              "system",
              """You are a portfolio manager making final trading decisions based on multiple tickers.

              Trading Rules:
              - For long positions:
                * Only buy if you have available cash
                * Only sell if you currently hold long shares of that ticker
                * Sell quantity must be ≤ current long position shares
                * Buy quantity must be ≤ max_shares for that ticker
              
              - For short positions:
                * Only short if you have available margin (position value × margin requirement)
                * Only cover if you currently have short shares of that ticker
                * Cover quantity must be ≤ current short position shares
                * Short quantity must respect margin requirements
              
              - The max_shares values are pre-calculated to respect position limits
              - Consider both long and short opportunities based on signals
              - Maintain appropriate risk management with both long and short exposure

              Available Actions:
              - "buy": Open or add to long position
              - "sell": Close or reduce long position
              - "short": Open or add to short position
              - "cover": Close or reduce short position
              - "hold": No action

              Inputs:
              - signals_by_ticker: dictionary of ticker → signals
              - max_shares: maximum shares allowed per ticker
              - portfolio_cash: current cash in portfolio
              - portfolio_positions: current positions (both long and short)
              - current_prices: current prices for each ticker
              - margin_requirement: current margin requirement for short positions (e.g., 0.5 means 50%)
              - total_margin_used: total margin currently in use
              """,
            ),
            (
              "human",
              """Based on the team's analysis, make your trading decisions for each ticker.

              Here are the signals by ticker:
              {signals_by_ticker}

              Current Prices:
              {current_prices}

              Maximum Shares Allowed For Purchases:
              {max_shares}

              Portfolio Cash: {portfolio_cash}
              Current Positions: {portfolio_positions}
              Current Margin Requirement: {margin_requirement}
              Total Margin Used: {total_margin_used}

              Output strictly in JSON with the following structure:
              {{
                "decisions": {{
                  "TICKER1": {{
                    "action": "buy/sell/short/cover/hold",
                    "quantity": integer,
                    "confidence": float between 0 and 100,
                    "reasoning": "string"
                  }},
                  "TICKER2": {{
                    ...
                  }},
                  ...
                }}
              }}
              """,
            ),
        ]
    )

    # 生成提示
    prompt = template.invoke(
        {
            "signals_by_ticker": json.dumps(signals_by_ticker, indent=2),
            "current_prices": json.dumps(current_prices, indent=2),
            "max_shares": json.dumps(max_shares, indent=2),
            "portfolio_cash": f"{portfolio.get('cash', 0):.2f}",
            "portfolio_positions": json.dumps(portfolio.get('positions', {}), indent=2),
            "margin_requirement": f"{portfolio.get('margin_requirement', 0):.2f}",
            "total_margin_used": f"{portfolio.get('margin_used', 0):.2f}",
        }
    )
    logger.debug(f"生成的提示: {prompt}")

    # 创建PortfolioManagerOutput的默认工厂
    def create_default_portfolio_output():
        logger.warning("投资组合管理出错，返回默认持有决策")
        return PortfolioManagerOutput(decisions={ticker: PortfolioDecision(action="hold", quantity=0, confidence=0.0, reasoning="投资组合管理出错，默认保持不操作") for ticker in tickers})

    result = call_llm(
        prompt=prompt, 
        model_name=model_name, 
        model_provider=model_provider, 
        pydantic_model=PortfolioManagerOutput, 
        agent_name="portfolio_management_agent", 
        default_factory=create_default_portfolio_output
    )
    logger.info(f"LLM返回的决策: {result}")
    
    return result
