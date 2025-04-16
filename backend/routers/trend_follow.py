from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import numpy as np
import talib
from utils.logger import logger
from datetime import datetime
from typing import List, Dict, Union
from strategies.trend_follow_strategy import TrendFollowStrategy

router = APIRouter()

def load_and_process_data(file_path, is_15min=False):
    try:
        logger.info(f"开始加载数据文件: {file_path}")
        
        if not file_path.exists():
            error_msg = f"数据文件不存在: {file_path}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
            
        df = pd.read_csv(file_path)
        logger.info(f"成功读取CSV文件，总数据行数: {len(df)}")
        
        logger.debug("开始处理时间列")
        df['date'] = pd.to_datetime(df['date'])
        
        if is_15min:
            logger.debug("开始计算15分钟EMA12和EMA26指标")
            df['ema12'] = talib.EMA(df['close'], timeperiod=12)
            df['ema26'] = talib.EMA(df['close'], timeperiod=26)
            # 处理NaN和Infinity值
            df = df.replace([np.inf, -np.inf], np.nan)
            df['ema12'] = df['ema12'].fillna(method='ffill').fillna(method='bfill')
            df['ema26'] = df['ema26'].fillna(method='ffill').fillna(method='bfill')
        else:
            logger.debug("开始计算60分钟EMA60指标")
            df['ema60'] = talib.EMA(df['close'], timeperiod=60)
            # 处理NaN和Infinity值
            df = df.replace([np.inf, -np.inf], np.nan)
            df['ema60'] = df['ema60'].fillna(method='ffill').fillna(method='bfill')
        
        logger.debug(f"数据中是否还存在NaN值: {df.isna().any().any()}")
        
        # 按时间升序排序
        df = df.sort_values('date')
        logger.info(f"数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
        
        # 转换为前端需要的格式
        columns = ['date', 'open', 'close', 'high', 'low']
        if is_15min:
            columns.extend(['ema12', 'ema26'])
        else:
            columns.append('ema60')
            
        result = df[columns].to_dict('records')
        for item in result:
            item['date'] = item['date'].strftime('%Y-%m-%d %H:%M')
            # 确保所有数值都是有效的JSON数字
            numeric_keys = ['open', 'close', 'high', 'low']
            if is_15min:
                numeric_keys.extend(['ema12', 'ema26'])
            else:
                numeric_keys.append('ema60')
                
            for key in numeric_keys:
                if not np.isfinite(item[key]):
                    item[key] = None
            
        logger.info(f"数据处理完成，返回 {len(result)} 条记录")
        return result
    except Exception as e:
        error_msg = f"处理数据时发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/15min")
async def get_15min_data():
    logger.info("收到15分钟数据请求")
    data_path = Path("data/M2501.DCE_future_15min_20240101_20251231.csv")
    logger.debug(f"15分钟数据文件路径: {data_path.absolute()}")
    return load_and_process_data(data_path, is_15min=True)

@router.get("/60min")
async def get_60min_data():
    logger.info("收到60分钟数据请求")
    data_path = Path("data/M2501.DCE_future_60min_20240101_20251231.csv")
    logger.debug(f"60分钟数据文件路径: {data_path.absolute()}")
    return load_and_process_data(data_path, is_15min=False)

@router.post("/backtest")
async def backtest_strategy():
    """执行策略回测"""
    try:
        logger.info("收到回测请求")
        
        # 加载数据
        data_path_15min = Path("data/M2501.DCE_future_15min_20240101_20251231.csv")
        data_path_60min = Path("data/M2501.DCE_future_60min_20240101_20251231.csv")
        
        # 读取并处理数据
        df_15min = pd.read_csv(data_path_15min)
        df_60min = pd.read_csv(data_path_60min)
        
        df_15min['date'] = pd.to_datetime(df_15min['date'])
        df_60min['date'] = pd.to_datetime(df_60min['date'])
        
        # 计算技术指标
        df_15min['ema12'] = talib.EMA(df_15min['close'], timeperiod=12)
        df_15min['ema26'] = talib.EMA(df_15min['close'], timeperiod=26)
        df_60min['ema60'] = talib.EMA(df_60min['close'], timeperiod=60)
        
        # 使用策略类计算信号和执行回测
        strategy = TrendFollowStrategy()
        df_with_signals = strategy.calculate_signals(df_15min, df_60min)
        result = strategy.run_backtest(df_with_signals)
        
        logger.info("回测完成")
        return result
        
    except Exception as e:
        error_msg = f"回测过程中发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg) 