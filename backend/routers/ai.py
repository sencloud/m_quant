from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

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
    try:
        # Run the hedge fund analysis
        result = run_hedge_fund(
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            portfolio=request.portfolio,
            selected_analysts=request.selected_analysts,
            model_name=request.model_name,
            model_provider=request.model_provider
        )
        
        # Initialize backtester
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
        
        # Run backtest
        backtest_results = backtester.run_backtest()
        
        return {
            "analysis": result,
            "backtest": backtest_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 