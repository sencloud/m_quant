import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import { API_ENDPOINTS } from '../../config/api';

interface HedgeData {
  ts_code: string;
  trade_date: string;
  futures_price: number;
  options_price: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  hedge_ratio: number;
  pl: number;
  cumulative_pl: number;
  signal: 'increase_hedge' | 'decrease_hedge' | 'maintain';
  volatility: number;
  risk_exposure: number | null;
}

const FuturesOptionsHedgeStrategy: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1m' | '3m' | '6m' | '1y'>('3m');
  const [hedgeType, setHedgeType] = useState<'delta' | 'delta_gamma'>('delta');

  const getDateRange = (range: string) => {
    const end = new Date();
    const start = new Date();
    
    switch (range) {
      case '1m':
        start.setMonth(start.getMonth() - 1);
        break;
      case '3m':
        start.setMonth(start.getMonth() - 3);
        break;
      case '6m':
        start.setMonth(start.getMonth() - 6);
        break;
      case '1y':
        start.setFullYear(start.getFullYear() - 1);
        break;
    }
    
    return {
      start_date: start.toISOString().split('T')[0].replace(/-/g, ''),
      end_date: end.toISOString().split('T')[0].replace(/-/g, '')
    };
  };

  const { data: hedgeData } = useQuery<HedgeData[]>({
    queryKey: ['hedgeData', timeRange, hedgeType],
    queryFn: async () => {
      const { start_date, end_date } = getDateRange(timeRange);
      const response = await axios.get(API_ENDPOINTS.market.optionsHedge, {
        params: { start_date, end_date, hedge_type: hedgeType }
      });
      return response.data;
    }
  });

  const getChartOption = () => {
    if (!hedgeData) return {};

    const dates = hedgeData.map(item => item.trade_date);
    const futuresPrices = hedgeData.map(item => item.futures_price);
    const optionsPrices = hedgeData.map(item => item.options_price);
    const hedgeRatios = hedgeData.map(item => item.hedge_ratio);
    const pnlData = hedgeData.map(item => item.cumulative_pl);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['期货价格', '期权价格', '对冲比例', '累计盈亏']
      },
      grid: [
        {
          left: '10%',
          right: '10%',
          height: '50%'
        },
        {
          left: '10%',
          right: '10%',
          top: '60%',
          height: '20%'
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          gridIndex: 0
        },
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          gridIndex: 1
        }
      ],
      yAxis: [
        {
          name: '价格',
          scale: true,
          splitArea: {
            show: true
          },
          gridIndex: 0
        },
        {
          name: '对冲比例',
          scale: true,
          splitArea: {
            show: true
          },
          gridIndex: 0,
          axisLabel: {
            formatter: '{value} %'
          }
        },
        {
          name: '盈亏',
          scale: true,
          gridIndex: 1
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: '5%',
          start: 50,
          end: 100
        }
      ],
      series: [
        {
          name: '期货价格',
          type: 'line',
          data: futuresPrices,
          yAxisIndex: 0,
          xAxisIndex: 0,
          itemStyle: {
            color: '#5470c6'
          },
          showSymbol: false
        },
        {
          name: '期权价格',
          type: 'line',
          data: optionsPrices,
          yAxisIndex: 0,
          xAxisIndex: 0,
          itemStyle: {
            color: '#91cc75'
          },
          showSymbol: false
        },
        {
          name: '对冲比例',
          type: 'line',
          data: hedgeRatios,
          yAxisIndex: 1,
          xAxisIndex: 0,
          itemStyle: {
            color: '#ee6666'
          },
          showSymbol: false
        },
        {
          name: '累计盈亏',
          type: 'bar',
          data: pnlData,
          yAxisIndex: 2,
          xAxisIndex: 1,
          itemStyle: {
            color: function(params: any) {
              return params.value >= 0 ? '#26a69a' : '#ef5350';
            }
          }
        }
      ]
    };
  };

  const latestData = hedgeData?.[hedgeData.length - 1];
  const signalColor = latestData?.signal === 'increase_hedge' ? 'text-green-600' : 
                      latestData?.signal === 'decrease_hedge' ? 'text-red-600' : 
                      'text-gray-600';

  const greekLabels: Record<string, string> = {
    delta: "Delta - 价格变动敏感度",
    gamma: "Gamma - Delta变化率",
    theta: "Theta - 时间价值衰减",
    vega: "Vega - 波动率敏感度"
  };

  return (
    <div className="space-y-6">
      {/* 策略说明 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-2">策略说明</h3>
        <p className="text-gray-600">
          期货期权对冲策略通过动态调整期货和期权的持仓比例来管理市场风险。策略根据期权的希腊字母指标
          (Delta、Gamma、Theta、Vega)计算最优对冲比例，以减少投资组合的价格波动敏感性。
          {hedgeType === 'delta' ? 
            '当前使用Delta对冲策略，主要对冲标的价格变动风险。' : 
            '当前使用Delta-Gamma对冲策略，同时对冲价格变动风险和Delta变化风险。'}
        </p>
      </div>

      {/* 对冲类型和时间范围选择 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">对冲类型</h4>
          <div className="flex space-x-4">
            <button
              onClick={() => setHedgeType('delta')}
              className={`px-4 py-2 rounded-md ${
                hedgeType === 'delta' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              Delta对冲
            </button>
            <button
              onClick={() => setHedgeType('delta_gamma')}
              className={`px-4 py-2 rounded-md ${
                hedgeType === 'delta_gamma' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              Delta-Gamma对冲
            </button>
          </div>
        </div>
        
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">时间范围</h4>
          <div className="flex space-x-4">
            <button
              onClick={() => setTimeRange('1m')}
              className={`px-4 py-2 rounded-md ${
                timeRange === '1m' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              1个月
            </button>
            <button
              onClick={() => setTimeRange('3m')}
              className={`px-4 py-2 rounded-md ${
                timeRange === '3m' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              3个月
            </button>
            <button
              onClick={() => setTimeRange('6m')}
              className={`px-4 py-2 rounded-md ${
                timeRange === '6m' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              6个月
            </button>
            <button
              onClick={() => setTimeRange('1y')}
              className={`px-4 py-2 rounded-md ${
                timeRange === '1y' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              1年
            </button>
          </div>
        </div>
      </div>

      {/* 当前希腊字母和信号 */}
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Object.entries({
            delta: latestData?.delta,
            gamma: latestData?.gamma,
            theta: latestData?.theta,
            vega: latestData?.vega
          }).map(([greek, value]) => (
            <div key={greek} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
              <h3 className="text-md font-medium text-gray-700 mb-2">{greekLabels[greek]}</h3>
              <p className="text-xl font-semibold text-gray-800">
                {value?.toFixed(4) || '-'}
              </p>
            </div>
          ))}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-md font-medium text-gray-700 mb-2">对冲信号</h3>
            <p className={`text-xl font-semibold ${signalColor}`}>
              {latestData?.signal === 'increase_hedge' ? '增加对冲仓位' :
               latestData?.signal === 'decrease_hedge' ? '减少对冲仓位' :
               '维持当前对冲'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-md font-medium text-gray-700 mb-2">当前对冲比例</h3>
            <p className="text-xl font-semibold text-blue-600">
              {latestData?.hedge_ratio?.toFixed(2)}%
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-md font-medium text-gray-700 mb-2">波动率</h3>
            <p className="text-xl font-semibold text-purple-600">
              {latestData?.volatility?.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>

      {/* 图表展示 */}
      <div className="bg-white rounded-lg p-4 h-[500px]">
        {hedgeData ? (
          <ReactECharts 
            option={getChartOption()} 
            style={{ height: '100%', width: '100%' }}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500">加载数据中...</p>
          </div>
        )}
      </div>

      {/* 策略绩效 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">策略绩效</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-1">累计收益</h4>
            <p className={`text-2xl font-bold ${(latestData?.cumulative_pl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {latestData?.cumulative_pl?.toFixed(2)}%
            </p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-1">最大回撤</h4>
            <p className="text-2xl font-bold text-red-600">
              {hedgeData ? Math.min(...hedgeData.map(item => item.pl)).toFixed(2) : '-'}%
            </p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-1">风险暴露</h4>
            <p className="text-2xl font-bold text-amber-600">
              {latestData?.risk_exposure?.toFixed(2) || '-'}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FuturesOptionsHedgeStrategy; 