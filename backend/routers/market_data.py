import json
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Body
from typing import List, Optional, Dict
from services.market_data import MarketDataService
from services.opt_service import OptService
from models.market_data import FuturesData, ETFData, OptionsData, InventoryData, TechnicalIndicators, OptionsHedgeData, OptionBasic, OptionDaily, CostComparisonData, PriceRangeAnalysis
from utils.logger import logger
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from pathlib import Path
from services.support_resistance import SupportResistanceService
from fastapi.responses import StreamingResponse
import akshare as ak
from openai import OpenAI
from config import settings
from starlette.background import BackgroundTask
from pydantic import BaseModel

router = APIRouter()

# 初始化OpenAI客户端
client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
)

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
        data = service.get_etf_data_weekly(start_date, end_date, symbol)
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
        
        # 创建一个按日期索引的字典来分别存储库存和仓单数据
        date_data = {}
        for item in history_data:
            date_value = item.get("date")
            if not date_value:
                continue
                
            # 统一日期格式为字符串
            try:
                # 尝试将日期转换为标准格式
                if isinstance(date_value, (date, datetime)):
                    date_str = date_value.strftime('%Y-%m-%d')
                elif isinstance(date_value, str):
                    # 如果是YYYYMMDD格式的字符串
                    if len(date_value) == 8 and date_value.isdigit():
                        date_str = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}"
                    else:
                        # 尝试解析其他格式的日期字符串
                        date_str = datetime.strptime(date_value, '%Y-%m-%d').strftime('%Y-%m-%d')
                else:
                    logger.warning(f"跳过无效的日期格式: {date_value}")
                    continue
            except Exception as e:
                logger.warning(f"日期格式转换失败: {date_value}, 错误: {str(e)}")
                continue
            
            if date_str not in date_data:
                date_data[date_str] = {
                    "date": date_str,
                    "inventory": None,
                    "warehouse_receipts": None
                }
            
            # 分别更新库存和仓单数据
            if "inventory" in item:
                date_data[date_str]["inventory"] = item["inventory"]
            if "warehouse_receipts" in item:
                date_data[date_str]["warehouse_receipts"] = item["warehouse_receipts"]
        
        # 按日期排序
        sorted_dates = sorted(date_data.keys())
        
        # 生成最终的数据列表
        for date_str in sorted_dates:
            item_data = date_data[date_str]
            
            # 处理库存数据
            if item_data["inventory"] is not None:
                current_value = item_data["inventory"]
                
                # 找到前一天的库存数据
                prev_idx = sorted_dates.index(date_str) - 1
                if prev_idx >= 0:
                    prev_date = sorted_dates[prev_idx]
                    prev_data = date_data[prev_date]
                    previous_value = prev_data["inventory"] if prev_data["inventory"] is not None else current_value
                else:
                    previous_value = current_value
                
                # 找到去年同期的库存数据
                year_ago_idx = max(0, sorted_dates.index(date_str) - 365)
                if year_ago_idx < len(sorted_dates):
                    last_year_date = sorted_dates[year_ago_idx]
                    last_year_data = date_data[last_year_date]
                    last_year_value = last_year_data["inventory"] if last_year_data["inventory"] is not None else current_value
                else:
                    last_year_value = current_value
                
                # mom_change改为直接相减
                mom_change = current_value - previous_value
                yoy_change = ((current_value - last_year_value) / last_year_value * 100) if last_year_value != 0 else 0
                
                inventory_list.append(InventoryData(
                    date=date_str,
                    value=float(current_value),
                    mom_change=float(mom_change),
                    yoy_change=float(yoy_change),
                    data_type="inventory"
                ))
            
            # 处理仓单数据
            if item_data["warehouse_receipts"] is not None:
                current_value = item_data["warehouse_receipts"]
                
                # 找到前一天的仓单数据
                prev_idx = sorted_dates.index(date_str) - 1
                if prev_idx >= 0:
                    prev_date = sorted_dates[prev_idx]
                    prev_data = date_data[prev_date]
                    previous_value = prev_data["warehouse_receipts"] if prev_data["warehouse_receipts"] is not None else current_value
                else:
                    previous_value = current_value
                
                # 找到去年同期的仓单数据
                year_ago_idx = max(0, sorted_dates.index(date_str) - 365)
                if year_ago_idx < len(sorted_dates):
                    last_year_date = sorted_dates[year_ago_idx]
                    last_year_data = date_data[last_year_date]
                    last_year_value = last_year_data["warehouse_receipts"] if last_year_data["warehouse_receipts"] is not None else current_value
                else:
                    last_year_value = current_value
                
                # mom_change改为直接相减
                mom_change = current_value - previous_value
                yoy_change = ((current_value - last_year_value) / last_year_value * 100) if last_year_value != 0 else 0
                
                inventory_list.append(InventoryData(
                    date=date_str,
                    value=float(current_value),
                    mom_change=float(mom_change),
                    yoy_change=float(yoy_change),
                    data_type="warehouse_receipts"
                ))
        
        # 按日期排序
        inventory_list.sort(key=lambda x: x.date)
        
        logger.info(f"成功返回库存和仓单数据，共{len(inventory_list)}条记录")
        return inventory_list
    except Exception as e:
        logger.error(f"库存和仓单数据请求失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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

@router.get("/arbitrage/realtime")
async def get_realtime_arbitrage_data(
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取实时套利数据"""
    try:
        data = service.get_realtime_arbitrage_data()
        return data
    except Exception as e:
        logger.error(f"获取实时套利数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/cost-comparison", response_model=List[CostComparisonData])
async def get_cost_comparison_data(
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取豆粕成本和主力合约价格比较数据"""
    logger.info("收到成本比较数据请求")
    try:
        data = service.get_cost_comparison_data()
        logger.info(f"成功返回成本比较数据，共{len(data)}条记录")
        return data
    except Exception as e:
        logger.error(f"成本比较数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/price-range-analysis", response_model=PriceRangeAnalysis)
async def get_price_range_analysis(
    contract: str = "M01",
    service: MarketDataService = Depends(get_market_data_service)
):
    """获取价格区间分析数据"""
    logger.info(f"收到价格区间分析请求 - 合约: {contract}")
    try:
        data = service.get_price_range_analysis(contract)
        logger.info(f"成功返回价格区间分析数据")
        return data
    except Exception as e:
        logger.error(f"价格区间分析数据请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/support-resistance")
async def get_support_resistance_data(period: str = "daily"):
    """获取支撑阻力数据"""
    logger.info(f"收到支撑阻力数据请求 - 周期: {period}")
    try:
        # 根据周期选择数据文件
        if period == "weekly":
            data_path = Path("daily_data/M2501.DCE_future_weekly_20100101_20251231.csv")
        elif period == "30min":
            data_path = Path("daily_data/M2501.DCE_future_30min_20100101_20251231.csv")
        else:  # daily
            data_path = Path("daily_data/M2501.DCE_future_daily_20100101_20251231.csv")
        
        if not data_path.exists():
            raise HTTPException(status_code=404, detail=f"数据文件不存在: {data_path}")
            
        # 读取数据
        df = pd.read_csv(data_path)
        
        # 处理字段映射
        if "30min" in str(data_path):
            df = df.rename(columns={
                "时间": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "vol",
                "成交额": "amount"
            })
        else:
            df = df.rename(columns={
                "datetime": "date",
                "open": "open",
                "close": "close",
                "high": "high",
                "low": "low",
                "volume": "vol",
                "amount": "amount"
            })
            
        # 确保数值列的类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'vol']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 处理日期列
        if "30min" in str(data_path):
            # 对于30分钟数据，日期格式可能不同，需要特殊处理
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S')
        else:
            # 对于日线和周线数据，尝试不同的日期格式
            try:
                # 先尝试 YYYYMMDD 格式
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            except ValueError:
                try:
                    # 再尝试 YYYY-MM-DD 格式
                    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                except ValueError:
                    # 如果都失败，使用混合格式解析
                    df['date'] = pd.to_datetime(df['date'])
            
        # 确保数据按时间排序
        df = df.sort_values('date')
        df = df.reset_index(drop=True)
        
        # 打印一些调试信息
        logger.debug(f"数据日期范围: {df['date'].min()} to {df['date'].max()}")
        
        # 使用SupportResistanceService计算支撑位和阻力位
        sr_service = SupportResistanceService()
        sr_levels = sr_service.get_sr_levels(df, period)
        
        # 准备K线数据
        market_data = []
        for _, row in df.iterrows():
            # 处理无效的浮点数值
            def clean_float(value):
                if pd.isna(value) or np.isinf(value):
                    return 0.0
                return float(value)
            
            market_data.append({
                "date": row['date'].strftime('%Y-%m-%d %H:%M:%S'),  # 使用 date 而不是 time
                "open": clean_float(row['open']),
                "high": clean_float(row['high']),
                "low": clean_float(row['low']),
                "close": clean_float(row['close']),
                "volume": clean_float(row['vol']) if 'vol' in row else 0,
                "support_level": None,  # 添加支撑位
                "resistance_level": None,  # 添加阻力位
                "signal": 0  # 添加信号，0表示无信号，1表示买入，-1表示卖出
            })
        
        # 更新支撑位和阻力位
        for sr_level in sr_levels:
            level_price = sr_level['price']
            level_type = sr_level['type']
            start_time = datetime.strptime(sr_level['start_time'], '%Y-%m-%d %H:%M:%S')
            break_time = datetime.strptime(sr_level['break_time'], '%Y-%m-%d %H:%M:%S') if sr_level['break_time'] else None
            
            for data in market_data:
                data_time = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
                if data_time >= start_time and (not break_time or data_time <= break_time):
                    if level_type == 'Support':
                        data['support_level'] = level_price
                        # 当价格接近支撑位时产生买入信号
                        if abs(data['low'] - level_price) / level_price < 0.01:  # 1%阈值
                            data['signal'] = 1
                    else:  # Resistance
                        data['resistance_level'] = level_price
                        # 当价格接近阻力位时产生卖出信号
                        if abs(data['high'] - level_price) / level_price < 0.01:  # 1%阈值
                            data['signal'] = -1
        
        logger.info(f"成功返回支撑阻力数据，共{len(sr_levels)}个水平和{len(market_data)}条K线数据")
        return market_data
        
    except Exception as e:
        logger.error(f"获取支撑阻力数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kline/{period}")
async def get_kline_data(period: str):
    """获取豆粕主力合约K线数据
    period: 15/30/60/d 分钟或日线
    """
    try:
        # 获取主力合约代码
        m_symbol = 'M2509'
        
        if period == 'd':
            # 日线数据
            df = ak.futures_zh_daily_sina(symbol=m_symbol)
            # 重命名列以匹配前端期望的格式
            df = df.rename(columns={
                'hold': 'open_interest'
            })
        else:
            # 分钟线数据 - 直接使用新浪财经分时数据接口
            # 将前端传入的period转换为接口需要的格式
            period_map = {"15": "15", "30": "30", "60": "60"}
            sina_period = period_map.get(period, "5")  # 默认使用5分钟
            
            df = ak.futures_zh_minute_sina(symbol=m_symbol, period=sina_period)
            # 重命名列以匹配前端期望的格式
            df = df.rename(columns={
                'datetime': 'date',
                'hold': 'open_interest'
            })

        # 确保数据按时间排序
        df = df.sort_values('date')
        df = df.reset_index(drop=True)

        # 使用SupportResistanceService计算支撑位和阻力位
        sr_service = SupportResistanceService()
        sr_levels = sr_service.get_sr_levels(df, period)
            
        # 转换为字典列表
        market_data = df.to_dict(orient='records')

        # 返回K线数据和支撑阻力位数据
        return {
            "kline_data": market_data,
            "sr_levels": sr_levels
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime")
async def get_realtime_data():
    """获取豆粕主力合约实时行情数据"""
    try:
        # 获取实时行情
        df = ak.futures_zh_spot(symbol='M2509', market="CF", adjust='0')
        if df.empty:
            raise HTTPException(status_code=404, detail="未获取到行情数据")
            
        # 计算涨跌幅
        price = float(df['current_price'].iloc[0])
        # 使用last_settle_price代替settlement
        settlement = float(df['last_settle_price'].iloc[0])
        change = price - settlement
        change_percent = (change / settlement) * 100
        
        return {
            "price": price,
            "change": change,
            "changePercent": change_percent,
            "volume": int(df['volume'].iloc[0]),
            "turnover": float(df.get('avg_price', 0).iloc[0]) if 'avg_price' in df.columns else 0,
            "openInterest": int(df['hold'].iloc[0]),
            "settlement": settlement
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 
    
async def stream_response(response, request: Request, next_day: str):
    last_content = ""
    
    try:
        for chunk in response:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                logger.info("客户端断开连接")
                break
                
            try:
                if hasattr(chunk, "references"):
                    pass
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content:
                    new_content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': new_content})}\n\n"
                    last_content += new_content
                    
            except Exception as e:
                logger.error(f"处理chunk时出错: {str(e)}")
                continue
        
        # 发送完成标记
        yield f"data: {json.dumps({'type': 'done', 'content': last_content})}\n\n"
        
    except Exception as e:
        logger.error(f"流式响应出错: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        logger.info("流式响应结束")

class SRLevel(BaseModel):
    price: float
    type: str
    strength: float
    start_time: str
    break_time: Optional[str]
    retest_times: List[str]
    timeframe: str

class StrategyRequest(BaseModel):
    sr_levels: List[SRLevel]

@router.post("/strategy")
async def get_strategy(
    request: Request,
    strategy_request: StrategyRequest = Body(...),
):
    """获取操盘策略"""
    try:
        logger.info("开始调用Deepseek API")
        
        prompt = f"""目标：基于豆粕2509合约行情数据分析得到的支撑阻力位数据分析给出操作策略，不要出现任何的引用和来源。
                支撑阻力位数据：
                {strategy_request.sr_levels}
                """

        logger.info(f"提示词：{prompt}")
        try:
            response = client.chat.completions.create(
                model="bot-20250329163710-8zcqm",
                messages=[
                    {"role": "system", "content": "你是一个豆粕期货量化策略专家，请根据我给你的豆粕2509合约行情数据分析得到的支撑阻力位数据，分析给出操作建议。"},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

            return StreamingResponse(
                stream_response(response, request, ""),
                media_type="text/event-stream",
                background=BackgroundTask(logger.info, "请求处理完成")
            )
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"API调用失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"获取操盘策略失败: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))