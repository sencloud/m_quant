import { API_BASE_URL } from '../config/api';
import axios from 'axios';

export interface Signal {
  id: number;
  date: string;
  symbol: string;
  symbol_type: string;
  type: 'buy' | 'sell';
  price: number;
  quantity: number;
  status: 'open' | 'closed';
  reason: string;
  close_date?: string;
  close_price?: number;
  profit: number;
  created_at: string;
  updated_at: string;
}

export interface SignalCreate {
  date: string;
  symbol: string;
  symbol_type: string;
  type: 'buy' | 'sell';
  price: number;
  quantity: number;
  status: 'open' | 'closed';
  reason: string;
  close_date?: string;
  close_price?: number;
  profit: number;
}

export interface SignalUpdate {
  status?: 'open' | 'closed';
  close_date?: string;
  close_price?: number;
  profit?: number;
}

export interface SignalResponse {
  signals: Signal[];
}

export const getSignals = async (
  startDate: string,
  endDate: string,
  type?: string
): Promise<SignalResponse> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/signals`, {
      params: {
        start_date: startDate,
        end_date: endDate,
        type
      }
    });
    return response.data;
  } catch (error) {
    console.error('获取信号失败:', error);
    throw error;
  }
};

export const createSignal = async (signal: SignalCreate): Promise<Signal> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/signals`, signal);
    return response.data;
  } catch (error) {
    console.error('创建信号失败:', error);
    throw error;
  }
};

export const updateSignal = async (signalId: string, signal: SignalUpdate): Promise<Signal> => {
  try {
    const response = await axios.put(`${API_BASE_URL}/signals/${signalId}`, signal);
    return response.data;
  } catch (error) {
    console.error('更新信号失败:', error);
    throw error;
  }
};

export const deleteSignal = async (signalId: string): Promise<void> => {
  try {
    await axios.delete(`${API_BASE_URL}/signals/${signalId}`);
  } catch (error) {
    console.error('删除信号失败:', error);
    throw error;
  }
}; 