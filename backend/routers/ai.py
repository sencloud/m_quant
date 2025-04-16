from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AI.AIService import run_hedge_fund
from AI.backtester import Backtester

router = APIRouter()

class BacktestRequest(BaseModel):
    tickers: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    portfolio: Dict[str, float]
    selected_analysts: Optional[List[str]] = []
    model_name: str = "bot-20250329163710-8zcqm"
    model_provider: str = "OpenAI"

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """
    运行回测接口
    
    参数:
        request: 回测请求对象，包含股票代码、日期范围、初始资金、投资组合等信息
        
    返回:
        包含分析结果和回测结果的字典
    """
    logger.info(f"开始回测: 股票={request.tickers}, 开始日期={request.start_date}, 结束日期={request.end_date}")
    logger.info(f"回测参数: 初始资金={request.initial_capital}, 模型={request.model_name}, 提供商={request.model_provider}")
    
    try:
        # 运行对冲基金分析
        logger.info("开始运行对冲基金分析...")
        result = run_hedge_fund(
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            portfolio=request.portfolio,
            selected_analysts=request.selected_analysts,
            model_name=request.model_name,
            model_provider=request.model_provider
        )
        logger.info("对冲基金分析完成")
        
        # 初始化回测器
        logger.info("初始化回测器...")
        backtester = Backtester(
            agent=run_hedge_fund,
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            model_name=request.model_name,
            model_provider=request.model_provider,
            selected_analysts=request.selected_analysts
        )
        
        # 运行回测
        logger.info("开始运行回测...")
        backtest_results = backtester.run_backtest()
        logger.info("回测完成")
        
        logger.info(f"回测成功: 股票数量={len(request.tickers)}, 回测结果={backtest_results}")
        
        return {
            "analysis": result,
            "backtest": backtest_results
        }
        
    except Exception as e:
        logger.error(f"回测失败: {str(e)}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e)) 