from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import date

class FuturesData(BaseModel):
    ts_code: str
    trade_date: str
    pre_close: float
    pre_settle: float
    open: float
    high: float
    low: float
    close: float
    settle: float
    change1: float
    change2: float
    vol: float
    amount: float
    oi: float
    oi_chg: float
    contract: str
    price: float
    historicalPrices: List[dict] = Field(default_factory=list)
    volume: Optional[float] = None

class ETFData(BaseModel):
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    vol: float
    amount: float
    ma5: float
    ma8: float
    atr: float
    signal: Optional[str] = None  # 'buy', 'sell', 'hold'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    last_signal: Optional[str] = None  # 上一个有效信号
    last_signal_date: Optional[str] = None  # 信号触发时间
    last_signal_price: Optional[float] = None  # 信号触发价格
    last_stop_loss: Optional[float] = None  # 上一个止损价格
    last_take_profit: Optional[float] = None  # 上一个止盈价格

class OptionsData(BaseModel):
    ts_code: str
    name: str
    underlying: str
    exchange: str
    call_put: str
    exercise_price: float
    exercise_date: date
    list_date: date
    delist_date: Optional[date]

class InventoryData(BaseModel):
    date: str
    value: float
    mom_change: float  # 环比变化
    yoy_change: float  # 同比变化

class TechnicalIndicators(BaseModel):
    contract: str
    last_updated: str
    current_price: float
    price_targets: dict
    ema: dict
    macd: dict
    rsi: dict
    kdj: dict
    bollinger_bands: dict
    volume: dict

class OptionsHedgeData(BaseModel):
    ts_code: str
    trade_date: str
    futures_price: float
    options_price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    hedge_ratio: float
    pl: float
    cumulative_pl: float
    signal: str
    volatility: float
    risk_exposure: Optional[float] = None

class OptionBasic(BaseModel):
    ts_code: str
    name: str
    exercise_price: float
    maturity_date: str
    call_put: str
    exchange: str = 'DCE'  # 默认为大连商品交易所
    opt_code: Optional[str] = None  # 标准期权代码
    underlying_code: Optional[str] = None  # 标的代码

class OptionDaily(BaseModel):
    ts_code: str
    trade_date: str
    exchange: str = 'DCE'  # 默认为大连商品交易所
    pre_settle: Optional[float] = None
    pre_close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    settle: Optional[float] = None
    vol: Optional[float] = None
    amount: Optional[float] = None
    oi: Optional[float] = None

class CostComparisonData(BaseModel):
    date: str
    cost: float  # 豆粕成本价
    futures_price: float  # 主力合约价格
    price_diff: float  # 价差
    price_ratio: float  # 价格比

class KlineData(BaseModel):
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    vol: float

class HistoricalBottom(BaseModel):
    start_date: str
    end_date: str
    duration: int
    bounce_amplitude: float
    lowest_price: float
    contract: str
    kline_data: Optional[List[KlineData]]

class ContractStats(BaseModel):
    contract: str
    lowest_price: float
    highest_price: float
    price_range: float
    start_price: float
    end_price: float
    volatility_30d: float  # 30日波动率
    quantile_coef: float  # 新增：分位系数 = 最低价/开始价格

class PriceRangeAnalysis(BaseModel):
    bottom_price: float
    current_price: float
    bottom_range_start: float
    bottom_range_end: float
    bounce_success_rate: float
    avg_bounce_amplitude: float
    avg_bottom_duration: float
    historical_bottoms: List[HistoricalBottom]
    contract_stats: List[ContractStats]
    price_quartiles: dict = Field(  # 新增：价格分位数
        default_factory=lambda: {
            'q1': 0.0,
            'q2': 0.0,
            'q3': 0.0
        }
    )
    volatility_quartiles: dict = Field(  # 新增：波动率分位数
        default_factory=lambda: {
            'q1': 0.0,
            'q2': 0.0,
            'q3': 0.0
        }
    ) 