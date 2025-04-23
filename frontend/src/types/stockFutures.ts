export type CompanyInfo = {
  code: string;
  name: string;
  type: 'upstream' | 'midstream' | 'downstream' | 'other';
  description: string;
};

export type StockFuturesData = {
  date: string;
  basis: number;
  crushingProfit: number;
};

export interface SignalCondition {
  type: 'positive' | 'negative' | 'arbitrage';
  description: string;
  triggered: boolean;
  details: {
    condition: string;
    value: number;
    threshold: number;
    met: boolean;
  }[];
}

export interface TradingSignal {
  timestamp: string;
  type: 'positive' | 'negative' | 'arbitrage';
  description: string;
  details?: {
    futuresPrice?: number;
    stockPrice?: number;
    correlation?: number;
    profitMargin?: number;
  };
  conditions?: SignalCondition[];
  recommendation?: {
    futures: {
      direction: 'long' | 'short';
      size: number;
    };
    stocks: {
      code: string;
      direction: 'long' | 'short';
      weight: number;
    }[];
  };
} 