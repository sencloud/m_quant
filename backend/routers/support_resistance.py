from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import numpy as np
import talib
from utils.logger import logger
from datetime import datetime
from typing import List, Dict, Union
from strategies.support_resistance_strategy import SupportResistanceStrategy
from pydantic import BaseModel

class BacktestRequest(BaseModel):
    data_period: str = 'daily'  # daily, weekly, 30min

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
            df['date'] = pd.to_datetime(df['date'])
        else:
            # 日线数据字段映射
            df = df.rename(columns={
                'datetime': 'date',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'volume': 'vol',
                'amount': 'amount'
            })
            df['date'] = pd.to_datetime(df['date'])
        
        # 计算支撑位和阻力位
        window = 20  # 用于计算支撑位和阻力位的窗口大小
        df['support_level'] = df['low'].rolling(window=window).min()
        df['resistance_level'] = df['high'].rolling(window=window).max()
        
        # 计算ATR
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 处理NaN和Infinity值
        df = df.replace([np.inf, -np.inf], np.nan)
        df['support_level'] = df['support_level'].fillna(method='ffill').fillna(method='bfill')
        df['resistance_level'] = df['resistance_level'].fillna(method='ffill').fillna(method='bfill')
        df['atr'] = df['atr'].fillna(method='ffill').fillna(method='bfill')
        
        logger.debug(f"数据中是否还存在NaN值: {df.isna().any().any()}")
        
        # 按时间升序排序
        df = df.sort_values('date')
        logger.info(f"数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
        
        # 转换为前端需要的格式
        columns = ['date', 'open', 'close', 'high', 'low', 'vol', 'amount', 'support_level', 'resistance_level', 'atr']
        result = df[columns].to_dict('records')
        for item in result:
            item['date'] = item['date'].strftime('%Y-%m-%d %H:%M')
            # 确保所有数值都是有效的JSON数字
            numeric_keys = ['open', 'close', 'high', 'low', 'vol', 'amount', 'support_level', 'resistance_level', 'atr']
            for key in numeric_keys:
                if not np.isfinite(item[key]):
                    item[key] = None
        
        logger.info(f"数据处理完成，返回 {len(result)} 条记录")
        return result
    except Exception as e:
        error_msg = f"处理数据时发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/support-resistance")
async def get_support_resistance_data(period: str = 'daily'):
    """获取支撑阻力数据"""
    logger.info(f"收到{period}数据请求")
    
    if period == 'weekly':
        data_path = Path("daily_data/M2501.DCE_future_weekly_20100101_20251231.csv")
    elif period == '30min':
        data_path = Path("daily_data/M2501.DCE_future_30min_20100101_20251231.csv")
    else:  # daily
        data_path = Path("daily_data/M2501.DCE_future_daily_20100101_20251231.csv")
    
    logger.debug(f"数据文件路径: {data_path.absolute()}")
    return load_and_process_data(data_path)

@router.post("/backtest")
async def backtest_strategy(request: BacktestRequest):
    """执行策略回测"""
    try:
        logger.info(f"收到回测请求，data_period={request.data_period}")
        
        # 根据选择的周期加载对应的数据文件
        if request.data_period == 'weekly':
            data_path = Path("daily_data/M2501.DCE_future_weekly_20100101_20251231.csv")
        elif request.data_period == '30min':
            data_path = Path("daily_data/M2501.DCE_future_30min_20100101_20251231.csv")
        else:  # daily
            data_path = Path("daily_data/M2501.DCE_future_daily_20100101_20251231.csv")
            
        # 读取并处理数据
        df = pd.read_csv(data_path)
        
        # 根据文件名判断数据周期并处理字段名
        if '30min' in str(data_path):
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
            df = df.rename(columns={
                'datetime': 'date',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'volume': 'vol',
                'amount': 'amount'
            })
        
        df['date'] = pd.to_datetime(df['date'])
        
        # 确保数值列不包含None或NaN
        numeric_columns = ['open', 'close', 'high', 'low', 'vol', 'amount']
        df[numeric_columns] = df[numeric_columns].fillna(method='ffill').fillna(method='bfill')
        
        # 使用策略类计算信号和执行回测
        strategy = SupportResistanceStrategy()
        df_with_signals = strategy.calculate_signals(df)
        
        # 确保信号列不包含None或NaN
        signal_columns = ['support_level', 'resistance_level', 'signal']
        if any(col in df_with_signals.columns for col in signal_columns):
            df_with_signals[signal_columns] = df_with_signals[signal_columns].fillna(0)
        
        result = strategy.run_backtest(df_with_signals)
        
        logger.info("回测完成")
        return result
        
    except Exception as e:
        error_msg = f"回测过程中发生错误: {str(e)}"
        import traceback
        traceback.print_exc()
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg) 