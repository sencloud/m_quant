from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

router = APIRouter()

class TradingModel:
    def __init__(self):
        self.model = self._build_model()
        self.scaler = MinMaxScaler()
        
    def _build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(60, 5)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(50, return_sequences=False),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def prepare_data(self, data: List[Dict]):
        df = pd.DataFrame(data)
        features = ['open', 'high', 'low', 'close', 'vol']
        scaled_data = self.scaler.fit_transform(df[features])
        
        X, y = [], []
        for i in range(60, len(scaled_data)):
            X.append(scaled_data[i-60:i])
            y.append(scaled_data[i, 3])  # 预测收盘价
            
        return np.array(X), np.array(y)

@router.get("/predict")
async def get_prediction(
    symbol: str = "M",
    days: int = 5
):
    """获取模型预测结果"""
    try:
        # 这里应该从数据库或API获取历史数据
        # 示例返回
        return {
            "next_day_prediction": 3500.0,
            "confidence": 0.85,
            "trend": "上涨",
            "risk_level": "中等",
            "suggested_position": "多头"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-performance")
async def get_model_performance():
    """获取模型性能指标"""
    try:
        return {
            "accuracy": 0.78,
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.15,
            "win_rate": 0.65,
            "profit_factor": 1.8
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 