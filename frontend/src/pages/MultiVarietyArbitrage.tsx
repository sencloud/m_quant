import React, { useState, useEffect, useMemo } from 'react';
import { Tabs, Card, Typography, Statistic, Row, Col, Alert, Spin, Switch } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import Layout from '../components/layout/Layout';
import Toast from '../components/Toast';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

const MultiVarietyArbitrage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [isRealtime, setIsRealtime] = useState(false);
  const [oilMealRatio, setOilMealRatio] = useState<number>(2.29);
  const [crushingMargin, setCrushingMargin] = useState<number>(240);
  const [historicalAverage, setHistoricalAverage] = useState<number>(150);
  const [timeData, setTimeData] = useState<string[]>([]);
  const [oilMealRatioData, setOilMealRatioData] = useState<number[]>(
    Array.from({length: 60}, () => 2 + Math.random() * 0.5)
  );
  const [crushingMarginData, setCrushingMarginData] = useState<number[]>(
    Array.from({length: 60}, () => 150 + Math.random() * 100)
  );
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // 获取数据
  const fetchData = async () => {
    try {
      setLoading(true);
      const apiPath = isRealtime ? '/market/arbitrage/realtime' : '/arbitrage/realtime';
      const response = await axios.get(`${API_BASE_URL}${apiPath}`);
      const data = response.data;
      
      // 更新时间轴数据
      setTimeData(data.timestamps);
      
      // 更新油粕比数据
      setOilMealRatio(data.oil_meal_ratio.current_ratio);
      setOilMealRatioData(data.oil_meal_ratio.values);
      
      // 更新压榨利润数据
      setCrushingMargin(data.crushing_margin.current_margin);
      setHistoricalAverage(data.crushing_margin.historical_average);
      setCrushingMarginData(data.crushing_margin.values);
      
    } catch (error) {
      console.error('获取数据失败:', error);
      setToast({
        message: '获取数据失败',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); // 首次加载
    
    let timer: NodeJS.Timeout | null = null;
    if (isRealtime) {
      timer = setInterval(fetchData, 60000); // 实时模式下每1分钟更新一次
    }
    
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isRealtime]);

  // 油粕比图表配置
  const oilMealRatioOption = useMemo(() => ({
    title: {
      text: '油粕比实时走势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0];
        return `${data.axisValue}<br/>${data.seriesName}: ${data.value.toFixed(3)}`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    dataZoom: [{
      type: 'inside',
      start: 80,
      end: 100
    }, {
      type: 'slider',
      start: 80,
      end: 100
    }],
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        rotate: 45,
        formatter: (value: string) => {
          return value.slice(11, 16); // 只显示时:分
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '油粕比',
      min: 2.2,
      max: 3.2,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [{
      name: '油粕比',
      data: oilMealRatioData,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#5470c6',
        width: 2
      },
      markLine: {
        data: [
          { yAxis: 2.5, name: '下限', lineStyle: { color: '#ff4d4f' } },
          { yAxis: 2.8, name: '上限', lineStyle: { color: '#ff4d4f' } }
        ]
      }
    }]
  }), [timeData, oilMealRatioData]);

  // 压榨利润图表配置
  const crushingMarginOption = useMemo(() => ({
    title: {
      text: '压榨利润实时走势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0];
        return `${data.axisValue}<br/>${data.seriesName}: ${data.value.toFixed(3)}元/吨`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    dataZoom: [{
      type: 'inside',
      start: 80,
      end: 100
    }, {
      type: 'slider',
      start: 80,
      end: 100
    }],
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        rotate: 45,
        formatter: (value: string) => {
          return value.slice(11, 16); // 只显示时:分
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '压榨利润(元/吨)',
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [{
      name: '压榨利润',
      data: crushingMarginData,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#91cc75',
        width: 2
      },
      markLine: {
        data: [
          { yAxis: historicalAverage, name: '历史均值', lineStyle: { color: '#5470c6' } }
        ]
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(145, 204, 117, 0.3)'
          }, {
            offset: 1,
            color: 'rgba(145, 204, 117, 0)'
          }]
        }
      }
    }]
  }), [timeData, crushingMarginData, historicalAverage]);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            多品种套利策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            基于豆二、豆粕、豆油三者价格关联性的日内动态套利策略
          </p>
        </div>

        <Row gutter={[24, 24]} className="mb-6">
          <Col span={8}>
            <Card>
              <Statistic
                title="当前油粕比"
                value={oilMealRatio}
                precision={3}
                valueStyle={{ color: oilMealRatio > 2.5 ? '#cf1322' : oilMealRatio < 2.0 ? '#3f8600' : '#000000' }}
                prefix={oilMealRatio > 2.5 ? <ArrowUpOutlined /> : oilMealRatio < 2.0 ? <ArrowDownOutlined /> : null}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="当前压榨利润"
                value={crushingMargin}
                precision={0}
                prefix="¥"
                suffix="/吨"
                valueStyle={{ color: crushingMargin > historicalAverage + 50 ? '#cf1322' : crushingMargin < historicalAverage - 50 ? '#3f8600' : '#000000' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="历史均值"
                value={historicalAverage}
                precision={3}
                prefix="¥"
                suffix="/吨"
              />
            </Card>
          </Col>
        </Row>
        
        <Alert
          message="策略说明及风险提示"
          description={
            <div>
              <p>豆二、豆油、豆粕三者之间存在压榨关系：100%大豆≈18%豆油+80%豆粕+1.5%损耗。这一比例关系决定了三者价格存在长期均衡性，但日内可能因供需错配出现短期偏离。</p>
              <ul className="list-disc pl-6 mt-2">
                <li>油粕比套利：豆油与豆粕价格比值（油粕比）通常波动于1.8-2.8区间，日内可捕捉比值回归的波动。</li>
                <li>压榨利润套利：当压榨利润（豆油+豆粕价格-大豆成本）偏离正常水平时，可通过多空组合对冲套利。</li>
              </ul>
              <br/>
              <p><b style={{color: 'red'}}>本策略仅供参考，测试结果基于三个品种的2509合约5分钟行情数据，实际交易中请注意风险控制，建议使用模拟盘进行测试。</b></p>
            </div>
          }
          type="warning"
          showIcon
          className="mb-6"
        />

        <Card className="mb-6">
          <div className="flex items-center justify-between">
            <Text strong>数据来源: 新浪财经期货行情</Text>
            <div className="flex items-center gap-2">
              <Text>实时数据</Text>
              <Switch 
                checked={isRealtime} 
                onChange={(checked) => {
                  setIsRealtime(checked);
                  if (checked) {
                    fetchData(); // 立即获取一次数据
                  }
                }}
                checkedChildren="开启" 
                unCheckedChildren="关闭"
              />
            </div>
          </div>
        </Card>

        <Spin spinning={loading}>
          <Tabs defaultActiveKey="1" type="card" className="bg-white rounded-lg shadow">
            <TabPane tab="策略1：油粕比日内波段套利" key="1">
              <div className="p-6">
                <Row gutter={[24, 24]} className="mb-6">
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="当前油粕比"
                        value={oilMealRatio}
                        precision={3}
                        valueStyle={{ color: oilMealRatio > 2.5 ? '#cf1322' : oilMealRatio < 2.0 ? '#3f8600' : '#000000' }}
                        prefix={oilMealRatio > 2.5 ? <ArrowUpOutlined /> : oilMealRatio < 2.0 ? <ArrowDownOutlined /> : null}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="建议操作"
                        value={oilMealRatio > 2.5 ? '做空油粕比' : oilMealRatio < 2.0 ? '做多油粕比' : '观望'}
                        valueStyle={{ color: oilMealRatio > 2.5 || oilMealRatio < 2.0 ? '#1890ff' : '#000000' }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="目标盈利"
                        value={200}
                        prefix="¥"
                        suffix="/组"
                      />
                    </Card>
                  </Col>
                </Row>

                <Card className="mb-6">
                  <ReactECharts option={oilMealRatioOption} style={{ height: '400px' }} />
                </Card>

                <Card>
                  <Title level={4}>策略说明</Title>
                  <Paragraph>
                    <Text strong>触发条件：</Text>
                    <ul className="list-disc pl-6 mt-2">
                      <li>当实时油粕比高于2.8或低于2.5时，视为短期超买/超卖信号</li>
                      <li>结合成交量放大（较前5分钟均值增长30%以上）确认趋势有效性</li>
                    </ul>
                  </Paragraph>
                  <Paragraph>
                    <Text strong>操作方向：</Text>
                    <ul className="list-disc pl-6 mt-2">
                      <li>比值高位（{'>'}2.8）：做空油粕比（卖出豆油、买入豆粕）</li>
                      <li>比值低位（{'<'}2.5）：做多油粕比（买入豆油、卖出豆粕）</li>
                    </ul>
                  </Paragraph>
                </Card>
              </div>
            </TabPane>

            <TabPane tab="策略2：压榨利润均值回归套利" key="2">
              <div className="p-6">
                <Row gutter={[24, 24]} className="mb-6">
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="当前压榨利润"
                        value={crushingMargin}
                        precision={0}
                        prefix="¥"
                        suffix="/吨"
                        valueStyle={{ color: crushingMargin > historicalAverage + 50 ? '#cf1322' : crushingMargin < historicalAverage - 50 ? '#3f8600' : '#000000' }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="历史均值"
                        value={historicalAverage}
                        precision={2}
                        prefix="¥"
                        suffix="/吨"
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="建议操作"
                        value={crushingMargin > historicalAverage + 50 ? '做空压榨利润' : crushingMargin < historicalAverage - 50 ? '做多压榨利润' : '观望'}
                        valueStyle={{ color: Math.abs(crushingMargin - historicalAverage) > 50 ? '#1890ff' : '#000000' }}
                      />
                    </Card>
                  </Col>
                </Row>

                <Card className="mb-6">
                  <ReactECharts option={crushingMarginOption} style={{ height: '400px' }} />
                </Card>

                <Card>
                  <Title level={4}>策略说明</Title>
                  <Paragraph>
                    <Text strong>触发条件：</Text>
                    <ul className="list-disc pl-6 mt-2">
                      <li>实时压榨利润 = （豆油价格×0.18 + 豆粕价格×0.8）- 豆二价格</li>
                      <li>当利润较前5日均值偏离50元/吨以上时，视为套利机会</li>
                    </ul>
                  </Paragraph>
                  <Paragraph>
                    <Text strong>操作方向：</Text>
                    <ul className="list-disc pl-6 mt-2">
                      <li>利润过高：做空压榨利润（卖出豆油+豆粕，买入豆二）</li>
                      <li>利润过低：做多压榨利润（买入豆油+豆粕，卖出豆二）</li>
                    </ul>
                  </Paragraph>
                </Card>
              </div>
            </TabPane>
          </Tabs>
        </Spin>
      </div>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </Layout>
  );
};

export default MultiVarietyArbitrage; 