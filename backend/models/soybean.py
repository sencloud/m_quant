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
    # 装船数据
    current_shipment = Column(Float, nullable=False)  # 当前装船量
    forecast_shipment = Column(Float, nullable=False)  # 预计装船量
    forecast_next_shipment = Column(Float, nullable=False)  # 下月预计装船量
    
    # 到港数据
    current_arrival = Column(Float, nullable=False)  # 当月到港量
    next_arrival = Column(Float, nullable=False)  # 下月到港预期
    current_month_arrival = Column(Float, nullable=False)  # 当月实际到港量
    next_month_arrival = Column(Float, nullable=False)  # 下月预计到港量
    
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

class ComparisonData(BaseModel):
    """月度对比数据"""
    month: str
    value: float
    type: str

class PortDistributionData(BaseModel):
    """港口分布数据"""
    port: str
    value: float
    type: str

class SoybeanImport(BaseModel):
    """用于API响应的大豆进口数据模型"""
    date: str  # YYYY-MM-DD
    
    # 装船数据
    current_shipment: float
    forecast_shipment: float
    forecast_next_shipment: float
    
    # 到港数据
    current_arrival: float
    next_arrival: float
    current_month_arrival: float
    next_month_arrival: float
    
    # 同环比数据
    current_shipment_yoy: float = 0.0
    current_shipment_mom: float = 0.0
    forecast_shipment_yoy: float = 0.0
    forecast_shipment_mom: float = 0.0
    current_arrival_yoy: float = 0.0
    current_arrival_mom: float = 0.0
    next_arrival_yoy: float = 0.0
    
    # 预期差异
    shipment_forecast_diff: float = 0.0
    arrival_forecast_diff: float = 0.0
    
    # 图表数据
    monthly_comparison: List[ComparisonData] = []
    port_distribution: List[PortDistributionData] = []
    
    # 详细数据
    port_details: List[PortDetail]
    customs_details: List[CustomsDetail]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 