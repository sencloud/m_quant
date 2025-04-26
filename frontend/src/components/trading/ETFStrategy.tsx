import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import type { 
  EChartsOption, 
  ScatterSeriesOption,
  CandlestickSeriesOption,
  LineSeriesOption
} from 'echarts';
import { API_ENDPOINTS } from '../../config/api';

interface ETFData {
  ts_code: string;
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  vol: number;
  amount: number;
  ma5: number;
  ma8: number;
  atr: number;
  signal: 'buy' | 'sell' | 'hold';
  stop_loss: number | null;
  take_profit: number | null;
  last_signal: 'buy' | 'sell' | 'hold' | null;
  last_signal_date: string | null;
  last_signal_price: number | null;
  last_stop_loss: number | null;
  last_take_profit: number | null;
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

type CustomSeriesOption = Omit<ScatterSeriesOption, 'data'> & {
  data?: any[];
  itemStyle?: {
    color?: string | ((params: any) => string);
  };
  label?: {
    show?: boolean;
    position?: string | number | number[];
    distance?: number;
    formatter?: string | ((params: any) => string);
    color?: string;
    fontSize?: number;
  };
  symbol?: string | ((value: any, params: any) => string);
  symbolSize?: number;
  z?: number;
};

type CandlestickDataItem = [string, number[]];  // [时间, [open, high, low, close]]

const ETFStrategy: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'3m' | '6m' | '1y' | '3y'>('1y');
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [showAllTrades, setShowAllTrades] = useState(false);  // 控制是否显示所有交易记录
  const [useAtrTp, setUseAtrTp] = useState(false);  // 新增ATR止盈状态
  const [dataPeriod, setDataPeriod] = useState<'weekly' | 'daily' | '30min'>('weekly');  // 新增行情数据周期选择

  const getDateRange = (range: string) => {
    const end = new Date();
    const start = new Date();
    
    switch (range) {
      case '3y':
        start.setFullYear(start.getFullYear() - 3);
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

  const { data: etfData } = useQuery<ETFData[]>({
    queryKey: ['etfData', timeRange],
    queryFn: async () => {
      const { start_date, end_date } = getDateRange(timeRange);
      const response = await axios.get(API_ENDPOINTS.market.etf, {
        params: { start_date, end_date }
      });
      return response.data;
    },
    refetchOnWindowFocus: false
  });

  const getChartOption = (): EChartsOption => {
    if (!etfData) return {};

    const candlestickData = etfData.map(item => [
      item.trade_date,
      item.open,
      item.close,
      item.low,
      item.high
    ]);

    const ma5Data = etfData.map(item => [
      item.trade_date,
      item.ma5
    ]);

    const ma8Data = etfData.map(item => [
      item.trade_date,
      item.ma8
    ]);

    // 添加交易信号点
    interface SignalPoint {
      name: string;
      value: [string, number];
      itemStyle: {
        color: string;
      };
    }

    const buySignals: SignalPoint[] = [];
    const sellSignals: SignalPoint[] = [];
    if (backtestResult) {
      backtestResult.trades.forEach(trade => {
        // 转换日期格式为yyyy-MM-dd
        const entryDate = trade.entry_date.split(' ')[0];
        const exitDate = trade.exit_date.split(' ')[0];
        
        // 开仓点
        buySignals.push({
          name: '买入',
          value: [entryDate, trade.entry_price],
          itemStyle: {
            color: '#ef5350'
          }
        });
        // 平仓点
        sellSignals.push({
          name: '卖出',
          value: [exitDate, trade.exit_price],
          itemStyle: {
            color: '#26a69a'
          }
        });
      });
    }

    // 只保留一个配置
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: (params: any) => {
          const time = params[0].axisValue;
          let result = `<div style="font-weight:bold">${time}</div>`;
          
          params.forEach((param: any) => {
            if (param.seriesName === 'K线') {
              const values = param.data;
              result += `
                <div style="display:flex;justify-content:space-between;min-width:180px">
                  <span>${param.marker}开盘:</span>
                  <span style="font-weight:bold">${values[1].toFixed(3)}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}最高:</span>
                  <span style="font-weight:bold">${values[2].toFixed(3)}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}最低:</span>
                  <span style="font-weight:bold">${values[3].toFixed(3)}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                  <span>${param.marker}收盘:</span>
                  <span style="font-weight:bold">${values[4].toFixed(3)}</span>
                </div>`;
            } else if (param.seriesName === 'MA8' || param.seriesName === 'MA21') {
              const value = param.value[1];
              result += `
                <div style="display:flex;justify-content:space-between;min-width:180px">
                  <span>${param.marker}${param.seriesName}:</span>
                  <span style="font-weight:bold;color:${param.color}">${value ? Number(value).toFixed(3) : '-'}</span>
                </div>`;
            } else if (param.seriesName === '买入信号' || param.seriesName === '卖出信号') {
              result += `
                <div style="display:flex;justify-content:space-between;min-width:180px">
                  <span>${param.marker}${param.seriesName}:</span>
                  <span style="font-weight:bold;color:${param.color}">${param.value[1].toFixed(3)}</span>
                </div>`;
            }
          });
          
          return result;
        }
      },
      legend: {
        data: ['K线', 'MA8', 'MA21', '买入信号', '卖出信号'],
        top: '30px'
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: etfData.map(item => item.trade_date),
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitArea: {
          show: true
        }
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
          data: candlestickData,
          itemStyle: {
            color: '#ef5350',
            color0: '#26a69a',
            borderColor: '#ef5350',
            borderColor0: '#26a69a'
          },
          encode: {
            x: 0,
            y: [1, 2, 3, 4]
          }
        },
        {
          name: 'MA8',
          type: 'line',
          data: ma5Data.map(item => [item[0], parseFloat(item[1].toString()).toFixed(3)]),
          smooth: true,
          lineStyle: {
            opacity: 0.5,
            width: 2
          },
          showSymbol: false
        },
        {
          name: 'MA21',
          type: 'line',
          data: ma8Data.map(item => [item[0], parseFloat(item[1].toString()).toFixed(3)]),
          smooth: true,
          lineStyle: {
            opacity: 0.5,
            width: 2
          },
          showSymbol: false
        },
        {
          name: '买入信号',
          type: 'scatter',
          data: buySignals,
          symbol: 'triangle',
          symbolSize: 10,
          itemStyle: {
            color: '#ef5350'
          },
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
          itemStyle: {
            color: '#26a69a'
          },
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

  const latestData = etfData?.[etfData.length - 1];
  const signalColor = latestData?.signal === 'buy' ? 'text-green-600' : 
                      latestData?.signal === 'sell' ? 'text-red-600' : 
                      'text-gray-600';

  const runBacktest = async () => {
    setIsBacktesting(true);
    try {
      const response = await axios.post(API_ENDPOINTS.dualma.backtest, {
        use_atr_tp: useAtrTp,
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
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useAtrTp}
                onChange={(e) => setUseAtrTp(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">使用ATR止盈</span>
            </label>
            <select
              value={dataPeriod}
              onChange={(e) => setDataPeriod(e.target.value as 'weekly' | 'daily' | '30min')}
              className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="weekly">周线行情数据</option>
              <option value="daily">日线行情数据</option>
              <option value="30min">30min行情数据</option>
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
          基于8日均线和21日均线的金叉做多策略。当8日均线上穿21日均线时产生买入信号。如果使用ATR，1.1倍ATR止盈价可以达到100%胜率。
        </p>
      </div>

      {/* 时间范围选择 */}
      {/* <div className="flex space-x-4">
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
        <button
          onClick={() => setTimeRange('3y')}
          className={`px-4 py-2 rounded-md ${
            timeRange === '3y' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
          }`}
        >
          3年
        </button>
      </div> */}

      {/* 当前信号和风险控制 */}
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">当前信号</h3>
            <p className={`text-xl font-semibold ${
              latestData?.signal === 'buy' ? 'text-emerald-600' : 
              latestData?.signal === 'sell' ? 'text-rose-600' : 
              'text-slate-600'
            }`}>
              {latestData?.signal === 'buy' ? '买入信号' :
               latestData?.signal === 'sell' ? '卖出信号' :
               '持仓观望'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">止损价格</h3>
            <p className="text-xl font-semibold text-rose-600">
              {latestData?.stop_loss?.toFixed(3) || '-'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">止盈价格</h3>
            <p className="text-xl font-semibold text-emerald-600">
              {latestData?.take_profit?.toFixed(3) || '-'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">上个有效信号</h3>
            <p className={`text-xl font-semibold ${
              latestData?.last_signal === 'buy' ? 'text-emerald-600' :
              latestData?.last_signal === 'sell' ? 'text-rose-600' :
              'text-slate-600'
            }`}>
              {latestData?.last_signal === 'buy' ? '买入信号' :
               latestData?.last_signal === 'sell' ? '卖出信号' :
               '无'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">信号触发时间</h3>
            <p className="text-xl font-semibold text-slate-600">
              {latestData?.last_signal_date || '-'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">信号触发价格</h3>
            <p className="text-xl font-semibold text-slate-600">
              {latestData?.last_signal_price?.toFixed(3) || '-'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">止盈价格</h3>
            <p className="text-xl font-semibold text-rose-600">
              {latestData?.last_take_profit?.toFixed(3) || '-'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">止损价格</h3>
            <p className="text-xl font-semibold text-emerald-600">
              {latestData?.last_stop_loss?.toFixed(3) || '-'}
            </p>
          </div>
        </div>
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
              <p className="text-xl font-semibold text-blue-600">
                {backtestResult.total_profit.toFixed(2)}元
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">手续费</p>
              <p className="text-xl font-semibold text-red-600">
                {backtestResult.commission.toFixed(2)}元
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">净收益</p>
              <p className="text-xl font-semibold text-blue-600">
                {backtestResult.net_profit.toFixed(2)}元
              </p>
            </div>
          </div>

          {/* 月度盈亏图表 */}
          <div className="mt-6 h-[300px]">
            <ReactECharts
              option={getMonthlyProfitsOption(backtestResult.monthly_profits)}
              style={{ height: '100%' }}
            />
          </div>

          {/* 交易记录 */}
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
                        {trade.entry_price.toFixed(3)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_price.toFixed(3)}
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
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {trade.exit_type === 'take_profit'
                            ? '止盈'
                            : trade.exit_type === 'stop_loss'
                            ? '止损'
                            : '信号'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`font-medium ${
                            trade.pnl >= 0 ? 'text-red-600' : 'text-green-600'
                          }`}
                        >
                          {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
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

      {/* K线图表 */}
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

export default ETFStrategy; 