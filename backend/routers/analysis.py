from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime, timedelta
import tushare as ts

router = APIRouter()

@router.get("/daily")
async def get_daily_analysis(
    symbol: str = "M",
    days: int = 5
):
    """获取每日分析"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = pro.fut_daily(
            ts_code=f"{symbol}.DCE",
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )
        
        # 计算技术指标
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['RSI'] = calculate_rsi(df['close'])
        
        analysis = {
            "price_trend": "上涨" if df['close'].iloc[-1] > df['close'].iloc[-2] else "下跌",
            "volume_trend": "放量" if df['vol'].iloc[-1] > df['vol'].iloc[-2] else "缩量",
            "technical_indicators": {
                "ma5": df['MA5'].iloc[-1],
                "ma10": df['MA10'].iloc[-1],
                "rsi": df['RSI'].iloc[-1]
            }
        }
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/core-view")
async def get_core_view():
    """获取核心观点"""
    try:
        # 这里可以接入更复杂的分析逻辑
        return {
            "market_trend": "震荡上行",
            "key_factors": [
                "美豆种植面积预期增加",
                "国内需求稳定",
                "库存处于历史低位"
            ],
            "risk_factors": [
                "天气因素影响",
                "中美贸易关系",
                "汇率波动"
            ],
            "trading_suggestion": "逢低做多"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)) 