import React from 'react';
import Layout from '../components/layout/Layout';
import ETFStrategy from '../components/trading/ETFStrategy';

const Trading: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            交易策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            探索专业的豆粕交易策略，包括ETF金叉策略
          </p>
        </div>

        {/* ETF策略部分 */}
        <div className="mb-12">
          <div className="bg-white rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <h2 className="text-xl font-semibold text-gray-900">豆粕ETF金叉策略</h2>
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
            <div className="p-1">
              <ETFStrategy />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Trading; 