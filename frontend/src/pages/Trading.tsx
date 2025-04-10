import React from 'react';
import Layout from '../components/layout/Layout';
import ETFStrategy from '../components/trading/ETFStrategy';
import FuturesOptionsHedgeStrategy from '../components/trading/FuturesOptionsHedgeStrategy';
import ArbitrageStrategy from '../components/trading/ArbitrageStrategy';

const Trading: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            交易策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            探索专业的豆粕交易策略，包括ETF金叉策略、期货期权对冲策略和近远月套利策略
          </p>
        </div>

        {/* ETF策略部分 */}
        <div className="mb-12">
          <div className="bg-white rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <h2 className="text-xl font-semibold text-gray-900">豆粕ETF金叉做多策略</h2>
                <div className="ml-auto flex gap-2">
                  <span className="px-3 py-1 text-sm font-medium text-blue-800 bg-blue-100 rounded-full">
                    技术面策略
                  </span>
                  <span className="px-3 py-1 text-sm font-medium text-green-800 bg-green-100 rounded-full">
                    已回测
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              <ETFStrategy />
            </div>
          </div>
        </div>

        {/* 近远月套利策略部分 */}
        <div className="mb-12">
          <div className="bg-white rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <h2 className="text-xl font-semibold text-gray-900">豆粕近远月套利策略</h2>
                <div className="ml-auto flex gap-2">
                  <span className="px-3 py-1 text-sm font-medium text-indigo-800 bg-indigo-100 rounded-full">
                    套利策略
                  </span>
                  <span className="px-3 py-1 text-sm font-medium text-orange-800 bg-orange-100 rounded-full">
                    价差交易
                  </span>
                  <span className="px-3 py-1 text-sm font-medium text-green-800 bg-green-100 rounded-full">
                    已回测
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              <ArbitrageStrategy />
            </div>
          </div>
        </div>

        {/* 期货期权对冲策略部分 */}
        {/* <div className="mb-12">
          <div className="bg-white rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <h2 className="text-xl font-semibold text-gray-900">豆粕期货期权对冲策略</h2>
                <div className="ml-auto flex gap-2">
                  <span className="px-3 py-1 text-sm font-medium text-purple-800 bg-purple-100 rounded-full">
                    期权策略
                  </span>
                  <span className="px-3 py-1 text-sm font-medium text-amber-800 bg-amber-100 rounded-full">
                    对冲风险
                  </span>
                </div>
              </div>
            </div>
            <div className="p-6">
              <FuturesOptionsHedgeStrategy />
            </div>
          </div>
        </div> */}
      </div>
    </Layout>
  );
};

export default Trading; 