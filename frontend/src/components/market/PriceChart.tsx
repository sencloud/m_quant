import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { ContractPrice } from '../../types/market';

interface PriceChartProps {
  contract: ContractPrice;
}

const PriceChart: React.FC<PriceChartProps> = ({ contract }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!chartRef.current) return;
    
    // 获取历史数据
    const historicalData = contract.historicalPrices
      .filter(item => item.contract === contract.contract)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    
    if (historicalData.length === 0) return;
    
    // 提取日期和价格数据
    const dates = historicalData.map(item => item.date);
    const prices = historicalData.map(item => item.close);
    
    // 创建ECharts实例
    const chartInstance = echarts.init(chartRef.current);
    
    // 图表配置项
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params: any) {
          const historicalPoint = params[0];
          const currentPoint = params[1];
          return `
            <div>
              <p>${historicalPoint.axisValue}</p>
              <p style="margin: 0">
                <span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:#1890ff;"></span>
                历史当日均价: ${historicalPoint.value.toFixed(2)}元/吨
              </p>
              <p style="margin: 0">
                <span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;border: 2px dashed #FF4D4F;"></span>
                当前价格: ${contract.price.toFixed(2)}元/吨
              </p>
            </div>
          `;
        }
      },
      legend: {
        data: ['历史当日均价', '当前价格'],
        top: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        name: '日期',
        nameLocation: 'middle',
        nameGap: 30
      },
      yAxis: {
        type: 'value',
        name: '价格 (元/吨)',
        nameLocation: 'middle',
        nameGap: 50,
        axisLabel: {
          formatter: '{value}.00'
        },
        min: function(value: any) {
          // 设置最小值为最低价格的95%
          return Math.floor(value.min * 0.95);
        },
        max: function(value: any) {
          // 设置最大值为最高价格的105%
          return Math.ceil(value.max * 1.05);
        },
        splitNumber: 5,  // 设置分割段数
        scale: true,  // 启用自动缩放
        boundaryGap: [0.1, 0.1]  // 设置边界留白比例
      },
      series: [
        {
          name: '历史当日均价',
          type: 'line',
          data: prices,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: '#1890ff'
          },
          itemStyle: {
            color: '#1890ff'
          },
          connectNulls: true,
          emphasis: {
            focus: 'series'
          }
        },
        {
          name: '当前价格',
          type: 'line',
          symbol: 'none',
          smooth: true,
          data: Array(dates.length).fill(parseFloat(contract.price.toString())),
          lineStyle: {
            width: 3,
            color: '#FF4D4F',
            type: 'dashed'
          },
          connectNulls: true,
          emphasis: {
            focus: 'series'
          }
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
  }, [contract]);

  return (
    <div className="bg-white rounded-lg p-4">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">价格走势</h3>
      <div ref={chartRef} style={{ width: '100%', height: '400px' }} />
    </div>
  );
};

export default PriceChart; 