import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { CompanyInfo, StockFuturesData, TradingSignal } from '../../types/stockFutures';
import Layout from '../../components/layout/Layout';
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

// 扩展信号的详细信息
const SIGNAL_DETAILS = {
  'positive': {
    title: '正向联动信号分析',
    indicators: [
      { name: '期货趋势', value: '连续上涨', status: 'positive' },
      { name: '基差变化', value: '贴水转升水', status: 'positive' },
      { name: '现货价格', value: '4280元/吨', status: 'neutral' },
      { name: '期货主力', value: '4350元/吨', status: 'neutral' },
      { name: '基差水平', value: '+70元/吨', status: 'positive' },
    ],
    technicalAnalysis: {
      momentum: { name: 'MACD', value: '金叉', interpretation: '多头动能增强' },
      trend: { name: 'MA', value: '多头排列', interpretation: '趋势向上' },
      volatility: { name: 'Bollinger Bands', value: '通道上移', interpretation: '波动率可控' }
    },
    fundamentals: [
      '南美大豆减产预期增强',
      '国内养殖需求逐步恢复',
      '压榨企业库存处于低位',
      '现货市场成交活跃度提升'
    ],
    relatedStocks: [
      { code: '300999.SZ', name: '金龙鱼', change: '+2.15%', reason: '压榨利润改善' },
      { code: '000930.SZ', name: '中粮科技', change: '+1.88%', reason: '库存价值提升' }
    ],
    tradingSuggestions: [
      '期货：可考虑逢低做多M2405合约',
      '现货：适当补库，控制库存周期',
      '股票：关注上游压榨企业机会',
      '套利：期现正套机会显现'
    ],
    riskFactors: [
      '美豆价格波动风险',
      '人民币汇率波动风险',
      '下游需求不及预期风险'
    ]
  },
  'negative': {
    title: '反向联动信号分析',
    indicators: [
      { name: '期货跌幅', value: '-15.3%', status: 'negative' },
      { name: '生猪存栏', value: '环比+5.2%', status: 'positive' },
      { name: '养殖利润', value: '320元/头', status: 'neutral' },
      { name: '豆粕库存', value: '98.5万吨', status: 'negative' },
      { name: '压榨开机率', value: '52.3%', status: 'negative' },
    ],
    technicalAnalysis: {
      momentum: { name: 'RSI', value: '超卖', interpretation: '下跌动能减弱' },
      trend: { name: 'KDJ', value: '死叉', interpretation: '短期看空' },
      volatility: { name: 'ATR', value: '扩大', interpretation: '波动加剧' }
    },
    fundamentals: [
      '美豆丰产预期强化',
      '生猪存栏持续回升',
      '豆粕库存压力较大',
      '压榨利润持续承压'
    ],
    relatedStocks: [
      { code: '002714.SZ', name: '牧原股份', change: '+3.25%', reason: '成本预期改善' },
      { code: '300498.SZ', name: '温氏股份', change: '+2.76%', reason: '养殖周期向上' }
    ],
    tradingSuggestions: [
      '期货：可考虑逢高做空M2405合约',
      '现货：维持低库存运行',
      '股票：关注下游养殖企业机会',
      '套利：期现反套可行性增加'
    ],
    riskFactors: [
      '南美天气异常风险',
      '生猪存栏不及预期风险',
      '政策调控风险'
    ]
  },
  'arbitrage': {
    title: '跨市场套利信号分析',
    indicators: [
      { name: '压榨利润', value: '628元/吨', status: 'positive' },
      { name: '相关系数', value: '-0.35', status: 'positive' },
      { name: '基差水平', value: '-120元/吨', status: 'negative' },
      { name: '股债性价比', value: '1.25', status: 'positive' },
      { name: '期限结构', value: '正向递增', status: 'neutral' },
    ],
    technicalAnalysis: {
      momentum: { name: 'CMF', value: '资金流入', interpretation: '市场情绪改善' },
      trend: { name: 'EMV', value: '底部企稳', interpretation: '市场动能转换' },
      volatility: { name: 'VWAP', value: '支撑明显', interpretation: '价格结构稳定' }
    },
    fundamentals: [
      '基差修复预期增强',
      '股票估值处于低位',
      '期货升水结构改善',
      '产业资金入场迹象明显'
    ],
    relatedStocks: [
      { code: '000930.SZ', name: '中粮科技', change: '-1.25%', reason: '低估机会显现' },
      { code: '300999.SZ', name: '金龙鱼', change: '-0.88%', reason: '市场预期差' }
    ],
    tradingSuggestions: [
      '期货：择机做空远月合约',
      '现货：考虑买入库存',
      '股票：布局低估值标的',
      '套利：期现套利性价比提升'
    ],
    riskFactors: [
      '市场流动性风险',
      '政策监管风险',
      '基本面预期差风险'
    ]
  }
};

const StockFutures: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [signals, setSignals] = useState<TradingSignal[]>(MOCK_SIGNALS);
  const [loading, setLoading] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<CompanyInfo>(COMPANIES[0]);
  const [selectedSignal, setSelectedSignal] = useState<TradingSignal>(MOCK_SIGNALS[0]);

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
      boundaryGap: true
    },
    yAxis: {
      type: 'value',
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

  const CompanyDetail = ({ company }: { company: CompanyInfo }) => {
    const details = COMPANY_DETAILS[company.code as keyof typeof COMPANY_DETAILS];
    if (!details) return null;

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h4 className="text-xl font-bold">{company.name} ({company.code})</h4>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            实时: 26.80 <span className="text-red-600">+2.15%</span>
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-4 border rounded-lg p-4 bg-gray-50">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">公司全称</span>
              <span className="font-medium">{details.fullName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">所属行业</span>
              <span className="font-medium">{details.industry}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">市值</span>
              <span className="font-medium">{details.marketCap}</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">市盈率</span>
              <span className="font-medium">{details.peRatio}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">市净率</span>
              <span className="font-medium">{details.pbRatio}</span>
            </div>
          </div>
        </div>

        <div>
          <h5 className="text-lg font-semibold mb-3">主营业务</h5>
          <ul className="list-disc pl-5 space-y-1">
            {details.mainBusiness.map((item, index) => (
              <li key={index} className="text-gray-700">{item}</li>
            ))}
          </ul>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border p-4">
            <h6 className="text-base font-semibold mb-3">核心优势</h6>
            <ul className="list-disc pl-5 space-y-1">
              {details.advantages.map((item, index) => (
                <li key={index} className="text-gray-700">{item}</li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <h6 className="text-base font-semibold mb-3">风险提示</h6>
            <ul className="list-disc pl-5 space-y-1">
              {details.risks.map((item, index) => (
                <li key={index} className="text-gray-700 text-sm">{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h6 className="text-base font-semibold mb-3">最新动态</h6>
          <ul className="list-disc pl-5 space-y-1">
            {details.recentNews.map((item, index) => (
              <li key={index} className="text-gray-700">{item}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const SignalDetail = ({ signal }: { signal: TradingSignal }) => {
    const details = SIGNAL_DETAILS[signal.type as keyof typeof SIGNAL_DETAILS];
    if (!details) return null;

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h4 className="text-xl font-bold">{details.title}</h4>
          <span className={`
            px-3 py-1 rounded-full text-sm font-medium
            ${signal.type === 'positive' ? 'bg-green-100 text-green-800' :
              signal.type === 'negative' ? 'bg-red-100 text-red-800' :
              'bg-blue-100 text-blue-800'}
          `}>
            {signal.type === 'positive' ? '正向联动' :
             signal.type === 'negative' ? '反向联动' : '套利机会'}
          </span>
        </div>

        <div className="grid grid-cols-5 gap-4">
          {details.indicators.map((indicator, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-sm text-gray-500 mb-1">{indicator.name}</div>
              <div className={`font-medium ${
                indicator.status === 'positive' ? 'text-green-600' :
                indicator.status === 'negative' ? 'text-red-600' :
                'text-gray-600'
              }`}>{indicator.value}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border p-4">
            <h6 className="text-base font-semibold mb-3">技术分析</h6>
            <div className="space-y-3">
              {Object.entries(details.technicalAnalysis).map(([key, analysis]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">{analysis.name}</span>
                  <div className="text-right">
                    <div className="font-medium text-gray-900">{analysis.value}</div>
                    <div className="text-xs text-gray-500">{analysis.interpretation}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <h6 className="text-base font-semibold mb-3">基本面因素</h6>
            <ul className="list-disc pl-5 space-y-1">
              {details.fundamentals.map((item, index) => (
                <li key={index} className="text-gray-600">{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <h6 className="text-base font-semibold mb-3">相关个股表现</h6>
          <div className="grid grid-cols-2 gap-4">
            {details.relatedStocks.map((stock, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div>
                  <div className="font-medium">{stock.name}</div>
                  <div className="text-sm text-gray-500">{stock.code}</div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${
                    stock.change.startsWith('+') ? 'text-red-600' : 'text-green-600'
                  }`}>{stock.change}</div>
                  <div className="text-xs text-gray-500">{stock.reason}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg border p-4">
            <h6 className="text-base font-semibold mb-3">交易建议</h6>
            <ul className="list-disc pl-5 space-y-1">
              {details.tradingSuggestions.map((item, index) => (
                <li key={index} className="text-gray-600">{item}</li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <h6 className="text-base font-semibold mb-3">风险因素</h6>
            <ul className="list-disc pl-5 space-y-1">
              {details.riskFactors.map((item, index) => (
                <li key={index} className="text-gray-600">{item}</li>
              ))}
            </ul>
          </div>
        </div>
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

        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                  市场概览
                </span>
              </button>
              <button
                onClick={() => setActiveTab('signals')}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === 'signals'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  联动信号
                </span>
              </button>
            </nav>
          </div>

          <div className="mt-6">
            {activeTab === 'overview' ? (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">代码</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名称</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">描述</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {COMPANIES.map((company) => (
                          <tr
                            key={company.code}
                            onClick={() => setSelectedCompany(company)}
                            className="hover:bg-gray-50 cursor-pointer"
                          >
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{company.code}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{company.name}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <span className={`
                                px-2 py-1 rounded-full text-xs font-medium
                                ${company.type === 'upstream' ? 'bg-blue-100 text-blue-800' :
                                  company.type === 'midstream' ? 'bg-green-100 text-green-800' :
                                  company.type === 'downstream' ? 'bg-orange-100 text-orange-800' :
                                  'bg-gray-100 text-gray-800'}
                              `}>
                                {company.type === 'upstream' ? '上游' :
                                 company.type === 'midstream' ? '中游' :
                                 company.type === 'downstream' ? '下游' : '其他'}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">{company.description}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 hover:text-blue-800">
                              <button className="flex items-center">
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                                查看详情
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">{selectedCompany.name} - 股票行情</h3>
                  <ReactECharts 
                    option={getKLineOption(generateKLineData(90))} 
                    style={{ height: '400px' }} 
                  />
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <CompanyDetail company={selectedCompany} />
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时间</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">描述</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {signals.map((signal) => (
                          <tr
                            key={signal.timestamp}
                            onClick={() => setSelectedSignal(signal)}
                            className={`hover:bg-gray-50 cursor-pointer ${
                              selectedSignal.timestamp === signal.timestamp ? 'bg-blue-50' : ''
                            }`}
                          >
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{signal.timestamp}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`
                                px-2 py-1 rounded-full text-xs font-medium
                                ${signal.type === 'positive' ? 'bg-green-100 text-green-800' :
                                  signal.type === 'negative' ? 'bg-red-100 text-red-800' :
                                  'bg-blue-100 text-blue-800'}
                              `}>
                                {signal.type === 'positive' ? '正向联动' :
                                 signal.type === 'negative' ? '反向联动' : '套利机会'}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">{signal.description}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 hover:text-blue-800">
                              <button className="flex items-center">
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                                查看详情
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <SignalDetail signal={selectedSignal} />
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">期现价差</h3>
                  <ReactECharts option={getBasicOption()} style={{ height: '400px' }} />
                </div>
              </div>
            )}
          </div>
        </div>

        <hr className="my-12 border-gray-200" />
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="prose max-w-none">
            <h2 className="text-2xl font-bold mb-6">策略说明</h2>
            <p className="text-gray-600">本策略通过监测豆粕期货与相关股票的价格联动，捕捉产业链利润传导、市场预期差及跨市场套利机会，形成3-6个月的中长期配置。</p>
            
            <h3 className="text-xl font-semibold mt-8 mb-4">核心逻辑</h3>
            <ul className="space-y-2 text-gray-600">
              <li><strong>产业链利润传导</strong>：豆粕期货价格变动 → 影响上下游企业利润 → 驱动股价波动</li>
              <li><strong>跨市场预期差</strong>：期货市场反映商品供需，股票市场反映企业盈利，两者背离时存在套利空间</li>
              <li><strong>周期共振</strong>：结合养殖周期、种植周期与政策周期，预判联动趋势</li>
            </ul>

            <h3 className="text-xl font-semibold mt-8 mb-4">信号类型</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900">1. 正向联动信号</h4>
                <ul className="mt-2 space-y-2 text-gray-600">
                  <li>豆粕期货连续3个月上涨，且基差从贴水转为升水</li>
                  <li>上游压榨企业PB分位数低于历史30%</li>
                  <li>操作建议：做多豆粕期货 + 做多压榨企业股票</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900">2. 反向联动信号</h4>
                <ul className="mt-2 space-y-2 text-gray-600">
                  <li>豆粕期货跌幅 {'>'} 15%（3个月内），且生猪存栏量环比回升</li>
                  <li>下游养殖企业PE低于历史10%</li>
                  <li>操作建议：做空豆粕期货 + 做多养殖企业股票</li>
                </ul>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900">3. 跨市场套利信号</h4>
                <ul className="mt-2 space-y-2 text-gray-600">
                  <li>压榨利润 {'>'} 500元/吨，且压榨企业股价未同步上涨</li>
                  <li>期货价格与股票指数60日相关系数 {'<'} -0.3</li>
                  <li>操作建议：做多压榨企业股票 + 做空豆粕期货</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default StockFutures; 