import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import OptionsStrategy from '../components/trading/OptionsStrategy';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

const OptionsStrategyPage: React.FC = () => {
  const minDate = "2025-04-10";
  const today = new Date().toISOString().split('T')[0];
  const initialDate = today < minDate ? minDate : today;
  
  const [selectedDate, setSelectedDate] = useState<string>(initialDate);
  const [isLoading, setIsLoading] = useState(false);
  const [fundamentalData, setFundamentalData] = useState(null);

  // 获取基本面数据
  const fetchFundamentalData = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_ENDPOINTS.analysis.fundamental}`, {
        params: { date: selectedDate }
      });
      setFundamentalData(response.data);
    } catch (error) {
      console.error('获取基本面数据失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 页面加载时调用一次获取基本面数据
  useEffect(() => {
    fetchFundamentalData();
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            基本面分析
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            基于基本面的豆粕策略分析
          </p>
        </div>

        {/* 日期选择和查看分析按钮 */}
        <div className="bg-white border rounded-lg p-6 mb-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label htmlFor="date" className="block text-sm font-medium text-gray-700">
                选择日期
              </label>
              <input
                type="date"
                id="date"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min={minDate}
                max={today}
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={fetchFundamentalData}
                disabled={isLoading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isLoading ? '加载中...' : '查看分析'}
              </button>
            </div>
          </div>
        </div>
        
        <OptionsStrategy selectedDate={selectedDate} fundamentalData={fundamentalData} />
      </div>
    </Layout>
  );
};

export default OptionsStrategyPage; 