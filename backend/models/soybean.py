from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SoybeanImportDB(Base):
    """大豆进口数据库模型"""
    __tablename__ = "soybean_imports"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    current_shipment = Column(Float, nullable=False)
    forecast_shipment = Column(Float, nullable=False)
    current_arrival = Column(Float, nullable=False)
    next_arrival = Column(Float, nullable=False)
    port_details = Column(JSON, nullable=False)  # 存储港口详细数据
    customs_details = Column(JSON, nullable=False)  # 存储海关详细数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortDetail(BaseModel):
    """港口详细数据模型"""
    port: str
    current: float
    next_month: float
    next_two_month: float

class CustomsDetail(BaseModel):
    """海关详细数据模型"""
    customs: str
    current: float
    next_period: float
    next_month: float
    next_two_month: float

class SoybeanImport(BaseModel):
    """用于API响应的大豆进口数据模型"""
    date: str  # 修改为字符串类型，格式为 YYYY-MM-DD
    current_shipment: float
    current_shipment_yoy: float
    forecast_shipment: float
    forecast_shipment_yoy: float
    current_arrival: float
    current_arrival_yoy: float
    next_arrival: float
    next_arrival_yoy: float
    port_details: List[PortDetail]
    customs_details: List[CustomsDetail]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 