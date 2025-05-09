import React, { useState, useEffect } from 'react';
import { Card, Table, DatePicker, Select, Spin, Row, Col, Statistic, Alert, Tabs, Modal, Button } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, LineChartOutlined, CalendarOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs, { Dayjs } from 'dayjs';
import { Line, Column, DualAxes } from '@ant-design/plots';
import Layout from '../components/layout/Layout';

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

const HoldingAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState('M2509');
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(5, 'day'),
    dayjs()
  ]);
  const [brokerData, setBrokerData] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [dailyData, setDailyData] = useState<any>(null);
  const [isDailyModalVisible, setIsDailyModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('broker');
  const [selectedDailyDate, setSelectedDailyDate] = useState<Dayjs>(dayjs());
  const [dailyLoading, setDailyLoading] = useState(false);

  const fetchBrokerData = async () => {
    try {
      setLoading(true);
      const [startDate, endDate] = dateRange;
      
      const res = await axios.get('http://localhost:8000/api/v1/holding/broker-holdings', {
        params: {
          symbol,
          start_date: startDate.format('YYYYMMDD'),
          end_date: endDate.format('YYYYMMDD')
        }
      });

      // 过滤掉多空持仓都为0和总成交量为0的数据
      const filteredData = res.data.data.filter((item: any) => {
        // 检查总成交量
        if (parseInt(item.summary.total_vol) === 0) {
          return false;
        }
        
        // 检查是否所有的持仓记录都是0
        const hasNonZeroHoldings = item.holdings_trend.some((trend: any) => 
          parseInt(trend.long_hld) !== 0 || parseInt(trend.short_hld) !== 0
        );
        return hasNonZeroHoldings;
      });

      const dataWithKeys = filteredData.map((item: any, index: number) => ({
        ...item,
        key: `${item.broker}-${index}`,
      }));

      setBrokerData(dataWithKeys);
    } catch (error) {
      console.error('获取期货公司持仓数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyData = async (date: string) => {
    try {
      setDailyLoading(true);
      const res = await axios.get('http://localhost:8000/api/v1/holding/daily-holdings', {
        params: {
          symbol,
          trade_date: date
        }
      });

      if (res.data.data) {
        const processedData = {
          ...res.data.data,
          top_long: res.data.data.top_long.map((item: any, index: number) => ({
            ...item,
            key: `long-${item.broker}-${index}`,
          })),
          top_short: res.data.data.top_short.map((item: any, index: number) => ({
            ...item,
            key: `short-${item.broker}-${index}`,
          })),
        };
        setDailyData(processedData);
      }
    } catch (error) {
      console.error('获取日持仓数据失败:', error);
    } finally {
      setDailyLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'broker') {
      fetchBrokerData();
    }
  }, [symbol, dateRange, activeTab]);

  useEffect(() => {
    if (activeTab === 'daily') {
      fetchDailyData(selectedDailyDate.format('YYYYMMDD'));
    }
  }, [symbol, selectedDailyDate, activeTab]);

  const renderTinyColumn = (data: any[], field: 'long_hld' | 'short_hld') => {
    const config = {
      data: data.map(item => ({
        date: item.date,
        value: item[field],
      })),
      xField: 'date',
      yField: 'value',
      height: 50,
      width: 150,
      autoFit: false,
      padding: [2, 2, 2, 2],
      columnStyle: {
        radius: [2, 2, 0, 0],
      },
      color: '#1890ff',
      tooltip: {
        title: '持仓量',
        formatter: (datum: any) => ({
          name: field === 'long_hld' ? '多头持仓' : '空头持仓',
          value: datum.value.toLocaleString(),
        }),
      },
      xAxis: false,
      yAxis: {
        label: null,
        grid: null,
      },
      meta: {
        value: {
          min: 0,
        },
      },
    };

    return <Column {...config} />;
  };

  const [selectedBroker, setSelectedBroker] = useState<any>(null);
  const [isDetailModalVisible, setIsDetailModalVisible] = useState(false);

  const showDetailModal = (broker: any) => {
    setSelectedBroker(broker);
    setIsDetailModalVisible(true);
  };

  const renderDetailChart = () => {
    if (!selectedBroker) return null;

    // 过滤掉多空持仓都为0的数据点
    const filteredTrend = selectedBroker.holdings_trend.filter((item: any) => 
      parseInt(String(item.long_hld)) !== 0 || parseInt(String(item.short_hld)) !== 0
    );

    // 确保数据格式正确
    const processedData = filteredTrend.map((item: any) => {
      const longHld = parseInt(String(item.long_hld)) || 0;
      const shortHld = parseInt(String(item.short_hld)) || 0;
      // 格式化日期：将YYYYMMDD转换为YYYY-MM-DD
      const formattedDate = item.date.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
      return {
        date: formattedDate,
        longHld,
        shortHld,
        netPosition: longHld - shortHld
      };
    });

    // 准备柱状图数据
    const columnData = processedData.flatMap((item: any) => [
      {
        date: item.date,
        持仓量: item.longHld,
        类型: '多头持仓'
      },
      {
        date: item.date,
        持仓量: item.shortHld,
        类型: '空头持仓'
      }
    ]);

    // 准备折线图数据
    const lineData = processedData.map((item: any) => ({
      date: item.date,
      净持仓: item.netPosition
    }));

    return (
      <div className="space-y-4">
        <Column
          data={columnData}
          xField="date"
          yField="持仓量"
          seriesField="类型"
          isGroup={true}
          columnWidthRatio={0.6}
          columnStyle={{
            radius: [2, 2, 0, 0],
          }}
          color={['#f5222d', '#52c41a']}
          xAxis={{
            type: 'time',
            tickCount: 5,
            label: {
              formatter: (text: string) => dayjs(text).format('MM-DD')
            }
          }}
          yAxis={{
            title: {
              text: '持仓量(手)',
            },
          }}
          meta={{
            持仓量: {
              alias: '持仓量(手)',
              formatter: (val: number) => `${val.toLocaleString()}手`
            }
          }}
          tooltip={{
            title: (title: string) => dayjs(title).format('YYYY-MM-DD'),
            formatter: (datum: any) => ({
              name: datum.类型,
              value: `${datum.持仓量.toLocaleString()}手`
            })
          }}
          legend={{
            position: 'top',
          }}
        />

        <Line
          data={lineData}
          xField="date"
          yField="净持仓"
          color="#1890ff"
          xAxis={{
            type: 'time',
            tickCount: 5,
            label: {
              formatter: (text: string) => dayjs(text).format('MM-DD')
            }
          }}
          yAxis={{
            title: {
              text: '净持仓(手)',
            },
          }}
          meta={{
            净持仓: {
              alias: '净持仓(手)',
              formatter: (val: number) => `${val.toLocaleString()}手`
            }
          }}
          tooltip={{
            title: (title: string) => dayjs(title).format('YYYY-MM-DD'),
            formatter: (datum: any) => ({
              name: '净持仓',
              value: `${datum.净持仓.toLocaleString()}手`
            })
          }}
          point={{
            size: 3,
            shape: 'circle',
            style: {
              fill: 'white',
              stroke: '#1890ff',
              lineWidth: 2,
            },
          }}
          smooth={true}
        />
      </div>
    );
  };

  const brokerColumns = [
    {
      title: '期货公司',
      dataIndex: 'broker',
      key: 'broker',
      width: 150,
      fixed: 'left' as const,
    },
    {
      title: '总成交量',
      dataIndex: ['summary', 'total_vol'],
      key: 'total_vol',
      sorter: (a: any, b: any) => a.summary.total_vol - b.summary.total_vol,
      width: 120,
    },
    {
      title: '多头持仓变化',
      dataIndex: ['summary', 'net_long_chg'],
      key: 'net_long_chg',
      width: 120,
      render: (value: number) => (
        <span style={{ color: value > 0 ? '#f5222d' : '#52c41a' }}>
          {value > 0 ? '+' : ''}{value.toLocaleString()}
        </span>
      ),
    },
    {
      title: '空头持仓变化',
      dataIndex: ['summary', 'net_short_chg'],
      key: 'net_short_chg',
      width: 120,
      render: (value: number) => (
        <span style={{ color: value > 0 ? '#f5222d' : '#52c41a' }}>
          {value > 0 ? '+' : ''}{value.toLocaleString()}
        </span>
      ),
    },
    {
      title: '净持仓变化',
      dataIndex: ['summary', 'net_position_change'],
      key: 'net_position_change',
      width: 120,
      render: (value: number) => (
        <span style={{ color: value > 0 ? '#f5222d' : '#52c41a' }}>
          {value > 0 ? '+' : ''}{value.toLocaleString()}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />}
          onClick={() => showDetailModal(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  const renderDailyView = () => {
    const longColumns = [
      {
        title: '期货公司',
        dataIndex: 'broker',
        key: 'broker',
      },
      {
        title: '持仓量',
        dataIndex: 'long_hld',
        key: 'long_hld',
        sorter: (a: any, b: any) => a.long_hld - b.long_hld,
      },
      {
        title: '持仓变化',
        dataIndex: 'long_chg',
        key: 'long_chg',
        render: (value: number) => (
          <span style={{ color: value > 0 ? '#f5222d' : value < 0 ? '#52c41a' : 'inherit' }}>
            {value > 0 ? '+' : ''}{value}
          </span>
        ),
      },
      {
        title: '影响力得分',
        dataIndex: 'impact_score',
        key: 'impact_score',
        render: (value: number) => value.toFixed(4),
        sorter: (a: any, b: any) => a.impact_score - b.impact_score,
      },
    ];

    const shortColumns = [
      {
        title: '期货公司',
        dataIndex: 'broker',
        key: 'broker',
      },
      {
        title: '持仓量',
        dataIndex: 'short_hld',
        key: 'short_hld',
        sorter: (a: any, b: any) => a.short_hld - b.short_hld,
      },
      {
        title: '持仓变化',
        dataIndex: 'short_chg',
        key: 'short_chg',
        render: (value: number) => (
          <span style={{ color: value > 0 ? '#f5222d' : value < 0 ? '#52c41a' : 'inherit' }}>
            {value > 0 ? '+' : ''}{value}
          </span>
        ),
      },
      {
        title: '影响力得分',
        dataIndex: 'impact_score',
        key: 'impact_score',
        render: (value: number) => value.toFixed(4),
        sorter: (a: any, b: any) => a.impact_score - b.impact_score,
      },
    ];

    return (
      <Spin spinning={dailyLoading}>
        {dailyData && (
          <>
            <Alert
              message={`交易日期: ${dailyData.trade_date}`}
              description={
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="总成交量"
                      value={dailyData.total_vol}
                      prefix={<ArrowUpOutlined />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="净持仓变化"
                      value={dailyData.net_position_change}
                      prefix={dailyData.net_position_change > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                      valueStyle={{ color: dailyData.net_position_change > 0 ? '#cf1322' : '#3f8600' }}
                    />
                  </Col>
                </Row>
              }
              type="info"
              showIcon
            />
            
            <Row gutter={16} className="mt-4">
              <Col span={12}>
                <Card title="多头持仓排名">
                  <Table
                    columns={longColumns}
                    dataSource={dailyData.top_long}
                    size="small"
                    pagination={false}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card title="空头持仓排名">
                  <Table
                    columns={shortColumns}
                    dataSource={dailyData.top_short}
                    size="small"
                    pagination={false}
                  />
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Spin>
    );
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 relative inline-block">
            持仓分析
            <span className="absolute -top-3 -right-12 bg-gradient-to-r from-yellow-400 to-yellow-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-md transform rotate-12">
              PRO
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            分析豆粕期货的持仓变化及其影响
          </p>
        </div>
        <div className="mb-6">
          <Row gutter={16} align="middle">
            <Col>
              <Select
                value={symbol}
                onChange={setSymbol}
                style={{ width: 120 }}
                options={[
                  { value: 'M2509', label: '豆粕2509' },
                  { value: 'M2601', label: '豆粕2601' },                  
                ]}
              />
            </Col>
            {activeTab === 'broker' ? (
              <Col>
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => {
                    if (dates && dates[0] && dates[1]) {
                      setDateRange([dates[0], dates[1]]);
                    }
                  }}
                />
              </Col>
            ) : (
              <Col>
                <DatePicker
                  value={selectedDailyDate}
                  onChange={(date) => date && setSelectedDailyDate(date)}
                />
              </Col>
            )}
          </Row>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="期货公司维度" key="broker">
            <Spin spinning={loading}>
              <Table
                columns={brokerColumns}
                dataSource={brokerData}
                pagination={false}
                scroll={{ x: 'max-content' }}
              />
            </Spin>
          </TabPane>
          <TabPane tab="每日持仓情况" key="daily">
            {renderDailyView()}
          </TabPane>
        </Tabs>

        <Modal
          title={`${selectedBroker?.broker || ''} 持仓详情分析`}
          open={isDetailModalVisible}
          onCancel={() => setIsDetailModalVisible(false)}
          width={800}
          footer={null}
        >
          {selectedBroker && (
            <div className="space-y-6">
              <Card title="持仓趋势" bordered={false}>
                {renderDetailChart()}
              </Card>
              
              <Card title="持仓变化统计" bordered={false}>
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="多头持仓变化"
                      value={selectedBroker.summary.net_long_chg}
                      valueStyle={{ color: selectedBroker.summary.net_long_chg > 0 ? '#f5222d' : '#52c41a' }}
                      prefix={selectedBroker.summary.net_long_chg > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="空头持仓变化"
                      value={selectedBroker.summary.net_short_chg}
                      valueStyle={{ color: selectedBroker.summary.net_short_chg > 0 ? '#f5222d' : '#52c41a' }}
                      prefix={selectedBroker.summary.net_short_chg > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="净持仓变化"
                      value={selectedBroker.summary.net_position_change}
                      valueStyle={{ color: selectedBroker.summary.net_position_change > 0 ? '#f5222d' : '#52c41a' }}
                      prefix={selectedBroker.summary.net_position_change > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    />
                  </Col>
                </Row>
              </Card>

              <Card title="分析说明" bordered={false}>
                <div className="text-gray-600">
                  <p>
                    {selectedBroker.broker}在观察期间（{dayjs(selectedBroker.holdings_trend[0].date).format('YYYY-MM-DD')} 至 
                    {dayjs(selectedBroker.holdings_trend[selectedBroker.holdings_trend.length - 1].date).format('YYYY-MM-DD')}）
                    的持仓表现如下：
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-2">
                    <li>
                      多头持仓{selectedBroker.summary.net_long_chg > 0 ? '增加' : '减少'}了
                      {Math.abs(selectedBroker.summary.net_long_chg).toLocaleString()}手，
                      表现出{selectedBroker.summary.net_long_chg > 0 ? '做多' : '减多'}意愿。
                    </li>
                    <li>
                      空头持仓{selectedBroker.summary.net_short_chg > 0 ? '增加' : '减少'}了
                      {Math.abs(selectedBroker.summary.net_short_chg).toLocaleString()}手，
                      表现出{selectedBroker.summary.net_short_chg > 0 ? '做空' : '减空'}意愿。
                    </li>
                    <li>
                      总体来看，该期货公司在此期间呈现
                      {selectedBroker.summary.net_position_change > 0 ? '净多头' : '净空头'}
                      趋势，净持仓变化
                      {selectedBroker.summary.net_position_change > 0 ? '增加' : '减少'}了
                      {Math.abs(selectedBroker.summary.net_position_change).toLocaleString()}手。
                    </li>
                  </ul>
                </div>
              </Card>
            </div>
          )}
        </Modal>
      </div>
    </Layout>
  );
};

export default HoldingAnalysis; 