import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';
import Layout from '../components/layout/Layout';
import { Card, Skeleton, Tabs, Tooltip, Select, List, Tag, Statistic, Row, Col, Progress } from 'antd';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { HeatMapOutlined, LineChartOutlined, HistoryOutlined, AreaChartOutlined } from '@ant-design/icons';
import MDEditor from '@uiw/react-md-editor';
import { EChartsOption } from 'echarts';

interface KeyEvent {
  date: string;
  event: string;
  impact: string;
}

interface MonthlyStats {
  month: number;
  up_days: number;
  total_days: number;
  up_prob: number;
  std: number;
  avg_volatility: number;
}

interface ContractData {
  heatmap_data: Record<string, Record<number, MonthlyStats>>;
  monthly_avg_stats: MonthlyStats[];
}

interface MonthlyProbabilityData {
  M01: ContractData;
  M05: ContractData;
  M09: ContractData;
  key_events: KeyEvent[];
}

interface CostComparisonData {
  date: string;
  cost: number;
  futures_price: number;
  price_diff: number;
  price_ratio: number;
}

interface PriceRangeData {
  bottom_price: number;
  current_price: number;
  bottom_range_start: number;
  bottom_range_end: number;
  bounce_success_rate: number;
  avg_bounce_amplitude: number;
  avg_bottom_duration: number;
  historical_bottoms: Array<{
    start_date: string;
    end_date: string;
    duration: number;
    bounce_amplitude: number;
    lowest_price: number;
    contract: string;
  }>;
}

type ContractType = 'M01' | 'M05' | 'M09';

const ProAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('1');
  const [selectedContract, setSelectedContract] = useState<ContractType>('M01');
  const [selectedEvent, setSelectedEvent] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('2023');
  const [selectedMonth, setSelectedMonth] = useState<string>('1');
  const [eventPriceData, setEventPriceData] = useState<any[]>([]);
  const [isLoadingEventPrice, setIsLoadingEventPrice] = useState(false);

  const { data: probabilityData, isLoading } = useQuery<MonthlyProbabilityData>({
    queryKey: ['monthlyProbability'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.monthlyProbability);
      return response.data;
    },
    refetchOnWindowFocus: false
  });

  const { data: costComparisonData, isLoading: isLoadingCostComparison } = useQuery<CostComparisonData[]>({
    queryKey: ['costComparison'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.futures + '/cost-comparison');
      return response.data;
    },
    refetchOnWindowFocus: false
  });

  const { data: priceRangeData, isLoading: isLoadingPriceRange } = useQuery<PriceRangeData>({
    queryKey: ['priceRange', selectedContract],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.market.futures + '/price-range-analysis', {
        params: { contract: selectedContract }
      });
      return response.data;
    },
    refetchOnWindowFocus: false
  });

  // 热力图配置
  const getHeatmapOption = (data: MonthlyProbabilityData | undefined, contract: string): EChartsOption => {
    if (!data) return {};
    
    const contractData = data[contract as keyof Omit<MonthlyProbabilityData, 'key_events'>];
    if (!contractData) return {};

    // 获取合约月份
    const contractMonth = parseInt(contract.slice(1));
    
    // 生成月份数组，从合约月份开始
    const months: number[] = [];
    for (let i = 0; i < 12; i++) {
      const month = ((contractMonth + i - 1) % 12) + 1;
      months.push(month);
    }

    // 获取所有合约名称
    const contractNames = Object.keys(contractData.heatmap_data);

    // 准备热力图数据
    const heatmapData: [number, number, number][] = [];
    contractNames.forEach((contractName, yIndex) => {
      months.forEach((month, xIndex) => {
        const stats = contractData.heatmap_data[contractName][month];
        if (stats) {
          // 使用上涨概率作为热力图的值
          heatmapData.push([xIndex, yIndex, stats.up_prob * 100]);
        }
      });
    });

    return {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const xIndex = params.data[0];
          const yIndex = params.data[1];
          const value = params.data[2];
          const contractName = contractNames[yIndex];
          const month = months[xIndex];
          const stats = contractData.heatmap_data[contractName][month];
          
          return `
            <div style="font-weight: bold">${contractName} - ${month}月</div>
            <div>上涨概率: ${value.toFixed(2)}%</div>
            <div>上涨天数: ${stats.up_days}天</div>
            <div>总天数: ${stats.total_days}天</div>
            <div>标准差: ${stats.std.toFixed(4)}</div>
            <div>平均波动率: ${(stats.avg_volatility * 100).toFixed(2)}%</div>
          `;
        }
      },
      grid: {
        top: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: months.map((m: number) => `${m}月`),
        splitArea: {
          show: true
        }
      },
      yAxis: {
        type: 'category',
        data: contractNames,
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: 0,
        max: 100,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        formatter: '{value}%',
        inRange: {
          color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
        }
      },
      series: [{
        name: '上涨概率',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: true,
          formatter: (params: any) => {
            const value = params.data[2];
            return `${value.toFixed(1)}%`;
          }
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

  // 核密度估计图配置
  const getKdeOption = () => {
    if (!probabilityData) return {};
    
    const contractData = probabilityData[selectedContract];
    const monthlyProbs = contractData.monthly_avg_stats;
    const months = monthlyProbs.map(item => item.month);
    const probs = monthlyProbs.map(item => item.up_prob);
    
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const month = params[0].dataIndex + 1;
          const prob = params[0].value;
          return `${month}月平均上涨概率: ${(prob * 100).toFixed(2)}%`;
        }
      },
      xAxis: {
        type: 'category',
        data: months.map(m => `${m}月`),
        name: '月份'
      },
      yAxis: {
        type: 'value',
        name: '上涨概率',
        axisLabel: {
          formatter: (value: number) => `${(value * 100).toFixed(0)}%`
        }
      },
      series: [{
        data: probs,
        type: 'line',
        smooth: true,
        showSymbol: false,
        areaStyle: {
          opacity: 0.3
        },
        lineStyle: {
          width: 2
        },
        label: {
          show: false
        }
      }]
    };
  };

  // 关键事件时间线配置
  const getTimelineOption = () => {
    if (!probabilityData) return {};
    
    const events = probabilityData.key_events;
    const data = events.map(event => {
      const date = new Date(event.date);
      const month = date.getMonth() + 1; // 1-12月
      // 将月份映射到0-1之间的值，1月最低，12月最高
      const yValue = (month - 1) / 11;
      
      return {
        value: [event.date, yValue],
        itemStyle: {
          color: event.impact.includes('下跌') || event.impact.includes('利空') ? '#52c41a' : 
                 event.impact.includes('上涨') || event.impact.includes('利多') ? '#f5222d' : '#1890ff'
        },
        symbolSize: 12,
        emphasis: {
          scale: true,
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        }
      };
    });
    
    return {
      title: {
        text: '关键事件时间线',
        subtext: '点击事件查看价格走势',
        left: 'center',
        top: 20,
        textStyle: {
          fontSize: 18,
          fontWeight: 'bold'
        },
        subtextStyle: {
          fontSize: 14,
          color: '#666'
        }
      },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#ccc',
        borderWidth: 1,
        textStyle: {
          color: '#333'
        },
        position: function (point: any, params: any, dom: any, rect: any, size: any) {
          return [point[0], point[1] - 10];
        },
        formatter: (params: any) => {
          const event = probabilityData.key_events.find(e => e.date === params.value[0]);
          if (!event) return '';
          const impactColor = event.impact.includes('下跌') || event.impact.includes('利空') ? '#52c41a' : 
                             event.impact.includes('上涨') || event.impact.includes('利多') ? '#f5222d' : '#1890ff';
          return `
            <div style="font-weight: bold; margin-bottom: 5px;">${event.date}</div>
            <div style="margin: 5px 0;">${event.event}</div>
            <div style="color: ${impactColor}; margin-top: 5px;">
              影响: ${event.impact}
            </div>
          `;
        }
      },
      grid: {
        top: '25%',
        bottom: '15%',
        left: '3%',
        right: '4%',
        containLabel: true
      },
      xAxis: {
        type: 'time',
        axisLabel: {
          formatter: '{yyyy}',
          color: '#666',
          rotate: 45,
          margin: 15
        },
        splitLine: {
          show: true,
          lineStyle: {
            type: 'dashed',
            color: '#ddd'
          }
        },
        axisLine: {
          lineStyle: {
            color: '#999'
          }
        },
        axisTick: {
          lineStyle: {
            color: '#999'
          }
        }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 1,
        splitNumber: 12,
        axisLabel: {
          formatter: (value: number) => {
            const month = Math.round(value * 11) + 1;
            return `${month}月`;
          },
          color: '#666'
        },
        splitLine: {
          show: true,
          lineStyle: {
            type: 'dashed',
            color: '#ddd'
          }
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: '#999'
          }
        }
      },
      series: [{
        name: '关键事件',
        type: 'scatter',
        data: data,
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            const event = probabilityData.key_events.find(e => e.date === params.value[0]);
            if (!event) return '';
            return event.event;
          },
          color: '#666',
          fontSize: 12,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          padding: [4, 8],
          borderRadius: 4,
          distance: 10,
          align: 'left',
          verticalAlign: 'bottom'
        },
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          lineStyle: {
            color: '#999',
            type: 'dashed',
            width: 1
          },
          data: probabilityData.key_events.map(event => ({
            xAxis: event.date
          }))
        }
      }],
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: 0,
          end: 100,
          height: 20,
          bottom: 0,
          borderColor: 'transparent',
          backgroundColor: '#e2e2e2',
          fillerColor: 'rgba(167,183,204,0.4)',
          handleStyle: {
            color: '#fff',
            borderColor: '#ACB8D1'
          },
          textStyle: {
            color: '#666'
          }
        }
      ]
    };
  };

  // 获取事件价格数据
  const fetchEventPriceData = async (eventDate: string) => {
    setIsLoadingEventPrice(true);
    try {
      const response = await axios.get(`${API_ENDPOINTS.market.futures}/event-price`, {
        params: {
          event_date: eventDate,
          contract: selectedContract,
          days_before: 30,
          days_after: 30
        }
      });
      setEventPriceData(response.data);
    } catch (error) {
      console.error('获取事件价格数据失败:', error);
    } finally {
      setIsLoadingEventPrice(false);
    }
  };

  // 修改事件点击处理函数
  const handleEventClick = (params: any) => {
    if (params.data) {
      const eventDate = params.data.value[0];
      setSelectedEvent(eventDate);
      fetchEventPriceData(eventDate);
    }
  };

  // 找到最近的时间点
  const findNearestDate = (targetDate: string, dateList: string[]) => {
    const target = new Date(targetDate).getTime();
    let nearestDate = dateList[0];
    let minDiff = Math.abs(new Date(dateList[0]).getTime() - target);
    
    for (const date of dateList) {
      const diff = Math.abs(new Date(date).getTime() - target);
      if (diff < minDiff) {
        minDiff = diff;
        nearestDate = date;
      }
    }
    return nearestDate;
  };

  // 修改K线图配置
  const getKLineOption = (eventDate: string) => {
    if (isLoadingEventPrice) {
      return {
        title: {
          text: '数据加载中...',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16
          }
        }
      };
    }

    if (!eventPriceData || eventPriceData.length === 0) {
      return {
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16
          }
        }
      };
    }

    // 准备K线图数据
    const klineData = eventPriceData.map(item => [
      item.open,
      item.close,
      item.low,
      item.high
    ]);
    
    // 准备成交量数据
    const volumeData = eventPriceData.map(item => item.vol);
    
    // 准备日期数据
    const dateData = eventPriceData.map(item => {
      const date = item.trade_date;
      return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;
    });

    // 找到最近的时间点
    const nearestDate = findNearestDate(eventDate, dateData);
    
    return {
      title: {
        text: '事件前后价格走势',
        subtext: `事件日期: ${eventDate} - ${probabilityData?.key_events.find(e => e.date === eventDate)?.event || ''}`,
        left: 'center',
        top: 0,
        textStyle: {
          fontSize: 18,
          fontWeight: 'bold'
        },
        subtextStyle: {
          fontSize: 14,
          color: '#666'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: function(params: any) {
          if (!params || params.length === 0) return '';
          
          // 检查是否是成交量区域
          if (params[0].seriesName === '成交量') {
            return `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>
                    <div>成交量: ${params[0].data}</div>`;
          }
          
          // K线区域
          const date = params[0].axisValue;
          const klineData = params[0].data;
          
          let tooltipContent = `
            <div style="font-weight: bold; margin-bottom: 5px;">${date}</div>
            <div>开盘: ${klineData[1]}</div>
            <div>收盘: ${klineData[2]}</div>
            <div>最低: ${klineData[3]}</div>
            <div>最高: ${klineData[4]}</div>
          `;
          
          return tooltipContent;
        }
      },
      legend: {
        data: ['K线', '成交量', 'MA5'],
        top: 60
      },
      grid: [
        {
          left: '5%',
          right: '3%',
          height: '60%',
          top: '15%'
        },
        {
          left: '5%',
          right: '3%',
          top: '80%',
          height: '15%'
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: dateData,
          axisLabel: {
            rotate: 45
          },
          gridIndex: 0
        },
        {
          type: 'category',
          data: dateData,
          axisLabel: {
            rotate: 45
          },
          gridIndex: 1
        }
      ],
      yAxis: [
        {
          type: 'value',
          scale: true,
          splitArea: {
            show: true
          },
          gridIndex: 0
        },
        {
          type: 'value',
          scale: true,
          splitArea: {
            show: false
          },
          gridIndex: 1
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 0,
          end: 100
        },
        {
          show: true,
          type: 'slider',
          bottom: '5%',
          xAxisIndex: [0, 1],
          start: 0,
          end: 100
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData,
          itemStyle: {
            color: '#ef5350',
            color0: '#26a69a',
            borderColor: '#ef5350',
            borderColor0: '#26a69a'
          },
          xAxisIndex: 0,
          yAxisIndex: 0,
          markLine: {
            silent: true,
            symbol: ['none', 'none'],
            data: [
              {
                xAxis: nearestDate,
                lineStyle: {
                  color: '#1890ff',
                  width: 3,
                  type: 'dashed'
                },
                label: {
                  formatter: `事件发生（${probabilityData?.key_events.find(e => e.date === eventDate)?.event || ''}）`,
                  position: 'end',
                  color: '#fff',
                  backgroundColor: '#1890ff',
                  padding: [4, 8],
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 'bold'
                }
              }
            ]
          }
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumeData,
          itemStyle: {
            color: function(params: any) {
              const klineData = eventPriceData[params.dataIndex];
              return klineData.close >= klineData.open ? '#ef5350' : '#26a69a';
            }
          }
        },
        {
          name: 'MA5',
          type: 'line',
          data: calculateMA(5, eventPriceData),
          smooth: true,
          lineStyle: {
            opacity: 0.5
          },
          xAxisIndex: 0,
          yAxisIndex: 0
        }
      ],
      markArea: {
        silent: true,
        data: [[
          {
            xAxis: eventDate,
            itemStyle: {
              color: 'rgba(24, 144, 255, 0.1)'
            }
          },
          {
            xAxis: eventDate
          }
        ]]
      }
    };
  };

  // 计算移动平均线
  const calculateMA = (dayCount: number, data: any[]) => {
    const result = [];
    for (let i = 0, len = data.length; i < len; i++) {
      if (i < dayCount - 1) {
        result.push('-');
        continue;
      }
      let sum = 0;
      for (let j = 0; j < dayCount; j++) {
        sum += data[i - j].close;
      }
      result.push((sum / dayCount).toFixed(2));
    }
    return result;
  };

  // 修改事件处理函数
  const handleContractChange = (value: ContractType) => {
    setSelectedContract(value);
  };

  const handleYearChange = (value: string) => {
    setSelectedYear(value);
  };

  const handleMonthChange = (value: string) => {
    setSelectedMonth(value);
  };

  // 获取合约标签颜色
  const getContractTagColor = (contract: ContractType) => {
    return selectedContract === contract ? 'blue' : 'default';
  };

  // 添加useEffect钩子，在组件加载时自动选择最新事件
  useEffect(() => {
    if (probabilityData && probabilityData.key_events && probabilityData.key_events.length > 0) {
      // 按日期排序，获取最新事件
      const sortedEvents = [...probabilityData.key_events].sort((a, b) => 
        new Date(b.date).getTime() - new Date(a.date).getTime()
      );
      const latestEvent = sortedEvents[0];
      
      // 设置选中的事件并加载价格数据
      setSelectedEvent(latestEvent.date);
      fetchEventPriceData(latestEvent.date);
    }
  }, [probabilityData]);

  useEffect(() => {
    if (activeTab === '1') {
      // 不需要额外的 resize 处理，ReactECharts 会自动处理
    }
  }, [activeTab]);

  // 修改月度统计表格部分
  const getMonthlyStatsColumns = (contract: string) => {
    const contractData = probabilityData?.[contract as keyof Omit<MonthlyProbabilityData, 'key_events'>];
    if (!contractData) return [];

    return [
      {
        title: '月份',
        dataIndex: 'month',
        key: 'month',
        render: (month: number) => `${month}月`
      },
      {
        title: '上涨天数',
        dataIndex: 'up_days',
        key: 'up_days',
        sorter: (a: MonthlyStats, b: MonthlyStats) => a.up_days - b.up_days
      },
      {
        title: '总天数',
        dataIndex: 'total_days',
        key: 'total_days',
        sorter: (a: MonthlyStats, b: MonthlyStats) => a.total_days - b.total_days
      },
      {
        title: '上涨概率',
        dataIndex: 'up_prob',
        key: 'up_prob',
        render: (prob: number) => `${(prob * 100).toFixed(2)}%`,
        sorter: (a: MonthlyStats, b: MonthlyStats) => a.up_prob - b.up_prob
      },
      {
        title: '标准差',
        dataIndex: 'std',
        key: 'std',
        render: (std: number) => std.toFixed(4),
        sorter: (a: MonthlyStats, b: MonthlyStats) => a.std - b.std
      },
      {
        title: '平均波动率',
        dataIndex: 'avg_volatility',
        key: 'avg_volatility',
        render: (vol: number) => `${(vol * 100).toFixed(2)}%`,
        sorter: (a: MonthlyStats, b: MonthlyStats) => a.avg_volatility - b.avg_volatility
      }
    ];
  };

  // 修改事件列表渲染
  const renderEventList = () => {
    const events = probabilityData?.key_events || [];
    return (
      <List
        dataSource={events}
        renderItem={(event: KeyEvent) => (
          <List.Item>
            <List.Item.Meta
              title={event.date}
              description={`${event.event} (${event.impact})`}
            />
          </List.Item>
        )}
      />
    );
  };

  // 成本价格比对图配置
  const getCostComparisonOption = () => {
    if (!costComparisonData) return {};
    
    const dates = costComparisonData.map(item => item.date);
    const costs = costComparisonData.map(item => item.cost);
    const futuresPrices = costComparisonData.map(item => item.futures_price);
    const priceDiffs = costComparisonData.map(item => item.price_diff);
    const priceRatios = costComparisonData.map(item => item.price_ratio);
    
    return {
      title: {
        text: '豆粕成本与期货价格比对',
        left: 'center',
        top: 0
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['成本价', '期货价', '价差', '价格比'],
        top: 30
      },
      grid: [
        {
          left: '5%',
          right: '5%',
          top: '20%',
          height: '35%'
        },
        {
          left: '5%',
          right: '5%',
          top: '65%',
          height: '25%'
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          axisLabel: {
            formatter: (value: string) => {
              return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`;
            }
          },
          gridIndex: 0
        },
        {
          type: 'category',
          data: dates,
          axisLabel: {
            formatter: (value: string) => {
              return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`;
            }
          },
          gridIndex: 1
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: '价格',
          gridIndex: 0
        },
        {
          type: 'value',
          name: '价差',
          gridIndex: 1
        },
        {
          type: 'value',
          name: '价格比',
          gridIndex: 1,
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 0,
          end: 100
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: '5%',
          start: 0,
          end: 100
        }
      ],
      series: [
        {
          name: '成本价',
          type: 'line',
          data: costs,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: {
            color: '#f5222d'
          },
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 2
          }
        },
        {
          name: '期货价',
          type: 'line',
          data: futuresPrices,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: {
            color: '#52c41a'
          },
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 2
          }
        },
        {
          name: '价差',
          type: 'bar',
          data: priceDiffs,
          xAxisIndex: 1,
          yAxisIndex: 1,
          itemStyle: {
            color: function(params: any) {
              return params.data >= 0 ? '#f5222d' : '#52c41a';
            }
          }
        },
        {
          name: '价格比',
          type: 'line',
          data: priceRatios.map(ratio => (ratio * 100).toFixed(2)),
          xAxisIndex: 1,
          yAxisIndex: 2,
          itemStyle: {
            color: '#1890ff'
          },
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 2
          }
        }
      ]
    };
  };

  // 价格区间分析图表配置
  const getPriceRangeOption = () => {
    if (!priceRangeData) return {};

    const historicalBottoms = priceRangeData.historical_bottoms;
    const dates = historicalBottoms.map(b => b.start_date);
    const durations = historicalBottoms.map(b => b.duration);
    const amplitudes = historicalBottoms.map(b => b.bounce_amplitude);
    const prices = historicalBottoms.map(b => b.lowest_price);

    return {
      title: {
        text: '历史底部区域分析',
        left: 'center',
        top: 0
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: function(params: any) {
          const idx = params[0].dataIndex;
          const bottom = historicalBottoms[idx];
          return `
            <div style="font-weight: bold">${bottom.start_date} 至 ${bottom.end_date}</div>
            <div>持续时间: ${bottom.duration}天</div>
            <div>反弹幅度: ${bottom.bounce_amplitude.toFixed(2)}%</div>
            <div>最低价: ${bottom.lowest_price}</div>
          `;
        }
      },
      legend: {
        data: ['持续时间', '反弹幅度', '最低价'],
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
        top: 100
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          formatter: (value: string) => {
            return value.slice(0, 4) + '\n' + value.slice(4, 6) + '-' + value.slice(6, 8);
          },
          interval: 0,
          rotate: 45
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '天数/幅度(%)',
          position: 'left'
        },
        {
          type: 'value',
          name: '价格',
          position: 'right'
        }
      ],
      series: [
        {
          name: '持续时间',
          type: 'bar',
          data: durations,
          itemStyle: {
            color: '#91cc75'
          }
        },
        {
          name: '反弹幅度',
          type: 'line',
          data: amplitudes,
          itemStyle: {
            color: '#ee6666'
          },
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 2
          }
        },
        {
          name: '最低价',
          type: 'line',
          yAxisIndex: 1,
          data: prices,
          itemStyle: {
            color: '#5470c6'
          },
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 2
          }
        }
      ]
    };
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 relative inline-block">
            历史规律分析
            <span className="absolute -top-3 -right-12 bg-gradient-to-r from-yellow-400 to-yellow-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-md transform rotate-12">
              PRO
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            基于过去十多年的历史数据，分析豆粕期货的月度涨跌概率
          </p>
        </div>

        <div className="mb-6 flex space-x-4">
          <Tag 
            color={getContractTagColor('M01')} 
            style={{ cursor: 'pointer', padding: '4px 12px', fontSize: '16px' }}
            onClick={() => handleContractChange('M01')}
          >
            豆粕01月合约
          </Tag>
          <Tag 
            color={getContractTagColor('M05')} 
            style={{ cursor: 'pointer', padding: '4px 12px', fontSize: '16px' }}
            onClick={() => handleContractChange('M05')}
          >
            豆粕05月合约
          </Tag>
          <Tag 
            color={getContractTagColor('M09')} 
            style={{ cursor: 'pointer', padding: '4px 12px', fontSize: '16px' }}
            onClick={() => handleContractChange('M09')}
          >
            豆粕09月合约
          </Tag>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: '1',
              label: (
                <span>
                  <HeatMapOutlined />
                  &nbsp; 热力图与核密度分析
                </span>
              ),
              children: (
                <Card>
                  {isLoading ? (
                    <Skeleton active />
                  ) : (
                    <>
                      <div className="mb-4">
                        <h2 className="text-xl font-bold text-gray-800">月度上涨概率热力图</h2>
                        <p className="text-sm text-gray-500 mb-2">注：第一列数据为空是为了剔除合约开始月和交割月的数据，确保分析结果的准确性</p>
                        <ReactECharts 
                          option={getHeatmapOption(probabilityData, selectedContract)} 
                          style={{ height: '600px' }}
                          notMerge={true}
                          lazyUpdate={true}
                        />
                      </div>
                      <div className="mt-8">
                        <h2 className="text-xl font-bold text-gray-800">月度上涨概率核密度估计</h2>
                        <ReactECharts option={getKdeOption()} style={{ height: '400px' }} />
                      </div>
                      <div className="mt-8 prose max-w-none">
                        <div className="markdown-content" data-color-mode="light" style={{
                          backgroundColor: 'white',
                          padding: '20px'
                        }}>
                          <MDEditor.Markdown 
                            source={`
根据豆粕期货过去十年01、05、09合约各月上涨概率统计，结合当前市场动态，分析如下：

### 一、合约季节性特征分析
1. **M01合约**  
   • **上涨概率较高的月份**：4月（56.1%）、7月（51.7%）、3月（51.1%）。  
   • **驱动因素**：  
     ◦ 4月正值南美大豆集中上市前夕，市场对供应节奏和关税政策敏感（如2025年4月中国反制美国关税导致进口成本上升，推升价格）；  
     ◦ 12月受春节前饲料企业备货需求提振，叠加北方油厂因天气或检修导致的阶段性供应紧张（如2025年4月华北地区因大风延误卸货加剧区域短缺）。

2. **M05合约**  
   • **上涨概率较高的月份**：2月（52.4%）、7月（51.1%）、8月（52.0%）。  
   • **驱动因素**：  
     ◦ 4月对应美豆新作种植意向报告发布期，种植面积下调预期常引发市场波动（如2025年USDA种植意向报告调低美豆面积，压缩天气容错率）；  
     ◦ 7-8月为北美大豆生长关键期，天气炒作频繁（如南美干旱或美豆产区降雨异常影响产量预期）。

3. **M09合约**  
   • **上涨概率较高的月份**：7月（55.3%）、4月（52.5%）、8月（51.6%）。  
   • **驱动因素**：  
     ◦ 4月受南美大豆出口节奏及国内到港延迟影响（如2025年巴西大豆因物流问题延迟到港）；  
     ◦ 6-7月为北美大豆生长期，叠加国内水产饲料需求旺季启动（如华南地区2025年4月水产饲料需求回暖支撑价格）。

-

### 二、关键事件对价格的影响
1. **政策与贸易摩擦**  
   • 中美贸易战（2018年）及2025年关税反制导致大豆进口转向南美，推高巴西大豆溢价，间接支撑豆粕价格。  
   • USDA报告（如2025年4月报告调低美豆期末库存）对远期合约影响显著，尤其是05和09合约。

2. **供应链与天气冲击**  
   • 新冠疫情（2020年）和俄乌冲突（2022年）引发全球供应链中断，加剧豆粕波动；2025年北方港口大风天气导致区域性供应紧张，进一步强化01合约年末上涨惯性。

-

### 三、未来需关注的风险点
1. **国际贸易政策**：中美关税博弈及巴西出口政策变化可能打破季节性规律。  
2. **天气与种植**：2025年美豆种植面积调低后，产区天气容错率下降，7-8月异常气候或放大09合约波动。  
3. **国内供需节奏**：二季度进口大豆到港量激增（预计4-6月到港850-1100万吨）可能压制05合约涨幅，但区域性供应分化（如北方港口卸货效率）或支撑01合约。

-

### 四、总结
1. 豆粕期货各合约的月度上涨概率反映了季节性供需、政策及天气的多重博弈。投资者需结合当期USDA报告、国内到港节奏及养殖需求周期，动态调整策略。当前背景下，01合约受政策反制及备货需求支撑，05合约关注美豆种植进展，09合约则需警惕天气升水与南美出口节奏的共振效应。
                            `}
                            style={{
                              fontSize: '14px',
                              lineHeight: '1.6',
                              color: '#333'
                            }}
                          />
                        </div>
                      </div>
                    </>
                  )}
                </Card>
              )
            },
            {
              key: '2',
              label: (
                <span>
                  <HistoryOutlined />
                  &nbsp; 关键事件影响
                </span>
              ),
              children: (
                <Card>
                  {isLoading ? (
                    <Skeleton active />
                  ) : (
                    <div>
                      <ReactECharts 
                        option={getTimelineOption()} 
                        style={{ height: '400px' }}
                        onEvents={{
                          click: handleEventClick
                        }}
                      />
                      {selectedEvent && (
                        <ReactECharts 
                          option={getKLineOption(selectedEvent)} 
                          style={{ height: '600px', marginTop: '20px' }} 
                        />
                      )}
                    </div>
                  )}
                </Card>
              )
            },
            {
              key: '3',
              label: (
                <span>
                  <LineChartOutlined />
                  &nbsp; 成本期价比
                </span>
              ),
              children: (
                <Card>
                  {isLoadingCostComparison ? (
                    <Skeleton active />
                  ) : (
                    <>
                      <div className="mb-4">
                        <h2 className="text-xl font-bold text-gray-800">豆粕成本与期货价格比对分析</h2>
                        <p className="text-sm text-gray-500 mb-2">
                          注：价差 = 成本价 - 期货价，价格比 = 成本价/期货价
                        </p>
                        <ReactECharts 
                          option={getCostComparisonOption()} 
                          style={{ height: '600px' }}
                          notMerge={true}
                          lazyUpdate={true}
                        />
                      </div>
                      <div className="mt-8 prose max-w-none">
                        <div className="markdown-content" data-color-mode="light" style={{
                          backgroundColor: 'white',
                          padding: '20px'
                        }}>
                          <MDEditor.Markdown 
                            source={`
### 豆粕成本与期货价格关系分析

1. **价差分析**
   - 正价差（成本价高于期货价）表明现货市场供应偏紧或需求旺盛
   - 负价差（成本价低于期货价）表明期货市场看涨预期较强

2. **价格比分析**
   - 价格比>1表示成本价高于期货价，可能存在套利机会
   - 价格比<1表示期货价高于成本价，需警惕价格回归风险

3. **市场启示**
   - 当价差和价格比处于历史极值时，往往预示着市场拐点
   - 可结合基本面和技术面指标，综合判断市场走势
                          `}
                            style={{
                              fontSize: '14px',
                              lineHeight: '1.6',
                              color: '#333'
                            }}
                          />
                        </div>
                      </div>
                    </>
                  )}
                </Card>
              )
            },
            {
              key: '4',
              label: (
                <span>
                  <AreaChartOutlined />
                  &nbsp; 价格区间
                </span>
              ),
              children: (
                <Card>
                  {isLoadingPriceRange ? (
                    <Skeleton active />
                  ) : (
                    <>
                      <div className="grid grid-cols-4 gap-4 mb-8">
                        <div className="bg-white rounded-lg shadow p-6">
                          <div className="text-sm text-gray-500 mb-1">历史底部价格</div>
                          <div className="text-2xl font-bold text-gray-900">
                            ¥{priceRangeData?.bottom_price.toFixed(2)}
                          </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                          <div className="text-sm text-gray-500 mb-1">当前价格</div>
                          <div className={`text-2xl font-bold ${
                            priceRangeData && priceRangeData.current_price <= priceRangeData.bottom_range_end 
                            ? 'text-green-600' 
                            : 'text-red-600'
                          }`}>
                            ¥{priceRangeData?.current_price.toFixed(2)}
                          </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                          <div className="text-sm text-gray-500 mb-1">反弹成功率</div>
                          <div className="text-2xl font-bold text-gray-900">
                            {priceRangeData?.bounce_success_rate.toFixed(2)}%
                          </div>
                          <div className="mt-2 h-2 bg-gray-200 rounded-full">
                            <div 
                              className="h-2 bg-gradient-to-r from-blue-500 to-green-500 rounded-full" 
                              style={{ width: `${priceRangeData?.bounce_success_rate}%` }}
                            />
                          </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                          <div className="text-sm text-gray-500 mb-1">平均反弹幅度</div>
                          <div className="text-2xl font-bold text-gray-900">
                            {priceRangeData?.avg_bounce_amplitude.toFixed(2)}%
                          </div>
                        </div>
                      </div>

                      <div className="mb-8 bg-white rounded-lg shadow">
                        <div className="p-6">
                          <h3 className="text-lg font-semibold text-gray-900 mb-4">底部区间分析</h3>
                          <div className="text-sm text-gray-500 mb-4">
                            底部区间定义：历史最低价（¥{priceRangeData?.bottom_price.toFixed(2)}）至其1.2倍（¥{priceRangeData?.bottom_range_end.toFixed(2)}）
                          </div>
                          <div className="text-sm text-gray-500 mb-4">
                            平均停留时间：{priceRangeData?.avg_bottom_duration}天
                          </div>
                          <ReactECharts
                            option={getPriceRangeOption()}
                            style={{ height: '400px' }}
                          />
                        </div>
                      </div>

                      <div className="bg-white rounded-lg shadow">
                        <div className="p-6">
                          <h3 className="text-lg font-semibold text-gray-900 mb-4">历史底部记录</h3>
                          <div className="space-y-4">
                            {priceRangeData?.historical_bottoms.map((item, index) => (
                              <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0">
                                <div className="font-medium text-gray-900">
                                  {item.start_date.slice(0, 4)}-{item.start_date.slice(4, 6)}-{item.start_date.slice(6, 8)} 至 {item.end_date.slice(0, 4)}-{item.end_date.slice(4, 6)}-{item.end_date.slice(6, 8)}
                                </div>
                                <div className="mt-2 flex gap-3">
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                    {item.contract}
                                  </span>
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    持续{item.duration}天
                                  </span>
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    最低价: ¥{item.lowest_price.toFixed(2)}
                                  </span>
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    反弹幅度: {item.bounce_amplitude.toFixed(2)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </Card>
              )
            }
          ]}
        />
      </div>
    </Layout>
  );
};

export default ProAnalysis; 