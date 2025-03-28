import React from 'react';
import ReactECharts from 'echarts-for-react';

interface FuturesData {
  ts_code: string;
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  vol: number;
  amount: number;
}

interface FuturesKLineChartProps {
  data: FuturesData[] | undefined;
}

const FuturesKLineChart: React.FC<FuturesKLineChartProps> = ({ data }) => {
  const getChartOption = () => {
    if (!data) return {};

    // 按合约分组数据
    const contractData = data.reduce((acc, item) => {
      if (!acc[item.ts_code]) {
        acc[item.ts_code] = [];
      }
      acc[item.ts_code].push([
        item.trade_date,
        item.open,
        item.close,
        item.low,
        item.high
      ]);
      return acc;
    }, {} as Record<string, any[]>);

    const series = Object.entries(contractData).map(([contract, data]) => ({
      name: contract,
      type: 'candlestick',
      data: data,
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
    }));

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: Object.keys(contractData)
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: Array.from(new Set(data.map(item => item.trade_date))),
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
      series
    };
  };

  return (
    <section className="py-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900">K线图表</h2>
          <p className="mt-4 text-lg text-gray-500">
            选择的时间范围内豆粕期货价格走势
          </p>
        </div>

        <div className="h-[600px] bg-white border rounded-lg p-4">
          <ReactECharts
            option={getChartOption()}
            style={{ height: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      </div>
    </section>
  );
};

export default FuturesKLineChart; 