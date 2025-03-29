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