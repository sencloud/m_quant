from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class KLineData(BaseModel):
    date: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    ema5: float
    ema20: float
    open_interest: float

class SignalRequest(BaseModel):
    start_date: str
    end_date: str
    type: Optional[str] = None
    page: int = 1
    page_size: int = 10
    klines: List[KLineData] 