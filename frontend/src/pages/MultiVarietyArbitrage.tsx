import React, { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import Layout from '../components/layout/Layout';
import Toast from '../components/Toast';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const MultiVarietyArbitrage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [isRealtime, setIsRealtime] = useState(false);
  const [activeTab, setActiveTab] = useState('1');
  const [oilMealRatio, setOilMealRatio] = useState<number>(2.29);
  const [crushingMargin, setCrushingMargin] = useState<number>(240);
  const [historicalAverage, setHistoricalAverage] = useState<number>(150);
  const [timeData, setTimeData] = useState<string[]>([]);
  const [oilMealRatioData, setOilMealRatioData] = useState<number[]>(
    Array.from({length: 60}, () => 2 + Math.random() * 0.5)
  );
  const [crushingMarginData, setCrushingMarginData] = useState<number[]>(
    Array.from({length: 60}, () => 150 + Math.random() * 100)
  );
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // 获取数据
  const fetchData = async () => {
    try {
      setLoading(true);
      const apiPath = isRealtime ? '/market/arbitrage/realtime' : '/arbitrage/realtime';
      const response = await axios.get(`${API_BASE_URL}${apiPath}`);
      const data = response.data;
      
      // 更新时间轴数据
      setTimeData(data.timestamps);
      
      // 更新油粕比数据
      setOilMealRatio(data.oil_meal_ratio.current_ratio);
      setOilMealRatioData(data.oil_meal_ratio.values);
      
      // 更新压榨利润数据
      setCrushingMargin(data.crushing_margin.current_margin);
      setHistoricalAverage(data.crushing_margin.historical_average);
      setCrushingMarginData(data.crushing_margin.values);
      
    } catch (error) {
      console.error('获取数据失败:', error);
      setToast({
        message: '获取数据失败',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); // 首次加载
    
    let timer: NodeJS.Timeout | null = null;
    if (isRealtime) {
      timer = setInterval(fetchData, 60000); // 实时模式下每1分钟更新一次
    }
    
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isRealtime]);

  // 油粕比图表配置
  const oilMealRatioOption = useMemo(() => ({
    title: {
      text: '油粕比实时走势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0];
        return `${data.axisValue}<br/>${data.seriesName}: ${data.value.toFixed(3)}`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    dataZoom: [{
      type: 'inside',
      start: 80,
      end: 100
    }, {
      type: 'slider',
      start: 80,
      end: 100
    }],
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        rotate: 45,
        formatter: (value: string) => {
          return value.slice(11, 16); // 只显示时:分
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '油粕比',
      min: 2.2,
      max: 3.2,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [{
      name: '油粕比',
      data: oilMealRatioData,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#5470c6',
        width: 2
      },
      markLine: {
        data: [
          { yAxis: 2.5, name: '下限', lineStyle: { color: '#ff4d4f' } },
          { yAxis: 2.8, name: '上限', lineStyle: { color: '#ff4d4f' } }
        ]
      }
    }]
  }), [timeData, oilMealRatioData]);

  // 压榨利润图表配置
  const crushingMarginOption = useMemo(() => ({
    title: {
      text: '压榨利润实时走势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0];
        return `${data.axisValue}<br/>${data.seriesName}: ${data.value.toFixed(3)}元/吨`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    dataZoom: [{
      type: 'inside',
      start: 80,
      end: 100
    }, {
      type: 'slider',
      start: 80,
      end: 100
    }],
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        rotate: 45,
        formatter: (value: string) => {
          return value.slice(11, 16); // 只显示时:分
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '压榨利润(元/吨)',
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [{
      name: '压榨利润',
      data: crushingMarginData,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#91cc75',
        width: 2
      },
      markLine: {
        data: [
          { yAxis: historicalAverage, name: '历史均值', lineStyle: { color: '#5470c6' } }
        ]
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(145, 204, 117, 0.3)'
          }, {
            offset: 1,
            color: 'rgba(145, 204, 117, 0)'
          }]
        }
      }
    }]
  }), [timeData, crushingMarginData, historicalAverage]);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            多品种套利策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            基于豆二、豆粕、豆油三者价格关联性的日内动态套利策略
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">当前油粕比</div>
            <div className={`text-2xl font-semibold ${
              oilMealRatio > 2.5 ? 'text-red-600' : 
              oilMealRatio < 2.0 ? 'text-green-600' : 
              'text-black'
            }`}>
              {oilMealRatio.toFixed(3)}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">当前压榨利润</div>
            <div className={`text-2xl font-semibold ${
              crushingMargin > historicalAverage + 50 ? 'text-red-600' : 
              crushingMargin < historicalAverage - 50 ? 'text-green-600' : 
              'text-black'
            }`}>
              ¥{crushingMargin.toFixed(0)}/吨
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">历史均值</div>
            <div className="text-2xl font-semibold">
              ¥{historicalAverage.toFixed(3)}/吨
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                豆二、豆油、豆粕三者之间存在压榨关系：100%大豆≈18%豆油+80%豆粕+1.5%损耗。这一比例关系决定了三者价格存在长期均衡性，但日内可能因供需错配出现短期偏离。
              </p>
              <ul className="list-disc pl-6 mt-2 text-sm text-yellow-700">
                <li>油粕比套利：豆油与豆粕价格比值（油粕比）通常波动于1.8-2.8区间，日内可捕捉比值回归的波动。</li>
                <li>压榨利润套利：当压榨利润（豆油+豆粕价格-大豆成本）偏离正常水平时，可通过多空组合对冲套利。</li>
              </ul>
              <p className="mt-4 text-sm font-bold text-red-600">
                本策略仅供参考，测试结果基于三个品种的2509合约5分钟行情数据，实际交易中请注意风险控制，建议使用模拟盘进行测试。
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <span className="font-semibold">数据来源: 新浪财经期货行情</span>
            <div className="flex items-center gap-2">
              <span>实时数据</span>
              <button
                onClick={() => {
                  setIsRealtime(!isRealtime);
                  if (!isRealtime) {
                    fetchData();
                  }
                }}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  isRealtime ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isRealtime ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className={`relative ${loading ? 'opacity-50' : ''}`}>
          <div className="bg-white rounded-lg shadow">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex">
                <button
                  onClick={() => setActiveTab('1')}
                  className={`w-1/2 py-4 px-1 text-center border-b-2 font-medium text-sm ${
                    activeTab === '1'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  策略1：油粕比日内波段套利
                </button>
                <button
                  onClick={() => setActiveTab('2')}
                  className={`w-1/2 py-4 px-1 text-center border-b-2 font-medium text-sm ${
                    activeTab === '2'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  策略2：压榨利润均值回归套利
                </button>
              </nav>
            </div>

            {activeTab === '1' && (
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-sm text-gray-500">当前油粕比</div>
                    <div className={`text-2xl font-semibold ${
                      oilMealRatio > 2.5 ? 'text-red-600' : 
                      oilMealRatio < 2.0 ? 'text-green-600' : 
                      'text-black'
                    }`}>
                      {oilMealRatio.toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-sm text-gray-500">建议操作</div>
                    <div className={`text-2xl font-semibold ${
                      oilMealRatio > 2.5 || oilMealRatio < 2.0 ? 'text-blue-600' : 'text-black'
                    }`}>
                      {oilMealRatio > 2.5 ? '做空油粕比' : oilMealRatio < 2.0 ? '做多油粕比' : '观望'}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-sm text-gray-500">目标盈利</div>
                    <div className="text-2xl font-semibold">¥200/组</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <ReactECharts option={oilMealRatioOption} style={{ height: '400px' }} />
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h4 className="text-lg font-semibold mb-4">策略说明</h4>
                  <div className="mb-4">
                    <span className="font-semibold">触发条件：</span>
                    <ul className="list-disc pl-6 mt-2">
                      <li>当实时油粕比高于2.8或低于2.5时，视为短期超买/超卖信号</li>
                      <li>结合成交量放大（较前5分钟均值增长30%以上）确认趋势有效性</li>
                    </ul>
                  </div>
                  <div>
                    <span className="font-semibold">操作方向：</span>
                    <ul className="list-disc pl-6 mt-2">
                      <li>比值高位（{'>'}2.8）：做空油粕比（卖出豆油、买入豆粕）</li>
                      <li>比值低位（{'<'}2.5）：做多油粕比（买入豆油、卖出豆粕）</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {activeTab === '2' && (
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-sm text-gray-500">当前压榨利润</div>
                    <div className={`text-2xl font-semibold ${
                      crushingMargin > historicalAverage + 50 ? 'text-red-600' : 
                      crushingMargin < historicalAverage - 50 ? 'text-green-600' : 
                      'text-black'
                    }`}>
                      ¥{crushingMargin.toFixed(0)}/吨
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-sm text-gray-500">历史均值</div>
                    <div className="text-2xl font-semibold">
                      ¥{historicalAverage.toFixed(2)}/吨
                    </div>
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-sm text-gray-500">建议操作</div>
                    <div className={`text-2xl font-semibold ${
                      Math.abs(crushingMargin - historicalAverage) > 50 ? 'text-blue-600' : 'text-black'
                    }`}>
                      {crushingMargin > historicalAverage + 50 ? '做空压榨利润' : 
                       crushingMargin < historicalAverage - 50 ? '做多压榨利润' : '观望'}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <ReactECharts option={crushingMarginOption} style={{ height: '400px' }} />
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h4 className="text-lg font-semibold mb-4">策略说明</h4>
                  <div className="mb-4">
                    <span className="font-semibold">触发条件：</span>
                    <ul className="list-disc pl-6 mt-2">
                      <li>实时压榨利润 = （豆油价格×0.18 + 豆粕价格×0.8）- 豆二价格</li>
                      <li>当利润较前5日均值偏离50元/吨以上时，视为套利机会</li>
                    </ul>
                  </div>
                  <div>
                    <span className="font-semibold">操作方向：</span>
                    <ul className="list-disc pl-6 mt-2">
                      <li>利润过高：做空压榨利润（卖出豆油+豆粕，买入豆二）</li>
                      <li>利润过低：做多压榨利润（买入豆油+豆粕，卖出豆二）</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
          {loading && (
            <div className="absolute inset-0 bg-white bg-opacity-50 flex items-center justify-center">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
            </div>
          )}
        </div>
      </div>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </Layout>
  );
};

export default MultiVarietyArbitrage; 