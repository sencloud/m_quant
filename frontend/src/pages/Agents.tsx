import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { Card, Row, Col, Avatar, Typography, Tabs, Button, Modal, Spin, Divider, Statistic, Progress, DatePicker, message } from 'antd';
import { 
  UserOutlined, 
  BarChartOutlined, 
  LineChartOutlined, 
  FundOutlined, 
  ArrowUpOutlined, 
  ArrowDownOutlined,
  InfoCircleOutlined,
  TeamOutlined,
  HistoryOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import * as echarts from 'echarts';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import { runBacktest } from '../api/ai';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

// 金融专家数据
const experts = [
  {
    id: 1,
    name: 'Ben Graham',
    title: '价值投资之父',
    avatar: '/images/experts/ben-graham.jpg',
    description: '本杰明·格雷厄姆是价值投资的奠基人，著有《证券分析》和《聪明的投资者》。他强调安全边际、内在价值和市场先生的概念，影响了包括沃伦·巴菲特在内的众多投资者。',
    specialties: ['价值投资', '安全边际', '基本面分析'],
    performance: 15.2,
    riskLevel: '低',
    recommendation: '基于当前市场估值，建议增持豆粕期货，同时配置相关农业股票以分散风险。'
  },
  {
    id: 2,
    name: 'Bill Ackman',
    title: '激进投资者',
    avatar: '/images/experts/bill-ackman.jpg',
    description: '比尔·阿克曼是潘兴广场资本管理的创始人，以激进投资策略和公开市场活动而闻名。他擅长通过深入研究和积极股东主义创造价值。',
    specialties: ['激进投资', '事件驱动', '公开市场活动'],
    performance: 18.7,
    riskLevel: '高',
    recommendation: '当前豆粕市场存在结构性机会，建议通过期权策略做多，同时关注相关农业科技公司。'
  },
  {
    id: 3,
    name: 'Cathie Wood',
    title: '颠覆性创新投资者',
    avatar: '/images/experts/cathie-wood.jpg',
    description: '凯茜·伍德是方舟投资管理公司的创始人，专注于颠覆性创新技术投资。她相信技术创新将重塑传统行业，包括农业和食品生产。',
    specialties: ['颠覆性创新', '长期投资', '技术趋势'],
    performance: 22.5,
    riskLevel: '高',
    recommendation: '农业科技革命将改变豆粕供应链，建议投资农业科技ETF和豆粕期货的组合。'
  },
  {
    id: 4,
    name: 'Charlie Munger',
    title: '伯克希尔副董事长',
    avatar: '/images/experts/charlie-munger.jpg',
    description: '查理·芒格是伯克希尔·哈撒韦公司的副董事长，沃伦·巴菲特的长期合作伙伴。他以多学科思维模型和逆向思维而闻名。',
    specialties: ['多学科思维', '逆向投资', '长期持有'],
    performance: 16.8,
    riskLevel: '中',
    recommendation: '从长期供需关系看，豆粕价格有上涨空间，建议持有豆粕期货和相关农业股票。'
  },
  {
    id: 5,
    name: 'Michael Burry',
    title: '大空头',
    avatar: '/images/experts/michael-burry.jpg',
    description: '迈克尔·伯里是Scion资产管理公司的创始人，因在2008年金融危机前做空次贷市场而闻名。他擅长发现市场非理性和泡沫。',
    specialties: ['逆向投资', '市场泡沫识别', '宏观分析'],
    performance: 19.3,
    riskLevel: '高',
    recommendation: '当前豆粕市场存在投机性泡沫，建议通过期权策略做空，同时持有实物豆粕作为对冲。'
  },
  {
    id: 6,
    name: 'Peter Lynch',
    title: '成长型投资大师',
    avatar: '/images/experts/peter-lynch.jpg',
    description: '彼得·林奇是富达麦哲伦基金的前经理，以识别高增长公司而闻名。他相信投资者应该投资于他们了解的行业。',
    specialties: ['成长型投资', '实地调研', '行业洞察'],
    performance: 17.6,
    riskLevel: '中',
    recommendation: '农业行业处于周期性底部，建议增持豆粕期货和相关农业股票，关注行业整合机会。'
  },
  {
    id: 7,
    name: 'Phil Fisher',
    title: '成长型投资先驱',
    avatar: '/images/experts/phil-fisher.jpg',
    description: '菲利普·费雪是成长型投资的先驱，著有《怎样选择成长股》。他强调通过深入研究和长期持有优质公司来获得超额回报。',
    specialties: ['成长型投资', '公司质量分析', '长期持有'],
    performance: 14.9,
    riskLevel: '中',
    recommendation: '从长期供需关系看，豆粕价格有上涨空间，建议持有豆粕期货和相关农业股票。'
  },
  {
    id: 8,
    name: 'Stanley Druckenmiller',
    title: '宏观交易大师',
    avatar: '/images/experts/stanley-druckenmiller.jpg',
    description: '斯坦利·德鲁肯米勒是杜肯家族办公室的创始人，以宏观交易和货币投资而闻名。他擅长通过宏观经济分析预测市场趋势。',
    specialties: ['宏观交易', '货币投资', '趋势跟踪'],
    performance: 21.4,
    riskLevel: '高',
    recommendation: '全球通胀预期上升，建议增持豆粕期货和相关农业股票，同时关注美元走势对商品价格的影响。'
  },
  {
    id: 9,
    name: 'Warren Buffett',
    title: '奥马哈先知',
    avatar: '/images/experts/warren-buffett.jpg',
    description: '沃伦·巴菲特是伯克希尔·哈撒韦公司的董事长兼CEO，被誉为"奥马哈先知"。他以价值投资和长期持有优质公司而闻名。',
    specialties: ['价值投资', '企业质量分析', '长期持有'],
    performance: 20.1,
    riskLevel: '中',
    recommendation: '从长期供需关系看，豆粕价格有上涨空间，建议持有豆粕期货和相关农业股票，关注行业整合机会。'
  }
];

// 回测数据
const backtestData = [
  { date: '2023-01', value: 100 },
  { date: '2023-02', value: 105 },
  { date: '2023-03', value: 103 },
  { date: '2023-04', value: 108 },
  { date: '2023-05', value: 112 },
  { date: '2023-06', value: 115 },
  { date: '2023-07', value: 118 },
  { date: '2023-08', value: 122 },
  { date: '2023-09', value: 125 },
  { date: '2023-10', value: 128 },
  { date: '2023-11', value: 132 },
  { date: '2023-12', value: 135 },
  { date: '2024-01', value: 138 },
  { date: '2024-02', value: 142 },
  { date: '2024-03', value: 145 },
  { date: '2024-04', value: 148 },
  { date: '2024-05', value: 152 },
  { date: '2024-06', value: 155 },
  { date: '2024-07', value: 158 },
  { date: '2024-08', value: 162 },
  { date: '2024-09', value: 165 },
  { date: '2024-10', value: 168 },
  { date: '2024-11', value: 172 },
  { date: '2024-12', value: 175 }
];

// 组合配置
const portfolioConfig = {
  '豆粕期货': 40,
  '农业股票ETF': 30,
  '农业科技股票': 20,
  '豆粕期权': 10
};

interface StrategyCardProps {
  title: string;
  tags: Array<{text: string; color: string}>;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const StrategyCard: React.FC<StrategyCardProps> = ({ title, tags, icon, children }) => {
  return (
    <div className="mb-12">
      <div className="bg-white rounded-lg overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 text-gray-600">
                {icon}
              </div>
              <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <div className="flex gap-2">
                {tags.map((tag, index) => (
                  <span 
                    key={index}
                    className={`px-3 py-1 text-sm font-medium ${tag.color} rounded-full`}
                  >
                    {tag.text}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

const Agents: React.FC = () => {
  const [selectedExpert, setSelectedExpert] = useState<number | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState<string>('1');
  const [showAnalysis, setShowAnalysis] = useState<boolean>(false);
  const [showBacktest, setShowBacktest] = useState<boolean>(false);
  const chartRef = React.useRef<HTMLDivElement>(null);
  const [chart, setChart] = useState<echarts.ECharts | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);

  useEffect(() => {
    if (chartRef.current) {
      const newChart = echarts.init(chartRef.current);
      setChart(newChart);
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: '{b}: {c}'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: backtestData.map(item => item.date)
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '组合价值',
            type: 'line',
            smooth: true,
            data: backtestData.map(item => item.value),
            areaStyle: {
              opacity: 0.3,
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                {
                  offset: 0,
                  color: 'rgba(24, 144, 255, 0.8)'
                },
                {
                  offset: 1,
                  color: 'rgba(24, 144, 255, 0.1)'
                }
              ])
            },
            lineStyle: {
              width: 2
            },
            itemStyle: {
              color: '#1890ff'
            }
          }
        ]
      };
      
      newChart.setOption(option);
      
      return () => {
        newChart.dispose();
      };
    }
  }, []);

  // 响应窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      if (chart) {
        chart.resize();
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [chart]);

  const showExpertDetail = (id: number) => {
    setSelectedExpert(id);
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setSelectedExpert(null);
  };

  const selectedExpertData = experts.find(expert => expert.id === selectedExpert);

  const handleBacktest = async () => {
    if (!startDate || !endDate) {
      message.error('请选择开始和结束日期');
      return;
    }

    setLoading(true);
    try {
      const request = {
        tickers: ['000333'], // 豆粕期货主力合约
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        initial_capital: 100000,
        portfolio: portfolioConfig,
        selected_analysts: ['ben_graham'],
        model_name: 'bot-20250329163710-8zcqm',
        model_provider: 'OpenAI'
      };

      const response = await runBacktest(request);
      
      // Update chart data
      if (chart) {
        const option = {
          tooltip: {
            trigger: 'axis',
            formatter: '{b}: {c}'
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: response.backtest.portfolio_values.map((_, index) => {
              const date = new Date(startDate);
              date.setDate(date.getDate() + index);
              return date.toISOString().split('T')[0];
            })
          },
          yAxis: {
            type: 'value'
          },
          series: [
            {
              name: '组合价值',
              type: 'line',
              smooth: true,
              data: response.backtest.portfolio_values,
              areaStyle: {
                opacity: 0.3,
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  {
                    offset: 0,
                    color: 'rgba(24, 144, 255, 0.8)'
                  },
                  {
                    offset: 1,
                    color: 'rgba(24, 144, 255, 0.1)'
                  }
                ])
              },
              lineStyle: {
                width: 2
              },
              itemStyle: {
                color: '#1890ff'
              }
            }
          ]
        };
        
        chart.setOption(option);
      }

      // Update performance metrics
      setPerformanceMetrics(response.backtest.performance_metrics);
      
      setShowBacktest(true);
      setShowAnalysis(false);
      setActiveTab('1');
    } catch (error) {
      console.error('Error running backtest:', error);
      message.error('回测分析失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeToday = () => {
    setShowAnalysis(true);
    setShowBacktest(false);
    setActiveTab('1');
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            多智能体组合分析策略
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            基于9位金融专家的投资理念和策略，构建智能体组合分析系统，为豆粕市场提供多维度分析和投资建议
          </p>
        </div>

        <StrategyCard
          title="金融专家智能体"
          tags={[
          ]}
          icon={<TeamOutlined />}
        >
          <Row gutter={[16, 16]}>
            {experts.map(expert => (
              <Col xs={24} sm={12} md={8} lg={6} key={expert.id}>
                <Card 
                  hoverable 
                  className="h-full flex flex-col"
                  onClick={() => showExpertDetail(expert.id)}
                >
                  <div className="flex flex-col items-center text-center">
                    <Avatar 
                      size={80} 
                      src={expert.avatar} 
                      icon={<UserOutlined />}
                      className="mb-4"
                    />
                    <Title level={4} className="mb-1">{expert.name}</Title>
                    <Text type="secondary" className="mb-2">{expert.title}</Text>
                    <div className="mt-auto">
                      <Button type="primary" ghost size="small">
                        查看分析
                      </Button>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </StrategyCard>

        <StrategyCard
          title="智能体组合分析"
          tags={[
            { text: "组合策略", color: "text-green-800 bg-green-100" },
            { text: "已回测", color: "text-blue-800 bg-blue-100" }
          ]}
          icon={<FundOutlined />}
        >
          <div className="mb-8">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={12} md={8}>
                <div className="flex flex-col">
                  <Text className="mb-2 text-gray-600">开始日期</Text>
                  <DatePicker
                    className="w-full"
                    placeholder="选择开始日期"
                    onChange={(date) => setStartDate(date?.toDate() || null)}
                  />
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="flex flex-col">
                  <Text className="mb-2 text-gray-600">结束日期</Text>
                  <DatePicker
                    className="w-full"
                    placeholder="选择结束日期"
                    onChange={(date) => setEndDate(date?.toDate() || null)}
                  />
                </div>
              </Col>
              <Col xs={24} sm={24} md={8}>
                <Row gutter={8}>
                  <Col span={12}>
                    <Button 
                      type="primary" 
                      icon={<HistoryOutlined />}
                      onClick={handleBacktest}
                      className="w-full h-10"
                      disabled={!startDate || !endDate}
                    >
                      回测分析
                    </Button>
                  </Col>
                  <Col span={12}>
                    <Button 
                      type="primary" 
                      icon={<CalendarOutlined />}
                      onClick={handleAnalyzeToday}
                      className="w-full h-10"
                    >
                      分析今日
                    </Button>
                  </Col>
                </Row>
              </Col>
            </Row>
          </div>

          {showBacktest && (
            <div className="bg-white rounded-lg p-6">
              <Tabs activeKey={activeTab} onChange={setActiveTab}>
                <TabPane tab="回测结果" key="1">
                  <Row gutter={[24, 24]}>
                    <Col xs={24} md={12}>
                      <Title level={4}>资产配置</Title>
                      <div className="mb-6">
                        {Object.entries(portfolioConfig).map(([asset, percentage]) => (
                          <div key={asset} className="mb-4">
                            <div className="flex justify-between mb-1">
                              <Text>{asset}</Text>
                              <Text strong>{percentage}%</Text>
                            </div>
                            <Progress percent={percentage} strokeColor="#1890ff" />
                          </div>
                        ))}
                      </div>
                    </Col>
                    <Col xs={24} md={12}>
                      <Title level={4}>历史回测</Title>
                      <div ref={chartRef} className="h-64"></div>
                      <div className="mt-4 grid grid-cols-2 gap-4">
                        <Statistic 
                          title="年化收益率" 
                          value={performanceMetrics?.annual_return} 
                          precision={2} 
                          suffix="%" 
                          valueStyle={{ color: '#3f8600' }}
                          prefix={<ArrowUpOutlined />}
                        />
                        <Statistic 
                          title="最大回撤" 
                          value={performanceMetrics?.max_drawdown} 
                          precision={2} 
                          suffix="%" 
                          valueStyle={{ color: '#cf1322' }}
                          prefix={<ArrowDownOutlined />}
                        />
                        <Statistic 
                          title="夏普比率" 
                          value={performanceMetrics?.sharpe_ratio} 
                          precision={2}
                        />
                        <Statistic 
                          title="波动率" 
                          value={performanceMetrics?.volatility} 
                          precision={2} 
                          suffix="%"
                        />
                      </div>
                    </Col>
                  </Row>
                </TabPane>
              </Tabs>
            </div>
          )}

          {showAnalysis && (
            <div className="bg-white rounded-lg p-6">
              <Tabs activeKey={activeTab} onChange={setActiveTab}>
                <TabPane tab="组合配置" key="1">
                  <Row gutter={[24, 24]}>
                    <Col xs={24} md={12}>
                      <Title level={4}>资产配置</Title>
                      <div className="mb-6">
                        {Object.entries(portfolioConfig).map(([asset, percentage]) => (
                          <div key={asset} className="mb-4">
                            <div className="flex justify-between mb-1">
                              <Text>{asset}</Text>
                              <Text strong>{percentage}%</Text>
                            </div>
                            <Progress percent={percentage} strokeColor="#1890ff" />
                          </div>
                        ))}
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <Title level={5}>组合特点</Title>
                        <ul className="list-disc pl-5">
                          <li>以豆粕期货为核心，占比40%</li>
                          <li>通过农业股票ETF分散风险，占比30%</li>
                          <li>配置农业科技股票捕捉创新机会，占比20%</li>
                          <li>使用豆粕期权进行风险对冲，占比10%</li>
                        </ul>
                      </div>
                    </Col>
                  </Row>
                </TabPane>
                <TabPane tab="专家共识" key="2">
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <Title level={4} className="mb-4">专家共识分析</Title>
                    <Paragraph>
                      基于9位金融专家的分析，我们对豆粕市场形成以下共识：
                    </Paragraph>
                    <ul className="list-disc pl-5 mb-6">
                      <li>长期供需关系支持豆粕价格上行</li>
                      <li>农业科技革命将改变豆粕供应链</li>
                      <li>全球通胀预期上升有利于商品价格</li>
                      <li>行业整合将带来结构性机会</li>
                    </ul>
                    <Divider />
                    <Title level={5} className="mb-4">投资建议</Title>
                    <Paragraph>
                      综合考虑各位专家的观点，我们建议：
                    </Paragraph>
                    <ol className="list-decimal pl-5">
                      <li>核心配置豆粕期货，占比40%</li>
                      <li>通过农业股票ETF分散风险，占比30%</li>
                      <li>配置农业科技股票捕捉创新机会，占比20%</li>
                      <li>使用豆粕期权进行风险对冲，占比10%</li>
                    </ol>
                  </div>
                </TabPane>
                <TabPane tab="风险提示" key="3">
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <Title level={4} className="mb-4">风险因素</Title>
                    <ul className="list-disc pl-5 mb-6">
                      <li>全球宏观经济波动可能导致商品价格剧烈波动</li>
                      <li>天气因素对农产品产量有重大影响</li>
                      <li>政策变化可能影响豆粕需求和价格</li>
                      <li>期权策略存在时间衰减风险</li>
                    </ul>
                    <Divider />
                    <Title level={5} className="mb-4">风险控制措施</Title>
                    <ol className="list-decimal pl-5">
                      <li>通过多元化配置降低单一资产风险</li>
                      <li>使用期权策略对冲下行风险</li>
                      <li>设置止损位控制最大回撤</li>
                      <li>定期再平衡维持目标配置比例</li>
                    </ol>
                  </div>
                </TabPane>
              </Tabs>
            </div>
          )}
        </StrategyCard>

        {/* 专家详情弹窗 */}
        <Modal
          title={selectedExpertData?.name}
          open={isModalVisible}
          onCancel={handleModalClose}
          footer={null}
          width={700}
        >
          {selectedExpertData ? (
            <div>
              <div className="flex items-center mb-6">
                <Avatar 
                  size={100} 
                  src={selectedExpertData.avatar} 
                  icon={<UserOutlined />}
                  className="mr-4"
                />
                <div>
                  <Title level={4} className="mb-1">{selectedExpertData.name}</Title>
                  <Text type="secondary" className="block mb-2">{selectedExpertData.title}</Text>
                  <div className="flex items-center">
                    <Text type="secondary" className="mr-4">年化收益: <Text strong type="success">{selectedExpertData.performance}%</Text></Text>
                    <Text type="secondary">风险等级: <Text strong>{selectedExpertData.riskLevel}</Text></Text>
                  </div>
                </div>
              </div>
              
              <Divider />
              
              <Title level={5} className="mb-2">专家简介</Title>
              <Paragraph className="mb-4">{selectedExpertData.description}</Paragraph>
              
              <Title level={5} className="mb-2">专业领域</Title>
              <div className="mb-4">
                {selectedExpertData.specialties.map((specialty, index) => (
                  <span key={index} className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full mr-2 mb-2">
                    {specialty}
                  </span>
                ))}
              </div>
              
              <Title level={5} className="mb-2">投资建议</Title>
              <Paragraph className="mb-4">{selectedExpertData.recommendation}</Paragraph>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <Title level={5} className="mb-2">模拟投资组合</Title>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card size="small" title="资产配置">
                      <div className="mb-2">
                        <div className="flex justify-between mb-1">
                          <Text>豆粕期货</Text>
                          <Text strong>40%</Text>
                        </div>
                        <Progress percent={40} strokeColor="#1890ff" />
                      </div>
                      <div className="mb-2">
                        <div className="flex justify-between mb-1">
                          <Text>农业股票ETF</Text>
                          <Text strong>30%</Text>
                        </div>
                        <Progress percent={30} strokeColor="#52c41a" />
                      </div>
                      <div className="mb-2">
                        <div className="flex justify-between mb-1">
                          <Text>农业科技股票</Text>
                          <Text strong>20%</Text>
                        </div>
                        <Progress percent={20} strokeColor="#faad14" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <Text>豆粕期权</Text>
                          <Text strong>10%</Text>
                        </div>
                        <Progress percent={10} strokeColor="#f5222d" />
                      </div>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small" title="绩效指标">
                      <Statistic 
                        title="年化收益率" 
                        value={selectedExpertData.performance} 
                        precision={2} 
                        suffix="%" 
                        valueStyle={{ color: '#3f8600' }}
                        prefix={<ArrowUpOutlined />}
                      />
                      <Statistic 
                        title="风险等级" 
                        value={selectedExpertData.riskLevel}
                        className="mt-2"
                      />
                    </Card>
                  </Col>
                </Row>
              </div>
            </div>
          ) : (
            <div className="flex justify-center items-center h-64">
              <Spin size="large" />
            </div>
          )}
        </Modal>
      </div>
    </Layout>
  );
};

export default Agents; 