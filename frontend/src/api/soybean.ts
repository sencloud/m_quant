import axios from 'axios';
import { API_BASE_URL } from '../config/api';

export interface ComparisonData {
  month: string;
  value: number;
  type: string;
}

export interface PortDistributionData {
  port: string;
  value: number;
  type: string;
}

export interface PortData {
  port: string;
  current: number;
  next_month: number;
  next_two_month: number;
}

export interface CustomsData {
  customs: string;
  current: number;
  next_period: number;
  next_month: number;
  next_two_month: number;
}

export interface SoybeanImportData {
  current_shipment: number;
  current_shipment_yoy: number;
  forecast_shipment: number;
  forecast_shipment_yoy: number;
  current_arrival: number;
  current_arrival_yoy: number;
  next_arrival: number;
  next_arrival_yoy: number;
  monthly_comparison: ComparisonData[];
  port_distribution: PortDistributionData[];
  port_details: PortData[];
  customs_details: CustomsData[];
}

export const fetchSoybeanImportData = async (): Promise<SoybeanImportData> => {
  const response = await axios.get(`${API_BASE_URL}/soybean/import`);
  return response.data;
}; 