from fastapi import APIRouter, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from services.market_data import MarketDataService
from models.market_data import FuturesData

router = APIRouter()

@router.get("/spread")
async def get_spread_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    near_contract: str = "M2509.DCE",
    far_contract: str = "M2601.DCE"
) -> List[dict]:
    """
    获取近远月合约价差数据
    """
    market_service = MarketDataService()
    
    # 如果没有指定日期，默认获取最近30天的数据
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    
    # 获取两个合约的数据
    near_data = market_service._get_futures_data(start_date, end_date, near_contract)
    far_data = market_service._get_futures_data(start_date, end_date, far_contract)
    
    if not near_data or not far_data:
        return []
    
    # 将数据转换为DataFrame以便处理
    import pandas as pd
    df = pd.DataFrame([{
        'trade_date': data.trade_date,
        'ts_code': data.ts_code,
        'close': data.close
    } for data in near_data + far_data])
    
    if df.empty:
        return []
    
    # 计算价差
    spread_data = []
    for date in df['trade_date'].unique():
        date_data = df[df['trade_date'] == date]
        if len(date_data) == 2:  # 确保两个合约都有数据
            near_price = date_data[date_data['ts_code'] == near_contract]['close'].iloc[0]
            far_price = date_data[date_data['ts_code'] == far_contract]['close'].iloc[0]
            spread = near_price - far_price
            spread_data.append({
                'date': date,
                'spread': spread
            })
    
    return spread_data 