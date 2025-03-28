from pydantic import BaseModel
from typing import List, Dict

class StrategyDetails(BaseModel):
    entry_points: List[str]
    exit_points: List[str]
    risk_management: List[str]

class OptionsStrategy(BaseModel):
    id: str
    title: str
    description: str
    risk_level: str
    expected_return: str
    time_horizon: str
    strategy_details: StrategyDetails 