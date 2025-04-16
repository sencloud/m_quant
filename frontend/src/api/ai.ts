import { API_BASE_URL } from '../config/api';
import axios from 'axios';

export interface BacktestRequest {
  tickers: string[];
  start_date: string;
  end_date: string;
  initial_capital?: number;
  portfolio: { [key: string]: number };
  selected_analysts?: string[];
  model_name?: string;
  model_provider?: string;
}

export interface BacktestResponse {
  analysis: {
    decisions: any;
    analyst_signals: any;
  };
  backtest: {
    portfolio_values: number[];
    performance_metrics: {
      total_return: number;
      annualized_return: number;
      sharpe_ratio: number;
      max_drawdown: number;
      volatility: number;
    };
  };
}

export const runBacktest = async (request: BacktestRequest): Promise<BacktestResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/ai/backtest`, request);
    return response.data;
  } catch (error) {
    console.error('Error running backtest:', error);
    throw error;
  }
}; 