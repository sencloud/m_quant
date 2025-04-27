import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import { Signal } from '../api/signals';
import SRLevels from './SRLevels';
import './Signallet.css';

interface SRLevel {
  price: number;
  type: 'Support' | 'Resistance';
  strength: number;
  start_time: string;
  break_time: string | null;
  retest_times: string[];
  timeframe: string;
}

const Signallet: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [srLevels, setSRLevels] = useState<SRLevel[]>([]);
  const [statistics, setStatistics] = useState({
    totalProfit: 0,
    winRate: 0,
    openSignals: 0
  });

  const fetchSignals = async () => {
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 7);
      
      const [statsResponse, accountResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/signals`, {
          params: {
            start_date: startDate.toISOString().split('T')[0],
            end_date: new Date().toISOString().split('T')[0],
            page: 1,
            page_size: 1000
          }
        }),
        axios.get(`${API_BASE_URL}/account/account`)
      ]);
      
      const signals = statsResponse.data.signals;
      const closedSignals = signals.filter((s: Signal) => 
        s.status === 'closed' || s.status === 'partial_closed'
      ).length;
      
      const totalProfit = signals.reduce((sum: number, s: Signal) => {
        if (s.status === 'closed' || s.status === 'partial_closed') {
          return sum + (s.profit || 0);
        }
        return sum;
      }, 0);
      
      const profitableSignals = signals.filter((s: Signal) => 
        (s.status === 'closed' || s.status === 'partial_closed') && s.profit > 0
      ).length;
      
      const winRate = closedSignals > 0 ? (profitableSignals / closedSignals) * 100 : 0;
      const openSignals = signals.filter((s: Signal) => s.status === 'open').length;
      
      setStatistics({
        totalProfit,
        winRate,
        openSignals
      });

      // 只获取最近的5个信号
      setSignals(signals.slice(0, 5));
    } catch (error) {
      console.error('获取信号数据失败:', error);
    }
  };

  const fetchSRLevels = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/market/kline/30`, {
        params: { contract: 'M2509' } // 默认使用主力合约
      });
      setSRLevels(response.data.sr_levels);
    } catch (error) {
      console.error('获取支撑阻力位数据失败:', error);
    }
  };

  useEffect(() => {
    fetchSignals();
    fetchSRLevels();
    const timer = setInterval(() => {
      fetchSignals();
      fetchSRLevels();
    }, 60000); // 每分钟更新一次
    return () => clearInterval(timer);
  }, []);

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

      <div className="signallet-section">
        <h3 className="text-sm font-medium text-gray-700 mb-2">交易信号</h3>
        <div className="signallet-signals">
          {signals.map((signal) => (
            <div key={signal.id} className="signal-item">
              <div className="signal-header">
                <span className="signal-symbol">{signal.symbol.split('-')[1]}</span>
                <span className={`signal-tag ${signal.type}`}>
                  {signal.type === 'BUY_OPEN' ? '买入开仓' : 
                   signal.type === 'SELL_OPEN' ? '卖出开仓' :
                   signal.type === 'BUY_CLOSE' ? '买入平仓' :
                   signal.type === 'SELL_CLOSE' ? '卖出平仓' : signal.type}
                </span>
              </div>
              <div className="signal-details">
                <div className="signal-info">
                  <span>价格: {signal.price.toFixed(2)}</span>
                  <span>数量: {signal.quantity}</span>
                </div>
                <div className="signal-status">
                  <span className={`status-tag ${signal.status}`}>
                    {signal.status === 'open' ? '持仓中' : 
                     signal.status === 'closed' ? '已平仓' :
                     signal.status === 'partial_closed' ? '部分平仓' : signal.status}
                  </span>
                  {signal.profit !== undefined && (
                    <span className={signal.profit >= 0 ? 'profit' : 'loss'}>
                      {signal.profit.toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="signallet-section">
        <h3 className="text-sm font-medium text-gray-700 mb-2">支撑阻力位</h3>
        <SRLevels levels={srLevels} />
      </div>
    </div>
  );
};

export default Signallet; 