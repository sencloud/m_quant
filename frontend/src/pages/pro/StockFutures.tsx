import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { CompanyInfo, StockFuturesData, TradingSignal } from '../../types/stockFutures';
import Layout from '../../components/layout/Layout';
import { Card, Skeleton, Tabs, Tag, Table } from 'antd';
import { LineChartOutlined, FundOutlined, TeamOutlined } from '@ant-design/icons';
import type { EChartsOption } from 'echarts';

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

const StockFutures: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [loading, setLoading] = useState(false);

  const getChartOption = (): EChartsOption => ({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['基差', '压榨利润']
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
      data: [] // 这里填充日期数据
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
        data: [], // 这里填充基差数据
        smooth: true,
        lineStyle: {
          color: '#8884d8'
        }
      },
      {
        name: '压榨利润',
        type: 'line',
        yAxisIndex: 1,
        data: [], // 这里填充压榨利润数据
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
    },
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
                <Card>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white rounded-lg shadow">
                      <div className="px-4 py-5 sm:px-6">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">产业链公司</h3>
                      </div>
                      <Table
                        columns={companyColumns}
                        dataSource={COMPANIES}
                        rowKey="code"
                        pagination={false}
                        size="small"
                      />
                    </div>
                    <div className="bg-white rounded-lg shadow">
                      <div className="px-4 py-5 sm:px-6">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">期现价差</h3>
                      </div>
                      <div className="p-4">
                        <ReactECharts option={getChartOption()} style={{ height: '300px' }} />
                      </div>
                    </div>
                  </div>
                </Card>
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
              ),
            },
            {
              key: 'strategy',
              label: (
                <span>
                  <TeamOutlined />
                  &nbsp; 策略说明
                </span>
              ),
              children: (
                <Card>
                  <div className="prose max-w-none">
                    <h2>策略概述</h2>
                    <p>本策略通过监测豆粕期货与相关股票的价格联动，捕捉产业链利润传导、市场预期差及跨市场套利机会，形成3-6个月的中长期配置。</p>
                    
                    <h3>核心逻辑</h3>
                    <ul>
                      <li><strong>产业链利润传导</strong>：豆粕期货价格变动 → 影响上下游企业利润 → 驱动股价波动</li>
                      <li><strong>跨市场预期差</strong>：期货市场反映商品供需，股票市场反映企业盈利，两者背离时存在套利空间</li>
                      <li><strong>周期共振</strong>：结合养殖周期、种植周期与政策周期，预判联动趋势</li>
                    </ul>

                    <h3>信号类型</h3>
                    <div className="space-y-6">
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
              ),
            },
          ]}
        />
      </div>
    </Layout>
  );
};

export default StockFutures; 