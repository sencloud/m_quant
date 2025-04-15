import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';
import Layout from '../components/layout/Layout';
import { Card, Tabs, List, Tag, Skeleton, DatePicker, Space, Typography, Table } from 'antd';
import { LineChartOutlined, HistoryOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface NewsItem {
  datetime: string;
  title: string;
  content: string;
  source: string;
}

interface NewsAnalysis {
  date: string;
  news_count: number;
  price_change: number;
  volume_change: number;
  analysis: {
    title: string;
    content: string;
    datetime: string;
    sentiment: 'positive' | 'negative' | 'neutral';
  }[];
}

const NewsAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('1');
  const [selectedDate, setSelectedDate] = useState<string>(dayjs().format('YYYYMMDD'));

  // 获取每日新闻
  const { data: dailyNews, isLoading: isLoadingNews } = useQuery<NewsItem[]>({
    queryKey: ['dailyNews'],
    queryFn: async () => {
      const response = await axios.get(API_ENDPOINTS.news.daily);
      return response.data;
    },
    refetchOnWindowFocus: false
  });

  // 获取新闻分析
  const { data: newsAnalysis, isLoading: isLoadingAnalysis, error } = useQuery<NewsAnalysis>({
    queryKey: ['newsAnalysis', selectedDate],
    queryFn: async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.news.analysis, {
          params: { news_date: selectedDate }
        });
        return response.data;
      } catch (error) {
        console.error('获取新闻分析失败:', error);
        return null;
      }
    },
    refetchOnWindowFocus: false
  });

  // 获取新闻分析图表配置
  const getAnalysisChartOption = () => {
    if (!newsAnalysis) return {};

    return {
      title: {
        text: '新闻影响分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['价格变化', '成交量变化'],
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: [newsAnalysis.date]
      },
      yAxis: [
        {
          type: 'value',
          name: '价格变化',
          position: 'left'
        },
        {
          type: 'value',
          name: '成交量变化',
          position: 'right'
        }
      ],
      series: [
        {
          name: '价格变化',
          type: 'bar',
          data: [newsAnalysis.price_change],
          itemStyle: {
            color: newsAnalysis.price_change >= 0 ? '#f5222d' : '#52c41a'
          }
        },
        {
          name: '成交量变化',
          type: 'line',
          yAxisIndex: 1,
          data: [newsAnalysis.volume_change],
          itemStyle: {
            color: '#1890ff'
          }
        }
      ]
    };
  };

  // 渲染新闻列表
  const renderNewsList = () => {
    if (isLoadingNews) {
      return <Skeleton active />;
    }

    const columns = [
      {
        title: '时间',
        dataIndex: 'datetime',
        key: 'datetime',
        width: 150,
      },
      {
        title: '内容（来源：新浪财经）',
        dataIndex: 'content',
        key: 'content',
      }
    ];

    return (
      <Table
        dataSource={dailyNews}
        columns={columns}
        rowKey="datetime"
        pagination={{ pageSize: 10 }}
      />
    );
  };

  // 渲染新闻分析
  const renderNewsAnalysis = () => {
    if (isLoadingAnalysis) {
      return <Skeleton active />;
    }

    if (error || !newsAnalysis) {
      return <Text type="danger">暂无分析数据，请选择其他日期</Text>;
    }

    return (
      <div>
        <div className="mb-4">
          <DatePicker
            value={dayjs(selectedDate)}
            onChange={(date) => setSelectedDate(date?.format('YYYYMMDD') || dayjs().format('YYYYMMDD'))}
          />
        </div>
        <Card className="mb-4">
          <ReactECharts option={getAnalysisChartOption()} style={{ height: '400px' }} />
        </Card>
        <List
          dataSource={newsAnalysis.analysis}
          renderItem={(item) => (
            <List.Item>
              <Card className="w-full">
                <div className="flex justify-between items-start">
                  <div>
                    <Title level={5}>{item.title}</Title>
                    <Text type="secondary">{item.content}</Text>
                  </div>
                  <Tag color={
                    item.sentiment === 'positive' ? 'success' :
                    item.sentiment === 'negative' ? 'error' : 'default'
                  }>
                    {item.sentiment === 'positive' ? '利多' :
                     item.sentiment === 'negative' ? '利空' : '中性'}
                  </Tag>
                </div>
              </Card>
            </List.Item>
          )}
        />
      </div>
    );
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 relative inline-block">
            消息面分析
            <span className="absolute -top-3 -right-12 bg-gradient-to-r from-yellow-400 to-yellow-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-md transform rotate-12">
              PRO
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            分析宏观、国际、天气、大豆、豆粕、豆油、菜粕、生猪等相关资讯对期货价格的影响
          </p>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: '1',
              label: (
                <span>
                  <HistoryOutlined />
                  &nbsp; 简讯快报
                </span>
              ),
              children: renderNewsList()
            },
            {
              key: '2',
              label: (
                <span>
                  <LineChartOutlined />
                  &nbsp; 资讯分析
                </span>
              ),
              children: renderNewsAnalysis()
            }
          ]}
        />
      </div>
    </Layout>
  );
};

export default NewsAnalysis; 