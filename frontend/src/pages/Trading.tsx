import React from 'react';
import Layout from '../components/layout/Layout';
import ETFStrategy from '../components/trading/ETFStrategy';
import OptionsStrategy from '../components/trading/OptionsStrategy';

const Trading: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            交易策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            探索专业的豆粕交易策略，包括ETF金叉策略和AI驱动的期权策略
          </p>
        </div>

        {/* ETF策略部分 */}
        <div className="mb-12">
          <div className="bg-white rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">豆粕ETF金叉策略</h2>
                <span className="px-3 py-1 text-sm font-medium text-blue-800 bg-blue-100 rounded-full">
                  技术分析
                </span>
              </div>
            </div>
            <div className="p-6">
              <ETFStrategy />
            </div>
          </div>
        </div>

        {/* 期权策略部分 */}
        <div>
          <div className="bg-white rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">期货期权策略</h2>
                <span className="px-3 py-1 text-sm font-medium text-purple-800 bg-purple-100 rounded-full">
                  AI驱动
                </span>
              </div>
            </div>
            <div className="p-6">
              <OptionsStrategy />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Trading; 