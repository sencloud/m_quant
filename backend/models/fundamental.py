from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy import Column, String, Date, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FundamentalAnalysisDB(Base):
    __tablename__ = "fundamental_analysis"

    date = Column(Date, primary_key=True)
    supply_demand = Column(JSON)
    seasonal = Column(JSON)
    weather = Column(JSON)
    crush_profit = Column(JSON)
    overall = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FundamentalAnalysis(BaseModel):
    """用于API响应的Pydantic模型"""
    date: date
    supply_demand: Dict[str, Any]
    seasonal: Dict[str, Any]
    weather: Dict[str, Any]
    crush_profit: Dict[str, Any]
    overall: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 