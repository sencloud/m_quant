from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

Base = declarative_base()

class PositionDB(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)  # 持仓成本
    quantity = Column(Integer, nullable=False)  # 持仓数量
    status = Column(String, nullable=False, default='open')  # open/closed
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class PositionBase(BaseModel):
    symbol: str
    price: float
    quantity: int
    status: str = 'open'

class PositionCreate(PositionBase):
    pass

class Position(PositionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 