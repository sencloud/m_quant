export interface ContractPrice {
  contract: string;
  price: number;
  historicalPrices: {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    contract: string;
  }[];
}

export interface TechnicalIndicators {
  contract: string;
  last_updated: string;
  current_price: number;
  price_targets: {
    support_levels: {
      s1: number;
      s2: number;
    };
    resistance_levels: {
      r1: number;
      r2: number;
    };
    trend: string;
  };
  ema: {
    ema12: number;
    ema26: number;
    trend: string;
  };
  macd: {
    diff: number;
    dea: number;
    bar: number;
    trend: string;
  };
  rsi: {
    value: number;
    trend: string;
  };
  kdj: {
    k: number;
    d: number;
    j: number;
    trend: string;
  };
  bollinger_bands: {
    upper: number;
    middle: number;
    lower: number;
    trend: string;
  };
  volume: {
    current: number;
    change_percent: number;
    trend: string;
  };
}

export interface KlineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface InventoryData {
  date: string;
  value: number;
  mom_change: number;
  yoy_change: number;
}

export interface InventoryResponse {
  status: string;
  data: {
    inventory_list: InventoryData[];
    current_status: {
      value: number;
      status: string;
      mom_change: number;
      yoy_change: number;
    };
  };
}

export interface OptionBasic {
  ts_code: string;
  exchange: string;
  name: string;
  per_unit: string;
  opt_code: string;
  opt_type: string;
  call_put: string;
  exercise_type: string;
  exercise_price: number;
  s_month: string;
  maturity_date: string;
  list_price: number;
  list_date: string;
  delist_date: string;
  last_edate: string;
  last_ddate: string;
  quote_unit: string;
  min_price_chg: string;
  underlying_symbol: string;
}

export interface OptionDaily {
  ts_code: string;
  trade_date: string;
  exchange: string;
  amount: number;
  close: number;
  high: number;
  low: number;
  oi: number;
  open: number;
  pre_close: number | null;
  pre_settle: number;
  settle: number;
  vol: number;
} 