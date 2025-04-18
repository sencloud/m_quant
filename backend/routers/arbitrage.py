from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from services.market_data import MarketDataService
from models.market_data import FuturesData
import pandas as pd
import numpy as np
import os
import logging

# 配置日志
logger = logging.getLogger(__name__)

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

def load_kline_data(symbol: str) -> pd.DataFrame:
    """加载K线数据"""
    try:
        file_path = os.path.join('data', f'{symbol}_future_5min_20240801_20241130.csv')
        logger.info(f"尝试加载数据文件: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"数据文件不存在: {file_path}")
            raise HTTPException(status_code=500, detail=f"Data file not found: {file_path}")
            
        df = pd.read_csv(file_path)
        logger.info(f"成功读取CSV文件: {symbol}, 数据行数: {len(df)}")
        
        df['datetime'] = pd.to_datetime(df['date'])
        df.set_index('datetime', inplace=True)
        logger.info(f"数据处理完成: {symbol}, 时间范围: {df.index.min()} 到 {df.index.max()}")
        
        return df
    except Exception as e:
        logger.error(f"加载数据失败 {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load data for {symbol}: {str(e)}")

def calculate_oil_meal_ratio(y_data: pd.DataFrame, m_data: pd.DataFrame) -> Dict:
    """计算油粕比"""
    try:
        logger.info(f"开始计算油粕比, 豆油数据行数: {len(y_data)}, 豆粕数据行数: {len(m_data)}")
        
        # 确保两个数据框的索引一致
        common_index = y_data.index.intersection(m_data.index)
        logger.info(f"共同时间点数量: {len(common_index)}")
        
        y_data = y_data.loc[common_index]
        m_data = m_data.loc[common_index]
        
        # 计算油粕比
        ratio = y_data['close'] / m_data['close']
        latest_ratio = ratio.iloc[-1]
        logger.info(f"当前油粕比: {latest_ratio:.4f}")
        
        # 获取最近60个数据点
        recent_ratios = ratio.tail(60).tolist()
        timestamps = [ts.strftime('%H:%M') for ts in ratio.tail(60).index]
        logger.info(f"历史数据点数: {len(recent_ratios)}")
        
        return {
            "current_ratio": latest_ratio,
            "historical_data": {
                "timestamps": timestamps,
                "values": recent_ratios
            }
        }
    except Exception as e:
        logger.error("计算油粕比失败", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate oil/meal ratio: {str(e)}")

def calculate_crushing_margin(y_data: pd.DataFrame, m_data: pd.DataFrame, b_data: pd.DataFrame) -> Dict:
    """计算压榨利润"""
    try:
        logger.info(f"开始计算压榨利润, 数据行数 - 豆油: {len(y_data)}, 豆粕: {len(m_data)}, 豆二: {len(b_data)}")
        
        # 确保所有数据框的索引一致
        common_index = y_data.index.intersection(m_data.index).intersection(b_data.index)
        logger.info(f"共同时间点数量: {len(common_index)}")
        
        y_data = y_data.loc[common_index]
        m_data = m_data.loc[common_index]
        b_data = b_data.loc[common_index]
        
        # 计算压榨利润
        margin = y_data['close'] * 0.18 + m_data['close'] * 0.8 - b_data['close']
        
        # 计算5日均值
        historical_avg = margin.rolling(window=5*48).mean().iloc[-1]
        latest_margin = margin.iloc[-1]
        logger.info(f"当前压榨利润: {latest_margin:.2f}, 历史均值: {historical_avg:.2f}")
        
        # 获取最近60个数据点
        recent_margins = margin.tail(60).tolist()
        timestamps = [ts.strftime('%H:%M') for ts in margin.tail(60).index]
        logger.info(f"历史数据点数: {len(recent_margins)}")
        
        return {
            "current_margin": latest_margin,
            "historical_average": historical_avg,
            "historical_data": {
                "timestamps": timestamps,
                "values": recent_margins
            }
        }
    except Exception as e:
        logger.error("计算压榨利润失败", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate crushing margin: {str(e)}")

@router.get("/realtime")
async def get_realtime_arbitrage():
    """获取实时套利数据"""
    try:
        logger.info("开始处理实时套利数据请求")
        
        # 加载数据
        logger.info("开始加载K线数据")
        y_data = load_kline_data('Y2501.DCE')  # 豆油
        m_data = load_kline_data('M2501.DCE')  # 豆粕
        b_data = load_kline_data('B2501.DCE')  # 豆二
        logger.info("K线数据加载完成")
        
        # 计算油粕比
        logger.info("开始计算油粕比")
        oil_meal_ratio = calculate_oil_meal_ratio(y_data, m_data)
        logger.info("油粕比计算完成")
        
        # 计算压榨利润
        logger.info("开始计算压榨利润")
        crushing_margin = calculate_crushing_margin(y_data, m_data, b_data)
        logger.info("压榨利润计算完成")
        
        logger.info("数据处理完成，准备返回结果")
        return {
            "oil_meal_ratio": oil_meal_ratio,
            "crushing_margin": crushing_margin
        }
    except Exception as e:
        logger.error("处理实时套利数据请求失败", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 