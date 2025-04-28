from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, date
from models.signals import Signal, SignalCreate, SignalUpdate
from services.signals import SignalService
from utils.logger import logger
from models.kline import KLineData, SignalRequest

router = APIRouter()

def get_signal_service() -> SignalService:
    return SignalService()

@router.post("/signals", response_model=dict)
async def get_signals(
    request: SignalRequest,
    signal_service: SignalService = Depends(get_signal_service)
):
    """获取交易信号列表"""
    try:
        # 将字符串日期转换为datetime对象，设置时间为当天的开始和结束
        start = datetime.strptime(request.start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        end = datetime.strptime(request.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        # 获取信号
        signals, total = signal_service.generate_signals(
            start, 
            end, 
            request.type, 
            request.page, 
            request.page_size,
            request.klines
        )
        
        return {
            "signals": signals,
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": (total + request.page_size - 1) // request.page_size
        }
    except Exception as e:
        logger.error(f"获取信号失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signals", response_model=Signal)
async def create_signal(
    signal: SignalCreate,
    signal_service: SignalService = Depends(get_signal_service)
):
    """创建新信号"""
    try:
        return signal_service.create_signal(signal)
    except Exception as e:
        logger.error(f"创建信号失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/signals/{signal_id}", response_model=Signal)
async def update_signal(
    signal_id: str,
    signal: SignalUpdate,
    signal_service: SignalService = Depends(get_signal_service)
):
    """更新信号"""
    try:
        return signal_service.update_signal(signal_id, signal)
    except Exception as e:
        logger.error(f"更新信号失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/signals/{signal_id}")
async def delete_signal(
    signal_id: str,
    signal_service: SignalService = Depends(get_signal_service)
):
    """删除信号"""
    try:
        signal_service.delete_signal(signal_id)
        return {"message": "信号已删除"}
    except Exception as e:
        logger.error(f"删除信号失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 