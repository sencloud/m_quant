import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { CompanyInfo, StockFuturesData, TradingSignal } from '../../types/stockFutures';
import Layout from '../../components/layout/Layout';
import { Card, Skeleton, Tabs, Tag, Table, Divider, Row, Col, Typography, Descriptions, Space } from 'antd';
import { LineChartOutlined, FundOutlined, TeamOutlined, InfoCircleOutlined, StockOutlined } from '@ant-design/icons';
import type { EChartsOption } from 'echarts';

const { Title, Paragraph } = Typography;

const COMPANIES: CompanyInfo[] = [
  { code: '300999.SZ', name: '金龙鱼', type: 'upstream', description: '大豆压榨及食用油生产' },
  { code: '000930.SZ', name: '中粮科技', type: 'upstream', description: '中粮集团旗下，涉及大豆加工' },
  { code: '600598.SH', name: '北大荒', type: 'upstream', description: '农业种植（大豆原料）' },
  { code: '000893.SZ', name: '东凌国际', type: 'midstream', description: '粮油贸易及加工' },
  { code: '600540.SH', name: '新赛股份', type: 'midstream', description: '农产品加工业务' },
  { code: '000876.SZ', name: '新希望', type: 'downstream', description: '饲料生产与生猪养殖' },
  { code: '002311.SZ', name: '海大集团', type: 'downstream', description: '饲料行业龙头' },
  { code: '002714.SZ', name: '牧原股份', type: 'downstream', description: '生猪养殖，豆粕需求方' },
  { code: '300498.SZ', name: '温氏股份', type: 'downstream', description: '养殖业巨头' },
  { code: '000895.SZ', name: '双汇发展', type: 'downstream', description: '食品加工' },
  { code: '603093.SH', name: '南华期货', type: 'other', description: '提供豆粕期货交易服务' },
  { code: '603822.SH', name: '嘉澳环保', type: 'other', description: '生物柴油（豆油原料）' },
];

// 模拟数据
const MOCK_DATES = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - i);
  return date.toISOString().split('T')[0];
}).reverse();

const MOCK_BASIS = Array.from({ length: 30 }, () => Math.floor(Math.random() * 200 - 100));
const MOCK_PROFIT = Array.from({ length: 30 }, () => Math.floor(Math.random() * 800 + 200));

const MOCK_SIGNALS: TradingSignal[] = [
  {
    timestamp: '2024-03-20 09:30:00',
    type: 'positive',
    description: '豆粕期货连续上涨，基差转为升水，建议做多豆粕期货及压榨企业'
  },
  {
    timestamp: '2024-03-19 14:00:00',
    type: 'arbitrage',
    description: '压榨利润超过600元/吨，期现价差存在套利空间'
  },
  {
    timestamp: '2024-03-18 10:15:00',
    type: 'negative',
    description: '豆粕期货大幅下跌，生猪存栏回升，养殖企业具备配置价值'
  },
  {
    timestamp: '2024-03-17 11:30:00',
    type: 'positive',
    description: '基差持续走强，产业链上游企业盈利预期改善'
  }
];

// 模拟K线数据
const generateKLineData = (days: number) => {
  const data = [];
  let basePrice = 20;
  for (let i = 0; i < days; i++) {
    const date = new Date();
    date.setDate(date.getDate() - days + i);
    const open = basePrice + Math.random() * 2 - 1;
    const close = open + Math.random() * 2 - 1;
    const low = Math.min(open, close) - Math.random();
    const high = Math.max(open, close) + Math.random();
    basePrice = close;
    data.push([
      date.toISOString().split('T')[0],
      open.toFixed(2),
      close.toFixed(2),
      low.toFixed(2),
      high.toFixed(2),
      Math.floor(Math.random() * 10000000)
    ]);
  }
  return data;
};

// 公司详细信息
const COMPANY_DETAILS = {
  '300999.SZ': {
    fullName: '嘉里粮油（金龙鱼）食品股份有限公司',
    industry: '食品加工',
    marketCap: '2,890亿元',
    peRatio: '28.5',
    pbRatio: '3.2',
    mainBusiness: [
      '食用植物油加工与销售',
      '大豆压榨',
      '饲料原料生产',
      '米面制品'
    ],
    advantages: [
      '行业龙头地位，市占率第一',
      '完整产业链布局',
      '品牌价值领先',
      '原料采购优势显著'
    ],
    risks: [
      '大宗商品价格波动风险',
      '食品安全风险',
      '汇率波动风险',
      '产能过剩风险'
    ],
    recentNews: [
      '2024Q1营收同比增长15.3%',
      '新建年产100万吨油脂项目投产',
      '东南亚业务扩张计划推进中'
    ]
  },
  // ... 其他公司详情可以按需添加
};

const StockFutures: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [signals, setSignals] = useState<TradingSignal[]>(MOCK_SIGNALS);
  const [loading, setLoading] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<CompanyInfo>(COMPANIES[0]);

  const getKLineOption = (data: any[]): EChartsOption => ({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: { data: ['K线'] },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item[0]),
      scale: true
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitArea: { show: true }
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
        bottom: '5%'
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: data.map(item => item.slice(1, 5)),
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a'
        }
      }
    ]
  });

  const getBasicOption = (): EChartsOption => ({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['基差', '压榨利润'],
      top: 10
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
      data: MOCK_DATES
    },
    yAxis: [
      {
        type: 'value',
        name: '基差',
        position: 'left',
      },
      {
        type: 'value',
        name: '压榨利润',
        position: 'right',
      }
    ],
    series: [
      {
        name: '基差',
        type: 'line',
        data: MOCK_BASIS,
        smooth: true,
        lineStyle: {
          color: '#8884d8'
        }
      },
      {
        name: '压榨利润',
        type: 'line',
        yAxisIndex: 1,
        data: MOCK_PROFIT,
        smooth: true,
        lineStyle: {
          color: '#82ca9d'
        }
      }
    ]
  });

  const companyColumns = [
    {
      title: '代码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => {
        const typeMap = {
          upstream: { text: '上游', color: 'blue' },
          midstream: { text: '中游', color: 'green' },
          downstream: { text: '下游', color: 'orange' },
          other: { text: '其他', color: 'gray' },
        };
        const { text, color } = typeMap[type as keyof typeof typeMap];
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => (
        <div className="flex items-center">
          <span className="mr-2">{text}</span>
          <InfoCircleOutlined className="text-gray-400" />
        </div>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: CompanyInfo) => (
        <a onClick={() => setSelectedCompany(record)}>
          <Space>
            <StockOutlined />
            查看详情
          </Space>
        </a>
      ),
    }
  ];

  const signalColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => {
        const typeMap = {
          positive: { text: '正向联动', color: 'success' },
          negative: { text: '反向联动', color: 'error' },
          arbitrage: { text: '套利机会', color: 'processing' },
        };
        const { text, color } = typeMap[type as keyof typeof typeMap];
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: TradingSignal) => (
        <a onClick={() => console.log('查看详情', record)}>查看详情</a>
      ),
    },
  ];

  const CompanyDetail = ({ company }: { company: CompanyInfo }) => {
    const details = COMPANY_DETAILS[company.code as keyof typeof COMPANY_DETAILS];
    if (!details) return null;

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <Title level={4}>{company.name} ({company.code})</Title>
          <Tag color="blue">实时: 26.80 +2.15%</Tag>
        </div>
        
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="公司全称">{details.fullName}</Descriptions.Item>
          <Descriptions.Item label="所属行业">{details.industry}</Descriptions.Item>
          <Descriptions.Item label="市值">{details.marketCap}</Descriptions.Item>
          <Descriptions.Item label="市盈率">{details.peRatio}</Descriptions.Item>
          <Descriptions.Item label="市净率">{details.pbRatio}</Descriptions.Item>
        </Descriptions>

        <div>
          <Title level={5}>主营业务</Title>
          <ul className="list-disc pl-5">
            {details.mainBusiness.map((item, index) => (
              <li key={index} className="text-gray-700">{item}</li>
            ))}
          </ul>
        </div>

        <Row gutter={16}>
          <Col span={12}>
            <Card size="small" title="核心优势" className="h-full">
              <ul className="list-disc pl-5">
                {details.advantages.map((item, index) => (
                  <li key={index} className="text-gray-700">{item}</li>
                ))}
              </ul>
            </Card>
          </Col>
          <Col span={12}>
            <Card size="small" title="风险提示" className="h-full">
              <ul className="list-disc pl-5">
                {details.risks.map((item, index) => (
                  <li key={index} className="text-gray-700 text-sm">{item}</li>
                ))}
              </ul>
            </Card>
          </Col>
        </Row>

        <Card size="small" title="最新动态">
          <ul className="list-disc pl-5">
            {details.recentNews.map((item, index) => (
              <li key={index} className="text-gray-700">{item}</li>
            ))}
          </ul>
        </Card>
      </div>
    );
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 relative inline-block">
            期股联动分析
            <span className="absolute -top-3 -right-12 bg-gradient-to-r from-yellow-400 to-yellow-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-md transform rotate-12">
              PRO
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            基于豆粕期货与相关股票的联动关系，捕捉市场机会
          </p>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'overview',
              label: (
                <span>
                  <FundOutlined />
                  &nbsp; 市场概览
                </span>
              ),
              children: (
                <div className="space-y-6">
                  <Card>
                    <Table
                      columns={companyColumns}
                      dataSource={COMPANIES}
                      rowKey="code"
                      pagination={false}
                      size="small"
                      onRow={(record) => ({
                        onClick: () => setSelectedCompany(record),
                        className: 'cursor-pointer hover:bg-gray-50'
                      })}
                    />
                  </Card>
                  
                  <Row gutter={16}>
                    <Col span={24}>
                      <Card title={`${selectedCompany.name} - 股票行情`} className="mb-6">
                        <ReactECharts 
                          option={getKLineOption(generateKLineData(90))} 
                          style={{ height: '400px' }} 
                        />
                      </Card>
                    </Col>
                  </Row>

                  <Card>
                    <CompanyDetail company={selectedCompany} />
                  </Card>
                </div>
              ),
            },
            {
              key: 'signals',
              label: (
                <span>
                  <LineChartOutlined />
                  &nbsp; 联动信号
                </span>
              ),
              children: (
                <div className="space-y-6">
                  <Card>
                    {loading ? (
                      <Skeleton active />
                    ) : (
                      <Table
                        columns={signalColumns}
                        dataSource={signals}
                        rowKey={(record) => record.timestamp}
                        pagination={{ pageSize: 10 }}
                      />
                    )}
                  </Card>

                  <Card title="期现价差">
                    <ReactECharts option={getBasicOption()} style={{ height: '400px' }} />
                  </Card>
                </div>
              ),
            }
          ]}
        />

        <Divider className="my-12" />
        
        <Card className="mt-8">
          <div className="prose max-w-none">
            <h2 className="text-2xl font-bold mb-6">策略说明</h2>
            <p>本策略通过监测豆粕期货与相关股票的价格联动，捕捉产业链利润传导、市场预期差及跨市场套利机会，形成3-6个月的中长期配置。</p>
            
            <h3 className="text-xl font-semibold mt-8 mb-4">核心逻辑</h3>
            <ul>
              <li><strong>产业链利润传导</strong>：豆粕期货价格变动 → 影响上下游企业利润 → 驱动股价波动</li>
              <li><strong>跨市场预期差</strong>：期货市场反映商品供需，股票市场反映企业盈利，两者背离时存在套利空间</li>
              <li><strong>周期共振</strong>：结合养殖周期、种植周期与政策周期，预判联动趋势</li>
            </ul>

            <h3 className="text-xl font-semibold mt-8 mb-4">信号类型</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900">1. 正向联动信号</h4>
                <ul className="mt-2 space-y-2">
                  <li>豆粕期货连续3个月上涨，且基差从贴水转为升水</li>
                  <li>上游压榨企业PB分位数低于历史30%</li>
                  <li>操作建议：做多豆粕期货 + 做多压榨企业股票</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900">2. 反向联动信号</h4>
                <ul className="mt-2 space-y-2">
                  <li>豆粕期货跌幅 {'>'} 15%（3个月内），且生猪存栏量环比回升</li>
                  <li>下游养殖企业PE低于历史10%</li>
                  <li>操作建议：做空豆粕期货 + 做多养殖企业股票</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900">3. 跨市场套利信号</h4>
                <ul className="mt-2 space-y-2">
                  <li>压榨利润 {'>'} 500元/吨，且压榨企业股价未同步上涨</li>
                  <li>期货价格与股票指数60日相关系数 {'<'} -0.3</li>
                  <li>操作建议：做多压榨企业股票 + 做空豆粕期货</li>
                </ul>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default StockFutures; 