from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import numpy as np
from utils.logger import logger
from datetime import datetime
from typing import List, Dict, Union
from strategies.grid_strategy import GridStrategy
from pydantic import BaseModel, Field

class BacktestRequest(BaseModel):
    grid_levels: int = Field(default=10, ge=2, le=50, description="网格数量，范围2-50")
    atr_period: int = Field(default=14, ge=5, le=30, description="ATR周期，范围5-30")
    data_period: str = Field(default='daily', description="数据周期: daily/weekly/30min")

    class Config:
        schema_extra = {
            "example": {
                "grid_levels": 10,
                "atr_period": 14,
                "data_period": "daily"
            }
        }

router = APIRouter()

def load_and_process_data(file_path: Path) -> pd.DataFrame:
    """加载并处理数据"""
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path)
        logger.info(f"成功读取CSV文件，总数据行数: {len(df)}")
        
        # 确保必要的列存在
        required_columns = ['date', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV文件缺少必要的列: {required_columns}")
        
        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        
        # 处理NaN和Infinity值
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # 按日期排序
        df = df.sort_values('date')
        
        # 确保数值列是浮点数类型
        numeric_columns = ['open', 'high', 'low', 'close']
        for col in numeric_columns:
            df[col] = df[col].astype(float)
        
        logger.info(f"数据处理完成，时间范围: {df['date'].min()} 至 {df['date'].max()}")
        return df
        
    except Exception as e:
        error_msg = f"加载数据文件失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        logger.info("开始网格策略回测")
        logger.info(f"参数: grid_levels={request.grid_levels}, atr_period={request.atr_period}, data_period={request.data_period}")
        
        # 根据数据周期选择数据文件
        data_file = {
            'weekly': 'data/M2501.DCE_future_daily_20240101_20251231.csv',
            'daily': 'data/M2501.DCE_future_daily_20240101_20251231.csv',
            '30min': 'data/M2501.DCE_future_daily_20240101_20251231.csv'
        }.get(request.data_period)
        
        if not data_file:
            raise HTTPException(status_code=400, detail=f"不支持的数据周期: {request.data_period}")
        
        # 加载数据
        df = load_and_process_data(Path(data_file))
        
        # 计算交易信号
        df_with_signals = GridStrategy.calculate_signals(
            df=df,
            grid_levels=request.grid_levels,
            atr_period=request.atr_period
        )
        
        # 执行回测
        backtest_results = GridStrategy.run_backtest(
            df=df_with_signals,
            grid_levels=request.grid_levels
        )
        
        logger.info("网格策略回测完成")
        return {
            "status": "success",
            "data": {
                "backtest_results": backtest_results,
                "summary": {
                    "total_trades": len(backtest_results['trades']),
                    "win_rate": round(backtest_results['win_rate'], 2),
                    "total_profit": round(backtest_results['total_profit'], 2),
                    "sharpe_ratio": round(backtest_results['sharpe_ratio'], 2),
                    "max_drawdown": round(backtest_results['max_drawdown'], 2),
                    "annual_returns": round(backtest_results['annual_returns'] * 100, 2)
                }
            }
        }
        
    except Exception as e:
        error_msg = f"执行回测失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/data")
async def get_grid_data():
    """获取网格策略的最新数据"""
    try:
        # 使用日线数据
        data_file = 'data/M2501.DCE_future_daily_20240101_20251231.csv'
        
        # 加载数据
        df = load_and_process_data(Path(data_file))
        
        # 计算网格信号
        df_with_signals = GridStrategy.calculate_signals(df)
        
        # 转换数据格式
        result = []
        for _, row in df_with_signals.iterrows():
            # 获取当前网格的价格
            grid_price = row['grids'][row['current_grid']] if not pd.isna(row['current_grid']) else None
            
            # 检查并处理无效的浮点数值
            def safe_float(value):
                if pd.isna(value) or np.isinf(value):
                    return None
                return float(value)
            
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': safe_float(row['open']),
                'close': safe_float(row['close']),
                'high': safe_float(row['high']),
                'low': safe_float(row['low']),
                'grid_level': int(row['current_grid']) if not pd.isna(row['current_grid']) else None,
                'grid_price': safe_float(grid_price)
            })
        
        return result
        
    except Exception as e:
        error_msg = f"获取网格数据失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg) 