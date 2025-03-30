import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import OptionsStrategy from '../components/trading/OptionsStrategy';
import CoreFactorAnalysis from '../components/analysis/CoreFactorAnalysis';
import StrategyAdvice from '../components/trading/StrategyAdvice';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

interface StrategyResponse {
  content: string;
  reasoning_content: string;
}

const Research: React.FC = () => {
  const minDate = "2025-03-28";
  const today = new Date().toISOString().split('T')[0];
  const initialDate = today < minDate ? minDate : today;
  
  const [selectedDate, setSelectedDate] = useState<string>(initialDate);
  const [isLoading, setIsLoading] = useState(false);
  const [strategyData, setStrategyData] = useState<StrategyResponse | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [fundamentalData, setFundamentalData] = useState(null);

  // 获取基本面数据
  const fetchFundamentalData = async () => {
    try {
      const response = await axios.get(`${API_ENDPOINTS.analysis.fundamental}`, {
        params: { date: selectedDate }
      });
      setFundamentalData(response.data);
    } catch (error) {
      console.error('获取基本面数据失败:', error);
    }
  };

  const handleViewAnalysis = async () => {
    setIsLoading(true);
    setIsStreaming(false);
    setStrategyData(null);

    // 同时获取基本面数据
    await fetchFundamentalData();

    try {
      const response = await fetch(`${API_ENDPOINTS.trading.options}?date=${selectedDate}`);
      
      // 检查响应类型
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/event-stream')) {
        // 处理流式响应
        setIsStreaming(true);
        const reader = response.body?.getReader();
        if (!reader) throw new Error('无法读取响应流');
        
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'reasoning') {
                setStrategyData(prev => ({ 
                  reasoning_content: data.content,
                  content: prev?.content || ''
                }));
              } else if (data.type === 'content') {
                setStrategyData(prev => ({ 
                  content: data.content,
                  reasoning_content: prev?.reasoning_content || ''
                }));
              } else if (data.type === 'done') {
                setIsLoading(false);
                setIsStreaming(false);
              } else if (data.type === 'error') {
                console.error('获取策略分析失败:', data.message);
                setIsLoading(false);
                setIsStreaming(false);
              }
            }
          }
        }
      } else {
        // 处理普通响应
        const data = await response.json();
        setStrategyData({
          content: data.content,
          reasoning_content: data.reasoning_content
        });
        setIsLoading(false);
      }
    } catch (error) {
      console.error('获取策略分析失败:', error);
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  // 页面加载时调用一次查看报告接口
  useEffect(() => {
    handleViewAnalysis();
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            研究报告
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            基于 DeepSeek 的豆粕市场分析和交易策略研究
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
                onClick={handleViewAnalysis}
                disabled={isLoading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isLoading ? '加载中...' : '查看报告'}
              </button>
            </div>
          </div>
        </div>
        
        <StrategyAdvice strategyData={strategyData} isStreaming={isStreaming} />
        <CoreFactorAnalysis />
        <OptionsStrategy selectedDate={selectedDate} fundamentalData={fundamentalData} />
        
      </div>
    </Layout>
  );
};

export default Research; 