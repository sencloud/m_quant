import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { ContractPrice, TechnicalIndicators, KlineData } from '../../types/market';

interface TechnicalChartProps {
  technicalData: TechnicalIndicators | null;
  contract: ContractPrice;
}

const TechnicalChart: React.FC<TechnicalChartProps> = ({ technicalData, contract }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!chartRef.current || !technicalData || !contract || !contract.historicalPrices) return;
    
    // 获取历史数据
    const historicalData = contract.historicalPrices
      .filter(item => item.contract === contract.contract)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    
    if (!historicalData || historicalData.length === 0) return;
    
    // 提取日期和价格数据
    const dates = historicalData.map(item => item.date);
    const closePrices = historicalData.map(item => item.close);
    
    // 计算技术指标
    const ma5 = calculateMA(5, closePrices);
    const ma10 = calculateMA(10, closePrices);
    const ma20 = calculateMA(20, closePrices);
    const { dif, dea, bar } = calculateMACD(closePrices);
    
    // 创建ECharts实例
    const chartInstance = echarts.init(chartRef.current);
    
    // 图表配置项
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['价格', 'MA5', 'MA10', 'MA20', 'MACD', 'DIF', 'DEA'],
        top: 0
      },
      grid: [
        {
          left: '3%',
          right: '4%',
          height: '60%',
          top: '10%'
        },
        {
          left: '3%',
          right: '4%',
          top: '75%',
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
          splitNumber: 20,
          gridIndex: 0
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          axisLabel: { show: false },
          splitLine: { show: false },
          axisLine: { show: false },
          splitNumber: 20
        }
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true
          },
          gridIndex: 0
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
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
          bottom: '5%',
          start: 50,
          end: 100
        }
      ],
      series: [
        {
          name: '价格',
          type: 'candlestick',
          data: historicalData.map(item => [
            item.date,
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
          },
          encode: {
            x: 0,
            y: [1, 2, 3, 4]
          },
          gridIndex: 0,
          connectNulls: true
        },
        {
          name: 'MA5',
          type: 'line',
          data: ma5,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            opacity: 0.5,
            width: 1
          },
          gridIndex: 0,
          connectNulls: true
        },
        {
          name: 'MA10',
          type: 'line',
          data: ma10,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            opacity: 0.5,
            width: 1
          },
          gridIndex: 0,
          connectNulls: true
        },
        {
          name: 'MA20',
          type: 'line',
          data: ma20,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            opacity: 0.5,
            width: 1
          },
          gridIndex: 0,
          connectNulls: true
        },
        {
          name: 'MACD',
          type: 'bar',
          data: bar,
          xAxisIndex: 1,
          yAxisIndex: 1,
          gridIndex: 1,
          connectNulls: true,
          itemStyle: {
            color: function(params: any) {
              return params.data >= 0 ? '#ef5350' : '#26a69a';
            }
          }
        },
        {
          name: 'DIF',
          type: 'line',
          data: dif,
          xAxisIndex: 1,
          yAxisIndex: 1,
          gridIndex: 1,
          symbol: 'none',
          lineStyle: {
            width: 1,
            opacity: 0.8
          },
          connectNulls: true
        },
        {
          name: 'DEA',
          type: 'line',
          data: dea,
          xAxisIndex: 1,
          yAxisIndex: 1,
          gridIndex: 1,
          symbol: 'none',
          lineStyle: {
            width: 1,
            opacity: 0.8
          },
          connectNulls: true
        }
      ]
    };
    
    // 渲染图表
    chartInstance.setOption(option);
    
    // 窗口大小变化时重绘图表
    const handleResize = () => {
      chartInstance.resize();
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.dispose();
    };
  }, [technicalData, contract]);

  return (
    <div className="bg-white rounded-lg p-4">
      <div ref={chartRef} style={{ width: '100%', height: '600px' }} />
    </div>
  );
};

// 计算移动平均线
function calculateMA(dayCount: number, data: number[]) {
  const result = [];
  for (let i = 0, len = data.length; i < len; i++) {
    if (i < dayCount - 1) {
      result.push('-');
      continue;
    }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j];
    }
    result.push(Number((sum / dayCount).toFixed(2)));
  }
  return result;
}

// 计算MACD
function calculateMACD(data: number[]) {
  const dif = calculateDIF(data);
  const dea = calculateDEA(dif);
  const bar = dif.map((value, index) => {
    const difValue = typeof value === 'string' ? 0 : value;
    const deaValue = typeof dea[index] === 'string' ? 0 : dea[index];
    return Number((difValue - deaValue) * 2).toFixed(2);
  });
  return { dif, dea, bar };
}

// 计算DIF
function calculateDIF(data: number[]) {
  const ema12 = calculateEMA(12, data);
  const ema26 = calculateEMA(26, data);
  return ema12.map((value, index) => {
    const ema12Value = typeof value === 'string' ? 0 : value;
    const ema26Value = typeof ema26[index] === 'string' ? 0 : ema26[index];
    return Number((ema12Value - ema26Value).toFixed(2));
  });
}

// 计算DEA
function calculateDEA(data: number[]) {
  return calculateEMA(9, data);
}

// 计算EMA
function calculateEMA(dayCount: number, data: number[]) {
  const result: number[] = [];
  const k = 2 / (dayCount + 1);
  
  for (let i = 0, len = data.length; i < len; i++) {
    if (i < dayCount - 1) {
      result.push(0);  // 使用0替代'-'
      continue;
    }
    
    let ema = data[i];
    for (let j = 1; j < dayCount; j++) {
      ema = data[i - j] * k + ema * (1 - k);
    }
    result.push(Number(ema.toFixed(2)));
  }
  
  return result;
}

export default TechnicalChart; 