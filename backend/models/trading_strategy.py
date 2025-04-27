from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TradingStrategy(Base):
    """操盘策略数据库模型"""
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    contract = Column(String, nullable=False, index=True)  # 合约代码
    strategy = Column(String, nullable=False)  # 策略内容
    sr_levels = Column(JSON, nullable=True)  # 支撑阻力位数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 