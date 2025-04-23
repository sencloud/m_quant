import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { API_ENDPOINTS } from '../../config/api';

interface MarketData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  vol: number;
  amount: number;
  support_level: number;
  resistance_level: number;
  signal: number;  // 1: buy, -1: sell, 0: hold
  atr: number;
}

interface Trade {
  date: string;
  type: 'buy' | 'sell';
  price: number;
  profit: number;
}

interface BacktestResult {
  trades: Trade[];
  equity_curve: Array<{
    date: string;
    equity: number;
  }>;
  metrics: {
    total_trades: number;
    win_rate: number;
    total_profit: number;
    average_profit: number;
    average_loss: number;
    profit_factor: number;
  };
}

const SupportResistanceStrategy: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'3m' | '6m' | '1y' | '3y'>('1y');
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [showAllTrades, setShowAllTrades] = useState(false);
  const [dataPeriod, setDataPeriod] = useState<'weekly' | 'daily' | '30min'>('daily');

  const { data: marketData } = useQuery<MarketData[]>({
    queryKey: ['supportResistanceData', timeRange],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.supportResistance, {
        params: { period: dataPeriod }
      });
      return response.data;
    },
    refetchOnWindowFocus: false
  });

  const getChartOption = (): EChartsOption => {
    if (!marketData) return {};

    const candlestickData = marketData.map(item => ([
      item.open,
      item.close,
      item.low,
      item.high
    ]));

    const supportData = marketData.map(item => [
      item.date,
      item.support_level
    ]);

    const resistanceData = marketData.map(item => [
      item.date,
      item.resistance_level
    ]);

    const buySignals = marketData
      .filter(item => item.signal === 1)
      .map(item => ({
        name: '买入',
        value: [item.date, item.close],
        itemStyle: { color: '#ef5350' }
      }));

    const sellSignals = marketData
      .filter(item => item.signal === -1)
      .map(item => ({
        name: '卖出',
        value: [item.date, item.close],
        itemStyle: { color: '#26a69a' }
      }));

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        formatter: (params: any) => {
          if (!params || !params[0]) return '';
          
          const time = params[0].axisValue;
          let result = `<div style="font-weight:bold">${time}</div>`;
          
          params.forEach((param: any) => {
            if (!param || !param.data) return;
            
            if (param.seriesName === 'K线') {
              const values = param.data;
              if (!Array.isArray(values) || values.length < 5) return;
              
              result += `
                <div style="display:flex;justify-content:space-between;min-width:180px">
                  <span>${param.marker}开盘:</span>
                  <span style="font-weight:bold">${values[1]?.toFixed(3) || '-'}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}收盘:</span>
                  <span style="font-weight:bold">${values[2]?.toFixed(3) || '-'}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}最低:</span>
                  <span style="font-weight:bold">${values[3]?.toFixed(3) || '-'}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}最高:</span>
                  <span style="font-weight:bold">${values[4]?.toFixed(3) || '-'}</span>
                </div>`;
            } else {
              const value = param.value?.[1];
              result += `
                <div style="display:flex;justify-content:space-between;min-width:180px">
                  <span>${param.marker}${param.seriesName}:</span>
                  <span style="font-weight:bold;color:${param.color}">${value ? Number(value).toFixed(3) : '-'}</span>
                </div>`;
            }
          });
          return result;
        }
      },
      legend: {
        data: ['K线', '支撑位', '阻力位', '买入信号', '卖出信号'],
        top: '30px'
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: marketData.map(item => item.date),
        boundaryGap: true,
        axisLine: { onZero: false },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitArea: { show: true }
      },
      dataZoom: [
        {
          type: 'inside',
          start: 50,
          end: 100
        },
        {
          show: true,
          type: 'slider',
          bottom: '5%',
          start: 50,
          end: 100
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: marketData.map(item => [
            item.open,
            item.close,
            item.low,
            item.high
          ]),
          itemStyle: {
            color: '#ef5350',
            color0: '#26a69a',
            borderColor: '#ef5350',
            borderColor0: '#26a69a'
          }
        },
        {
          name: '支撑位',
          type: 'line',
          data: supportData,
          smooth: true,
          lineStyle: {
            color: '#2196F3',
            width: 2,
            type: 'dashed'
          },
          showSymbol: false
        },
        {
          name: '阻力位',
          type: 'line',
          data: resistanceData,
          smooth: true,
          lineStyle: {
            color: '#FF5722',
            width: 2,
            type: 'dashed'
          },
          showSymbol: false
        },
        {
          name: '买入信号',
          type: 'scatter',
          data: buySignals,
          symbol: 'triangle',
          symbolSize: 10,
          label: {
            show: true,
            position: 'top',
            formatter: '买入',
            color: '#ef5350',
            fontSize: 12
          }
        },
        {
          name: '卖出信号',
          type: 'scatter',
          data: sellSignals,
          symbol: 'triangle',
          symbolSize: 10,
          label: {
            show: true,
            position: 'bottom',
            formatter: '卖出',
            color: '#26a69a',
            fontSize: 12
          }
        }
      ]
    };
  };

  const runBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await axios.post(API_ENDPOINTS.supportResistance.backtest, {
        data_period: dataPeriod
      });
      setBacktestResult(response.data);
    } catch (error) {
      console.error('回测执行失败:', error);
    } finally {
      setIsBacktesting(false);
    }
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getMonthlyProfitsOption = (monthlyProfits: { [key: string]: number }) => {
    const months = Object.keys(monthlyProfits).sort();
    const profits = months.map(month => monthlyProfits[month]);
    
    return {
      title: {
        text: '月度盈亏统计',
        left: 'center',
        top: 0
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const month = params[0].name;
          const profit = params[0].value;
          return `${month}<br/>盈亏：${profit >= 0 ? '+' : ''}${profit.toFixed(2)}元`;
        }
      },
      grid: {
        top: '50px',
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: months,
        axisLabel: {
          interval: 0,
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '盈亏（元）',
        axisLine: { show: true },
        splitLine: { show: true }
      },
      series: [{
        name: '月度盈亏',
        type: 'bar',
        data: profits,
        itemStyle: {
          color: (params: any) => {
            return params.value >= 0 ? '#ef232a' : '#14b143';
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            return params.value >= 0 ? `+${params.value.toFixed(2)}` : params.value.toFixed(2);
          }
        }
      }]
    };
  };

  const latestData = marketData?.[marketData.length - 1];

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">策略说明</h3>
          <div className="flex items-center space-x-4">
            <select
              value={dataPeriod}
              onChange={(e) => setDataPeriod(e.target.value as 'weekly' | 'daily' | '30min')}
              className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="daily">日线行情数据</option>
              <option value="30min">30min行情数据</option>
              <option value="weekly">周线行情数据</option>
            </select>
            <button
              onClick={runBacktest}
              disabled={isBacktesting}
              className={`px-4 py-2 rounded-md text-white ${
                isBacktesting
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isBacktesting ? '回测中...' : '运行回测'}
            </button>
          </div>
        </div>
        <p className="text-gray-600">
          基于支撑位和阻力位的交易策略。当价格接近支撑位时产生买入信号，接近阻力位时产生卖出信号。
          使用动态止损和止盈设置来管理风险。支撑位和阻力位通过历史价格波动和成交量分布计算得出。
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-2">当前信号</h3>
          <p className={`text-xl font-semibold ${
            latestData?.signal === 1 ? 'text-emerald-600' : 
            latestData?.signal === -1 ? 'text-rose-600' : 
            'text-slate-600'
          }`}>
            {latestData?.signal === 1 ? '买入信号' :
             latestData?.signal === -1 ? '卖出信号' :
             '持仓观望'}
          </p>
        </div>
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-2">支撑位</h3>
          <p className="text-xl font-semibold text-blue-600">
            {latestData?.support_level?.toFixed(3) || '-'}
          </p>
        </div>
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
          <h3 className="text-lg font-medium text-gray-700 mb-2">阻力位</h3>
          <p className="text-xl font-semibold text-red-600">
            {latestData?.resistance_level?.toFixed(3) || '-'}
          </p>
        </div>
      </div>

      {backtestResult && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">回测结果</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">总收益率</p>
              <p className="text-xl font-semibold text-blue-600">
                {formatPercentage(backtestResult.metrics.total_profit / backtestResult.metrics.total_trades)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">胜率</p>
              <p className="text-xl font-semibold text-blue-600">
                {formatPercentage(backtestResult.metrics.win_rate)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">总收益</p>
              <p className="text-xl font-semibold text-blue-600">
                {backtestResult.metrics.total_profit.toFixed(2)}元
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">平均收益</p>
              <p className="text-xl font-semibold text-blue-600">
                {backtestResult.metrics.average_profit.toFixed(2)}元
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">平均损失</p>
              <p className="text-xl font-semibold text-red-600">
                {backtestResult.metrics.average_loss.toFixed(2)}元
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">利润因子</p>
              <p className="text-xl font-semibold text-blue-600">
                {backtestResult.metrics.profit_factor.toFixed(2)}
              </p>
            </div>
          </div>

          <div className="mt-6 h-[300px]">
            <ReactECharts
              option={getMonthlyProfitsOption(backtestResult.equity_curve.reduce((acc, { date, equity }) => {
                acc[date] = equity;
                return acc;
              }, {} as { [key: string]: number }))}
              style={{ height: '100%' }}
            />
          </div>

          <div className="mt-6">
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-md font-medium text-gray-900">交易记录</h4>
              <button
                onClick={() => setShowAllTrades(!showAllTrades)}
                className="px-3 py-1 text-sm rounded-md text-blue-600 hover:text-blue-700 border border-blue-600 hover:border-blue-700"
              >
                {showAllTrades ? '收起' : '展开全部'}
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      开仓时间
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      开仓价格
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      平仓时间
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      平仓价格
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      方向
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      盈亏
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(showAllTrades ? backtestResult.trades : backtestResult.trades.slice(-10)).map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.price.toFixed(3)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.price.toFixed(3)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800`}
                        >
                          {trade.type === 'buy' ? '做多' : '做空'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`font-medium ${
                            trade.profit >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {trade.profit >= 0 ? '+' : ''}{trade.profit.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <div className="h-[600px] bg-white border rounded-lg p-4">
        <ReactECharts
          option={getChartOption()}
          style={{ height: '100%' }}
          opts={{ renderer: 'svg' }}
        />
      </div>
    </div>
  );
};

export default SupportResistanceStrategy; 