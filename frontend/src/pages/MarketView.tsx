import React, { useState, useEffect } from 'react';
import KLineChart from '../components/KLineChart';
import { Card, Statistic, Row, Col, Spin } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import Toast from '../components/Toast';
import Layout from '../components/layout/Layout';

interface MarketData {
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  turnover: number;
  openInterest: number;
  settlement: number;
}

const MarketView: React.FC = () => {
  const [loading, setLoading] = useState(false);
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

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            实时行情
          </h1>
          <p className="mt-3 max-w-2xl mx-auto text-xl text-gray-500 sm:mt-4">
            豆粕期货主力合约实时行情监控，提供K线图表与核心指标分析
          </p>
        </div>

        <div className="mb-8">
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="最新价"
                  value={marketData.price}
                  precision={2}
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
            <h1 className="text-2xl font-bold">豆粕主力实时行情</h1>
            {loading && <Spin />}
          </div>
          <KLineChart />
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