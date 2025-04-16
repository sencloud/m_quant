from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import numpy as np
import talib
from utils.logger import logger
from datetime import datetime
from typing import List, Dict, Union
from strategies.obv_adx_ema_strategy import OBVADXEMAStrategy

router = APIRouter()

def load_and_process_data(file_path):
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
        
        # 计算技术指标
        df['ema20'] = talib.EMA(df['close'], timeperiod=20)
        df['ema60'] = talib.EMA(df['close'], timeperiod=60)
        df['ema5'] = talib.EMA(df['close'], timeperiod=5)
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        df['obv'] = talib.OBV(df['close'], df['volume'])
        df['obv_ma30'] = talib.SMA(df['obv'], timeperiod=30)
        
        # 处理NaN和Infinity值
        df = df.replace([np.inf, -np.inf], np.nan)
        df['ema20'] = df['ema20'].fillna(method='ffill').fillna(method='bfill')
        df['ema60'] = df['ema60'].fillna(method='ffill').fillna(method='bfill')
        df['ema5'] = df['ema5'].fillna(method='ffill').fillna(method='bfill')
        df['adx'] = df['adx'].fillna(method='ffill').fillna(method='bfill')
        df['obv'] = df['obv'].fillna(method='ffill').fillna(method='bfill')
        df['obv_ma30'] = df['obv_ma30'].fillna(method='ffill').fillna(method='bfill')

        logger.debug(f"数据中是否还存在NaN值: {df.isna().any().any()}")
        
        # 按时间升序排序
        df = df.sort_values('date')
        logger.info(f"数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
        
        # 转换为前端需要的格式
        columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'ema20', 'ema60', 'ema5', 'adx', 'obv', 'obv_ma30']
        result = df[columns].to_dict('records')
        for item in result:
            item['date'] = item['date'].strftime('%Y-%m-%d %H:%M')
            # 确保所有数值都是有效的JSON数字
            numeric_keys = ['open', 'close', 'high', 'low', 'volume', 'ema20', 'ema60', 'ema5', 'adx', 'obv', 'obv_ma30']
            for key in numeric_keys:
                if not np.isfinite(item[key]):
                    item[key] = None
            
        logger.info(f"数据处理完成，返回 {len(result)} 条记录")
        return result
    except Exception as e:
        error_msg = f"处理数据时发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/data")
async def get_data():
    logger.info("收到OBV、ADX与EMA组合策略数据请求")
    data_path = Path("data/M2501.DCE_future_60min_20240101_20251231.csv")
    logger.debug(f"60分钟数据文件路径: {data_path.absolute()}")
    return load_and_process_data(data_path)

@router.post("/backtest")
async def backtest_strategy():
    """执行策略回测"""
    try:
        logger.info("收到OBV、ADX与EMA组合策略回测请求")
        
        # 加载数据
        data_path = Path("data/M2501.DCE_future_60min_20240101_20251231.csv")
        
        # 读取并处理数据
        df_60min = pd.read_csv(data_path)
        df_60min['date'] = pd.to_datetime(df_60min['date'])
        
        # 使用策略类计算信号和执行回测
        strategy = OBVADXEMAStrategy()
        df_with_signals = strategy.calculate_signals(df_60min)
        result = strategy.run_backtest(df_with_signals)
        
        logger.info("OBV、ADX与EMA组合策略回测完成")
        return result
        
    except Exception as e:
        error_msg = f"回测过程中发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg) 