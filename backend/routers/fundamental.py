from fastapi import APIRouter, HTTPException
from services.fundamental import FundamentalAnalyzer
from utils.logger import logger
from datetime import datetime
from typing import Dict, Any

router = APIRouter()
analyzer = FundamentalAnalyzer()

@router.get("/analysis")
async def get_fundamental_analysis(date: str):
    """获取基本面分析数据"""
    try:
        # 验证日期格式
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
            
        return await analyzer.get_fundamental_analysis(date)
    except Exception as e:
        logger.error(f"获取基本面分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supply-demand")
async def get_supply_demand() -> Dict[str, Any]:
    """获取供需平衡数据"""
    try:
        return await analyzer.get_supply_demand_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/seasonal")
async def get_seasonal_pattern() -> Dict[str, Any]:
    """获取季节性规律数据"""
    try:
        return {"data": await analyzer.get_seasonal_pattern()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather")
async def get_weather_data() -> Dict[str, Any]:
    """获取天气数据"""
    try:
        return await analyzer.get_weather_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crush-profit")
async def get_crush_profit() -> Dict[str, Any]:
    """获取压榨利润数据"""
    try:
        return await analyzer.get_crush_profit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overall")
async def get_overall_assessment() -> Dict[str, Any]:
    """获取综合评估数据"""
    try:
        return await analyzer.get_overall_assessment()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 