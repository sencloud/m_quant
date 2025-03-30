from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Any
from services.core_factor import CoreFactorAnalyzer

router = APIRouter()
analyzer = CoreFactorAnalyzer()

@router.get("/{date}")
async def get_core_factor_analysis(date: str) -> Dict[str, Any]:
    """获取指定日期的核心驱动因子分析数据"""
    try:
        return await analyzer.get_core_factor_analysis(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 