import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
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

const ETFStrategy: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1m' | '3m' | '6m' | '1y'>('3m');

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

  const { data: etfData } = useQuery<ETFData[]>({
    queryKey: ['etfData', timeRange],
    queryFn: async () => {
      const { start_date, end_date } = getDateRange(timeRange);
      const response = await axios.get(API_ENDPOINTS.market.etf, {
        params: { start_date, end_date }
      });
      return response.data;
    }
  });

  const getChartOption = () => {
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

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['K线', 'MA5', 'MA8']
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: etfData.map(item => item.trade_date),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        splitNumber: 20
      },
      yAxis: {
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
          name: 'MA5',
          type: 'line',
          data: ma5Data,
          smooth: true,
          lineStyle: {
            opacity: 0.5,
            width: 2
          },
          showSymbol: false
        },
        {
          name: 'MA8',
          type: 'line',
          data: ma8Data,
          smooth: true,
          lineStyle: {
            opacity: 0.5,
            width: 2
          },
          showSymbol: false
        }
      ]
    };
  };

  const latestData = etfData?.[etfData.length - 1];
  const signalColor = latestData?.signal === 'buy' ? 'text-green-600' : 
                      latestData?.signal === 'sell' ? 'text-red-600' : 
                      'text-gray-600';

  return (
    <div className="space-y-6">
      {/* 策略说明 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-2">策略说明</h3>
        <p className="text-gray-600">
          基于5日均线和8日均线的金叉/死叉策略。当5日均线上穿8日均线时产生买入信号，
          当5日均线下穿8日均线时产生卖出信号。使用ATR进行风险管理，止损设置为1.8倍ATR，
          止盈设置为2.6倍ATR。
        </p>
      </div>

      {/* 时间范围选择 */}
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