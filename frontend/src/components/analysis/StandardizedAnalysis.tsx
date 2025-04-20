import React from 'react';
import ReactECharts from 'echarts-for-react';

interface ContractStat {
  contract: string;
  lowest_price: number;
  highest_price: number;
  price_range: number;
  start_price: number;
  end_price: number;
  volatility_30d: number;
  quantile_coef: number;
  standardized_value: number;
}

interface PredictedLow {
  base: number;
  lower: number;
  upper: number;
  confidence: number;
  factors: {
    supply_pressure: number;
    policy_risk: number;
    basis_impact: number;
  };
}

interface Props {
  contractStats: ContractStat[];
  selectedContract: string;
  predictedLow?: PredictedLow;
}

const StandardizedAnalysis: React.FC<Props> = ({ contractStats, selectedContract, predictedLow }) => {
  // 按合约月份过滤数据
  const month = selectedContract.slice(1);  // 获取月份部分，如 "01"
  const filteredStats = contractStats.filter(stat => stat.contract.endsWith(month));

  // 计算波动率和标准化值的统计数据
  const volatilities = filteredStats.map(stat => stat.volatility_30d);
  const standardizedValues = filteredStats.map(stat => stat.standardized_value);

  // 获取当前合约的数据
  const currentStat = filteredStats[filteredStats.length - 1];

  // 波动率分析图表配置
  const getVolatilityOption = () => ({
    title: {
      text: '历史波动率分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const stat = filteredStats[params[0].dataIndex];
        return `${stat.contract}<br/>
                波动率: ${stat.volatility_30d.toFixed(2)}%<br/>
                价格区间: ${stat.lowest_price} - ${stat.highest_price}`;
      }
    },
    xAxis: {
      type: 'category',
      data: filteredStats.map(stat => stat.contract),
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: '30日波动率(%)',
      splitLine: { show: true }
    },
    series: [
      {
        name: '波动率',
        type: 'line',
        data: volatilities,
        markLine: {
          data: [
            { type: 'average', name: '平均值' },
            { yAxis: Math.min(...volatilities), name: '最小值' },
            { yAxis: Math.max(...volatilities), name: '最大值' }
          ]
        },
        itemStyle: {
          color: '#1890ff'
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
              color: 'rgba(24,144,255,0.3)'
            }, {
              offset: 1,
              color: 'rgba(24,144,255,0.1)'
            }]
          }
        }
      }
    ]
  });

  // 标准化分析图表配置
  const getStandardizedOption = () => ({
    title: {
      text: '价格标准化分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const stat = filteredStats[params[0].dataIndex];
        return `${stat.contract}<br/>
                标准化值: ${(stat.standardized_value * 100).toFixed(2)}%<br/>
                当前价格: ${stat.end_price}<br/>
                历史区间: ${stat.lowest_price} - ${stat.highest_price}`;
      }
    },
    xAxis: {
      type: 'category',
      data: filteredStats.map(stat => stat.contract),
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: '标准化值',
      axisLabel: {
        formatter: '{value}%'
      },
      max: 100,
      splitLine: { show: true }
    },
    series: [
      {
        name: '标准化值',
        type: 'bar',
        data: standardizedValues.map(v => (v * 100).toFixed(2)),
        itemStyle: {
          color: function(params: any) {
            const value = standardizedValues[params.dataIndex];
            if (value <= 0.2) return '#52c41a';
            if (value <= 0.4) return '#faad14';
            if (value <= 0.6) return '#fa8c16';
            if (value <= 0.8) return '#f5222d';
            return '#a8071a';
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }
    ]
  });

  // 获取波动率状态颜色
  const getVolatilityColor = (value: number) => {
    if (value <= 15) return '#52c41a';
    if (value <= 25) return '#faad14';
    return '#f5222d';
  };

  // 获取标准化值状态颜色
  const getStandardizedColor = (value: number) => {
    if (value <= 0.2) return '#52c41a';
    if (value <= 0.4) return '#1890ff';
    if (value <= 0.6) return '#faad14';
    if (value <= 0.8) return '#f5222d';
    return '#eb2f96';
  };

  // 获取波动率解读文本
  const getVolatilityText = (value: number) => {
    if (value <= 15) return '当前波动率处于低位，市场相对平稳，可能处于蓄势阶段。';
    if (value <= 25) return '波动率处于中等水平，市场活跃度适中，需要保持关注。';
    return '波动率较高，市场波动剧烈，建议谨慎操作。';
  };

  // 获取标准化值解读文本
  const getStandardizedText = (value: number) => {
    if (value <= 0.2) return '当前价格处于历史低位区域，具有较好的安全边际。';
    if (value <= 0.4) return '价格处于历史中低位，风险收益比较为合理。';
    if (value <= 0.6) return '价格处于历史中位水平，需要关注市场变化方向。';
    if (value <= 0.8) return '价格处于历史高位，注意防范回调风险。';
    return '价格处于历史极高位置，建议保持谨慎。';
  };

  return (
    <div className="space-y-8">
      {/* 波动率分析卡片 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-6">
          <h3 className="text-xl font-semibold">波动率分析</h3>
          <div className="relative group">
            <svg className="w-5 h-5 text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="absolute hidden group-hover:block bg-gray-800 text-white text-sm rounded p-2 w-64 z-10 -mt-2 ml-6">
              基于30日历史波动率计算，反映价格波动的剧烈程度
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <ReactECharts option={getVolatilityOption()} style={{ height: '400px' }} />
          </div>
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium mb-4">当前波动率状态</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span>当前30日波动率</span>
                  <span className="px-3 py-1 rounded-full text-white text-sm" 
                        style={{ backgroundColor: getVolatilityColor(currentStat.volatility_30d) }}>
                    {currentStat.volatility_30d.toFixed(2)}%
                  </span>
                </div>
                <div className="relative pt-1">
                  <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
                    <div
                      style={{
                        width: `${Math.min(100, (currentStat.volatility_30d / 30) * 100)}%`,
                        backgroundColor: getVolatilityColor(currentStat.volatility_30d)
                      }}
                      className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center transition-all duration-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-medium mb-4">波动率解读</h4>
              <div className="space-y-2">
                <p className="text-gray-600">
                  {getVolatilityText(currentStat.volatility_30d)}
                </p>
                <p className="text-gray-600">
                  历史波动率范围：{Math.min(...volatilities).toFixed(2)}% - {Math.max(...volatilities).toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 价格标准化分析卡片 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-6">
          <h3 className="text-xl font-semibold">价格标准化分析</h3>
          <div className="relative group">
            <svg className="w-5 h-5 text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="absolute hidden group-hover:block bg-gray-800 text-white text-sm rounded p-2 w-64 z-10 -mt-2 ml-6">
              价格标准化值反映当前价格在历史区间中的位置，0%表示历史最低点，100%表示历史最高点
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <ReactECharts option={getStandardizedOption()} style={{ height: '400px' }} />
          </div>
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium mb-4">当前标准化状态</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span>当前标准化值</span>
                  <span className="px-3 py-1 rounded-full text-white text-sm"
                        style={{ backgroundColor: getStandardizedColor(currentStat.standardized_value) }}>
                    {(currentStat.standardized_value * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="relative pt-1">
                  <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
                    <div
                      style={{
                        width: `${currentStat.standardized_value * 100}%`,
                        backgroundColor: getStandardizedColor(currentStat.standardized_value)
                      }}
                      className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center transition-all duration-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-medium mb-4">价格区间分析</h4>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">历史最低价</span>
                  <span className="font-medium">{currentStat.lowest_price}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">当前价格</span>
                  <span className="font-medium">{currentStat.end_price}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">历史最高价</span>
                  <span className="font-medium">{currentStat.highest_price}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">价格区间</span>
                  <span className="font-medium">{currentStat.price_range}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-medium mb-4">标准化解读</h4>
              <p className="text-gray-600">
                {getStandardizedText(currentStat.standardized_value)}
              </p>
            </div>

            {predictedLow && (
              <div>
                <h4 className="text-lg font-medium mb-4">最低价预测</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">基准预测价</span>
                      <span className="font-medium text-blue-600">¥{predictedLow.base}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">预测区间</span>
                      <span className="font-medium">
                        ¥{predictedLow.lower} - ¥{predictedLow.upper}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">置信度</span>
                      <span className={`px-3 py-1 rounded-full text-white text-sm ${
                        predictedLow.confidence >= 80 ? 'bg-green-500' :
                        predictedLow.confidence >= 60 ? 'bg-blue-500' :
                        'bg-orange-500'
                      }`}>
                        {predictedLow.confidence * 100}%
                      </span>
                    </div>
                    <div className="mt-2">
                      <div className="text-sm text-gray-600 mb-2">影响因素：</div>
                      <div className="flex flex-wrap gap-2">
                        <div className="space-y-2 w-full">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">供应压力</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              predictedLow.factors.supply_pressure > 0.6 ? 'bg-red-100 text-red-800' :
                              predictedLow.factors.supply_pressure > 0.3 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {(predictedLow.factors.supply_pressure * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">政策风险</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              predictedLow.factors.policy_risk > 0.6 ? 'bg-red-100 text-red-800' :
                              predictedLow.factors.policy_risk > 0.3 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {(predictedLow.factors.policy_risk * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">基差影响</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              predictedLow.factors.basis_impact > 0.6 ? 'bg-red-100 text-red-800' :
                              predictedLow.factors.basis_impact > 0.3 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {(predictedLow.factors.basis_impact * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StandardizedAnalysis; 