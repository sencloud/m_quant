from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, Date, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class CoreFactorAnalysisDB(Base):
    __tablename__ = "core_factor_analysis"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    inventory_cycle = Column(JSON)
    technical_signals = Column(JSON)
    price_anchors = Column(JSON)
    news_policy = Column(JSON)
    hog_market = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CoreFactorAnalysis(BaseModel):
    date: date
    inventory_cycle: Dict[str, Any]
    technical_signals: Dict[str, Any]
    price_anchors: Dict[str, Any]
    news_policy: Dict[str, Any]
    hog_market: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 