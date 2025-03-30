import React, { useState, useEffect } from 'react';
import { OptionBasic, OptionDaily } from '../../types/market';
import { Card, Tag, Radio, Typography, Divider, Button, Tooltip, Select } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface OptionDataProps {
  optionBasics: OptionBasic[];
  optionDaily: OptionDaily[];
}

const OptionData: React.FC<OptionDataProps> = ({ optionBasics }) => {
  const [optionType, setOptionType] = useState<string>('C');
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [selectedContract, setSelectedContract] = useState<string>('');
  const [optionDailyData, setOptionDailyData] = useState<OptionDaily[]>([]);
  const [loading, setLoading] = useState(false);

  // 获取所有可用的合约月份
  const availableContracts = React.useMemo(() => {
    if (!Array.isArray(optionBasics)) return [];
    const contracts = Array.from(new Set(optionBasics.map(option => option.opt_code || '')));
    return contracts.filter(Boolean).sort((a, b) => a.localeCompare(b));
  }, [optionBasics]);

  // 初始化选中合约
  useEffect(() => {
    if (availableContracts.length > 0 && !selectedContract) {
      setSelectedContract(availableContracts[0]);
    }
  }, [availableContracts]);

  // 获取期权日线数据
  const fetchOptionDailyData = async (tsCode: string) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_ENDPOINTS.market.options}/daily/${tsCode}`);
      console.log('Raw option daily data:', response.data);
      setOptionDailyData(response.data);
    } catch (error) {
      console.error('Error fetching option daily data:', error);
      setOptionDailyData([]);
    } finally {
      setLoading(false);
    }
  };

  // 当选择期权变化时获取数据
  useEffect(() => {
    if (selectedOption) {
      fetchOptionDailyData(selectedOption);
    }
  }, [selectedOption]);

  // 按合约和期权类型过滤并排序
  const filteredOptions = React.useMemo(() => {
    if (!Array.isArray(optionBasics)) return [];
    
    return optionBasics
      .filter(option => 
        option.call_put === optionType && 
        (option.opt_code === selectedContract || !selectedContract)
      )
      .sort((a, b) => {
        // 先按到期日排序
        const dateCompare = a.maturity_date.localeCompare(b.maturity_date);
        if (dateCompare !== 0) return dateCompare;
        
        // 同到期日按行权价排序
        return optionType === 'C' 
          ? a.exercise_price - b.exercise_price  // 看涨期权按行权价升序
          : b.exercise_price - a.exercise_price; // 看跌期权按行权价降序
      });
  }, [optionBasics, optionType, selectedContract]);

  // 获取当前选中期权的信息
  const selectedOptionInfo = React.useMemo(() => {
    if (!selectedOption || !Array.isArray(optionBasics)) return null;
    return optionBasics.find(option => option.ts_code === selectedOption);
  }, [selectedOption, optionBasics]);

  // 准备K线图数据
  const chartData = React.useMemo(() => {
    if (!Array.isArray(optionDailyData) || optionDailyData.length === 0) return {
      dates: [],
      data: [],
      volumes: []
    };

    const sortedData = [...optionDailyData].sort((a, b) => 
      a.trade_date.localeCompare(b.trade_date)
    );

    return {
      dates: sortedData.map(item => item.trade_date),
      data: sortedData.map(item => item.settle || item.close || item.pre_settle || 0),
      volumes: sortedData.map(item => Number(item.vol || 0))
    };
  }, [optionDailyData]);

  // 禁用自动刷新
  useEffect(() => {
    const cleanup = () => {
      // 清理任何可能的定时器或订阅
      if (selectedOption) {
        setOptionDailyData([]); // 清理数据
      }
    };
    return cleanup;
  }, []);

  // 当选择期权变化时获取数据
  useEffect(() => {
    let mounted = true;
    
    const fetchData = async () => {
      if (!selectedOption) return;
      
      try {
        setLoading(true);
        const response = await axios.get(`${API_ENDPOINTS.market.options}/daily/${selectedOption}`);
        if (mounted) {
          setOptionDailyData(response.data);
        }
      } catch (error) {
        console.error('Error fetching option daily data:', error);
        if (mounted) {
          setOptionDailyData([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      mounted = false;
    };
  }, [selectedOption]);

  // 添加数据监控
  useEffect(() => {
    if (optionDailyData && optionDailyData.length > 0) {
      console.log('Sample data structure:', {
        first: optionDailyData[0],
        chartData: chartData.data[0]
      });
    }
  }, [optionDailyData, chartData]);

  const hasChartData = chartData.dates.length > 0;

  const getChartOption = () => {
    if (!hasChartData) {
      return {
        title: {
          text: loading ? '数据加载中...' : '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16
          }
        }
      };
    }

    const callColor = '#52c41a'; // 绿色 - 看涨
    const putColor = '#1890ff';  // 蓝色 - 看跌
    const themeColor = optionType === 'C' ? callColor : putColor;
    
    try {
      return {
        animation: true,
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#ccc',
          borderWidth: 1,
          textStyle: {
            color: '#333'
          },
          formatter: function(params: any[]) {
            const date = params[0].axisValue;
            let result = `<div style="font-weight: bold; margin-bottom: 5px;">${date}</div>`;
            
            // 结算价数据
            const priceData = params.find(p => p.seriesName === '结算价');
            if (priceData) {
              result += `
                <div style="margin: 3px 0;">
                  <span>结算价：</span><span style="float: right; font-weight: bold;">${priceData.data}</span>
                </div>`;
            }
            
            // 成交量数据
            const volData = params.find(p => p.seriesName === '成交量');
            if (volData) {
              result += `<div style="margin-top: 5px; padding-top: 5px; border-top: 1px dashed #ccc;">
                <span>成交量：</span><span style="float: right; font-weight: bold;">${volData.value}</span>
              </div>`;
            }
            
            return result;
          }
        },
        legend: {
          data: ['结算价', '成交量'],
          textStyle: {
            color: '#666'
          }
        },
        grid: [{
          left: '3%',
          right: '3%',
          height: '60%'
        }, {
          left: '3%',
          right: '3%',
          top: '75%',
          height: '15%'
        }],
        xAxis: [{
          type: 'category',
          data: chartData.dates,
          scale: true,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#ddd' } },
          axisLabel: {
            color: '#666',
            fontSize: 12,
            rotate: 30
          },
          min: 'dataMin',
          max: 'dataMax',
          axisPointer: { show: true }
        }, {
          type: 'category',
          gridIndex: 1,
          data: chartData.dates,
          scale: true,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#ddd' } },
          axisLabel: { show: false },
          axisTick: { show: false }
        }],
        yAxis: [{
          scale: true,
          splitLine: { show: true, lineStyle: { color: '#eee', type: 'dashed' } },
          axisLabel: {
            color: '#666',
            formatter: '{value} 元'
          }
        }, {
          gridIndex: 1,
          splitNumber: 3,
          axisLine: { lineStyle: { color: '#ddd' } },
          axisLabel: {
            color: '#666',
            formatter: '{value} 手'
          },
          splitLine: { show: false }
        }],
        dataZoom: [{
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 0,
          end: 100
        }, {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: '0%',
          height: 20,
          start: 0,
          end: 100
        }],
        series: [{
          name: '结算价',
          type: 'line',
          data: chartData.data,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            color: themeColor,
            width: 2
          },
          itemStyle: {
            color: themeColor,
            borderWidth: 2,
            borderColor: '#fff'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: themeColor === callColor ? 'rgba(82, 196, 26, 0.2)' : 'rgba(24, 144, 255, 0.2)'
              },
              {
                offset: 1,
                color: 'rgba(255, 255, 255, 0.2)'
              }
            ])
          }
        }, {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: chartData.volumes,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{
                offset: 0,
                color: themeColor === callColor ? '#ef5350' : '#26a69a'
              }, {
                offset: 1,
                color: themeColor === callColor ? '#ef9a9a' : '#80cbc4'
              }]
            }
          }
        }]
      };
    } catch (error) {
      console.error('Error generating chart options:', error);
      return {
        title: {
          text: '图表生成错误，请刷新页面重试',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#f5222d',
            fontSize: 16
          }
        }
      };
    }
  };

  return (
    <Card 
      className="mb-8 shadow-md hover:shadow-lg transition-shadow duration-300"
      bordered={false}
      bodyStyle={{ padding: '24px' }}
    >
      <div className="flex justify-between items-center mb-6">
        <Title level={4} style={{ margin: 0 }}>期权数据分析</Title>
        <Tooltip title="下载数据">
          <Button icon={<DownloadOutlined />} type="primary" ghost>
            下载数据
          </Button>
        </Tooltip>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div>
              <Text strong>合约月份：</Text>
              <Select
                value={selectedContract}
                onChange={setSelectedContract}
                style={{ width: 120 }}
                className="ml-2"
              >
                {availableContracts.map(contract => (
                  <Option key={contract} value={contract}>{contract}</Option>
                ))}
              </Select>
            </div>
            <div>
              <Text strong>期权类型：</Text>
              <Radio.Group 
                value={optionType} 
                onChange={e => setOptionType(e.target.value)}
                buttonStyle="solid"
                className="ml-2"
              >
                <Radio.Button value="C" className="rounded-l-md">
                  看涨期权
                </Radio.Button>
                <Radio.Button value="P" className="rounded-r-md">
                  看跌期权
                </Radio.Button>
              </Radio.Group>
            </div>
          </div>
          <div>
            <Text type="secondary">
              数据来源: Tushare
            </Text>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-1 bg-white rounded-lg shadow">
          <div className="p-4">
            <Text strong>可选期权列表</Text>
          </div>
          <div className="max-h-[600px] overflow-y-auto">
            {filteredOptions.map(option => (
              <div
                key={option.ts_code}
                className={`
                  p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors
                  ${option.ts_code === selectedOption ? 'bg-blue-50' : ''}
                `}
                onClick={() => setSelectedOption(option.ts_code)}
              >
                <div className="font-medium text-gray-900">{option.name}</div>
                <div className="text-sm text-gray-500 mt-1">
                  <span>行权价: {option.exercise_price}</span>
                  <span className="mx-2">|</span>
                  <span>到期日: {option.maturity_date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="md:col-span-3 bg-white rounded-lg shadow">
          {selectedOption && selectedOptionInfo ? (
            <>
              <div className="p-4 bg-gray-50 rounded-t-lg">
                <div className="flex flex-wrap items-center">
                  <div className="mr-6">
                    <Text type="secondary">期权名称:</Text>
                    <div className="mt-1">
                      <Text strong className="text-lg">
                        {selectedOptionInfo.name} 
                      </Text>
                      <Tag 
                        color={optionType === 'C' ? 'green' : 'blue'} 
                        className="ml-2"
                      >
                        {optionType === 'C' ? '看涨' : '看跌'}
                      </Tag>
                    </div>
                  </div>
                  <Divider type="vertical" className="h-10" />
                  <div className="mr-6">
                    <Text type="secondary">行权价:</Text>
                    <div className="mt-1">
                      <Text strong>{selectedOptionInfo.exercise_price}</Text>
                    </div>
                  </div>
                  <Divider type="vertical" className="h-10" />
                  <div>
                    <Text type="secondary">到期日:</Text>
                    <div className="mt-1">
                      <Text strong>{selectedOptionInfo.maturity_date}</Text>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="p-4">
                <ReactECharts 
                  option={getChartOption()} 
                  style={{ height: '600px', width: '100%' }}
                  notMerge={true}
                />
              </div>
            </>
          ) : (
            <div className="text-center py-24 text-gray-500">
              <div className="text-6xl mb-4 opacity-30">🔍</div>
              {filteredOptions.length > 0 
                ? "请先选择一个期权合约" 
                : `当前没有可用的${optionType === 'C' ? '看涨' : '看跌'}期权数据`
              }
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default OptionData; 