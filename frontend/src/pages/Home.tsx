import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';
import Layout from '../components/layout/Layout';
import MarketOverview from '../components/market/MarketOverview';
import PriceChart from '../components/market/PriceChart';
import TechnicalChart from '../components/market/TechnicalChart';
import TechnicalIndicators from '../components/market/TechnicalIndicators';
import InventoryChart from '../components/market/InventoryChart';
import { ContractPrice, TechnicalIndicators as TechnicalIndicatorsType, InventoryData } from '../types/market';

const Home: React.FC = () => {
  // 获取期货数据
  const { data: futuresData } = useQuery<ContractPrice[]>({
    queryKey: ['futuresData'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.futures);
      return response.data;
    }
  });

  // 获取库存数据
  const { data: inventoryData } = useQuery<InventoryData[]>({
    queryKey: ['inventoryData'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.inventory);
      return response.data;
    }
  });

  // 获取技术分析数据
  const { data: technicalData } = useQuery<TechnicalIndicatorsType>({
    queryKey: ['technicalIndicators'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.technical);
      return response.data;
    }
  });

  // 获取默认合约（豆粕）
  const defaultContract = futuresData?.[0]?.historicalPrices ? futuresData[0] : null;

  return (
    <Layout>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              豆粕品种量化交易策略平台
            </h1>
            <p className="mt-3 max-w-md mx-auto text-base sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
              提供全方位的市场数据分析、技术分析和交易策略服务，助力您的投资决策。
            </p>
            <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
              <div className="rounded-md shadow">
                <a
                  href="#market-data"
                  className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
                >
                  探索
                </a>
              </div>
              <div className="mt-3 sm:mt-0 sm:ml-3">
                <a
                  href="#learn-more"
                  className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-500 hover:bg-blue-600 md:py-4 md:text-lg md:px-10"
                >
                  了解更多
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">核心功能</h2>
            <p className="mt-4 text-lg text-gray-500">
              为您提供全方位的量化交易解决方案
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-blue-600 mb-4">
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">市场数据分析</h3>
              <p className="text-gray-500">
                提供全面的市场数据分析，包括价格走势、成交量、持仓量等关键指标。
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-blue-600 mb-4">
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">技术分析</h3>
              <p className="text-gray-500">
                支持多种技术分析指标，帮助您更好地把握市场趋势。
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-blue-600 mb-4">
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">品种组合</h3>
              <p className="text-gray-500">
                提供ETF、期货、期权等多种品种组合策略，支持策略回测。
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Market Data Section */}
      <section id="market-data" className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">市场数据</h2>
            <p className="mt-4 text-lg text-gray-500">
              实时获取豆粕期货市场数据，掌握市场动态
            </p>
          </div>

          {/* 市场概览 */}
          <div className="mb-8">
            <MarketOverview />
          </div>

          {/* 价格图表 */}
          {defaultContract && defaultContract.historicalPrices && (
            <div className="mb-8">
              <PriceChart contract={defaultContract} />
            </div>
          )}

          {/* 技术分析图表 */}
          {defaultContract && defaultContract.historicalPrices && technicalData && (
            <div className="mb-8">
              <TechnicalChart technicalData={technicalData} contract={defaultContract} />
            </div>
          )}

          {/* 技术分析指标 */}
          {technicalData && (
            <div className="mb-8">
              <TechnicalIndicators data={technicalData} />
            </div>
          )}

          {/* 库存图表 */}
          {inventoryData && (
            <div className="mb-8">
              <InventoryChart data={inventoryData} />
            </div>
          )}
        </div>
      </section>
    </Layout>
  );
};

export default Home; 