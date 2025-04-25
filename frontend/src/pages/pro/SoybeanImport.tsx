import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { fetchSoybeanImportData } from '../../api/soybean';
import Layout from '../../components/layout/Layout';
import type { EChartsOption, LineSeriesOption, HeatmapSeriesOption } from 'echarts';

// 定义港口详情类型
interface PortDetailType {
  location: string;
  capacity: string;
  features: string[];
  advantages: string[];
  risks: string[];
}

// 定义海关详情类型
interface CustomsDetailType {
  jurisdiction: string;
  features: string[];
  advantages: string[];
  statistics: {
    averageProcessingTime: string;
    inspectionPassRate: string;
    annualProcessingVolume: string;
  };
}

interface ComparisonData {
  month: string;
  value: number;
  type: string;
}

interface PortDistributionData {
  port: string;
  value: number;
  type: string;
}

interface PortData {
  port: string;
  current: number;
  next_month: number;
  next_two_month: number;
}

interface CustomsData {
  customs: string;
  current: number;
  next_period: number;
  next_month: number;
  next_two_month: number;
}

interface PolicyEvent {
  date: string;
  event: string;
  impact: string;
  type: string;
}

interface SoybeanImportData {
  date: string;
  current_shipment: number;
  forecast_shipment: number;
  forecast_next_shipment: number;
  current_arrival: number;
  next_arrival: number;
  current_month_arrival: number;
  next_month_arrival: number;
  current_shipment_yoy: number;
  current_shipment_mom: number;
  forecast_shipment_yoy: number;
  forecast_shipment_mom: number;
  current_arrival_yoy: number;
  current_arrival_mom: number;
  next_arrival_yoy: number;
  shipment_forecast_diff: number;
  arrival_forecast_diff: number;
  monthly_comparison: ComparisonData[];
  port_distribution: PortDistributionData[];
  port_details: PortData[];
  customs_details: CustomsData[];
  policy_events: PolicyEvent[];
  created_at: string;
  updated_at: string;
}

const SoybeanImport: React.FC = () => {
  const [data, setData] = useState<SoybeanImportData | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'trend' | 'structure' | 'supply' | 'policy' | 'risk'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetchSoybeanImportData();
        setData(response as SoybeanImportData);
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // 一、时间序列趋势分析
  const getTrendLineOption = (): EChartsOption => {
    if (!data?.monthly_comparison) return {};
    
    // 按类型和日期对数据进行分组
    const groupedData = data.monthly_comparison.reduce((acc, item) => {
      if (!acc[item.type]) {
        acc[item.type] = [];
      }
      acc[item.type].push({
        month: item.month,
        value: item.value,
        date: new Date(item.month)
      });
      return acc;
    }, {} as Record<string, { month: string; value: number; date: Date }[]>);

    // 获取所有唯一日期并排序
    const allDates = Array.from(new Set(data.monthly_comparison.map(item => item.month)))
      .map(date => new Date(date))
      .sort((a, b) => a.getTime() - b.getTime());

    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
    const series: LineSeriesOption[] = ['实际装船量', '预报装船量', '实际到港量', '预报到港量'].map((type, index) => {
      const typeData = groupedData[type] || [];
      // 确保数据按日期排序
      typeData.sort((a, b) => a.date.getTime() - b.date.getTime());
      
      return {
        name: type,
        type: 'line',
        data: typeData.map(item => item.value),
        yAxisIndex: 0,
        itemStyle: {
          color: colors[index]
        },
        lineStyle: {
          color: colors[index],
          width: 2
        },
        symbol: 'circle',
        symbolSize: 8,
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
          fontSize: 12,
          color: colors[index]
        }
      };
    });

    // 计算同比增长
    const actualShipmentData = groupedData['实际装船量'] || [];
    const yoyData = actualShipmentData.map(current => {
      const prevYearDate = new Date(current.date);
      prevYearDate.setFullYear(prevYearDate.getFullYear() - 1);
      
      const prevYearData = actualShipmentData.find(d => {
        const isSameMonth = d.date.getMonth() === prevYearDate.getMonth();
        const isSameHalf = (d.date.getDate() > 15) === (current.date.getDate() > 15);
        return isSameMonth && isSameHalf;
      });
      
      if (!prevYearData) return null;
      return Number(((current.value - prevYearData.value) / prevYearData.value * 100).toFixed(2));
    });

    // 添加同比增长曲线
    series.push({
      name: '实际装船量同比增幅',
      type: 'line',
      yAxisIndex: 1,
      data: yoyData,
      itemStyle: {
        color: colors[4]
      },
      lineStyle: {
        color: colors[4],
        width: 2
      },
      symbol: 'circle',
      symbolSize: 8,
      label: {
        show: true,
        position: 'top',
        formatter: '{c}%',
        fontSize: 12,
        color: colors[4]
      }
    });

    return {
      color: colors,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: { 
        data: ['实际装船量', '预报装船量', '实际到港量', '预报到港量', '实际装船量同比增幅'],
        textStyle: { fontSize: 12 }
      },
      grid: { right: '10%', top: '15%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: allDates.map(date => {
          const month = date.getMonth() + 1;
          const isSecondHalf = date.getDate() > 15;
          return `${date.getFullYear()}/${month}${isSecondHalf ? '下' : '上'}`;
        }),
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 12
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '数量(万吨)',
          position: 'left',
          axisLabel: {
            fontSize: 12
          }
        },
        {
          type: 'value',
          name: '同比增幅(%)',
          position: 'right',
          axisLine: { show: true },
          axisLabel: { 
            formatter: '{value}%',
            fontSize: 12
          }
        }
      ],
      series
    };
  };

  const getBoxplotOption = (): EChartsOption => {
    if (!data?.monthly_comparison) return {};

    // Debug: 打印原始数据
    console.log('Original Data:', data.monthly_comparison);

    // 只按月份分组，不考虑年份，并确保数据是数值类型
    const monthlyStats = data.monthly_comparison
      .filter(item => item.type === "实际到港量")
      .reduce((acc, curr) => {
        const month = new Date(curr.month).getMonth() + 1;
        const value = Number(curr.value);
        if (!acc[month]) acc[month] = [];
        if (!isNaN(value)) {  // 只添加有效的数值
          acc[month].push(value);
        }
        return acc;
      }, {} as Record<number, number[]>);

    // Debug: 打印按月分组的数据
    console.log('Monthly Stats:', monthlyStats);

    // 计算箱线图数据
    const boxplotData: number[][] = [];
    const outlierData: [number, number][] = [];

    Array.from({ length: 12 }, (_, i) => i + 1).forEach(month => {
      const values = monthlyStats[month] || [];
      
      // Debug: 打印每月的值
      console.log(`Month ${month} values:`, values);
      
      // 如果某月没有数据，使用null
      if (values.length === 0) {
        boxplotData[month - 1] = [0, 0, 0, 0, 0];  // ECharts需要有值，即使是0
        return;
      }

      // 对数据点计算统计量
      const sortedValues = [...values].sort((a, b) => a - b);
      
      // 如果只有一个数据点，使用该值作为所有统计量
      if (sortedValues.length === 1) {
        const value = sortedValues[0];
        boxplotData[month - 1] = [value, value, value, value, value];
        return;
      }

      // 如果有两个数据点，使用较小值作为最小值和Q1，较大值作为最大值和Q3，平均值作为中位数
      if (sortedValues.length === 2) {
        const min = sortedValues[0];
        const max = sortedValues[1];
        const median = (min + max) / 2;
        boxplotData[month - 1] = [min, min, median, max, max];
        return;
      }

      // 对三个或更多数据点计算完整的箱线图统计量
      const q1 = sortedValues[Math.floor((sortedValues.length - 1) * 0.25)];
      const q3 = sortedValues[Math.floor((sortedValues.length - 1) * 0.75)];
      const median = sortedValues[Math.floor((sortedValues.length - 1) * 0.5)];
      const iqr = q3 - q1;
      const lowerBound = q1 - 1.5 * iqr;
      const upperBound = q3 + 1.5 * iqr;

      // 找出异常值
      const monthOutliers = values.filter(v => v < lowerBound || v > upperBound);
      monthOutliers.forEach(value => {
        outlierData.push([month - 1, value]);  // ECharts的索引从0开始
      });

      // 计算有效的最小值和最大值（排除异常值）
      const validValues = values.filter(v => v >= lowerBound && v <= upperBound);
      const min = validValues.length > 0 ? Math.min(...validValues) : sortedValues[0];
      const max = validValues.length > 0 ? Math.max(...validValues) : sortedValues[sortedValues.length - 1];

      boxplotData[month - 1] = [min, q1, median, q3, max];

      // Debug: 打印计算结果
      console.log(`Month ${month} stats:`, { min, q1, median, q3, max, outliers: monthOutliers });
    });

    // Debug: 打印最终数据
    console.log('Boxplot Data:', boxplotData);
    console.log('Outlier Data:', outlierData);

    return {
      title: { text: '月度到港量波动分析' },
      tooltip: { 
        trigger: 'item',
        formatter: (params: any) => {
          if (params.seriesIndex === 1) {
            return `异常值: ${params.data[1].toFixed(2)}万吨`;
          }
          const data = params.data;
          return `最小值: ${data[1].toFixed(2)}万吨<br/>
                  下四分位: ${data[2].toFixed(2)}万吨<br/>
                  中位数: ${data[3].toFixed(2)}万吨<br/>
                  上四分位: ${data[4].toFixed(2)}万吨<br/>
                  最大值: ${data[5].toFixed(2)}万吨`;
        }
      },
      grid: { left: '10%', right: '10%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: Array.from({ length: 12 }, (_, i) => `${i + 1}月`),
        boundaryGap: true,
        nameGap: 30,
        splitArea: { show: false },
        axisLabel: {
          formatter: '{value}'
        }
      },
      yAxis: {
        type: 'value',
        name: '到港量(万吨)',
        splitArea: { show: true }
      },
      series: [
        {
          name: '月度到港量',
          type: 'boxplot',
          data: boxplotData,
          itemStyle: {
            borderColor: '#3B82F6',
            borderWidth: 2
          },
          boxWidth: ['40%', '40%'],
          tooltip: { trigger: 'item' }
        },
        {
          name: '异常值',
          type: 'scatter',
          data: outlierData,
          itemStyle: {
            color: '#EF4444'
          }
        }
      ]
    };
  };

  // 二、结构对比分析
  const getAccuracyBarOption = (): EChartsOption => {
    if (!data) return {};

    const categories = ['装船量', '到港量'];
    const actualData = [data.current_shipment, data.current_arrival];
    const forecastData = [data.forecast_shipment, data.next_arrival];
    const diffData = actualData.map((actual, i) => Number((actual - forecastData[i]).toFixed(2)));
    const diffPercentage = diffData.map((diff, i) => (diff / forecastData[i] * 100).toFixed(2));

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['实际值', '预报值', '差额'] },
      grid: { top: '10%', bottom: '15%', containLabel: true },
      xAxis: { type: 'value', name: '数量(万吨)' },
      yAxis: { type: 'category', data: categories },
      series: [
        {
          name: '实际值',
          type: 'bar',
          stack: 'total',
          color: '#3B82F6',
          label: { show: true },
          data: actualData
        },
        {
          name: '预报值',
          type: 'bar',
          stack: 'total',
          color: '#10B981',
          label: { show: true },
          data: forecastData
        },
        {
          name: '差额',
          type: 'bar',
          stack: 'total',
          color: '#F59E0B',
          label: {
            show: true,
            formatter: (params: any) => `${params.value}(${diffPercentage[params.dataIndex]}%)`
          },
          data: diffData
        }
      ]
    };
  };

  const getHeatmapOption = (data: SoybeanImportData): EChartsOption => {
    // 只获取今年的月份
    const currentYear = new Date().getFullYear();
    const months = Array.from(new Set(data.monthly_comparison
      .filter(item => new Date(item.month).getFullYear() === currentYear)
      .map(item => item.month)))
      .sort();
    
    // 计算同比增长率
    const calculateYoY = (currentMonth: string, type: string) => {
      const currentItem = data.monthly_comparison.find(d => d.month === currentMonth && d.type === type);
      const prevDate = new Date(currentMonth);
      prevDate.setFullYear(prevDate.getFullYear() - 1);
      const prevMonth = prevDate.toISOString().split('T')[0].substring(0, 7);
      const prevItem = data.monthly_comparison.find(d => 
        d.month.startsWith(prevMonth) && d.type === type
      );
      
      if (!currentItem || !prevItem) return null;
      return Number(((currentItem.value - prevItem.value) / prevItem.value * 100).toFixed(2));
    };

    // 生成热力图数据
    const heatmapData: [number, number, number][] = [];
    const types = ['实际装船量', '实际到港量'];
    
    types.forEach((type, typeIndex) => {
      months.forEach((month, monthIndex) => {
        const yoyValue = calculateYoY(month, type);
        // 只添加有效的数据点
        if (yoyValue !== null && !isNaN(yoyValue) && isFinite(yoyValue)) {
          heatmapData.push([monthIndex, typeIndex, yoyValue]);
        }
      });
    });

    // 计算有效值的范围
    const validValues = heatmapData.map(item => item[2]);
    const minValue = Math.min(...validValues);
    const maxValue = Math.max(...validValues);
    const absMax = Math.max(Math.abs(minValue), Math.abs(maxValue));

    return {
      title: { text: '同比增幅热力图' },
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const month = months[params.data[0]];
          const type = types[params.data[1]];
          const value = params.data[2];
          const date = new Date(month);
          return `${date.getFullYear()}年${date.getMonth() + 1}月<br/>${type}<br/>同比增幅: ${value.toFixed(2)}%`;
        }
      },
      grid: { 
        left: '15%',
        right: '15%',
        top: '10%',
        bottom: '20%'
      },
      xAxis: {
        type: 'category',
        data: months.map(month => {
          const date = new Date(month);
          return `${date.getMonth() + 1}月`;
        }),
        splitArea: {
          show: true
        },
        axisLabel: {
          interval: 0
        }
      },
      yAxis: {
        type: 'category',
        data: types,
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: -absMax,
        max: absMax,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        text: ['增长', '下降'],
        inRange: {
          color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
        }
      },
      series: [{
        name: '同比增幅',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: true,
          formatter: (params: any) => `${params.data[2].toFixed(1)}%`,
          color: '#000000',
          fontSize: 12,
          position: 'inside'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
  };

  // 三、供应链波动性分析
  const getSupplyChainOption = (): EChartsOption => {
    if (!data?.monthly_comparison) return {};

    // 计算运输周期散点图数据
    const scatterData = data.monthly_comparison.map(item => {
      const shipDate = new Date(item.month);
      const arrivalDate = new Date(shipDate);
      arrivalDate.setDate(arrivalDate.getDate() + 40); // 假设平均40天运输周期
      return [
        shipDate.getTime(),
        arrivalDate.getTime(),
        item.value,
        item.type === 'actual' ? item.value : null
      ];
    });

    return {
      title: { text: '运输周期分析' },
      tooltip: {
        formatter: (params: any) => {
          const shipDate = new Date(params.value[0]);
          const arrivalDate = new Date(params.value[1]);
          return `装船: ${shipDate.toLocaleDateString()}<br/>` +
                 `到港: ${arrivalDate.toLocaleDateString()}<br/>` +
                 `数量: ${params.value[2]}万吨`;
        }
      },
      xAxis: {
        type: 'time',
        name: '装船日期'
      },
      yAxis: {
        type: 'time',
        name: '到港日期'
      },
      series: [{
        name: '运输周期',
        type: 'scatter',
        symbolSize: (data) => Math.sqrt(data[2]) / 2,
        data: scatterData,
        itemStyle: {
          color: '#3B82F6',
          opacity: 0.7
        }
      }]
    };
  };

  // 四、政策与市场关联分析
  const getPolicyTimelineOption = (): EChartsOption => {
    if (!data?.policy_events) return {};

    const events = data.policy_events;
    const eventTypes = Array.from(new Set(events.map(e => e.type)));
    const typeColors = {
      '贸易政策': '#3B82F6',
      '供应因素': '#10B981',
      '产业政策': '#F59E0B',
      '市场因素': '#EF4444'
    };

    // 将事件按时间排序
    const sortedEvents = [...events].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return {
      title: {
        text: '政策事件影响分析',
        left: 'center',
        top: 10
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params: any) {
          const event = events.find(e => e.date === params.name);
          if (!event) return '';
          
          return `<div style="font-weight: bold">${event.date}</div>
                  <div style="margin-top: 5px">${event.event}</div>
                  <div style="margin-top: 5px; color: #666">${event.impact}</div>
                  <div style="margin-top: 5px">
                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${typeColors[event.type as keyof typeof typeColors]}"></span>
                    <span style="margin-left: 5px">${event.type}</span>
                  </div>`;
        }
      },
      legend: {
        data: eventTypes,
        bottom: 10,
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8,
        textStyle: {
          color: '#666'
        }
      },
      xAxis: {
        type: 'category',
        data: sortedEvents.map(e => e.date),
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}月${date.getDate()}日`;
          },
          interval: 0,
          rotate: 45
        },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'category',
        data: eventTypes,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      },
      series: eventTypes.map(type => ({
        name: type,
        type: 'scatter',
        symbolSize: 15,
        data: sortedEvents
          .filter(e => e.type === type)
          .map(e => ({
            name: e.date,
            value: [e.date, type],
            itemStyle: {
              color: typeColors[type as keyof typeof typeColors]
            }
          }))
      }))
    };
  };

  // 五、风险预警仪表盘
  const getRiskRadarOption = (): EChartsOption => {
    const indicators = [
      { name: '预报偏差率', max: 100 },
      { name: '市场集中度', max: 100 },
      { name: '库存消耗比', max: 100 },
      { name: '价格波动率', max: 100 }
    ];

    // 示例风险指标数据
    const riskData = [85, 92, 65, 78];

    return {
      radar: {
        indicator: indicators,
        shape: 'circle',
        splitNumber: 4,
        axisName: {
          color: '#333',
          backgroundColor: '#eee',
          padding: [3, 5]
        }
      },
      series: [{
        type: 'radar',
        data: [{
          value: riskData,
          name: '风险指标',
          itemStyle: {
            color: '#3B82F6'
          },
          areaStyle: {
            color: 'rgba(59, 130, 246, 0.2)'
          },
          lineStyle: {
            color: '#3B82F6',
            width: 2
          }
        }]
      }]
    };
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">加载中...</div>;
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 relative inline-block">
            大豆进口分析
            <span className="absolute -top-3 -right-12 bg-gradient-to-r from-yellow-400 to-yellow-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-md transform rotate-12">
              PRO
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            基于大豆进口数据，分析进口量、装船量、到港量等指标的波动特征
          </p>
          
          <p className="mt-2 text-gray-500">最后更新: {data?.date ? new Date(data.date).toLocaleDateString('zh-CN') : '-'}</p>
        </div>

        {/* 分析维度切换Tab */}
        <div className="mb-8">
          <nav className="flex space-x-4" aria-label="Tabs">
            {[
              { id: 'overview', name: '概述' },
              { id: 'trend', name: '时间序列趋势' },
              { id: 'structure', name: '结构对比' },
              { id: 'supply', name: '供应链波动' },
              // { id: 'policy', name: '政策关联' },
              // { id: 'risk', name: '风险预警' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                } px-3 py-2 font-medium text-sm rounded-md`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* 概述 */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="prose max-w-none">
                <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-6">关键差异原因分析</h2>
                <p className="text-sm text-gray-500 mb-4">数据来源：<a href="https://wms.mofcom.gov.cn/dzncpjkxxfb/index.html" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">商务部大宗农产品进口信息发布</a></p>
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">1. 装船与预报装船差异</h3>
                    <div className="pl-4 space-y-4">
                      <div>
                        <p className="font-medium text-gray-800 mb-2">时间差因素：</p>
                        <p className="text-gray-700">
                          实际装船反映已执行合同，而预报装船是未来计划。本期装船激增可能是前期延迟订单的集中兑现（如船期调整或港口拥堵缓解）。
                        </p>
                      </div>
                      <div>
                        <p className="font-medium text-gray-800 mb-2">市场预期变化：</p>
                        <p className="text-gray-700 mb-2">
                          预报装船暴跌反映未来采购意愿下降。可能原因包括：
                        </p>
                        <ul className="list-disc pl-5 space-y-2 text-gray-700">
                          <li>
                            <span className="font-medium">价格波动：</span>
                            国际大豆价格下跌（如美国大豆降价吸引短期采购，但远期价格预期回升导致买家观望）；
                          </li>
                          <li>
                            <span className="font-medium">库存策略：</span>
                            国内油厂因压榨利润波动调整采购节奏，优先消化现有库存；
                          </li>
                          <li>
                            <span className="font-medium">政策调整：</span>
                            中国可能减少对特定来源（如巴西）的依赖，转向多元化采购。
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">2. 到港量波动</h3>
                    <div className="pl-4 space-y-4">
                      <div>
                        <p className="font-medium text-gray-800 mb-2">运输周期影响：</p>
                        <p className="text-gray-700">
                          实际到港量受海运时间（通常南美至中国需35-45天）制约。本期到港量激增可能对应2-3个月前装船高峰，而下月预报下降则反映当前装船量收缩的滞后效应。
                        </p>
                      </div>
                      <div>
                        <p className="font-medium text-gray-800 mb-2">港口吞吐能力：</p>
                        <p className="text-gray-700">
                          685.54万吨的下期预报到港量（同比+24.65%）显示短期集中到港压力，可能引发港口滞港风险（如网页8提到的装卸效率冲突）。
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 时间序列趋势分析 */}
        {activeTab === 'trend' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">趋势对比分析</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">📊 <strong>趋势分析要点：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><span className="text-blue-600">实际装船量</span>：关注南美/北美大豆收获季节性波动（3-5月/9-11月），以及中美贸易摩擦带来的供应链重构</li>
                  <li><span className="text-green-600">预报装船量</span>：重点观察与实际装船量的偏差趋势，尤其是贸易商延期/取消订单导致的预报下修</li>
                  <li><span className="text-amber-600">实际到港量</span>：验证35-45天南美航程规律，关注港口拥堵、天气等不确定因素造成的延误</li>
                  <li><span className="text-red-600">预报到港量</span>：结合油厂压榨利润和库存周期，预判国内供需错配风险</li>
                  <li><span className="text-purple-600">同比增幅</span>：剔除季节性因素后的真实增长，需要结合基数效应解读（如去年同期是否异常）</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 建议：重点关注预报值断崖式下跌（{'>'}30%）或连续下修情况，可能暗示供应链风险</p>
              </div>
              <ReactECharts option={getTrendLineOption()} style={{ height: '400px' }} />
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">月度波动分析</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">📈 <strong>波动特征解读：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>箱体区间</strong>：25%~75%分位数范围，反映正常波动区间。超出此区间需结合天气、政策等因素分析</li>
                  <li><strong>中位线走势</strong>：体现季节性规律，如巴西大豆3-5月集中到港，美豆10-12月到港高峰</li>
                  <li><strong>异常值分布</strong>：单个异常值（如台风导致延误）vs.连续异常（如贸易政策调整）的识别</li>
                  <li><strong>波动区间</strong>：区间扩大预示市场不确定性上升，可能需要调整采购策略</li>
                  <li><strong>季节性特征</strong>：不同月份波动特征差异，帮助优化库存和采购时点</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 注意：极端天气、地缘政治等黑天鹅事件可能打破历史波动规律</p>
              </div>
              <ReactECharts option={getBoxplotOption()} style={{ height: '400px' }} />
            </div>
          </div>
        )}

        {/* 结构对比分析 */}
        {activeTab === 'structure' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">预报准确度分析</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">🎯 <strong>预报偏差分析：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>实际值解读</strong>：需剔除不可抗力因素（如天气、罢工）导致的偏差，聚焦可控部分</li>
                  <li><strong>预报值失准</strong>：关注系统性偏差（如始终低估）vs.随机偏差，优化预测模型</li>
                  <li><strong>差额成因</strong>：装船差额（贸易商行为）vs.到港差额（物流因素）的区分</li>
                  <li><strong>预警机制</strong>：±20%为一般预警阈值，但特殊时期（如疫情）可适当放宽至±30%</li>
                  <li><strong>修正建议</strong>：持续偏差{'>'}30%时建议校准预测模型参数，尤其是季节性因子</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 提示：预报准确度通常在旺季好于淡季，建议分季节设置差异化阈值</p>
              </div>
              <ReactECharts option={getAccuracyBarOption()} style={{ height: '400px' }} />
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">同比增幅热力图</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">🌡️ <strong>变化强度分析：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>颜色解读</strong>：深红/深蓝（|变化|{'>'}50%）通常暗示结构性变化，需特别关注</li>
                  <li><strong>时序特征</strong>：连续3个月同向变化可能预示趋势性转变，而非短期波动</li>
                  <li><strong>联动效应</strong>：装船量与到港量变化不同步时，需排查运力/港口瓶颈</li>
                  <li><strong>季节性偏差</strong>：同比数据受基期影响，建议结合历史同期均值判断</li>
                  <li><strong>预警信号</strong>：相邻月份变化方向反转，可能暗示市场拐点来临</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 建议：结合国际大豆期货走势和人民币汇率变化综合研判</p>
              </div>
              <ReactECharts option={data ? getHeatmapOption(data) : {}} style={{ height: '400px' }} />
            </div>
          </div>
        )}

        {/* 供应链波动性分析 */}
        {activeTab === 'supply' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">运输周期分析</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">🚢 <strong>物流效率分析：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>周期规律</strong>：巴西航线35-40天，美国航线40-45天，阿根廷38-42天，偏离需关注</li>
                  <li><strong>运力分布</strong>：散点密集度反映运力饱和度，疏密不均预示调度优化空间</li>
                  <li><strong>异常识别</strong>：单点延误（天气）vs.系统性延误（港口拥堵）的甄别</li>
                  <li><strong>效率评估</strong>：实际周期/标准周期{'>'}1.2时，需启动应急预案</li>
                  <li><strong>优化建议</strong>：基于历史数据，为不同航线和季节制定差异化物流方案</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 关注：南美收获季和中国春节前后的运力压力峰值</p>
              </div>
              <ReactECharts option={getSupplyChainOption()} style={{ height: '400px' }} />
            </div>
          </div>
        )}

        {/* 政策与市场关联分析 */}
        {activeTab === 'policy' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">政策事件影响分析</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">📋 <strong>政策冲击评估：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>时点影响</strong>：贸易政策（即时）vs.产业政策（滞后），区分短期和长期效应</li>
                  <li><strong>传导路径</strong>：直接影响（关税）vs.间接影响（补贴），量化政策扰动</li>
                  <li><strong>叠加研判</strong>：多重政策同时实施时，注意互补或对冲效应</li>
                  <li><strong>区域差异</strong>：中美关系vs.中巴合作，评估供应链重构影响</li>
                  <li><strong>应对策略</strong>：预判政策持续性，适时调整采购和库存策略</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 建议：建立政策预警库，定期评估政策风险暴露度</p>
              </div>
              <ReactECharts option={getPolicyTimelineOption()} style={{ height: '400px' }} />
            </div>
          </div>
        )}

        {/* 风险预警仪表盘 */}
        {activeTab === 'risk' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-2">风险预警指标</h2>
              <div className="mb-4 text-sm text-gray-600">
                <p className="mb-2">⚠️ <strong>风险监测维度：</strong></p>
                <ul className="list-disc pl-5 space-y-1">
                  <li><strong>预报偏差</strong>：持续偏差{'>'}30%或波动加剧{'>'}50%时，预示预测模型失效风险</li>
                  <li><strong>市场集中度</strong>：CR4{'>'}85%为高度集中，需防范供应商议价风险</li>
                  <li><strong>库存周转</strong>：可用天数{'<'}15天为警戒线，{'<'}10天需启动应急采购</li>
                  <li><strong>价格波动</strong>：30天波动率{'>'}15%且趋势向上，关注成本上涨风险</li>
                  <li><strong>综合研判</strong>：多维度风险指标联动上升，考虑调整采购策略</li>
                </ul>
                <p className="mt-2 text-xs text-gray-500">* 注意：风险指标权重应随市场环境动态调整</p>
              </div>
              <ReactECharts option={getRiskRadarOption()} style={{ height: '400px' }} />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SoybeanImport;