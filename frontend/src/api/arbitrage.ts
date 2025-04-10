import axios from 'axios';
import { API_BASE_URL } from '../config/api';

export interface SpreadData {
  date: string;
  spread: number;
}

export const getSpreadData = async (
  startDate?: string,
  endDate?: string,
  nearContract: string = 'M2509',
  farContract: string = 'M2601'
): Promise<SpreadData[]> => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  params.append('near_contract', nearContract);
  params.append('far_contract', farContract);

  const response = await axios.get(`${API_BASE_URL}/arbitrage/spread?${params.toString()}`);
  return response.data;
}; 