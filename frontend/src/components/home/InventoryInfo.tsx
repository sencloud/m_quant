import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface InventoryData {
  total_inventory: number;
  warehouse_inventory: number;
  port_inventory: number;
  update_date: string;
  history_data?: {
    date: string;
    inventory: number;
  }[];
}

interface InventoryInfoProps {
  data: InventoryData | undefined;
}

const InventoryInfo: React.FC<InventoryInfoProps> = ({ data }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data?.history_data) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    const option = {
      grid: {
        top: 25,
        right: 5,
        bottom: 25,
        left: 5,
        containLabel: true
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params: any) => {
          const data = params[0];
          return `${data.name}<br/>库存: ${data.value.toLocaleString()} 吨`;
        }
      },
      xAxis: {
        type: 'category',
        show: true,
        data: data.history_data.map(item => {
          const date = new Date(item.date);
          return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
        }),
        axisLabel: {
          fontSize: 10,
          color: '#666'
        }
      },
      yAxis: {
        type: 'value',
        show: true,
        min: 'dataMin',
        max: 'dataMax',
        axisLabel: {
          fontSize: 10,
          color: '#666',
          formatter: (value: number) => {
            return (value / 1000).toFixed(1) + 'k';
          }
        }
      },
      series: [{
        data: data.history_data.map(item => item.inventory),
        type: 'bar',
        barWidth: '80%',
        itemStyle: {
          color: '#3B82F6'
        }
      }]
    };

    chartInstance.current.setOption(option);

    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, [data]);

  return (
    <section className="py-12 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900">库存信息</h2>
          <p className="mt-4 text-lg text-gray-500">
            实时获取豆粕期货库存信息
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">总库存</h3>
            <p className="text-xl font-semibold text-blue-600">
              {data?.total_inventory.toLocaleString() || '-'} 吨
            </p>
            {data?.history_data && (
              <div ref={chartRef} className="h-32 mt-2"></div>
            )}
          </div>
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">仓库库存</h3>
            <p className="text-xl font-semibold text-green-600">
              {data?.warehouse_inventory.toLocaleString() || '-'} 吨
            </p>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-2">港口库存</h3>
            <p className="text-xl font-semibold text-orange-600">
              {data?.port_inventory.toLocaleString() || '-'} 吨
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default InventoryInfo; 