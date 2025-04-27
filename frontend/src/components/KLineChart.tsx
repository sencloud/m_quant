import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Radio } from 'antd';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  open_interest: number;
}

interface SRLevel {
  price: number;
  type: 'Support' | 'Resistance';
  strength: number;
  start_time: string;
  break_time: string | null;
  retest_times: string[];
  timeframe: string;
}

interface KLineChartProps {
  contract?: string;
}

const KLineChart = React.forwardRef<any, KLineChartProps>((props, ref) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [period, setPeriod] = React.useState('30');

  // 在组件挂载时将echarts实例暴露给父组件
  useEffect(() => {
    if (ref && 'current' in ref) {
      ref.current = {
        getEchartsInstance: () => chartInstance.current
      };
    }
  }, [ref]);

  // 更新最高最低点标记
  const updateMarkPoints = () => {
    if (!chartInstance.current) return;
    
    const option = chartInstance.current.getOption();
    const klineData = (option.series as any)[0].data as number[][];
    if (!klineData || !klineData.length) return;

    // 获取当前可视区域的数据
    const dataZoom = (option.dataZoom as any)[0];
    const start = Math.floor(klineData.length * dataZoom.start / 100);
    const end = Math.ceil(klineData.length * dataZoom.end / 100);
    const visibleData = klineData.slice(start, end);

    // 计算最高最低点
    interface MarkPoint {
      value: number;
      coord: [number, number];
      symbol: string;
      symbolSize: number;
      itemStyle: { color: string };
    }
    
    const highPoints: MarkPoint[] = [];
    const lowPoints: MarkPoint[] = [];
    
    visibleData.forEach((item: number[], index: number) => {
      const high = item[3];  // 最高价
      const low = item[2];   // 最低价
      
      // 将当前点与前后的点比较，找出局部最高最低点
      const prev = visibleData[index - 1];
      const next = visibleData[index + 1];
      
      if ((!prev || high >= prev[3]) && (!next || high >= next[3])) {
        highPoints.push({
          value: high,
          coord: [start + index, high],
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: { color: '#ef232a' }
        });
      }
      
      if ((!prev || low <= prev[2]) && (!next || low <= next[2])) {
        lowPoints.push({
          value: low,
          coord: [start + index, low],
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: { color: '#14b143' }
        });
      }
    });

    // 按价格排序并只取前三个
    highPoints.sort((a, b) => b.value - a.value);
    lowPoints.sort((a, b) => a.value - b.value);

    // 过滤掉相邻的价差小于10的点
    const filteredHighPoints = highPoints.reduce((acc: MarkPoint[], curr) => {
      if (acc.length === 0 || Math.abs(acc[acc.length - 1].value - curr.value) >= 10) {
        acc.push(curr);
      }
      return acc;
    }, []).slice(0, 3);

    const filteredLowPoints = lowPoints.reduce((acc: MarkPoint[], curr) => {
      if (acc.length === 0 || Math.abs(acc[acc.length - 1].value - curr.value) >= 10) {
        acc.push(curr);
      }
      return acc;
    }, []).slice(0, 3);

    chartInstance.current.setOption({
      series: [{
        markPoint: {
          data: [...filteredHighPoints, ...filteredLowPoints]
        }
      }]
    });
  };

  // 计算初始展示位置
  const calculateInitialRange = (dataLength: number) => {
    if (dataLength <= 100) {
      return { start: 0, end: 100 };
    }
    return {
      start: Math.max(0, ((dataLength - 100) / dataLength) * 100),
      end: 100
    };
  };

  const fetchData = async () => {
    if (!props.contract) return;
    try {
      const response = await axios.get(API_ENDPOINTS.market.kline(period), {
        params: { contract: props.contract }
      });
      const { kline_data: data, sr_levels } = response.data;
      
      // 更新图表
      if (chartInstance.current) {
        const dates = data.map((item: KLineData) => item.date);
        const klineData = data.map((item: KLineData) => [
          Number(item.open),
          Number(item.close),
          Number(item.low),
          Number(item.high)
        ]);
        
        // 成交量数据
        const volumes = data.map((item: KLineData) => ({
          value: Number(item.volume),
          itemStyle: {
            color: Number(item.close) >= Number(item.open) ? '#ef232a' : '#14b143'
          }
        }));

        // 生成支撑位和阻力位的标记线数据
        const formattedMarkLines = [];

        // 调试日志
        console.log('K线时间序列:', dates);
        console.log('支撑阻力位数据:', sr_levels);

        // 处理支撑位和阻力位
        for (const level of sr_levels) {
          // 确保日期格式匹配
          const startIndex = dates.findIndex((date: string) => {
            const klineDate = new Date(date).getTime();
            const levelDate = new Date(level.start_time).getTime();
            return klineDate === levelDate;
          });

          const endIndex = level.break_time 
            ? dates.findIndex((date: string) => {
                const klineDate = new Date(date).getTime();
                const levelDate = new Date(level.break_time!).getTime();
                return klineDate === levelDate;
              })
            : dates.length - 1;

          // 调试日志
          console.log(`支撑阻力位 ${level.price} (${level.type}):`, {
            startTime: level.start_time,
            breakTime: level.break_time,
            startIndex,
            endIndex
          });

          if (startIndex === -1) continue;

          const lineColor = level.type === 'Support' ? '#14b143' : '#ef232a';
          const lineWidth = level.strength; // 使用强度作为线宽

          formattedMarkLines.push([{
            name: level.type,
            coord: [startIndex, level.price],
            lineStyle: {
              color: lineColor,
              type: 'dashed',
              width: lineWidth
            },
            label: {
              show: true,
              position: 'middle',
              formatter: level.price.toFixed(0),
              color: lineColor,
              fontSize: 11,
              backgroundColor: level.type === 'Support' 
                ? 'rgba(20, 177, 67, 0.1)' 
                : 'rgba(239, 35, 42, 0.1)',
              padding: [2, 4]
            }
          }, {
            coord: [endIndex, level.price]
          }]);

          // 如果有重测时间点，添加重测标记
          level.retest_times.forEach((retestTime: string) => {
            const retestIndex = dates.findIndex((date: string) => {
              const klineDate = new Date(date).getTime();
              const levelDate = new Date(retestTime).getTime();
              return klineDate === levelDate;
            });

            if (retestIndex !== -1) {
              formattedMarkLines.push([{
                name: `${level.type === 'Support' ? '支撑位测试' : '阻力位测试'}`,
                coord: [retestIndex, level.price],
                symbol: 'circle',
                symbolSize: 5,
                lineStyle: {
                  color: lineColor,
                  type: 'dashed',
                  width: 1
                },
                label: {
                  show: true,
                  position: 'middle',
                  formatter: `${level.type === 'Support' ? '支撑位测试' : '阻力位测试'}`,
                  color: lineColor,
                  fontSize: 10,
                  backgroundColor: level.type === 'Support' 
                    ? 'rgba(20, 177, 67, 0.1)' 
                    : 'rgba(239, 35, 42, 0.1)',
                  padding: [2, 4]
                }
              }, {
                coord: [retestIndex + 1, level.price]
              }]);
            }
          });
        }

        // 调试日志
        console.log('格式化后的标记线数据:', formattedMarkLines);

        const { start, end } = calculateInitialRange(dates.length);

        chartInstance.current.setOption({
          xAxis: [{
            data: dates
          }, {
            data: dates
          }],
          dataZoom: [{
            start: start,
            end: end
          }, {
            start: start,
            end: end
          }],
          series: [{
            name: '豆粕主力',
            type: 'candlestick',
            data: klineData,
            itemStyle: {
              color: '#ef232a',
              color0: '#14b143',
              borderColor: '#ef232a',
              borderColor0: '#14b143'
            },
            markLine: {
              symbol: ['none', 'none'],
              data: formattedMarkLines,
              animation: false,
              emphasis: {
                lineStyle: {
                  width: 2
                }
              }
            }
          }, {
            name: 'Volume',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes
          }]
        });

        // 初始化后立即更新最高最低点标记
        setTimeout(() => {
          updateMarkPoints();
        }, 0);
      }
    } catch (error) {
      console.error('获取K线数据失败:', error);
    }
  };

  // 当合约变化时重新获取数据
  useEffect(() => {
    if (props.contract) {
      fetchData();
    }
  }, [props.contract]);

  useEffect(() => {
    if (chartRef.current) {
      chartInstance.current = echarts.init(chartRef.current);
      
      const option = {
        animation: false,
        legend: {
          bottom: 10,
          left: 'center',
          data: ['豆粕主力']
        },
        toolbox: {
          right: '5%',
          top: '5%',
          feature: {
            dataZoom: {
              yAxisIndex: 'none',
              title: {
                zoom: '区域缩放',
                back: '区域缩放还原'
              }
            },
            restore: {
              title: '还原'
            },
            saveAsImage: {
              title: '保存为图片'
            },
            fullScreen: {
              show: true,
              title: {
                fullScreen: '全屏',
                cancelFullScreen: '退出全屏'
              }
            }
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: function (params: any) {
            if (params[0].componentSubType === 'candlestick') {
              const kline = params[0];
              return [
                '时间: ' + kline.axisValue + '<br/>',
                '开: ' + kline.data[1] + '<br/>',
                '高: ' + kline.data[4] + '<br/>',
                '低: ' + kline.data[3] + '<br/>',
                '收: ' + kline.data[2]
              ].join('');
            } else {
              return '成交量: ' + params[0].data.value;
            }
          }
        },
        grid: [
          {
            left: '5%',
            right: '5%',
            top: '5%',
            height: '60%'
          },
          {
            left: '5%',
            right: '5%',
            top: '70%',
            height: '20%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: [],
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            splitNumber: 20,
            min: 'dataMin',
            max: 'dataMax'
          },
          {
            type: 'category',
            gridIndex: 1,
            data: [],
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            splitNumber: 20,
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        yAxis: [
          {
            scale: true,
            splitArea: {
              show: true
            }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
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
            top: '92%',
            start: 50,
            end: 100
          }
        ],
        series: [
          {
            name: '豆粕主力',
            type: 'candlestick',
            data: [],
            itemStyle: {
              color: '#ef232a',
              color0: '#14b143',
              borderColor: '#ef232a',
              borderColor0: '#14b143'
            },
            markPoint: {
              data: [],
              label: {
                formatter: function(param: any) {
                  return typeof param.value === 'number' ? param.value.toFixed(0) : param.value;
                }
              }
            }
          },
          {
            name: 'Volume',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: []
          }
        ]
      };

      chartInstance.current.setOption(option);
    }

    // 监听缩放事件
    if (chartInstance.current) {
      chartInstance.current.on('dataZoom', updateMarkPoints);
    }

    // 判断当前是否为交易时间
    const isTradeTime = () => {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();

        const day = now.getDay();
        if (day === 0 || day === 6) { // 0是周日，6是周六
          return false;
        }
        
        // 上午9:00-11:30
        if ((hours === 9 && minutes >= 0) || 
            (hours === 10) || 
            (hours === 11 && minutes <= 30)) {
            return true;
        }
        
        // 下午13:30-15:00
        if ((hours === 13 && minutes >= 30) || 
            (hours === 14)) {
            return true;
        }
        
        // 晚上21:00-23:00
        if ((hours === 21) || 
            (hours === 22)) {
            return true;
        }
        
        return false;
    };

    // 只在交易时间内每60秒刷新一次数据
    const timer = setInterval(() => {
        if (isTradeTime()) {
            fetchData();
        }
      }, 60000);

    return () => {
      clearInterval(timer);
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, [period]);

  const handlePeriodChange = (e: any) => {
    setPeriod(e.target.value);
  };

  return (
    <div>
      <div className="mb-4">
        <Radio.Group value={period} onChange={handlePeriodChange}>
          <Radio.Button value="1">1分钟</Radio.Button>
          <Radio.Button value="5">5分钟</Radio.Button>
          <Radio.Button value="15">15分钟</Radio.Button>
          <Radio.Button value="30">30分钟</Radio.Button>
          <Radio.Button value="60">1小时</Radio.Button>
          <Radio.Button value="D">日线</Radio.Button>
        </Radio.Group>
      </div>
      <div ref={chartRef} style={{ width: '100%', height: '600px' }} />
    </div>
  );
});

export default KLineChart; 