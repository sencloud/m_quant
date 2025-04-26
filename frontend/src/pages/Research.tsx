import React from 'react';
import Layout from '../components/layout/Layout';
import { Link } from 'react-router-dom';
import { BarChartOutlined, LineChartOutlined, FundOutlined } from '@ant-design/icons';

const Research: React.FC = () => {
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

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* 交易策略建议卡片 */}
          <Link to="/research/strategy-advice" className="block">
            <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-300">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                    <BarChartOutlined className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5">
                    <h3 className="text-lg font-medium text-gray-900">交易策略建议</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      基于市场数据的交易策略分析和建议
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Link>

          {/* 核心驱动因子分析卡片 */}
          <Link to="/research/core-factor" className="block">
            <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-300">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                    <LineChartOutlined className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5">
                    <h3 className="text-lg font-medium text-gray-900">核心驱动因子分析</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      豆粕市场核心驱动因子的深度分析
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Link>

          {/* 基本面分析卡片 */}
          <Link to="/research/options-strategy" className="block">
            <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-300">
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                    <FundOutlined className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5">
                    <h3 className="text-lg font-medium text-gray-900">基本面分析</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      基于基本面的豆粕策略分析
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </Layout>
  );
};

export default Research; 