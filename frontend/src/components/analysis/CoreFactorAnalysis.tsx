import React from 'react';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import { Spin } from 'antd';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';

interface InventoryData {
  mom_change: number;
  yoy_change: number;
}

interface CoreFactorData {
  inventory_cycle: {
    current_inventory: {
      value: number;
      unit: string;
      level: string;
      mom_change: number;
      yoy_change: number;
    };
    forecast: {
      arrival: {
        period: string;
        volume: string;
        unit: string;
      };
      turning_point: string;
    };
    impact: string;
  };
  technical_signals: {
    trends: {
      weekly: {
        pattern: string;
        key_levels: {
          support: number[];
          resistance: number[];
        };
      };
      daily: {
        pattern: string;
        key_levels: {
          support: number[];
          resistance: number[];
        };
      };
    };
    volatility: {
      current: number;
      strategy: string;
    };
    signals: {
      trend: string;
      strength: string;
      recommendation: string;
    };
  };
  price_anchors: {
    historical: {
      low: {
        value: number;
        period: string;
      };
      high: {
        value: number;
        period: string;
      };
      average: {
        value: number;
        period: string;
      };
    };
    seasonal: {
      current_period: string;
      probability: number;
      historical_pattern: string;
    };
    current_price: {
      value: number;
      position: string;
    };
  };
  news_policy: {
    positive_factors: Array<{
      event: string;
      impact: string;
      probability: string;
    }>;
    negative_factors: Array<{
      event: string;
      impact: string;
      probability: string;
    }>;
    policy_updates: Array<{
      policy: string;
      content: string;
      impact: string;
    }>;
    key_monitoring: string;
  };
  hog_market: {
    hog_market: {
      inventory: {
        value: number;
        unit: string;
        yoy_change: number;
      };
      price: {
        current: number;
        unit: string;
        trend: string;
      };
    };
    feed_demand: {
      status: string;
      inventory_cycle: string;
    };
    substitution: {
      rapeseed_meal: {
        price_spread: number;
        impact: string;
      };
    };
    outlook: string;
  };
}

const CoreFactorAnalysis: React.FC = () => {
  // 使用新的状态管理API数据
  const [coreFactorData, setCoreFactorData] = React.useState<CoreFactorData | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isExpanded, setIsExpanded] = React.useState(false);

  // 当组件展开时加载数据
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const today = new Date().toISOString().split('T')[0];
        const response = await axios.get(`${API_ENDPOINTS.analysis.coreFactor}/${today}`);
        setCoreFactorData(response.data);
      } catch (err) {
        console.error('获取核心驱动因子数据失败:', err);
        setError('获取数据失败，请稍后重试');
      } finally {
        setLoading(false);
      }
    };

    if (isExpanded && !coreFactorData && !loading) {
      fetchData();
    }
  }, [isExpanded, coreFactorData, loading]);

  return (
    <div className="bg-white rounded-lg overflow-hidden mb-6">
      <div 
        className="p-4 border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors duration-150"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">核心驱动因子分析</h2>
            <p className="text-sm text-gray-500 mt-1">多维度分析豆粕市场核心驱动因素</p>
          </div>
          <svg 
            className={`w-5 h-5 text-gray-500 transform transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      <div className={`transition-all duration-300 ease-in-out ${isExpanded ? 'max-h-[5000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center items-center h-[200px]">
              <Spin size="large" />
            </div>
          ) : error ? (
            <div className="text-center text-red-500 py-4">
              {error}
            </div>
          ) : coreFactorData ? (
            <>
              {/* 库存周期验证 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  库存周期验证
                </h3>
                <div className="space-y-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="space-y-2 text-sm text-gray-600">
                      <p>• 当前库存水平：{coreFactorData.inventory_cycle.current_inventory.value} {coreFactorData.inventory_cycle.current_inventory.unit}，处于{coreFactorData.inventory_cycle.current_inventory.level}。</p>
                      <p>• 库存拐点预判：{coreFactorData.inventory_cycle.forecast.turning_point}</p>
                    </div>
                    <div className="mt-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-500">最近库存变化</span>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm">
                            环比: <span className={coreFactorData.inventory_cycle.current_inventory.mom_change >= 0 ? "text-red-500" : "text-green-500"}>
                              {coreFactorData.inventory_cycle.current_inventory.mom_change >= 0 ? "+" : ""}{coreFactorData.inventory_cycle.current_inventory.mom_change}%
                            </span>
                          </span>
                          <span className="text-sm">
                            同比: <span className={coreFactorData.inventory_cycle.current_inventory.yoy_change >= 0 ? "text-red-500" : "text-green-500"}>
                              {coreFactorData.inventory_cycle.current_inventory.yoy_change >= 0 ? "+" : ""}{coreFactorData.inventory_cycle.current_inventory.yoy_change}%
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 技术面信号 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  技术面信号
                </h3>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• 周线趋势：{coreFactorData.technical_signals.trends.weekly.pattern}</p>
                    <p>• 日线关键位：支撑位 {coreFactorData.technical_signals.trends.daily.key_levels.support.join('、')}元；压力位 {coreFactorData.technical_signals.trends.daily.key_levels.resistance.join('、')}元</p>
                    <p>• 波动率策略：{coreFactorData.technical_signals.volatility.strategy}</p>
                  </div>
                </div>
              </div>

              {/* 历史价格锚定 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  历史价格锚定
                </h3>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• {coreFactorData.price_anchors.historical.low.period}低位均值：{coreFactorData.price_anchors.historical.low.value}元/吨</p>
                    <p>• 当前价格：{coreFactorData.price_anchors.current_price.value}元/吨，{coreFactorData.price_anchors.current_price.position}</p>
                    <p>• 季节性规律：{coreFactorData.price_anchors.seasonal.current_period}，上涨概率{coreFactorData.price_anchors.seasonal.probability}%</p>
                  </div>
                </div>
              </div>

              {/* 资讯与政策扰动 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  资讯与政策扰动
                </h3>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="space-y-2 text-sm text-gray-600">
                    {coreFactorData.news_policy.positive_factors.map((factor, index) => (
                      <p key={`pos-${index}`}>• 利多：{factor.event}（影响：{factor.impact}，概率：{factor.probability}）</p>
                    ))}
                    {coreFactorData.news_policy.negative_factors.map((factor, index) => (
                      <p key={`neg-${index}`}>• 利空：{factor.event}（影响：{factor.impact}，概率：{factor.probability}）</p>
                    ))}
                    <p>• 重点关注：{coreFactorData.news_policy.key_monitoring}</p>
                  </div>
                </div>
              </div>

              {/* 生猪市场联动 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  生猪市场联动
                </h3>
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• 生猪存栏：{coreFactorData.hog_market.hog_market.inventory.value}{coreFactorData.hog_market.hog_market.inventory.unit}（同比{coreFactorData.hog_market.hog_market.inventory.yoy_change >= 0 ? "+" : ""}{coreFactorData.hog_market.hog_market.inventory.yoy_change}%）</p>
                    <p>• 生猪价格：{coreFactorData.hog_market.hog_market.price.current}{coreFactorData.hog_market.hog_market.price.unit}（{coreFactorData.hog_market.hog_market.price.trend}）</p>
                    <p>• 饲料需求：{coreFactorData.hog_market.feed_demand.status}</p>
                    <p>• 豆菜价差：{coreFactorData.hog_market.substitution.rapeseed_meal.price_spread}元/吨，{coreFactorData.hog_market.substitution.rapeseed_meal.impact}</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center text-gray-500 py-4">
              暂无核心驱动因子数据
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoreFactorAnalysis; 