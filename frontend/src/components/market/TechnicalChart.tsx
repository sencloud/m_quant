import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { ContractPrice, TechnicalIndicators } from '../../types/market';

interface TechnicalChartProps {
  technicalData: TechnicalIndicators | null;
  contract: ContractPrice;
}

const TechnicalChart: React.FC<TechnicalChartProps> = ({ technicalData, contract }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !technicalData || !contract || !contract.historicalPrices) {
      console.log('Missing required data');
      return;
    }
    
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
    
    // 创建ECharts实例
    const chartInstance = echarts.init(chartRef.current);

    // 基础系列数据
    const series: any[] = [
      {
        name: '价格',
        type: 'candlestick',
        data: historicalData.map(item => [
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
        name: 'MA5',
        type: 'line',
        data: ma5,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, opacity: 0.5 }
      },
      {
        name: 'MA10',
        type: 'line',
        data: ma10,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, opacity: 0.5 }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, opacity: 0.5 }
      }
    ];

    // 添加价格目标线
    if (technicalData.price_targets) {
      console.log('Adding price target lines');
      const { support_levels, resistance_levels } = technicalData.price_targets;
      series.push(
        {
          name: '支撑位S1',
          type: 'line',
          data: dates.map(() => support_levels.s1),
          symbol: 'none',
          lineStyle: { width: 2, type: 'dashed', color: '#26a69a' },
          markPoint: {
            symbol: 'rect',
            symbolSize: [60, 20],
            data: [
              { 
                value: support_levels.s1.toFixed(2),
                xAxis: dates.length - 1,
                yAxis: support_levels.s1,
                itemStyle: { color: '#26a69a' }
              }
            ],
            label: {
              color: '#fff',
              position: 'inside'
            }
          }
        },
        {
          name: '支撑位S2',
          type: 'line',
          data: dates.map(() => support_levels.s2),
          symbol: 'none',
          lineStyle: { width: 1, type: 'dashed', color: '#26a69a', opacity: 0.8 },
          markPoint: {
            symbol: 'rect',
            symbolSize: [60, 20],
            data: [
              { 
                value: support_levels.s2.toFixed(2),
                xAxis: dates.length - 1,
                yAxis: support_levels.s2,
                itemStyle: { color: '#26a69a' }
              }
            ],
            label: {
              color: '#fff',
              position: 'inside'
            }
          }
        },
        {
          name: '阻力位R1',
          type: 'line',
          data: dates.map(() => resistance_levels.r1),
          symbol: 'none',
          lineStyle: { width: 2, type: 'dashed', color: '#ef5350' },
          markPoint: {
            symbol: 'rect',
            symbolSize: [60, 20],
            data: [
              { 
                value: resistance_levels.r1.toFixed(2),
                xAxis: dates.length - 1,
                yAxis: resistance_levels.r1,
                itemStyle: { color: '#ef5350' }
              }
            ],
            label: {
              color: '#fff',
              position: 'inside'
            }
          }
        },
        {
          name: '阻力位R2',
          type: 'line',
          data: dates.map(() => resistance_levels.r2),
          symbol: 'none',
          lineStyle: { width: 1, type: 'dashed', color: '#ef5350', opacity: 0.8 },
          markPoint: {
            symbol: 'rect',
            symbolSize: [60, 20],
            data: [
              { 
                value: resistance_levels.r2.toFixed(2),
                xAxis: dates.length - 1,
                yAxis: resistance_levels.r2,
                itemStyle: { color: '#ef5350' }
              }
            ],
            label: {
              color: '#fff',
              position: 'inside'
            }
          }
        }
      );
    }
    
    // 图表配置项
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: [
          '价格', 'MA5', 'MA10', 'MA20',
          '支撑位S1', '支撑位S2', '阻力位R1', '阻力位R2'
        ],
        top: 0,
        selected: {
          'MA5': false,
          'MA10': false,
          'MA20': false
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: true,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      yAxis: {
        scale: true,
        splitArea: { show: true }
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          show: true,
          type: 'slider',
          bottom: '5%',
          start: 0,
          end: 100
        }
      ],
      series
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
      <h3 className="text-xl font-semibold text-gray-900 mb-4">技术分析图表</h3>
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

export default TechnicalChart; 