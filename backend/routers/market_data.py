from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from services.market_data import MarketDataService
from services.opt_service import OptService
from models.market_data import FuturesData, ETFData, OptionsData, InventoryData, TechnicalIndicators, OptionsHedgeData, OptionBasic, OptionDaily
from utils.logger import logger
from datetime import datetime, timedelta

router = APIRouter()

def get_market_data_service() -> MarketDataService:
    logger.debug("创建市场数据服务实例")
    service = MarketDataService()
    if not hasattr(service, 'pro') or service.pro is None:
        logger.error("MarketDataService 初始化失败，Tushare API 不可用")
    return service

def get_opt_service() -> OptService:
    logger.debug("创建期权服务实例")
    return OptService()

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
        # 确保返回的数据包含完整的K线信息
        for item in data:
            if not hasattr(item, 'open') or not hasattr(item, 'high') or not hasattr(item, 'low'):
                item.open = item.price
                item.high = item.price
                item.low = item.price
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

@router.get("/inventory", response_model=List[InventoryData])
async def get_inventory_data(
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取豆粕库存数据"""
    logger.info("收到库存数据请求")
    try:
        data = service.get_futures_inventory()
        if not data:
            return []
        
        # 转换数据格式
        inventory_list = []
        history_data = data.get("history_data", [])
        for i, item in enumerate(history_data):
            # 计算环比和同比变化
            current_value = item["inventory"]
            previous_value = history_data[i-1]["inventory"] if i > 0 else current_value
            last_year_value = data.get("history_data", [])[12]["inventory"] if len(data.get("history_data", [])) > 12 else current_value
            
            # mom_change改为直接相减
            mom_change = current_value - previous_value
            yoy_change = ((current_value - last_year_value) / last_year_value * 100) if last_year_value != 0 else 0
            
            inventory_list.append(InventoryData(
                date=item["date"].strftime('%Y-%m-%d'),
                value=float(current_value),
                mom_change=float(mom_change),
                yoy_change=float(yoy_change)
            ))
        
        logger.info(f"成功返回库存数据，共{len(inventory_list)}条记录")
        return inventory_list
    except Exception as e:
        logger.error(f"库存数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/technical", response_model=TechnicalIndicators)
async def get_technical_indicators(
    symbol: str = "M",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取技术分析指标"""
    logger.info(f"收到技术分析指标请求 - 品种: {symbol}")
    try:
        data = service.get_technical_indicators(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="未找到技术分析指标数据")
        logger.info("成功返回技术分析指标数据")
        return data
    except Exception as e:
        logger.error(f"技术分析指标请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/hedge", response_model=List[OptionsHedgeData])
async def get_options_hedge_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    hedge_type: str = "delta",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取期权对冲策略数据"""
    logger.info(f"收到期权对冲数据请求 - 开始日期: {start_date}, 结束日期: {end_date}, 对冲类型: {hedge_type}")
    try:
        data = service.get_options_hedge_data(start_date, end_date, hedge_type)
        if not data:
            raise HTTPException(status_code=404, detail="未找到期权对冲数据")
        logger.info(f"成功返回期权对冲数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"期权对冲数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/basic", response_model=List[OptionBasic])
async def get_option_basics(
    service: OptService = Depends(get_opt_service)
):
    """获取期权基础信息"""
    try:
        logger.info("收到期权基础信息请求")
        result = await service.get_option_basics()
        logger.info(f"成功获取期权基础信息，共{len(result)}条记录")
        return result
    except Exception as e:
        logger.error(f"获取期权基础信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/daily", response_model=List[OptionDaily])
async def get_option_daily(
    service: OptService = Depends(get_opt_service)
):
    """获取期权日线数据"""
    try:
        logger.info("收到期权日线行情数据请求")
        result = await service.get_option_daily()
        logger.info(f"成功获取期权日线数据，共{len(result)}条记录")
        return result
    except Exception as e:
        logger.error(f"期权日线行情数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/daily/{ts_code}", response_model=List[OptionDaily])
async def get_option_daily_by_code(
    ts_code: str,
    service: OptService = Depends(get_opt_service)
):
    """获取指定期权的日线数据"""
    try:
        logger.info(f"收到期权日线行情数据请求 - TS代码: {ts_code}")
        # 计算一年前的日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        result = await service.get_option_daily_by_code(
            ts_code=ts_code,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d")
        )
        logger.info(f"成功获取期权 {ts_code} 的日线数据，共{len(result)}条记录")
        return result
    except Exception as e:
        logger.error(f"获取期权 {ts_code} 的日线数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/historical", response_model=List[FuturesData])
async def get_historical_comparison_data(
    symbol: str = "M",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取历史同期数据"""
    logger.info(f"收到历史同期数据请求 - 品种: {symbol}")
    try:
        data = service.get_historical_comparison_data(symbol)
        logger.info(f"成功返回历史同期数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"历史同期数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/monthly-probability", response_model=dict)
async def get_monthly_probability_data(
    symbol: str = "M",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取历史月度涨跌概率数据"""
    logger.info(f"收到历史月度涨跌概率数据请求 - 品种: {symbol}")
    try:
        data = service.get_monthly_probability_data(symbol)
        logger.info(f"成功返回历史月度涨跌概率数据")
        return data
    except Exception as e:
        logger.error(f"历史月度涨跌概率数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/event-price", response_model=List[FuturesData])
async def get_event_price_data(
    event_date: str,
    contract: str = "M01",
    days_before: int = 30,
    days_after: int = 30,
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取事件前后的价格走势数据"""
    logger.info(f"收到事件价格数据请求 - 事件日期: {event_date}, 合约: {contract}, 前后天数: {days_before}/{days_after}")
    try:
        data = service.get_event_price_data(event_date, contract, days_before, days_after)
        logger.info(f"成功返回事件价格数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"事件价格数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 