from sqlalchemy import Column, Integer, String, DateTime, Float, func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

Base = declarative_base()

class AccountDB(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    initial_balance = Column(Float, nullable=False, default=1000000.0)  # 初始资金
    current_balance = Column(Float, nullable=False, default=1000000.0)  # 当前资产
    available_balance = Column(Float, nullable=False)
    total_profit = Column(Float, nullable=False, default=0.0)
    total_commission = Column(Float, nullable=False, default=0.0)  # 总手续费
    position_cost = Column(Float, nullable=False, default=0.0)  # 持仓成本
    position_quantity = Column(Integer, nullable=False, default=0)  # 持仓数量
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class AccountBase(BaseModel):
    initial_balance: float
    current_balance: float
    available_balance: float
    total_profit: float
    total_commission: float
    position_cost: float = 0.0  # 持仓成本
    position_quantity: int = 0   # 持仓数量

class AccountCreate(AccountBase):
    pass

class Account(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 