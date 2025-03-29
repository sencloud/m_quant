import React from 'react';
import Layout from '../components/layout/Layout';
import OptionsStrategy from '../components/trading/OptionsStrategy';

const Research: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            研究报告
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            基于 AI 的豆粕市场分析和交易策略研究
          </p>
        </div>
        <OptionsStrategy />
      </div>
    </Layout>
  );
};

export default Research; 