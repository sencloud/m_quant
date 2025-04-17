import React, { useState } from 'react';
import Layout from '../components/layout/Layout';
import ETFStrategy from '../components/trading/ETFStrategy';
import FuturesOptionsHedgeStrategy from '../components/trading/FuturesOptionsHedgeStrategy';
import ArbitrageStrategy from '../components/trading/ArbitrageStrategy';
import TrendFollowStrategy from '../components/trading/TrendFollowStrategy';
import OBVADXEMAStrategy from '../components/trading/OBVADXEMAStrategy';
import { ChartBarIcon, ChartPieIcon, ArrowsRightLeftIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface StrategyCardProps {
  title: string;
  tags: Array<{text: string; color: string}>;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const StrategyCard: React.FC<StrategyCardProps> = ({ title, tags, icon, children }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mb-12">
      <div className="bg-white rounded-lg overflow-hidden shadow-sm">
        <div 
          className="px-6 py-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 text-gray-600">
                {icon}
              </div>
              <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <div className="flex gap-2">
                {tags.map((tag, index) => (
                  <span 
                    key={index}
                    className={`px-3 py-1 text-sm font-medium ${tag.color} rounded-full`}
                  >
                    {tag.text}
                  </span>
                ))}
              </div>
              <ChevronDownIcon 
                className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'transform rotate-180' : ''}`}
              />
            </div>
          </div>
        </div>
        <div 
          className={`transition-all duration-300 ease-in-out ${
            isExpanded ? 'max-h-[20000px] opacity-100' : 'max-h-0 opacity-0'
          } overflow-hidden`}
        >
          <div className="p-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

const Trading: React.FC = () => {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            交易策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            探索专业的豆粕交易策略，包括ETF金叉策略、近远月套利策略等
          </p>
        </div>

        <StrategyCard
          title="豆粕近远月套利策略"
          tags={[
            { text: "套利策略", color: "text-indigo-800 bg-indigo-100" },
            { text: "价差交易", color: "text-orange-800 bg-orange-100" },
            { text: "已回测", color: "text-green-800 bg-green-100" }
          ]}
          icon={<ArrowsRightLeftIcon />}
        >
          <ArbitrageStrategy />
        </StrategyCard>
        
        {/* <StrategyCard
          title="豆粕均线趋势跟随策略（以M2501合约为例）"
          tags={[
            { text: "趋势策略", color: "text-blue-800 bg-blue-100" },
            { text: "已回测", color: "text-green-800 bg-green-100" }
          ]}
          icon={<ChartBarIcon />}
        >
          <TrendFollowStrategy />
        </StrategyCard> */}

        <StrategyCard
          title="豆粕ETF（159985）金叉做多策略"
          tags={[
            { text: "技术面策略", color: "text-blue-800 bg-blue-100" },
            { text: "已回测", color: "text-green-800 bg-green-100" }
          ]}
          icon={<ChartPieIcon />}
        >
          <ETFStrategy />
        </StrategyCard>

        

        {/* <StrategyCard
          title="OBV-EMA组合策略"
          tags={[
            { text: "技术面策略", color: "text-blue-800 bg-blue-100" },
            { text: "趋势跟踪", color: "text-purple-800 bg-purple-100" },
            { text: "已回测", color: "text-green-800 bg-green-100" }
          ]}
          icon={<ChartBarIcon />}
        >
          <OBVADXEMAStrategy />
        </StrategyCard> */}

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