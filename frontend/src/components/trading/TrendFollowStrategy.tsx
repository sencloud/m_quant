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
  ema60?: number;
  ema12?: number;
  ema26?: number;
}

interface BacktestResult {
  total_returns: number;
  annual_returns: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_profit: number;  // 总收益（元）
  commission: number;    // 手续费（元）
  net_profit: number;    // 净收益（元）
  monthly_profits: { [key: string]: number };  // 月度盈亏统计，key格式为'YYYY-MM'
  trades: Array<{
    entry_date: string;
    entry_price: number;
    exit_date: string;
    exit_price: number;
    pnl: number;
    position: 'long' | 'short';
    exit_type: 'take_profit' | 'stop_loss' | 'signal';
  }>;
}

const TrendFollowStrategy: React.FC = () => {
  const [data15min, setData15min] = useState<KLineData[]>([]);
  const [data60min, setData60min] = useState<KLineData[]>([]);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [showAllTrades, setShowAllTrades] = useState(false);  // 控制是否显示所有交易记录
  const chart15minRef = useRef<ECharts | null>(null);
  const chart60minRef = useRef<ECharts | null>(null);
  const isUpdatingRef = useRef(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [response15min, response60min] = await Promise.all([
          axios.get(API_ENDPOINTS.trendFollow.data15min),
          axios.get(API_ENDPOINTS.trendFollow.data60min)
        ]);
        setData15min(response15min.data);
        setData60min(response60min.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  // 图表联动处理函数
  const handleChartReady = (chart: ECharts, type: '15min' | '60min') => {
    if (type === '15min') {
      chart15minRef.current = chart;
    } else {
      chart60minRef.current = chart;
    }
  };

  // 数据缩放联动处理函数
  const handleDataZoomChange = (type: '15min' | '60min') => {
    return (params: any) => {
      if (isUpdatingRef.current) return;
      isUpdatingRef.current = true;

      try {
        const sourceChart = type === '15min' ? chart15minRef.current : chart60minRef.current;
        const targetChart = type === '15min' ? chart60minRef.current : chart15minRef.current;
        
        if (sourceChart && targetChart) {
          const option = sourceChart.getOption();
          const dataZoom = Array.isArray(option.dataZoom) ? option.dataZoom[0] : option.dataZoom;
          if (dataZoom && typeof dataZoom.start === 'number' && typeof dataZoom.end === 'number') {
            targetChart.dispatchAction({
              type: 'dataZoom',
              start: dataZoom.start,
              end: dataZoom.end
            });
          }
        }
      } finally {
        // 使用 setTimeout 确保在下一个事件循环中重置标志
        setTimeout(() => {
          isUpdatingRef.current = false;
        }, 0);
      }
    };
  };

  const get15minOption = (data: KLineData[], trades: BacktestResult['trades'] = []) => ({
    title: {
      text: '15分钟K线图',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any[]) => {
        const time = params[0].axisValue;
        let result = `<div style="font-weight:bold">${time}</div>`;
        
        params.forEach(param => {
          if (param.seriesName === 'K线') {
            const data = param.data;
            result += `
              <div style="display:flex;justify-content:space-between;min-width:180px">
                <span>${param.marker}开盘:</span>
                <span style="font-weight:bold">${data[1].toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}收盘:</span>
                <span style="font-weight:bold">${data[2].toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}最低:</span>
                <span style="font-weight:bold">${data[3].toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}最高:</span>
                <span style="font-weight:bold">${data[4].toFixed(2)}</span>
              </div>`;
          } else if (param.seriesName === '开仓' || param.seriesName === '平仓') {
            const data = param.data.value;
            const price = data[1];
            const position = data[2];
            const type = data[3];
            const pnl = data[4];
            
            result += `
              <div style="display:flex;justify-content:space-between;min-width:180px">
                <span>${param.marker}${param.seriesName}:</span>
                <span style="font-weight:bold">${price.toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}方向:</span>
                <span style="font-weight:bold">${position === 'long' ? '做多' : '做空'}</span>
              </div>`;
            
            if (type !== '开仓') {
              result += `
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}类型:</span>
                  <span style="font-weight:bold">${
                    type === 'take_profit' ? '止盈' : 
                    type === 'stop_loss' ? '止损' : '信号'
                  }</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}盈亏:</span>
                  <span style="font-weight:bold;color:${pnl >= 0 ? '#ef232a' : '#14b143'}">${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}</span>
                </div>`;
            }
          } else {
            result += `
              <div style="display:flex;justify-content:space-between;min-width:180px">
                <span>${param.marker}${param.seriesName}:</span>
                <span style="font-weight:bold;color:${param.color}">${param.value.toFixed(2)}</span>
              </div>`;
          }
        });
        
        return result;
      }
    },
    legend: {
      data: ['K线', 'EMA12', 'EMA26', '开仓', '平仓'],
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
        name: 'EMA12',
        type: 'line',
        data: data.map(item => item.ema12),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#2196F3',  // 蓝色
          opacity: 0.8
        },
        z: 100
      },
      {
        name: 'EMA26',
        type: 'line',
        data: data.map(item => item.ema26),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#FF9800',  // 橙色
          opacity: 0.8
        },
        z: 100
      },
      {
        name: '开仓',
        type: 'scatter',
        data: trades.map(trade => ({
          value: [
            trade.entry_date,
            trade.entry_price,
            trade.position,
            '开仓'
          ],
          label: {
            show: true,
            position: trade.position === 'long' ? 'top' : 'bottom',
            distance: 5,
            formatter: () => `${trade.entry_price}\n${trade.position === 'long' ? '做多' : '做空'}`,
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
            trade.position,
            trade.exit_type,
            trade.pnl
          ],
          label: {
            show: true,
            position: trade.position === 'long' ? 'bottom' : 'top',
            distance: 5,
            formatter: () => {
              const exitTypeText = trade.exit_type === 'take_profit' ? '止盈' : 
                                 trade.exit_type === 'stop_loss' ? '止损' : '信号';
              return `${trade.exit_price}\n${exitTypeText}`;
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

  const get60minOption = (data: KLineData[]) => ({
    title: {
      text: '60分钟K线图',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any[]) => {
        const time = params[0].axisValue;
        let result = `<div style="font-weight:bold">${time}</div>`;
        
        params.forEach(param => {
          if (param.seriesName === 'K线') {
            const data = param.data;
            result += `
              <div style="display:flex;justify-content:space-between;min-width:180px">
                <span>${param.marker}开盘:</span>
                <span style="font-weight:bold">${data[1].toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}收盘:</span>
                <span style="font-weight:bold">${data[2].toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}最低:</span>
                <span style="font-weight:bold">${data[3].toFixed(2)}</span>
              </div>
              <div style="display:flex;justify-content:space-between">
                <span>${param.marker}最高:</span>
                <span style="font-weight:bold">${data[4].toFixed(2)}</span>
              </div>`;
          } else if (param.seriesName === 'EMA60') {
            result += `
              <div style="display:flex;justify-content:space-between;min-width:180px">
                <span>${param.marker}${param.seriesName}:</span>
                <span style="font-weight:bold;color:${param.color}">${param.value.toFixed(2)}</span>
              </div>`;
          }
        });
        
        return result;
      }
    },
    legend: {
      data: ['K线', 'EMA60'],
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
        name: 'EMA60',
        type: 'line',
        data: data.map(item => item.ema60),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2,
          color: '#ffa500',
          opacity: 0.8
        },
        z: 100
      }
    ]
  });

  const runBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await axios.post(API_ENDPOINTS.trendFollow.backtest);
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

  // 计算月度盈亏的辅助函数
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
          基于60分钟K线图，当价格在EMA60上方时，做多；当价格在EMA60下方时，做空。
          具体做多做空时机则依据15分钟K线图的EMA12、EMA26指标的交叉情况。
        </p>
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
              <p className="text-sm text-gray-500">手续费</p>
              <p className="text-xl font-semibold text-orange-600">
                ¥{backtestResult.commission.toFixed(2)}
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">净收益</p>
              <p className={`text-xl font-semibold ${backtestResult.net_profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                ¥{backtestResult.net_profit.toFixed(2)}
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
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            trade.exit_type === 'take_profit'
                              ? 'bg-red-100 text-red-800'
                              : trade.exit_type === 'stop_loss'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {trade.exit_type === 'take_profit' ? '止盈' : trade.exit_type === 'stop_loss' ? '止损' : '信号'}
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

      {/* 保持现有的图表组件不变 */}
      <div className="bg-white p-4 rounded-lg shadow">
        <ReactECharts 
          option={get15minOption(data15min, backtestResult?.trades || [])} 
          style={{ height: '400px' }}
          onChartReady={(chart) => handleChartReady(chart, '15min')}
          onEvents={{
            datazoom: handleDataZoomChange('15min')
          }}
        />
      </div>
      <div className="bg-white p-4 rounded-lg shadow">
        <ReactECharts 
          option={get60minOption(data60min)} 
          style={{ height: '400px' }}
          onChartReady={(chart) => handleChartReady(chart, '60min')}
          onEvents={{
            datazoom: handleDataZoomChange('60min')
          }}
        />
      </div>
    </div>
  );
};

export default TrendFollowStrategy; 