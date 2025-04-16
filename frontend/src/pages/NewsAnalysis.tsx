import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';
import Layout from '../components/layout/Layout';
import { Card, Tabs, List, Tag, Skeleton, DatePicker, Space, Typography, Table, Button } from 'antd';
import { LineChartOutlined, HistoryOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import dayjs from 'dayjs';
import ReactMarkdown from 'react-markdown';

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
  analysis: {
    title: string;
    content: string;
    datetime: string;
    importance: string;
    sentiment: string;
    impact_level: string;
    analysis: string;
  }[];
}

const NewsAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('1');
  const [selectedDate, setSelectedDate] = useState<string>(dayjs().format('YYYYMMDD'));
  const [isAnalyzing, setIsAnalyzing] = useState(false);

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
  const { data: newsAnalysis, isLoading: isLoadingAnalysis, error, refetch } = useQuery<NewsAnalysis>({
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

  // 分析新闻
  const handleAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      await axios.post(API_ENDPOINTS.news.analyze, null, {
        params: { news_date: selectedDate }
      });
      await refetch();
    } catch (error) {
      console.error('分析新闻失败:', error);
    } finally {
      setIsAnalyzing(false);
    }
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
        <div className="mb-4 flex items-center gap-4">
          <DatePicker
            value={dayjs(selectedDate)}
            onChange={(date) => setSelectedDate(date?.format('YYYYMMDD') || dayjs().format('YYYYMMDD'))}
          />
          <Button 
            type="primary" 
            onClick={handleAnalyze} 
            loading={isAnalyzing}
          >
            分析
          </Button>
        </div>
        <List
          dataSource={newsAnalysis.analysis}
          renderItem={(item) => (
            <List.Item>
              <Card className="w-full">
                <div className="flex justify-between items-start">
                  <div>
                    <Title level={5}>{item.title}</Title>
                    <Text type="secondary">{item.content}</Text>
                    <div className="mt-2">
                      <Text type="secondary">重要性：</Text>
                      <Tag color={
                        item.importance === '高' ? 'red' :
                        item.importance === '中' ? 'orange' : 'blue'
                      }>
                        {item.importance}
                      </Tag>
                      <Text type="secondary" className="ml-4">影响：</Text>
                      <Tag color={
                        item.sentiment === '利多' ? 'success' :
                        item.sentiment === '利空' ? 'error' : 'default'
                      }>
                        {item.sentiment}
                      </Tag>
                      <Text type="secondary" className="ml-4">程度：</Text>
                      <Tag color={
                        item.impact_level === '强' ? 'red' :
                        item.impact_level === '中' ? 'orange' : 'blue'
                      }>
                        {item.impact_level}
                      </Tag>
                    </div>
                    <div className="mt-2">
                      <Text type="secondary">分析：</Text>
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{item.analysis}</ReactMarkdown>
                      </div>
                    </div>
                  </div>
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