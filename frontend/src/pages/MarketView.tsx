import React, { useState, useEffect, useRef } from 'react';
import KLineChart from '../components/KLineChart';
import { Card, Statistic, Row, Col, Spin, Button } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import Toast from '../components/Toast';
import Layout from '../components/layout/Layout';
import ReactMarkdown from 'react-markdown';

interface MarketData {
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  turnover: number;
  openInterest: number;
  settlement: number;
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

const MarketView: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState<string>('');
  const [streamingStrategy, setStreamingStrategy] = useState<string>('');
  const chartRef = useRef<any>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [marketData, setMarketData] = useState<MarketData>({
    price: 0,
    change: 0,
    changePercent: 0,
    volume: 0,
    turnover: 0,
    openInterest: 0,
    settlement: 0
  });
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // 获取实时行情数据
  const fetchMarketData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/market/realtime`);
      setMarketData(response.data);
    } catch (error) {
      console.error('获取行情数据失败:', error);
      setToast({
        message: '获取行情数据失败',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初始加载数据
    fetchMarketData();

    // 判断当前是否为交易时间
    const isTradeTime = () => {
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      
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

    // 只在交易时间内每3秒刷新一次数据
    const timer = setInterval(() => {
      if (isTradeTime()) {
        fetchMarketData();
      }
    }, 3000);

    return () => {
      clearInterval(timer);
    };
  }, []);

  // 清理函数
  const cleanupEventSource = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      cleanupEventSource();
    };
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            操盘
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            豆粕期货主力合约行情监控，提供K线图表与支撑阻力位分析
          </p>
        </div>

        <div className="mb-8">
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="最新价"
                  value={marketData.price}
                  precision={0}
                  valueStyle={{ color: marketData.change >= 0 ? '#cf1322' : '#3f8600' }}
                  prefix={marketData.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  suffix="元"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="涨跌幅"
                  value={marketData.changePercent}
                  precision={2}
                  valueStyle={{ color: marketData.change >= 0 ? '#cf1322' : '#3f8600' }}
                  prefix={marketData.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  suffix="%"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="成交量"
                  value={marketData.volume}
                  precision={0}
                  suffix="手"
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="持仓量"
                  value={marketData.openInterest}
                  precision={0}
                  suffix="手"
                />
              </Card>
            </Col>
          </Row>
        </div>

        <div className="bg-white rounded-lg">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">豆粕2509合约行情</h1>
            <div className="flex items-center">
              {loading && <Spin className="mr-4" />}
            </div>
          </div>
          <div>
            <KLineChart ref={chartRef} />
          </div>
        </div>
        <div className="bg-white rounded-lg mt-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">操盘策略（DeepSeek提示）</h1>
            <div className="flex items-center">
              {loading && <Spin className="mr-4" />}
              <Button 
                type="primary" 
                onClick={async () => {
                  try {
                    setLoading(true);
                    setStreamingStrategy(''); // 清空之前的内容
                    setStrategy(''); // 清空之前的完整内容
                    
                    // 清理之前的 EventSource
                    cleanupEventSource();

                    // 获取当前K线图的sr_levels数据
                    const chartInstance = chartRef.current?.getEchartsInstance();
                    const option = chartInstance?.getOption();
                    const markLines = option?.series[0]?.markLine?.data || [];
                    
                    // 转换为后端需要的格式
                    const sr_levels = markLines.map((line: any) => ({
                      price: Number(line[0].coord[1]),
                      type: line[0].name === 'Support' ? 'Support' : 'Resistance',
                      strength: Number(line[0].lineStyle.width),
                      start_time: option.xAxis[0].data[line[0].coord[0]],
                      break_time: line[1].coord ? option.xAxis[0].data[line[1].coord[0]] : null,
                      retest_times: [],
                      timeframe: '30m'
                    }));

                    // 发送 POST 请求并处理流式响应
                    const response = await fetch(`${API_BASE_URL}/market/strategy`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream',
                      },
                      body: JSON.stringify({ sr_levels }),
                    });

                    if (!response.ok) {
                      throw new Error('Strategy request failed');
                    }

                    // 创建响应流读取器
                    const reader = response.body?.getReader();
                    const decoder = new TextDecoder();

                    if (!reader) {
                      throw new Error('Failed to create stream reader');
                    }

                    // 读取流数据
                    while (true) {
                      const { done, value } = await reader.read();
                      if (done) {
                        setLoading(false);
                        break;
                      }

                      // 解码并处理数据
                      const text = decoder.decode(value);
                      const lines = text.split('\n');
                      
                      for (const line of lines) {
                        if (line.startsWith('data: ')) {
                          try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'content') {
                              setStreamingStrategy(prev => prev + data.content);
                            } else if (data.type === 'done') {
                              setStrategy(data.content);
                              setLoading(false);
                              reader.cancel();
                              break;
                            }
                          } catch (error) {
                            console.error('Error parsing SSE data:', error);
                          }
                        }
                      }
                    }

                  } catch (error) {
                    console.error('获取策略失败:', error);
                    setToast({
                      message: '获取策略失败，请稍后重试',
                      type: 'error'
                    });
                    setLoading(false);
                  }
                }}
              >
                立即获取
              </Button>
            </div>
          </div>
          {(streamingStrategy || strategy) && (
            <div className="strategy-content p-4 whitespace-pre-wrap">
              <ReactMarkdown>{streamingStrategy || strategy}</ReactMarkdown>
            </div>
          )}
        </div>

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </div>
    </Layout>
  );
};

export default MarketView; 