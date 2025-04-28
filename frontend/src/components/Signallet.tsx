import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import { Signal } from '../api/signals';
import SRLevels from './SRLevels';
import './Signallet.css';

interface KLineData {
  date: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema5: number;
  ema20: number;
  open_interest: number;
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

interface SignalletProps {
  srLevels: SRLevel[];
  selectedContract: string;
}

const Signallet: React.FC<SignalletProps> = ({ srLevels, selectedContract }) => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [activeTab, setActiveTab] = useState<'signals' | 'srlevels'>('signals');
  const [statistics, setStatistics] = useState({
    totalProfit: 0,
    winRate: 0,
    openSignals: 0
  });

  const isSignalNearSRLevel = (signal: Signal): boolean => {
    const priceDiff = 0.01; // 1% 的价格差异阈值
    return srLevels.some(level => 
      Math.abs(signal.price - level.price) / level.price <= priceDiff
    );
  };

  const fetchSignals = async () => {
    try {
      // 如果没有选中合约，直接返回
      if (!selectedContract) {
        return;
      }

      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 7);
      
      const [klineResponse, accountResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/market/kline/30`, {
          params: {
            contract: selectedContract
          }
        }),
        axios.get(`${API_BASE_URL}/account/account`)
      ]);

      // 确保K线数据存在且格式正确
      if (!klineResponse.data?.kline_data || !Array.isArray(klineResponse.data.kline_data)) {
        console.error('K线数据格式错误:', klineResponse.data);
        return;
      }

      // 转换K线数据格式
      const formattedKlines = klineResponse.data.kline_data.map((kline: KLineData) => ({
        date: kline.date,
        symbol: "期货-" + selectedContract,
        open: kline.open,
        high: kline.high,
        low: kline.low,
        close: kline.close,
        volume: kline.volume,
        ema5: kline.ema5,
        ema20: kline.ema20,
        open_interest: kline.open_interest
      }));

      const signalResponse = await axios.post(`${API_BASE_URL}/signals`, {
        start_date: startDate.toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        page: 1,
        page_size: 1000,
        klines: formattedKlines
      });
      
      const allSignals = signalResponse.data.signals;
      const validSignals = allSignals.filter(isSignalNearSRLevel);
      
      const closedSignals = validSignals.filter((s: Signal) => 
        s.status === 'closed' || s.status === 'partial_closed'
      ).length;
      
      const totalProfit = validSignals.reduce((sum: number, s: Signal) => {
        if (s.status === 'closed' || s.status === 'partial_closed') {
          return sum + (s.profit || 0);
        }
        return sum;
      }, 0);
      
      const profitableSignals = validSignals.filter((s: Signal) => 
        (s.status === 'closed' || s.status === 'partial_closed') && s.profit > 0
      ).length;
      
      const winRate = closedSignals > 0 ? (profitableSignals / closedSignals) * 100 : 0;
      const openSignals = validSignals.filter((s: Signal) => s.status === 'open').length;
      
      setStatistics({
        totalProfit,
        winRate,
        openSignals
      });

      setSignals(validSignals);
    } catch (error) {
      console.error('获取信号数据失败:', error);
    }
  };

  useEffect(() => {
    // 只有在有选中合约时才开始轮询
    if (selectedContract) {
      fetchSignals();
      const timer = setInterval(fetchSignals, 60000);
      return () => clearInterval(timer);
    }
  }, [srLevels, selectedContract]);

  return (
    <div className="signallet">
      <div className="signallet-header">
        <h2>信号监控</h2>
      </div>
      
      <div className="signallet-stats">
        <div className="stat-item">
          <span>持仓信号</span>
          <span className="value">{statistics.openSignals}</span>
        </div>
        <div className="stat-item">
          <span>总盈亏</span>
          <span className={`value ${statistics.totalProfit >= 0 ? 'profit' : 'loss'}`}>
            {statistics.totalProfit.toFixed(2)}
          </span>
        </div>
        <div className="stat-item">
          <span>胜率</span>
          <span className={`value ${statistics.winRate >= 50 ? 'profit' : 'loss'}`}>
            {statistics.winRate.toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="border-b border-gray-200 mb-4">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('signals')}
            className={`${
              activeTab === 'signals'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            交易信号
          </button>
          <button
            onClick={() => setActiveTab('srlevels')}
            className={`${
              activeTab === 'srlevels'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            支撑阻力位
          </button>
        </nav>
      </div>

      {activeTab === 'signals' && (
        <div className="signallet-signals space-y-4">
          {signals.map((signal) => (
            <div key={signal.id} className="signal-item bg-white rounded-lg shadow p-4">
              <div className="signal-header flex justify-between items-center mb-2">
                <div className="flex items-center space-x-2">
                  <span className="signal-symbol font-semibold">{signal.symbol.split('-')[1]}</span>
                  <span className={`signal-tag px-2 py-1 rounded text-sm ${
                    signal.type === 'BUY_OPEN' ? 'bg-red-100 text-red-800' :
                    signal.type === 'SELL_OPEN' ? 'bg-green-100 text-green-800' :
                    signal.type === 'BUY_CLOSE' ? 'bg-green-100 text-green-800' :
                    'bg-red-100 text-red-800'  // SELL_CLOSE
                  }`}>
                    {signal.type === 'BUY_OPEN' ? '买入开仓' : 
                     signal.type === 'SELL_OPEN' ? '卖出开仓' :
                     signal.type === 'BUY_CLOSE' ? '买入平仓' :
                     signal.type === 'SELL_CLOSE' ? '卖出平仓' : signal.type}
                  </span>
                </div>
              </div>

              <div className="signal-details space-y-2 text-sm">
                <div className="space-y-2">
                  <div>
                    <span className="text-gray-500">开仓价格:</span>
                    <span className="ml-2 font-medium">{signal.price.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">开仓时间:</span>
                    <span className="ml-2">{new Date(signal.date).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">信号说明:</span>
                    <span className="ml-2">{signal.reason}</span>
                  </div>
                  {signal.close_price && (
                    <div>
                      <span className="text-gray-500">平仓价格:</span>
                      <span className="ml-2 font-medium">{signal.close_price.toFixed(2)}</span>
                    </div>
                  )}
                  {signal.close_date && (
                    <div>
                      <span className="text-gray-500">平仓时间:</span>
                      <span className="ml-2">{new Date(signal.close_date).toLocaleString()}</span>
                    </div>
                  )}
                  {signal.profit !== undefined && signal.profit !== 0 && (
                    <div>
                      <span className="text-gray-500">盈亏:</span>
                      <span className={`ml-2 font-medium ${signal.profit >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {signal.profit >= 0 ? '+' : ''}{signal.profit.toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'srlevels' && (
        <div className="signallet-section">
          <SRLevels levels={srLevels} />
        </div>
      )}
    </div>
  );
};

export default Signallet; 