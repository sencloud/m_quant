from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from services.market_data import MarketDataService
from models.market_data import FuturesData, ETFData, OptionsData
from utils.logger import logger

router = APIRouter()

def get_market_data_service() -> MarketDataService:
    logger.debug("创建市场数据服务实例")
    return MarketDataService()

@router.get("/futures", response_model=List[FuturesData])
async def get_futures_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbol: str = "M",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取豆粕期货数据"""
    logger.info(f"收到期货数据请求 - 品种: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}")
    try:
        data = service.get_futures_data(start_date, end_date, symbol)
        logger.info(f"成功返回期货数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"期货数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/etf", response_model=List[ETFData])
async def get_etf_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbol: str = "159985.SZ",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取豆粕ETF数据"""
    logger.info(f"收到ETF数据请求 - 代码: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}")
    try:
        data = service.get_etf_data(start_date, end_date, symbol)
        logger.info(f"成功返回ETF数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"ETF数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options", response_model=List[OptionsData])
async def get_options_data(
    underlying: str = "M",
    exchange: str = "DCE",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取豆粕期权数据"""
    logger.info(f"收到期权数据请求 - 标的: {underlying}, 交易所: {exchange}")
    try:
        data = service.get_options_data(underlying, exchange)
        logger.info(f"成功返回期权数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"期权数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/contracts", response_model=List[FuturesData])
async def get_futures_contracts_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    contracts: List[str] = ["M2401", "M2405", "M2409"],
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取多个豆粕期货合约数据"""
    logger.info(f"收到多合约数据请求 - 合约: {contracts}, 开始日期: {start_date}, 结束日期: {end_date}")
    try:
        data = service.get_futures_contracts_data(start_date, end_date, contracts)
        logger.info(f"成功返回多合约数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"多合约数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/inventory")
async def get_futures_inventory(
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取豆粕库存数据"""
    logger.info("收到库存数据请求")
    try:
        data = service.get_futures_inventory()
        logger.info("成功返回库存数据")
        return data
    except Exception as e:
        logger.error(f"库存数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 