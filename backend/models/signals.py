from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

class SignalType(str, Enum):
    BUY_OPEN = "BUY_OPEN"
    SELL_OPEN = "SELL_OPEN"
    BUY_CLOSE = "BUY_CLOSE"
    SELL_CLOSE = "SELL_CLOSE"

class SignalStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL_CLOSED = "partial_closed"

class SignalBase(BaseModel):
    date: datetime
    symbol: str
    type: SignalType
    price: float
    quantity: int
    status: SignalStatus
    reason: str  # 开平仓原因
    close_date: Optional[datetime] = None
    close_price: Optional[float] = None
    profit: float = 0.0

class SignalCreate(SignalBase):
    pass

class SignalUpdate(BaseModel):
    status: Optional[SignalStatus] = None
    close_date: Optional[datetime] = None
    close_price: Optional[float] = None
    profit: Optional[float] = None
    reason: Optional[str] = None  # 平仓原因

class Signal(SignalBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 