import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';

interface MarketData {
  trade_date: string;
  close: number;
  change1: number;
  vol: number;
  amount: number;
}

const MarketOverview: React.FC = () => {
  const { data: marketData } = useQuery<MarketData[]>({
    queryKey: ['marketData'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.futures);
      return response.data;
    }
  });

  const latestData = marketData?.[marketData.length - 1];
  const pctChange = latestData?.change1 ?? 0;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">市场概览</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-500">最新价格</p>
          <p className="text-2xl font-bold text-gray-900">
            ¥{latestData?.close?.toFixed(2) ?? '0.00'}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-500">涨跌额（收盘价-昨结算价）</p>
          <p className={`text-2xl font-bold ${pctChange < 0 ? 'text-green-600' : 'text-red-600'}`}>
            {pctChange}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-500">成交量</p>
          <p className="text-2xl font-bold text-gray-900">
            {(latestData?.vol ?? 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-sm text-gray-500">成交额（万）</p>
          <p className="text-2xl font-bold text-gray-900">
            ¥{(latestData?.amount ?? 0).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview; 