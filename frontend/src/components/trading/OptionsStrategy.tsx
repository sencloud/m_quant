import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Components } from 'react-markdown';

interface StrategyResponse {
  content: string;
  reasoning_content: string;
}

interface WeatherRegion {
  name: string;
  condition: string;
}

interface WeatherData {
  regions: WeatherRegion[];
  overall: string;
  status_type: 'warning' | 'danger' | 'success' | 'neutral';
}

interface CrushProfitRegion {
  name: string;
  soybean_cost: number;
  soymeal_price: number;
  soyoil_price: number;
  profit: number;
  weekly_change: number;
}

interface FundamentalData {
  supply_demand: {
    global_soybean_production: {
      value: number;
      unit: string;
      yoy: number;
    };
    global_soymeal_production: {
      value: number;
      unit: string;
      yoy: number;
    };
    china_soymeal_consumption: {
      value: number;
      unit: string;
      yoy: number;
    };
    global_soybean_inventory: {
      value: number;
      unit: string;
      inventory_ratio: number;
    };
    summary: string;
  };
  seasonal: {
    data: Array<{
      period: string;
      pattern: string;
      factors: string;
      status: string;
      status_type: 'positive' | 'negative' | 'neutral';
    }>;
  };
  weather: {
    brazil: WeatherData;
    argentina: WeatherData;
    others: WeatherData;
    summary: string;
  };
  crush_profit: {
    regions: CrushProfitRegion[];
    summary: string;
  };
  overall: {
    rating: {
      level: string;
      score: number;
    };
    analysis: {
      short_term: string;
      medium_term: string;
      long_term: string;
    };
  };
}

interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  [key: string]: any;
}

interface OptionsStrategyProps {
  selectedDate: string;
  fundamentalData: FundamentalData | null;
}

const OptionsStrategy: React.FC<OptionsStrategyProps> = ({ selectedDate, fundamentalData }) => {
  const [strategyData, setStrategyData] = useState<StrategyResponse | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [isFundamentalExpanded, setIsFundamentalExpanded] = useState(true);

  const handleViewAnalysis = async () => {
    setIsStreaming(false);
    setShowReasoning(false);
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
                setIsStreaming(false);
              } else if (data.type === 'error') {
                console.error('获取策略分析失败:', data.message);
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
      }
    } catch (error) {
      console.error('获取策略分析失败:', error);
      setIsStreaming(false);
    }
  };

  const renderFundamentalLoading = () => (
    <div className="flex items-center justify-center py-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
    </div>
  );

  const renderSupplyDemand = () => {
    if (!fundamentalData?.supply_demand) {
      console.log('Supply demand data is missing');
      return null;
    }

    const data = fundamentalData.supply_demand;

    // 检查必要的字段是否存在
    if (!data.global_soybean_production?.value ||
        !data.global_soymeal_production?.value ||
        !data.china_soymeal_consumption?.value ||
        !data.global_soybean_inventory?.value) {
      console.log('Missing required supply demand fields:', data);
      return null;
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-500">全球大豆产量</h4>
          <div className="mt-2 flex justify-between items-end">
            <div className="text-2xl font-bold text-gray-900">{data.global_soybean_production.value}</div>
            <div className="text-sm text-gray-500">{data.global_soybean_production.unit}</div>
          </div>
          <div className={`mt-1 text-sm ${data.global_soybean_production.yoy >= 0 ? 'text-red-600' : 'text-green-600'}`}>
            同比{data.global_soybean_production.yoy >= 0 ? '+' : ''}{data.global_soybean_production.yoy}%
          </div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-500">全球豆粕产量</h4>
          <div className="mt-2 flex justify-between items-end">
            <div className="text-2xl font-bold text-gray-900">{data.global_soymeal_production.value}</div>
            <div className="text-sm text-gray-500">{data.global_soymeal_production.unit}</div>
          </div>
          <div className={`mt-1 text-sm ${data.global_soymeal_production.yoy >= 0 ? 'text-red-600' : 'text-green-600'}`}>
            同比{data.global_soymeal_production.yoy >= 0 ? '+' : ''}{data.global_soymeal_production.yoy}%
          </div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-500">中国豆粕消费量</h4>
          <div className="mt-2 flex justify-between items-end">
            <div className="text-2xl font-bold text-gray-900">{data.china_soymeal_consumption.value}</div>
            <div className="text-sm text-gray-500">{data.china_soymeal_consumption.unit}</div>
          </div>
          <div className={`mt-1 text-sm ${data.china_soymeal_consumption.yoy >= 0 ? 'text-red-600' : 'text-green-600'}`}>
            同比{data.china_soymeal_consumption.yoy >= 0 ? '+' : ''}{data.china_soymeal_consumption.yoy}%
          </div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-500">全球大豆库存</h4>
          <div className="mt-2 flex justify-between items-end">
            <div className="text-2xl font-bold text-gray-900">{data.global_soybean_inventory.value}</div>
            <div className="text-sm text-gray-500">{data.global_soybean_inventory.unit}</div>
          </div>
          <div className="mt-1 text-sm text-gray-500">
            库存比{data.global_soybean_inventory.inventory_ratio}%
          </div>
        </div>
      </div>
    );
  };

  const renderSeasonalPattern = () => {
    if (!fundamentalData?.seasonal?.data) {
      console.log('Seasonal data is missing');
      return null;
    }

    return (
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时段</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">典型表现</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">影响因素</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">当前状态</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {fundamentalData.seasonal.data.map((item: any, index: number) => (
              <tr key={index}>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{item.period}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{item.pattern}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.factors}</td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    item.status_type === 'positive' ? 'bg-green-100 text-green-800' :
                    item.status_type === 'negative' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderWeatherConditions = () => {
    if (!fundamentalData?.weather) {
      console.log('Weather data is missing');
      return null;
    }

    const weather = fundamentalData.weather;

    // 检查必要的字段是否存在
    if (!weather.brazil || !weather.argentina || !weather.others) {
      console.log('Missing required weather regions:', weather);
      return null;
    }

    const getStatusColor = (status_type: string) => {
      switch (status_type) {
        case 'warning': return 'bg-yellow-100 text-yellow-800';
        case 'danger': return 'bg-red-100 text-red-800';
        case 'success': return 'bg-green-100 text-green-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    };

    const regions = ['brazil', 'argentina', 'others'] as const;

    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {regions.map((region) => (
          <div key={region} className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-blue-50 px-4 py-2 border-b border-gray-200">
              <h4 className="font-medium text-gray-900">
                {region === 'brazil' ? '巴西主产区' : 
                 region === 'argentina' ? '阿根廷主产区' : 
                 '巴拉圭/乌拉圭'}
              </h4>
            </div>
            <div className="p-4">
              {weather[region].regions.map((item, index) => (
                <div key={index} className="flex items-center mb-2">
                  <span className="text-sm font-medium text-gray-500 w-24">{item.name}:</span>
                  <span className="text-sm text-gray-700">{item.condition}</span>
                </div>
              ))}
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-500 w-24">整体评估:</span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(weather[region].status_type)}`}>
                  {weather[region].overall}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderCrushProfit = () => {
    if (!fundamentalData?.crush_profit?.regions) {
      console.log('Crush profit data is missing or invalid:', fundamentalData?.crush_profit);
      return null;
    }

    const data = fundamentalData.crush_profit;

    return (
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">地区</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">大豆成本</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">豆粕售价</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">豆油售价</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">压榨利润</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">周环比</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.regions.map((region: CrushProfitRegion, index: number) => (
              <tr key={index}>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{region.name}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 text-right">{region.soybean_cost}元/吨</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 text-right">{region.soymeal_price}元/吨</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 text-right">{region.soyoil_price}元/吨</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">{region.profit}元/吨</td>
                <td className="px-4 py-3 whitespace-nowrap text-center">
                  <span className={region.weekly_change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {region.weekly_change >= 0 ? '+' : ''}{region.weekly_change}元
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderOverallAssessment = () => {
    if (!fundamentalData?.overall) {
      console.log('Overall assessment data is missing');
      return null;
    }

    const assessment = fundamentalData.overall;

    return (
      <div className="space-y-4">
        {/* 多空评级 */}
        <div className="bg-indigo-50 rounded-lg p-4">
          <div className="mb-4">
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">多空评级</span>
              <span className="text-sm font-medium text-gray-700">{assessment.rating.level}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-green-600 h-2.5 rounded-full" 
                style={{ width: `${assessment.rating.score}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>看空</span>
              <span>中性</span>
              <span>看多</span>
            </div>
          </div>
        </div>

        {/* 市场展望 */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">市场展望</h4>
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              <span className="font-medium">短期(1-2周)：</span>
              {assessment.analysis.short_term}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">中期(1-2月)：</span>
              {assessment.analysis.medium_term}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">远期(3-6月)：</span>
              {assessment.analysis.long_term}
            </p>
          </div>
        </div>
      </div>
    );
  };

  const markdownComponents: Components = {
    code({ node, inline, className, children, ...props }: CodeProps) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={vscDarkPlus as any}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className="bg-gray-100 dark:bg-gray-800 rounded px-1 py-0.5" {...props}>
          {children}
        </code>
      );
    },
    h1: ({ children }) => <h1 className="text-2xl font-bold mb-4">{children}</h1>,
    h2: ({ children }) => <h2 className="text-xl font-bold mb-3">{children}</h2>,
    h3: ({ children }) => <h3 className="text-lg font-medium text-gray-900 mb-2">{children}</h3>,
    p: ({ children }) => <p className="mb-4 leading-relaxed">{children}</p>,
    ul: ({ children }) => <ul className="list-disc pl-6 mb-4">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-6 mb-4">{children}</ol>,
    li: ({ children }) => <li className="mb-2">{children}</li>,
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 italic my-4">
        {children}
      </blockquote>
    ),
    table: ({ children }) => (
      <div className="overflow-x-auto mb-4">
        <table className="min-w-full divide-y divide-gray-200">
          {children}
        </table>
      </div>
    ),
    th: ({ children }) => (
      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {children}
      </td>
    ),
  };

  return (
    <div className="space-y-6">
      {/* 基本面分析区域 */}
      <div className="bg-white rounded-lg overflow-hidden mb-6">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">基本面分析</h2>
              <p className="text-sm text-gray-500 mt-1">多维度分析豆粕市场基本面情况</p>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          {!fundamentalData ? (
            <div className="text-center text-gray-500 py-4">暂无数据</div>
          ) : (
            <>
              {/* 供需平衡 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  供需平衡情况
                </h3>
                {renderSupplyDemand()}
                {fundamentalData?.supply_demand && (
                  <div className="mt-4 p-3 border border-blue-100 rounded-lg bg-blue-50">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">供需评估：</span>
                      {fundamentalData.supply_demand.summary}
                    </p>
                  </div>
                )}
              </div>
              
              {/* 季节性规律 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  季节性规律
                </h3>
                {renderSeasonalPattern()}
              </div>
              
              {/* 南美天气 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                  </svg>
                  南美天气状况
                </h3>
                {renderWeatherConditions()}
                {fundamentalData?.weather && (
                  <div className="mt-4 p-3 border border-yellow-100 rounded-lg bg-yellow-50">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">天气影响评估：</span>
                      {fundamentalData.weather.summary}
                    </p>
                  </div>
                )}
              </div>
              
              {/* 加工利润 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  豆粕压榨利润
                </h3>
                {renderCrushProfit()}
                {fundamentalData?.crush_profit && (
                  <div className="mt-4 p-3 border border-red-100 rounded-lg bg-red-50">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">压榨利润评估：</span>
                      {fundamentalData.crush_profit.summary}
                    </p>
                  </div>
                )}
              </div>
              
              {/* 基本面综合评估 */}
              <div>
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  基本面综合评估
                </h3>
                {renderOverallAssessment()}
              </div>
            </>
          )}
        </div>
      </div>

      {/* 策略内容 */}
      {strategyData && (
        <div className="space-y-4">
          {/* 最终回答 */}
          <div className="bg-white border rounded-lg p-6 relative">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-medium text-gray-900">策略建议</h3>
              {!isStreaming && strategyData?.reasoning_content && (
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {showReasoning ? '收起思维链' : '查看思维链'}
                </button>
              )}
            </div>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {strategyData?.content || ''}
              </ReactMarkdown>
            </div>
            
            {/* 思维链分析 */}
            {!isStreaming && strategyData?.reasoning_content && (
              <div className={`mt-4 transition-all duration-300 ease-in-out overflow-hidden ${
                showReasoning ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
              }`}>
                <div className="border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">思维链分析</h4>
                  <div className="prose prose-sm max-w-none text-gray-500">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {strategyData?.reasoning_content || ''}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OptionsStrategy; 