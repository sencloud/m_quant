from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from utils.logger import logger
from services.stockfutures import StockFuturesService

router = APIRouter()

class StockRecommendation(BaseModel):
    """股票推荐结果模型"""
    code: str
    name: str
    level: str  # 推荐级别：强烈推荐/推荐
    price: float
    change_pct: float
    reason: str

class StockPickingResponse(BaseModel):
    """选股返回结果模型"""
    timestamp: str
    recommendations: List[StockRecommendation]

def get_stock_futures_service():
    """依赖注入：获取StockFuturesService实例"""
    return StockFuturesService()

@router.post("/stock-picking", response_model=StockPickingResponse)
async def pick_stocks(
    limit: Optional[int] = Query(10, description="返回的股票数量，默认10只"),
    service: StockFuturesService = Depends(get_stock_futures_service)
):
    """智能选股接口"""
    try:
        # 获取支撑位附近的股票
        stocks_near_support = service.find_stocks_near_support(threshold_percent=0.03)
        
        if not stocks_near_support:
            logger.warning("未找到符合条件的股票")
            return StockPickingResponse(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                recommendations=[]
            )
        
        # 转换为推荐结果格式
        recommendations = []
        for stock in stocks_near_support:  # 已经在service层限制了数量
            # 计算推荐级别：距离支撑位越近，级别越高
            level = "强烈推荐" if stock['hourly_distance_percent'] < 0.02 else "推荐"
            
            # 构建推荐理由
            reason = (
                f"日线距支撑位{stock['distance_percent']*100:.1f}%，"
                f"小时线距支撑位{stock['hourly_distance_percent']*100:.1f}%，"
            )
            if 'industry' in stock:
                reason += f"所属{stock['industry']}行业，"
            reason += "多级别支撑共振，建议关注"
            
            recommendations.append(
                StockRecommendation(
                    code=stock['ts_code'],
                    name=stock['name'],
                    level=level,
                    price=stock['hourly_latest_price'],  # 使用小时级别的最新价格
                    change_pct=stock['pct_chg'],  # 保持使用日线的涨跌幅
                    reason=reason
                )
            )
        
        return StockPickingResponse(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"选股失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hs300-stocks")
async def get_hs300_stocks(service: StockFuturesService = Depends(get_stock_futures_service)):
    """获取沪深300成分股列表"""
    try:
        stocks = service.get_hs300_stocks()
        if not stocks:
            raise HTTPException(status_code=404, detail="未找到沪深300成分股数据")
        return stocks
    except Exception as e:
        logger.error(f"获取沪深300成分股失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock-daily/{ts_code}")
async def get_stock_daily(
    ts_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service: StockFuturesService = Depends(get_stock_futures_service)
):
    """获取股票日线数据"""
    try:
        df = service.get_stock_daily(ts_code, start_date, end_date)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票{ts_code}的日线数据")
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"获取股票{ts_code}日线数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 