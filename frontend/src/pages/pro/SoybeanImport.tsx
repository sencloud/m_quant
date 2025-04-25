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
    
    const months = Array.from(new Set(data.monthly_comparison.map(item => item.month))).sort();
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
    const series: LineSeriesOption[] = ['实际装船量', '预报装船量', '实际到港量', '预报到港量'].map((type, index) => ({
      name: type,
      type: 'line',
      data: months.map(month => {
        const item = data.monthly_comparison.find(d => d.month === month && d.type === type);
        return item ? item.value : null;
      }),
      yAxisIndex: 0,
      itemStyle: {
        color: colors[index]
      },
      lineStyle: {
        color: colors[index],
        width: 2
      }
    }));

    // 添加同比增幅曲线
    series.push({
      name: '同比增幅',
      type: 'line',
      yAxisIndex: 1,
      itemStyle: {
        color: colors[4]
      },
      lineStyle: {
        color: colors[4],
        width: 2
      },
      data: months.map(month => {
        const currentItem = data.monthly_comparison.find(d => d.month === month && d.type === '实际装船量');
        const prevDate = new Date(month);
        prevDate.setFullYear(prevDate.getFullYear() - 1);
        const prevMonth = prevDate.toISOString().split('T')[0].substring(0, 7);
        const prevItem = data.monthly_comparison.find(d => 
          d.month.startsWith(prevMonth) && d.type === '实际装船量'
        );
        
        if (!currentItem || !prevItem) return null;
        return Number(((currentItem.value - prevItem.value) / prevItem.value * 100).toFixed(2));
      })
    });

    return {
      color: colors,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: { data: ['实际装船量', '预报装船量', '实际到港量', '预报到港量', '同比增幅'] },
      grid: { right: '10%' },
      xAxis: {
        type: 'category',
        data: months,
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getFullYear()}/${date.getMonth() + 1}`;
          }
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '数量(万吨)',
          position: 'left'
        },
        {
          type: 'value',
          name: '同比增幅(%)',
          position: 'right',
          axisLine: { show: true },
          axisLabel: { formatter: '{value}%' }
        }
      ],
      series
    };
  };

  const getBoxplotOption = (): EChartsOption => {
    if (!data?.monthly_comparison) return {};

    // 按月份分组计算箱线图数据
    const monthlyStats = data.monthly_comparison.reduce((acc, curr) => {
      const month = new Date(curr.month).getMonth() + 1;
      if (!acc[month]) acc[month] = [];
      acc[month].push(curr.value);
      return acc;
    }, {} as Record<number, number[]>);

    // 计算箱线图数据
    const boxData = Object.entries(monthlyStats).map(([month, values]) => {
      values.sort((a, b) => a - b);
      const q1 = values[Math.floor(values.length * 0.25)];
      const q3 = values[Math.floor(values.length * 0.75)];
      const iqr = q3 - q1;
      const min = Math.max(q1 - 1.5 * iqr, values[0]);
      const max = Math.min(q3 + 1.5 * iqr, values[values.length - 1]);
      return [min, q1, values[Math.floor(values.length * 0.5)], q3, max];
    });

    return {
      title: { text: '月度波动箱线图' },
      tooltip: { trigger: 'item' },
      grid: { left: '10%', right: '10%' },
      xAxis: {
        type: 'category',
        data: Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
      },
      yAxis: { type: 'value', name: '数量(万吨)' },
      series: [{
        name: '箱线图',
        type: 'boxplot',
        data: boxData,
        itemStyle: {
          borderColor: '#3B82F6',
          borderWidth: 2
        }
      }]
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
    const months = Array.from(new Set(data.monthly_comparison.map(item => item.month))).sort();
    
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
        if (yoyValue !== null) {
          heatmapData.push([monthIndex, typeIndex, yoyValue]);
        }
      });
    });

    const series: HeatmapSeriesOption[] = [{
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
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }];

    return {
      title: { text: '同比增幅热力图' },
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const month = months[params.data[0]];
          const type = types[params.data[1]];
          const value = params.data[2];
          return `${month}<br/>${type}<br/>同比增幅: ${value.toFixed(2)}%`;
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
        data: months,
        splitArea: {
          show: true
        },
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getFullYear()}/${date.getMonth() + 1}`;
          },
          interval: 0,
          rotate: 45
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
        min: -100,
        max: 100,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        text: ['增长', '下降'],
        inRange: {
          color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
        }
      },
      series
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
    // 示例政策事件数据
    const events = [
      { date: '2024-01', event: '中美第一阶段经贸协议执行情况评估' },
      { date: '2024-02', event: '巴西大豆收获季节开始' },
      { date: '2024-03', event: '国内油厂压榨利润转负' }
    ];

    return {
      timeline: {
        data: events.map(e => e.date),
        label: {
          formatter: function(value: string | number): string {
            const date = new Date(String(value));
            return `${date.getFullYear()}/${date.getMonth() + 1}`;
          },
          color: '#333'
        },
        lineStyle: {
          color: '#3B82F6',
          width: 2
        },
        itemStyle: {
          color: '#3B82F6',
          borderWidth: 1,
          borderColor: '#fff'
        },
        checkpointStyle: {
          color: '#3B82F6',
          borderColor: '#fff',
          borderWidth: 2
        },
        controlStyle: {
          color: '#3B82F6',
          borderColor: '#3B82F6'
        }
      },
      baseOption: {
        title: { text: '政策事件时间轴' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category' },
        yAxis: { type: 'value' }
      },
      options: events.map(event => ({
        title: { subtext: event.event },
        series: [{
          type: 'line',
          data: data?.monthly_comparison
            .filter(item => item.type === 'actual')
            .map(item => item.value),
          itemStyle: {
            color: '#3B82F6'
          },
          lineStyle: {
            color: '#3B82F6',
            width: 2
          },
          areaStyle: {
            color: '#DBEAFE'
          }
        }]
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
          <h1 className="text-3xl font-bold text-gray-900">大豆进口分析</h1>
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
              { id: 'policy', name: '政策关联' },
              { id: 'risk', name: '风险预警' }
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
                <h2 className="text-xl font-semibold text-gray-900 mb-6">一、数据概览</h2>
                <div className="space-y-4">
                  <p className="text-gray-700">
                    <span className="font-semibold">实际装船量：</span>
                    本期37.72万吨（同比+119.68%），但本月及下月预报装船量分别降至125.79万吨（同比-88.41%）、98.7万吨（同比-92.47%），呈现短期激增后断崖式下降。
                  </p>
                  <p className="text-gray-700">
                    <span className="font-semibold">到港量：</span>
                    本月实际到港983.7万吨（同比+21.92%），但下月预报到港675.48万吨（同比-40.16%），显示到港节奏前高后低。
                  </p>
                </div>

                <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-6">二、关键差异原因分析</h2>
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