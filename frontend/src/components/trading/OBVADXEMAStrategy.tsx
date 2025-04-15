import React, { useEffect, useState, useRef } from 'react';
import * as echarts from 'echarts';
import { API_ENDPOINTS } from '../../config/api';
import axios from 'axios';

interface MarketData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema20: number;
  ema60: number;
  adx: number;
  obv: number;
  signal: number;
}

interface Trade {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  position: string;
  pnl: number;
  exit_type: string;
}

interface BacktestResult {
  trades: Trade[];
  total_returns: number;
  annual_returns: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_profit: number;
  commission: number;
  net_profit: number;
  monthly_profits: { [key: string]: number };
}

const OBVADXEMAStrategy: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [showAllTrades, setShowAllTrades] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const monthlyChartRef = useRef<HTMLDivElement>(null);
  const monthlyChartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    fetchData();
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
      if (monthlyChartInstance.current) {
        monthlyChartInstance.current.dispose();
      }
    };
  }, []);

  useEffect(() => {
    if (marketData.length > 0 && chartRef.current) {
      initChart();
    }
  }, [marketData]);

  useEffect(() => {
    if (backtestResult?.monthly_profits) {
      initMonthlyChart();
    }
  }, [backtestResult]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(API_ENDPOINTS.obvAdxEma.data);
      setMarketData(response.data);
    } catch (error) {
      console.error('Error fetching market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runBacktest = async () => {
    try {
      setLoading(true);
      const response = await axios.post(API_ENDPOINTS.obvAdxEma.backtest);
      setBacktestResult(response.data);
    } catch (error) {
      console.error('Error running backtest:', error);
    } finally {
      setLoading(false);
    }
  };

  const initChart = () => {
    if (!chartRef.current) return;

    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    chartInstance.current = echarts.init(chartRef.current);
    const option = {
      title: {
        text: 'OBV-ADX-EMA组合策略分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['价格', 'EMA20', 'EMA60', 'ADX', 'OBV', '信号'],
        top: 30
      },
      grid: [
        { left: '3%', right: '3%', height: '40%' },
        { left: '3%', right: '3%', top: '55%', height: '20%' },
        { left: '3%', right: '3%', top: '80%', height: '15%' }
      ],
      xAxis: [
        {
          type: 'category',
          data: marketData.map(d => d.date),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          gridIndex: 0
        },
        {
          type: 'category',
          gridIndex: 1,
          data: marketData.map(d => d.date),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false }
        },
        {
          type: 'category',
          gridIndex: 2,
          data: marketData.map(d => d.date),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false }
        }
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true
          }
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        },
        {
          scale: true,
          gridIndex: 2,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1, 2],
          start: 0,
          end: 100
        },
        {
          show: true,
          xAxisIndex: [0, 1, 2],
          type: 'slider',
          bottom: '0%',
          start: 0,
          end: 100
        }
      ],
      series: [
        {
          name: '价格',
          type: 'candlestick',
          data: marketData.map(d => [d.open, d.close, d.low, d.high])
        },
        {
          name: 'EMA20',
          type: 'line',
          data: marketData.map(d => d.ema20),
          smooth: true,
          lineStyle: {
            opacity: 0.5
          }
        },
        {
          name: 'EMA60',
          type: 'line',
          data: marketData.map(d => d.ema60),
          smooth: true,
          lineStyle: {
            opacity: 0.5
          }
        },
        {
          name: 'ADX',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: marketData.map(d => d.adx)
        },
        {
          name: 'OBV',
          type: 'line',
          xAxisIndex: 2,
          yAxisIndex: 2,
          data: marketData.map(d => d.obv)
        },
        {
          name: '信号',
          type: 'scatter',
          data: marketData.map((d, i) => ({
            value: d.signal === 1 ? d.low : d.signal === -1 ? d.high : null,
            itemStyle: {
              color: d.signal === 1 ? '#f5222d' : '#52c41a'
            }
          }))
        }
      ]
    };

    chartInstance.current.setOption(option);
  };

  const initMonthlyChart = () => {
    if (!monthlyChartRef.current) return;

    if (monthlyChartInstance.current) {
      monthlyChartInstance.current.dispose();
    }

    monthlyChartInstance.current = echarts.init(monthlyChartRef.current);
    const monthlyData = Object.entries(backtestResult!.monthly_profits).sort((a, b) => a[0].localeCompare(b[0]));
    
    const option = {
      title: {
        text: '月度盈亏统计',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: monthlyData.map(item => item[0]),
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '盈亏（元）'
      },
      series: [
        {
          name: '月度盈亏',
          type: 'bar',
          data: monthlyData.map(item => item[1]),
          itemStyle: {
            color: function(params: any) {
              return params.value >= 0 ? '#EF4444' : '#10B981';
            }
          }
        }
      ]
    };

    monthlyChartInstance.current.setOption(option);
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">策略说明</h2>
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            onClick={runBacktest}
            disabled={loading}
          >
            {loading ? '回测中...' : '开始回测'}
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">策略逻辑</h3>
            <p className="text-gray-600">
              OBV-ADX-EMA组合策略是一个结合了成交量、趋势强度和价格趋势的多因子策略。该策略通过以下三个指标的组合来识别市场趋势和交易机会：
            </p>
            <ul className="list-disc list-inside mt-2 text-gray-600 space-y-1">
              <li>OBV（能量潮指标）：通过成交量的累积变化来确认价格趋势的强度</li>
              <li>ADX（平均趋向指标）：用于衡量趋势的强度，帮助过滤假突破</li>
              <li>EMA（指数移动平均线）：用于确认价格趋势的方向和支撑/阻力位</li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">交易规则</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              <li>做多条件：OBV上升 + ADX {'>'} 25 + 价格在EMA20上方</li>
              <li>做空条件：OBV下降 + ADX {'>'} 25 + 价格在EMA20下方</li>
              <li>止损：2%</li>
              <li>止盈：6%</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">策略优势</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              <li>多因子确认：通过成交量、趋势强度和价格趋势三重确认，降低假信号</li>
              <li>趋势跟踪：能够有效捕捉中期趋势行情</li>
              <li>风险控制：通过ADX过滤弱趋势，OBV确认成交量支撑</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div ref={chartRef} className="h-[600px]" />
      </div>

      {backtestResult && (
        <>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">回测结果</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">总收益率</div>
                <div className="text-2xl font-semibold text-green-600">
                  {backtestResult.total_returns?.toFixed(2) || '-'}%
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">年化收益率</div>
                <div className="text-2xl font-semibold text-green-600">
                  {backtestResult.annual_returns?.toFixed(2) || '-'}%
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">夏普比率</div>
                <div className="text-2xl font-semibold">
                  {backtestResult.sharpe_ratio?.toFixed(2) || '-'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">胜率</div>
                <div className="text-2xl font-semibold text-green-600">
                  {backtestResult.win_rate?.toFixed(2) || '-'}%
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">总收益</div>
                <div className={`text-2xl font-semibold ${backtestResult.total_profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ¥{backtestResult.total_profit?.toFixed(2) || '-'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">手续费</div>
                <div className="text-2xl font-semibold text-orange-600">
                  ¥{backtestResult.commission?.toFixed(2) || '-'}
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-500">净收益</div>
                <div className={`text-2xl font-semibold ${backtestResult.net_profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ¥{backtestResult.net_profit?.toFixed(2) || '-'}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">交易记录</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">入场日期</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">出场日期</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">方向</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">入场价格</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">出场价格</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">盈亏</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(backtestResult.trades || [])
                    .sort((a, b) => new Date(b.entry_date).getTime() - new Date(a.entry_date).getTime())
                    .slice(0, showAllTrades ? undefined : 10)
                    .map((trade, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.entry_date}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{trade.exit_date}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          trade.position === 'long' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {trade.position === 'long' ? '做多' : '做空'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.entry_price?.toFixed(2) || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_price?.toFixed(2) || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={trade.pnl >= 0 ? 'text-red-600' : 'text-green-600'}>
                          {trade.pnl?.toFixed(2) || '-'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {backtestResult.trades && backtestResult.trades.length > 10 && (
                <div className="mt-4 text-center">
                  <button
                    onClick={() => setShowAllTrades(!showAllTrades)}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    {showAllTrades ? '收起' : '展开全部'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* 月度盈亏图表 */}
          <div className="mt-6 bg-white p-4 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">月度盈亏</h2>
            <div ref={monthlyChartRef} style={{ height: '300px' }}></div>
          </div>
        </>
      )}
    </div>
  );
};

export default OBVADXEMAStrategy; 