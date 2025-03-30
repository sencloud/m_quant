from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from typing import List
from models.market_data import OptionBasic, OptionDaily
from services.tushare_service import TushareService

router = APIRouter()
ts = TushareService()

@router.get("/options/basic", response_model=List[OptionBasic])
async def get_option_basics():
    try:
        return await ts.get_option_basics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/daily", response_model=List[OptionDaily])
async def get_option_daily():
    try:
        return await ts.get_option_daily()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/daily/{ts_code}", response_model=List[OptionDaily])
async def get_option_daily_by_code(ts_code: str):
    try:
        # 计算一年前的日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        return await ts.get_option_daily_by_code(
            ts_code=ts_code,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 