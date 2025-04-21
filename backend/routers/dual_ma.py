from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import numpy as np
import talib
from utils.logger import logger
from datetime import datetime
from typing import List, Dict, Union
from strategies.dual_ma_strategy import DualMAStrategy
from pydantic import BaseModel

class BacktestRequest(BaseModel):
    use_atr_tp: bool = False
    data_period: str = 'weekly'  # 新增数据周期参数

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
        # 根据文件名判断数据周期
        if '30min' in str(file_path):
            # 30分钟数据字段映射
            df = df.rename(columns={
                '时间': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'vol',
                '成交额': 'amount'
            })
        else:
            # 周线和日线数据保持原有字段名
            df['date'] = pd.to_datetime(df['date'])
    
        logger.debug("开始计算EMA指标")
        df['ema_short'] = talib.EMA(df['close'], timeperiod=8)
        df['ema_long'] = talib.EMA(df['close'], timeperiod=21)
        # 处理NaN和Infinity值
        df = df.replace([np.inf, -np.inf], np.nan)
        df['ema_short'] = df['ema_short'].fillna(method='ffill').fillna(method='bfill')
        df['ema_long'] = df['ema_long'].fillna(method='ffill').fillna(method='bfill')
    
        logger.debug(f"数据中是否还存在NaN值: {df.isna().any().any()}")
        
        # 按时间升序排序
        df = df.sort_values('date')
        logger.info(f"数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
        
        # 转换为前端需要的格式
        columns = ['date', 'open', 'close', 'high', 'low']
        columns.extend(['ema_short', 'ema_long'])
            
        result = df[columns].to_dict('records')
        for item in result:
            item['date'] = item['date'].strftime('%Y-%m-%d %H:%M')
            # 确保所有数值都是有效的JSON数字
            numeric_keys = ['open', 'close', 'high', 'low']
            numeric_keys.extend(['ema_short', 'ema_long'])
                
            for key in numeric_keys:
                if not np.isfinite(item[key]):
                    item[key] = None
            
        logger.info(f"数据处理完成，返回 {len(result)} 条记录")
        return result
    except Exception as e:
        error_msg = f"处理数据时发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/weekly")
async def get_weekly_data():
    logger.info("收到周线数据请求")
    data_path = Path("data/159985.SZ_fund_weekly_20190101_20251231.csv")
    logger.debug(f"周线数据文件路径: {data_path.absolute()}")
    return load_and_process_data(data_path)

@router.post("/backtest")
async def backtest_strategy(request: BacktestRequest):
    """执行策略回测"""
    try:
        logger.info(f"收到回测请求，use_atr_tp={request.use_atr_tp}, data_period={request.data_period}")
        
        # 根据选择的周期加载对应的数据文件
        if request.data_period == 'weekly':
            data_path = Path("data/159985.SZ_fund_weekly_20190101_20251231.csv")
        elif request.data_period == 'daily':
            data_path = Path("data/159985.SZ_fund_daily_20190101_20251231.csv")
        else:  # 30min
            data_path = Path("data/159985.SZ_fund_30min_20190101_20251231.csv")
            
        # 读取并处理数据
        df = pd.read_csv(data_path)
        
        # 根据文件名判断数据周期并处理字段名
        if '30min' in str(data_path):
            # 30分钟数据字段映射
            df = df.rename(columns={
                '时间': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'vol',
                '成交额': 'amount'
            })
            df['date'] = pd.to_datetime(df['date'])
        else:
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        
        # 使用策略类计算信号和执行回测
        strategy = DualMAStrategy()
        df_with_signals = strategy.calculate_signals(df, use_atr_tp=request.use_atr_tp)
        result = strategy.run_backtest(df_with_signals, use_atr_tp=request.use_atr_tp)
        
        logger.info("回测完成")
        return result
        
    except Exception as e:
        error_msg = f"回测过程中发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg) 