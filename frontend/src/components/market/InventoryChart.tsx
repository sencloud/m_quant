import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { InventoryData } from '../../types/market';

interface InventoryChartProps {
  data: InventoryData[];
}

const InventoryChart: React.FC<InventoryChartProps> = ({ data }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!chartRef.current || !data.length) return;
    
    // 创建ECharts实例
    const chartInstance = echarts.init(chartRef.current);
    
    // 准备数据
    const dates = data.map(item => item.date);
    const values = data.map(item => item.value);
    const momChanges = data.map(item => item.mom_change);
    const yoyChanges = data.map(item => item.yoy_change);
    
    // 图表配置项
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['库存量', '环比变化'],
        top: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        top: '10%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: [
        {
          type: 'value',
          name: '库存量 (吨)',
          position: 'left'
        },
        {
          type: 'value',
          name: '变化率 (%)',
          position: 'right',
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: '库存量',
          type: 'bar',
          data: values.map(v => Number(v.toFixed(2))),
          itemStyle: {
            color: '#1890ff'
          },
          yAxisIndex: 0
        },
        {
          name: '环比变化',
          type: 'line',
          data: momChanges.map(v => Number(v.toFixed(2))),
          smooth: true,
          itemStyle: {
            color: '#ff4d4f'
          },
          yAxisIndex: 1
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
  }, [data]);

  return (
    <div style={{ 
      background: '#fff', 
      padding: '24px', 
      borderRadius: '8px'
    }}>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">库存情况</h3>
      <div ref={chartRef} style={{ width: '100%', height: '400px' }} />
    </div>
  );
};

export default InventoryChart; 