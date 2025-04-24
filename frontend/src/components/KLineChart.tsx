import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Radio } from 'antd';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const KLineChart: React.FC = () => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [period, setPeriod] = React.useState('30');

  const fetchData = async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.market.kline(period));
      const data = response.data;
      
      // 更新图表
      if (chartInstance.current) {
        const dates = data.map((item: KLineData) => item.date);
        const klineData = data.map((item: KLineData) => [
          Number(item.open),
          Number(item.close),
          Number(item.low),
          Number(item.high)
        ]);
        // 根据开盘收盘价判断涨跌，设置成交量颜色
        const volumes = data.map((item: KLineData) => ({
          value: Number(item.volume),
          itemStyle: {
            color: Number(item.close) >= Number(item.open) ? '#ef232a' : '#14b143'
          }
        }));

        chartInstance.current.setOption({
          xAxis: [{
            data: dates
          }, {
            data: dates
          }],
          series: [{
            name: '豆粕主力',
            type: 'candlestick',
            data: klineData
          }, {
            name: 'Volume',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes
          }]
        });
      }
    } catch (error) {
      console.error('获取K线数据失败:', error);
    }
  };

  useEffect(() => {
    if (chartRef.current) {
      chartInstance.current = echarts.init(chartRef.current);
      
      const option = {
        animation: false,
        legend: {
          bottom: 10,
          left: 'center',
          data: ['豆粕主力']
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: function (params: any) {
            if (params[0].componentSubType === 'candlestick') {
              const kline = params[0];
              return [
                '时间: ' + kline.axisValue + '<br/>',
                '开: ' + kline.data[1] + '<br/>',
                '收: ' + kline.data[2] + '<br/>',
                '低: ' + kline.data[3] + '<br/>',
                '高: ' + kline.data[4]
              ].join('');
            } else {
              return '成交量: ' + params[0].data;
            }
          }
        },
        grid: [
          {
            left: '10%',
            right: '8%',
            height: '60%'
          },
          {
            left: '10%',
            right: '8%',
            top: '75%',
            height: '15%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: [],
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            splitNumber: 20
          },
          {
            type: 'category',
            gridIndex: 1,
            data: [],
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            splitNumber: 20
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
            top: '85%',
            start: 50,
            end: 100
          }
        ],
        series: [
          {
            name: '豆粕主力',
            type: 'candlestick',
            data: [],
            itemStyle: {
              color: '#ef232a',
              color0: '#14b143',
              borderColor: '#ef232a',
              borderColor0: '#14b143'
            }
          },
          {
            name: 'Volume',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: [],
            itemStyle: {
              color: '#7fbe9e'
            }
          }
        ]
      };

      chartInstance.current.setOption(option);
    }

    // 初始加载数据
    fetchData();

    // 判断当前是否为交易时间
    const isTradeTime = () => {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        
        // 上午9:00-11:30
        if ((hours === 9 && minutes >= 0) || 
            (hours === 10) || 
            (hours === 11 && minutes <= 30)) {
            return true;
        }
        
        // 下午13:30-15:00
        if ((hours === 13 && minutes >= 30) || 
            (hours === 14)) {
            return true;
        }
        
        // 晚上21:00-23:00
        if ((hours === 21) || 
            (hours === 22)) {
            return true;
        }
        
        return false;
    };

    // 设置定时器,每30秒更新一次数据
    // 只在交易时间内每3秒刷新一次数据
    const timer = setInterval(() => {
        if (isTradeTime()) {
            fetchData();
        }
      }, 3000);

    return () => {
      clearInterval(timer);
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, [period]);

  const handlePeriodChange = (e: any) => {
    setPeriod(e.target.value);
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="mb-4">
        <Radio.Group value={period} onChange={handlePeriodChange}>
          <Radio.Button value="15">15分钟</Radio.Button>
          <Radio.Button value="30">30分钟</Radio.Button>
          <Radio.Button value="60">1小时</Radio.Button>
          <Radio.Button value="d">日线</Radio.Button>
        </Radio.Group>
      </div>
      <div ref={chartRef} className="flex-1" style={{ minHeight: '600px' }} />
    </div>
  );
};

export default KLineChart; 