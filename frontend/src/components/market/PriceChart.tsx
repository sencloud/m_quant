import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import ReactECharts from 'echarts-for-react';
import { API_ENDPOINTS } from '../../config/api';

interface MarketData {
  trade_date: string;
  close: number;
  open: number;
  high: number;
  low: number;
}

const PriceChart: React.FC = () => {
  const { data: marketData } = useQuery<MarketData[]>({
    queryKey: ['marketData'],
    queryFn: async () => {
      // 获取最近一年的数据
      const end = new Date();
      const start = new Date();
      start.setFullYear(start.getFullYear() - 1);
      
      const response = await axios.get(API_ENDPOINTS.market.futures, {
        params: { 
          symbol: 'M',
          start_date: start.toISOString().split('T')[0].replace(/-/g, ''),
          end_date: end.toISOString().split('T')[0].replace(/-/g, '')
        }
      });
      return response.data;
    }
  });

  const getChartOption = () => {
    if (!marketData) return {};

    const klineData = marketData.map(item => [
      item.trade_date,
      item.open,
      item.close,
      item.low,
      item.high
    ]);

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['K线']
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: marketData.map(item => item.trade_date),
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
          data: klineData,
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
        }
      ]
    };
  };

  return (
    <div className="bg-white rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">豆粕期货主力合约K线图</h3>
      <div className="h-[400px]">
        <ReactECharts
          option={getChartOption()}
          style={{ height: '100%' }}
          opts={{ renderer: 'svg' }}
        />
      </div>
    </div>
  );
};

export default PriceChart; 