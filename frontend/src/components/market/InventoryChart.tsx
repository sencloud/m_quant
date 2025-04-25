import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { InventoryData } from '../../types/market';

interface InventoryChartProps {
  data: InventoryData[];
}

const InventoryChart: React.FC<InventoryChartProps> = ({ data }) => {
  const mainChartRef = useRef<HTMLDivElement>(null);
  const compareChartRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!mainChartRef.current || !compareChartRef.current || !data.length) return;
    
    // 创建ECharts实例
    const mainChartInstance = echarts.init(mainChartRef.current);
    const compareChartInstance = echarts.init(compareChartRef.current);
    
    // 分离库存和仓单数据
    const inventoryData = data.filter(item => item.data_type === 'inventory');
    const warehouseData = data.filter(item => item.data_type === 'warehouse_receipts');
    
    // 获取所有唯一日期并排序
    const allDates = Array.from(new Set(data.map(item => item.date))).sort();
    
    // 准备库存数据
    const inventoryValues = allDates.map(date => {
      const item = inventoryData.find(d => d.date === date);
      return item ? item.value : null;
    });
    const inventoryMomChanges = allDates.map(date => {
      const item = inventoryData.find(d => d.date === date);
      return item ? item.mom_change : null;
    });
    
    // 准备仓单数据
    const warehouseValues = allDates.map(date => {
      const item = warehouseData.find(d => d.date === date);
      return item ? item.value : null;
    });
    const warehouseMomChanges = allDates.map(date => {
      const item = warehouseData.find(d => d.date === date);
      return item ? item.mom_change : null;
    });
    
    // 主图表配置项
    const mainOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['库存量', '仓单量', '库存环比', '仓单环比'],
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
        data: allDates,
        axisLabel: {
          formatter: (value: string) => {
            return value.slice(5); // 只显示MM-DD格式
          }
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '数量 (吨)',
          position: 'left'
        },
        {
          type: 'value',
          name: '变化量 (吨)',
          position: 'right'
        }
      ],
      series: [
        {
          name: '库存量',
          type: 'bar',
          data: inventoryValues.map(v => v !== null ? Number(v.toFixed(2)) : null),
          itemStyle: {
            color: '#1890ff'
          },
          yAxisIndex: 0
        },
        {
          name: '仓单量',
          type: 'bar',
          data: warehouseValues.map(v => v !== null ? Number(v.toFixed(2)) : null),
          itemStyle: {
            color: '#52c41a'
          },
          yAxisIndex: 0
        },
        {
          name: '库存环比',
          type: 'line',
          data: inventoryMomChanges.map(v => v !== null ? Number(v.toFixed(2)) : null),
          smooth: true,
          itemStyle: {
            color: '#ff4d4f'
          },
          yAxisIndex: 1
        },
        {
          name: '仓单环比',
          type: 'line',
          data: warehouseMomChanges.map(v => v !== null ? Number(v.toFixed(2)) : null),
          smooth: true,
          itemStyle: {
            color: '#faad14'
          },
          yAxisIndex: 1
        }
      ]
    };

    // 准备同比数据
    const currentYear = new Date().getFullYear();
    const lastYear = currentYear - 1;
    
    // 将日期格式化为MM-DD格式用于比较
    const getMMDD = (dateStr: string) => dateStr.slice(5);
    
    // 获取所有MM-DD格式的日期并排序
    const allMMDD = Array.from(new Set(warehouseData.map(item => getMMDD(item.date)))).sort();
    
    // 按年份分组数据
    const groupedData = warehouseData.reduce((acc, item) => {
      const year = item.date.slice(0, 4);
      if (!acc[year]) {
        acc[year] = {};
      }
      acc[year][getMMDD(item.date)] = item.value;
      return acc;
    }, {} as Record<string, Record<string, number>>);

    // 准备今年和去年的数据，使用线性插值填充缺失值
    const getInterpolatedValue = (data: Record<string, number>, mmdd: string, prevMMDD?: string, nextMMDD?: string) => {
      if (data[mmdd] !== undefined) return data[mmdd];
      if (!prevMMDD || !nextMMDD) return null;
      
      const prevValue = data[prevMMDD];
      const nextValue = data[nextMMDD];
      
      if (prevValue === undefined || nextValue === undefined) return null;
      
      // 计算日期在prevMMDD和nextMMDD之间的位置
      const allDatesInRange = allMMDD.slice(
        allMMDD.indexOf(prevMMDD),
        allMMDD.indexOf(nextMMDD) + 1
      );
      const position = allDatesInRange.indexOf(mmdd) / (allDatesInRange.length - 1);
      
      // 线性插值
      return prevValue + (nextValue - prevValue) * position;
    };

    const thisYearData = allMMDD.map((mmdd, index) => {
      const thisYearValues = groupedData[currentYear.toString()] || {};
      if (thisYearValues[mmdd] !== undefined) return thisYearValues[mmdd];
      
      // 找到前后有数据的点
      let prevIndex = index - 1;
      let nextIndex = index + 1;
      let prevMMDD: string | undefined;
      let nextMMDD: string | undefined;
      
      while (prevIndex >= 0) {
        if (thisYearValues[allMMDD[prevIndex]] !== undefined) {
          prevMMDD = allMMDD[prevIndex];
          break;
        }
        prevIndex--;
      }
      
      while (nextIndex < allMMDD.length) {
        if (thisYearValues[allMMDD[nextIndex]] !== undefined) {
          nextMMDD = allMMDD[nextIndex];
          break;
        }
        nextIndex++;
      }
      
      return getInterpolatedValue(thisYearValues, mmdd, prevMMDD, nextMMDD);
    });

    const lastYearData = allMMDD.map((mmdd, index) => {
      const lastYearValues = groupedData[lastYear.toString()] || {};
      if (lastYearValues[mmdd] !== undefined) return lastYearValues[mmdd];
      
      // 找到前后有数据的点
      let prevIndex = index - 1;
      let nextIndex = index + 1;
      let prevMMDD: string | undefined;
      let nextMMDD: string | undefined;
      
      while (prevIndex >= 0) {
        if (lastYearValues[allMMDD[prevIndex]] !== undefined) {
          prevMMDD = allMMDD[prevIndex];
          break;
        }
        prevIndex--;
      }
      
      while (nextIndex < allMMDD.length) {
        if (lastYearValues[allMMDD[nextIndex]] !== undefined) {
          nextMMDD = allMMDD[nextIndex];
          break;
        }
        nextIndex++;
      }
      
      return getInterpolatedValue(lastYearValues, mmdd, prevMMDD, nextMMDD);
    });

    // 计算差值数据
    const diffData = allMMDD.map((_, index) => {
      const thisYear = thisYearData[index];
      const lastYear = lastYearData[index];
      if (thisYear === null || lastYear === null) return null;
      return Number((thisYear - lastYear).toFixed(2));
    });

    // 同比图表配置
    const compareOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function (params: any[]) {
          let result = params[0].name + '<br/>';
          params.forEach(param => {
            const marker = param.marker;
            const seriesName = param.seriesName;
            let valueText;
            if (param.value === null || param.value === undefined) {
              valueText = '暂无数据';
            } else {
              try {
                valueText = param.value.toLocaleString();
              } catch (e) {
                valueText = param.value.toString();
              }
            }
            result += marker + seriesName + ': ' + valueText + '<br/>';
          });
          return result;
        }
      },
      legend: {
        data: [`${lastYear}年仓单`, `${currentYear}年仓单`, '同比差值'],
        top: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        top: '15%',
        bottom: '15%',
        containLabel: true
      },
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: 0,
          end: 100,
          bottom: '3%'
        },
        {
          type: 'inside',
          xAxisIndex: [0],
          start: 0,
          end: 100
        }
      ],
      xAxis: {
        type: 'category',
        data: allMMDD,
        axisLabel: {
          interval: 'auto'
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '仓单量 (吨)',
          position: 'left'
        },
        {
          type: 'value',
          name: '差值 (吨)',
          position: 'right'
        }
      ],
      series: [
        {
          name: `${lastYear}年仓单`,
          type: 'bar',
          data: lastYearData.map(v => v !== null ? Number(v.toFixed(2)) : null),
          itemStyle: {
            color: '#8c8c8c'
          }
        },
        {
          name: `${currentYear}年仓单`,
          type: 'bar',
          data: thisYearData.map(v => v !== null ? Number(v.toFixed(2)) : null),
          itemStyle: {
            color: '#52c41a'
          }
        },
        {
          name: '同比差值',
          type: 'line',
          yAxisIndex: 1,
          data: diffData,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            color: '#ff4d4f',
            width: 2
          },
          itemStyle: {
            color: '#ff4d4f'
          },
          connectNulls: true // 连接空值点
        }
      ]
    };
    
    // 渲染图表
    mainChartInstance.setOption(mainOption);
    compareChartInstance.setOption(compareOption);
    
    // 窗口大小变化时重绘图表
    const handleResize = () => {
      mainChartInstance.resize();
      compareChartInstance.resize();
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      mainChartInstance.dispose();
      compareChartInstance.dispose();
    };
  }, [data]);

  return (
    <div style={{ 
      background: '#fff', 
      padding: '24px', 
      borderRadius: '8px'
    }}>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">库存与仓单情况</h3>
      <div className="mb-6 text-sm text-gray-600">
        <div className="mb-4">
          <h4 className="font-medium text-gray-800 mb-2">仓单是库存的子集</h4>
          <p className="leading-relaxed">
            只有符合交易所交割标准（如品质、包装、存放地点等）的库存，才能注册生成仓单。
            因此，仓单量 ≤ 库存量。例如，某商品总库存为100万吨，但仅有60万吨符合交割标准并注册为仓单。
          </p>
        </div>
        <div className="mb-4">
          <h4 className="font-medium text-gray-800 mb-2">仓单与库存的流动性差异</h4>
          <p className="leading-relaxed">
            仓单可直接用于期货交割，流动性高，直接影响期货市场的交割压力。
            库存中的非仓单部分流动性较低，主要用于现货市场流通。
          </p>
        </div>
      </div>
      <div ref={mainChartRef} style={{ width: '100%', height: '400px', marginBottom: '24px' }} />
      <h3 className="text-xl font-semibold text-gray-900 mb-4">仓单同比对比</h3>
      <div ref={compareChartRef} style={{ width: '100%', height: '400px' }} />
    </div>
  );
};

export default InventoryChart; 