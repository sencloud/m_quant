import React, { useEffect, useState, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { ECharts } from 'echarts';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';

interface KLineData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  grid_level?: number;  // 网格层级
  grid_price?: number;  // 网格价格
}

interface BacktestResult {
  total_returns: number;
  annual_returns: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_profit: number;
  final_assets: number;
  monthly_profits: { [key: string]: number };
  trades: Array<{
    entry_date: string;
    entry_price: number;
    exit_date: string;
    exit_price: number;
    position: 'long' | 'short';
    shares: number;
    pnl: number;
    grid: number;
  }>;
}

const GridStrategy: React.FC = () => {
  const [data, setData] = useState<KLineData[]>([]);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [showAllTrades, setShowAllTrades] = useState(false);
  const chartRef = useRef<ECharts | null>(null);
  const isUpdatingRef = useRef(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.grid.data);
        if (Array.isArray(response.data)) {
          setData(response.data);
        } else {
          console.error('Invalid data format:', response.data);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  const getChartOption = (data: KLineData[], trades: BacktestResult['trades'] = []) => ({
    title: {
      text: '网格交易策略',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any[]) => {
        const date = params[0].axisValue;
        let result = `<div class="font-medium">${date}</div>`;
        
        params.forEach(param => {
          const value = param.value;
          const color = param.color;
          const marker = param.marker;
          const seriesName = param.seriesName;
          
          // 安全地格式化数值
          const formatValue = (val: any) => {
            if (val === null || val === undefined || isNaN(val)) {
              return '暂无数据';
            }
            return val.toFixed(2);
          };
          
          result += `<div class="flex items-center justify-between gap-2">
            <span>${marker} ${seriesName}</span>
            <span class="font-medium" style="color: ${color}">${formatValue(value)}</span>
          </div>`;
        });
        
        return result;
      }
    },
    legend: {
      data: ['K线', '网格线', '开仓', '平仓'],
      top: '30px'
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date),
      scale: true,
      boundaryGap: false,
      axisLine: { onZero: false },
      splitLine: { show: false },
      min: 'dataMin',
      max: 'dataMax'
    },
    yAxis: {
      scale: true,
      splitLine: {
        show: true,
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 80,
        end: 100,
        xAxisIndex: 0
      },
      {
        show: true,
        type: 'slider',
        bottom: '5%',
        start: 80,
        end: 100,
        xAxisIndex: 0,
        textStyle: {
          color: '#8392A5'
        }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: data.map(item => [item.open, item.close, item.low, item.high]),
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        }
      },
      {
        name: '网格线',
        type: 'line',
        data: data.map(item => [item.date, item.grid_price, item.grid_level]),
        lineStyle: {
          type: 'dashed',
          color: '#888888',
          width: 1
        },
        symbol: 'none',
        z: 100
      },
      {
        name: '开仓',
        type: 'scatter',
        data: trades.map(trade => ({
          value: [
            trade.entry_date,
            trade.entry_price,
            trade.grid,
            '开仓'
          ],
          label: {
            show: true,
            position: trade.position === 'long' ? 'top' : 'bottom',
            distance: 5,
            formatter: () => `${trade.entry_price}\n${trade.position === 'long' ? '做多' : '做空'}\n网格${trade.grid}`,
            color: trade.position === 'long' ? '#ef232a' : '#14b143',
            fontSize: 11
          }
        })),
        symbol: (value: any, params: any) => {
          const position = params.data.value[2];
          return position === 'long' ? 'triangle' : 'arrow';
        },
        symbolSize: 12,
        itemStyle: {
          color: (params: any) => {
            const position = params.data.value[2];
            return position === 'long' ? '#ef232a' : '#14b143';
          }
        },
        z: 101
      },
      {
        name: '平仓',
        type: 'scatter',
        data: trades.map(trade => ({
          value: [
            trade.exit_date,
            trade.exit_price,
            trade.grid,
            trade.position === 'long' ? '止盈' : '止损',
            trade.pnl
          ],
          label: {
            show: true,
            position: trade.position === 'long' ? 'bottom' : 'top',
            distance: 5,
            formatter: () => {
              const exitTypeText = trade.position === 'long' ? '止盈' : '止损';
              return `${trade.exit_price}\n${exitTypeText}\n网格${trade.grid}`;
            },
            color: trade.pnl >= 0 ? '#ef232a' : '#14b143',
            fontSize: 11
          }
        })),
        symbol: (value: any, params: any) => {
          const position = params.data.value[2];
          return position === 'long' ? 'arrow' : 'triangle';
        },
        symbolSize: 12,
        itemStyle: {
          color: (params: any) => {
            const pnl = params.data.value[4];
            return pnl >= 0 ? '#ef232a' : '#14b143';
          }
        },
        z: 101
      }
    ]
  });

  const runBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await axios.post(API_ENDPOINTS.grid.backtest, {
        grid_levels: 10,
        atr_period: 14,
        data_period: 'daily'
      });
      if (response.data?.data?.backtest_results) {
        setBacktestResult(response.data.data.backtest_results);
      } else {
        console.error('Invalid backtest results format:', response.data);
      }
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

  return (
    <div className="space-y-6">
      {/* 策略说明和回测按钮 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">策略说明</h3>
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
        <p className="text-gray-600">
          网格交易策略是一种在预设价格区间内进行买卖的策略。当价格下跌到网格线时买入，上涨到网格线时卖出。
          通过在不同价格区间设置网格，实现低买高卖，获取价格波动带来的收益。
        </p>
      </div>

      {/* 图表组件 */}
      <div className="bg-white p-4 rounded-lg shadow">
        <ReactECharts 
          option={getChartOption(data, backtestResult?.trades || [])} 
          style={{ height: '600px' }}
          onChartReady={(chart) => {
            chartRef.current = chart;
          }}
        />
      </div>

      {/* 回测结果展示 */}
      {backtestResult && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">回测结果</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">总收益率</p>
              <p className="text-xl font-semibold text-blue-600">
                {formatPercentage(backtestResult.total_returns)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">年化收益率</p>
              <p className="text-xl font-semibold text-blue-600">
                {formatPercentage(backtestResult.annual_returns)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">夏普比率</p>
              <p className="text-xl font-semibold text-blue-600">
                {backtestResult.sharpe_ratio.toFixed(2)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">最大回撤</p>
              <p className="text-xl font-semibold text-red-600">
                {formatPercentage(backtestResult.max_drawdown)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">胜率</p>
              <p className="text-xl font-semibold text-blue-600">
                {formatPercentage(backtestResult.win_rate)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">总收益</p>
              <p className={`text-xl font-semibold ${backtestResult.total_profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                ¥{backtestResult.total_profit.toFixed(2)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">最终资产</p>
              <p className="text-xl font-semibold text-blue-600">
                ¥{backtestResult.final_assets.toFixed(2)}
              </p>
            </div>
          </div>

          {/* 月度盈亏图表 */}
          <div className="mt-6 bg-white p-4 rounded-lg">
            <ReactECharts 
              option={getMonthlyProfitsOption(backtestResult.monthly_profits)} 
              style={{ height: '300px' }}
            />
          </div>

          {/* 交易记录表格 */}
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
                      网格层级
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      平仓类型
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      盈亏
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(showAllTrades ? [...backtestResult.trades].reverse() : [...backtestResult.trades].reverse().slice(0, 10)).map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.entry_date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.entry_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800`}
                        >
                          {trade.position === 'long' ? '做多' : '做空'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.grid}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            trade.position === 'long'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {trade.position === 'long' ? '止盈' : '止损'}
                        </span>
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                        trade.pnl >= 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!showAllTrades && backtestResult.trades.length > 10 && (
                <div className="text-center text-sm text-gray-500 mt-2">
                  显示前10条记录，共 {backtestResult.trades.length} 条
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GridStrategy; 