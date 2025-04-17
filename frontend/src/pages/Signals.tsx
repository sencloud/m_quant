import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import { Signal } from '../api/signals';
import Toast from '../components/Toast';
import './Signals.css';

const Signals: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[Date, Date]>([
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    new Date()
  ]);
  const [signalType, setSignalType] = useState<string>('all');
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState({
    sms: false,
    wecom: false,
    phone: '',
    wecomKey: ''
  });
  const [statistics, setStatistics] = useState({
    totalSignals: 0,
    openSignals: 0,
    closedSignals: 0,
    totalProfit: 0,
    winRate: 0,
    initialBalance: 0,
    currentBalance: 0,
    totalCommission: 0
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [formData, setFormData] = useState({
    date: (() => {
      const now = new Date();
      now.setHours(now.getHours() + 8);
      return now.toISOString().slice(0, 19);
    })(),
    symbol_type: 'stock',
    symbol: '',
    type: 'BUY_OPEN',
    price: '',
    quantity: '',
    reason: ''
  });
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const startDate = dateRange[0].toISOString().split('T')[0];
      const endDate = dateRange[1].toISOString().split('T')[0];
      
      // 获取统计数据
      const [statsResponse, accountResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/signals`, {
          params: {
            start_date: startDate,
            end_date: endDate,
            type: signalType !== 'all' ? signalType : undefined,
            page: 1,
            page_size: 1000
          }
        }),
        axios.get(`${API_BASE_URL}/account/account`)
      ]);
      
      // 计算统计数据
      const totalSignals = statsResponse.data.total;
      const signals = statsResponse.data.signals;
      
      // 只计算已完全平仓或部分平仓的信号
      const closedSignals = signals.filter((s: Signal) => 
        s.status === 'closed' || s.status === 'partial_closed'
      ).length;
      
      // 计算总盈亏（只计算已平仓和部分平仓的信号）
      const totalProfit = signals.reduce((sum: number, s: Signal) => {
        if (s.status === 'closed' || s.status === 'partial_closed') {
          return sum + (s.profit || 0);
        }
        return sum;
      }, 0);
      
      // 计算盈利的信号数（只计算已平仓和部分平仓的信号）
      const profitableSignals = signals.filter((s: Signal) => 
        (s.status === 'closed' || s.status === 'partial_closed') && s.profit > 0
      ).length;
      
      // 计算胜率
      const winRate = closedSignals > 0 ? (profitableSignals / closedSignals) * 100 : 0;
      
      // 计算持仓中的信号数
      const openSignals = signals.filter((s: Signal) => s.status === 'open').length;
      
      setStatistics({
        totalSignals,
        openSignals,
        closedSignals,
        totalProfit,
        winRate,
        initialBalance: accountResponse.data.initial_balance,
        currentBalance: accountResponse.data.initial_balance + totalProfit - accountResponse.data.total_commission,
        totalCommission: accountResponse.data.total_commission
      });

      // 获取分页数据
      const response = await axios.get(`${API_BASE_URL}/signals`, {
        params: {
          start_date: startDate,
          end_date: endDate,
          type: signalType !== 'all' ? signalType : undefined,
          page: pagination.current,
          page_size: pagination.pageSize
        }
      });
      
      setSignals(response.data.signals);
      setPagination({
        ...pagination,
        total: response.data.total
      });
    } catch (error) {
      console.error('获取信号数据失败:', error);
      setToast({
        message: '获取信号数据失败',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [dateRange, signalType, pagination.current, pagination.pageSize]);

  const handlePageChange = (page: number, pageSize: number) => {
    setPagination({
      ...pagination,
      current: page,
      pageSize: pageSize
    });
  };

  const handleSaveNotificationSettings = async () => {
    try {
      await axios.post(`${API_BASE_URL}/notification-settings`, notificationSettings);
      setShowNotificationModal(false);
      setToast({
        message: '推送设置已保存',
        type: 'success'
      });
    } catch (error) {
      console.error('保存推送设置失败:', error);
      setToast({
        message: '保存推送设置失败',
        type: 'error'
      });
    }
  };

  const handleAddSignal = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const signalData = {
        ...formData,
        date: new Date(formData.date).toISOString(),
        status: 'open',
        symbol: `${formData.symbol_type}-${formData.symbol}`,
        price: parseFloat(formData.price),
        quantity: parseInt(formData.quantity),
        reason: formData.reason || '手动添加'
      };
      
      await axios.post(`${API_BASE_URL}/signals`, signalData);
      setToast({
        message: '添加信号成功',
        type: 'success'
      });
      setIsModalVisible(false);
      setFormData({
        date: (() => {
          const now = new Date();
          now.setHours(now.getHours() + 8);
          return now.toISOString().slice(0, 19);
        })(),
        symbol_type: 'stock',
        symbol: '',
        type: 'BUY_OPEN',
        price: '',
        quantity: '',
        reason: ''
      });
      fetchSignals();
    } catch (error) {
      console.error('Error adding signal:', error);
      setToast({
        message: '添加信号失败',
        type: 'error'
      });
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <Layout>
      <div className="signals-container">
        <div className="signals-header">
          <h1>交易信号</h1>
          <p>实盘买涨买跌信号及交易记录</p>
        </div>

        <div className="signals-controls">
          <div className="date-range">
            <input 
              type="date" 
              value={dateRange[0].toISOString().split('T')[0]}
              onChange={(e) => setDateRange([new Date(e.target.value), dateRange[1]])}
            />
            <span>至</span>
            <input 
              type="date" 
              value={dateRange[1].toISOString().split('T')[0]}
              onChange={(e) => setDateRange([dateRange[0], new Date(e.target.value)])}
            />
          </div>
          
          <select 
            value={signalType} 
            onChange={(e) => setSignalType(e.target.value)}
            className="signal-type-select"
          >
            <option value="all">全部信号</option>
            <option value="BUY_OPEN">买入开仓</option>
            <option value="SELL_OPEN">卖出开仓</option>
            <option value="BUY_CLOSE">买入平仓</option>
            <option value="SELL_CLOSE">卖出平仓</option>
            <option value="open">持仓中</option>
            <option value="closed">已平仓</option>
          </select>

          <div className="button-group">
            <button 
              className="add-button"
              onClick={() => setIsModalVisible(true)}
            >
              添加信号
            </button>
            <button 
              onClick={() => setShowNotificationModal(true)}
              className="notification-button"
            >
              推送配置
            </button>
          </div>
        </div>

        <div className="statistics-grid">
          <div className="stat-card">
            <h3>总信号数</h3>
            <p className="stat-value">{statistics.totalSignals}</p>
          </div>
          <div className="stat-card">
            <h3>总资产</h3>
            <p className="stat-value">
              {statistics.currentBalance.toFixed(2)}
              <span className="stat-label">初始: {statistics.initialBalance.toFixed(2)}</span>
            </p>
          </div>
          <div className="stat-card">
            <h3>总手续费</h3>
            <p className="stat-value">{statistics.totalCommission.toFixed(2)}</p>
          </div>
          <div className="stat-card">
            <h3>总盈亏</h3>
            <p className={`stat-value ${statistics.totalProfit >= 0 ? 'profit' : 'loss'}`}>
              {statistics.totalProfit.toFixed(2)}
            </p>
          </div>
          <div className="stat-card">
            <h3>胜率</h3>
            <p className={`stat-value ${statistics.winRate >= 50 ? 'profit' : 'loss'}`}>
              {statistics.winRate.toFixed(2)}%
            </p>
          </div>
        </div>

        <div className="signals-table">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>品种</th>
                <th>类型</th>
                <th>价格</th>
                <th>数量</th>
                <th>状态</th>
                <th>原因</th>
                <th>平仓时间</th>
                <th>平仓价格</th>
                <th>盈亏</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((signal) => (
                <tr key={signal.id}>
                  <td>{new Date(signal.date).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                  })}</td>
                  <td>
                    <div className="symbol-cell">
                      <span className="symbol-text">{signal.symbol.split('-')[1]}</span>
                      <span className="symbol-type-tag">
                        {signal.symbol.split('-')[0].toUpperCase() === 'STOCK' ? '股票' : 
                         signal.symbol.split('-')[0].toUpperCase() === 'FUTURES' ? '期货' :
                         signal.symbol.split('-')[0].toUpperCase() === 'OPTIONS' ? '期权' :
                         signal.symbol.split('-')[0].toUpperCase() === 'ETF' ? 'ETF' : 
                         signal.symbol.split('-')[0]}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`signal-tag ${signal.type}`}>
                      {signal.type === 'BUY_OPEN' ? '买入开仓' : 
                       signal.type === 'SELL_OPEN' ? '卖出开仓' :
                       signal.type === 'BUY_CLOSE' ? '买入平仓' :
                       signal.type === 'SELL_CLOSE' ? '卖出平仓' : signal.type}
                    </span>
                  </td>
                  <td>{signal.price.toFixed(2)}</td>
                  <td>{signal.quantity}</td>
                  <td>
                    <span className={`status-tag ${signal.status}`}>
                      {signal.status === 'open' ? '持仓中' : 
                       signal.status === 'closed' ? '已平仓' :
                       signal.status === 'partial_closed' ? '部分平仓' : signal.status}
                    </span>
                  </td>
                  <td>{signal.reason}</td>
                  <td>{signal.close_date ? new Date(signal.close_date).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                  }) : '-'}</td>
                  <td>{signal.close_price ? signal.close_price.toFixed(2) : '-'}</td>
                  <td className={signal.profit >= 0 ? 'profit' : 'loss'}>
                    {signal.profit.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <button 
              onClick={() => handlePageChange(pagination.current - 1, pagination.pageSize)}
              disabled={pagination.current === 1}
            >
              上一页
            </button>
            <span>
              第 {pagination.current} 页 / 共 {Math.ceil(pagination.total / pagination.pageSize)} 页
            </span>
            <button 
              onClick={() => handlePageChange(pagination.current + 1, pagination.pageSize)}
              disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
            >
              下一页
            </button>
            <select 
              value={pagination.pageSize}
              onChange={(e) => handlePageChange(1, Number(e.target.value))}
            >
              <option value="10">10条/页</option>
              <option value="20">20条/页</option>
              <option value="50">50条/页</option>
              <option value="100">100条/页</option>
            </select>
          </div>
        </div>

        {showNotificationModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2>推送配置</h2>
              <div className="notification-options">
                <div className="notification-option">
                  <label>
                    <input
                      type="checkbox"
                      checked={notificationSettings.sms}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        sms: e.target.checked
                      })}
                    />
                    短信推送
                  </label>
                  {notificationSettings.sms && (
                    <input
                      type="tel"
                      placeholder="请输入手机号"
                      value={notificationSettings.phone}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        phone: e.target.value
                      })}
                      className="notification-input"
                    />
                  )}
                </div>
                <div className="notification-option">
                  <label>
                    <input
                      type="checkbox"
                      checked={notificationSettings.wecom}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        wecom: e.target.checked
                      })}
                    />
                    企业微信推送
                  </label>
                  {notificationSettings.wecom && (
                    <input
                      type="text"
                      placeholder="请输入企业微信Webhook密钥"
                      value={notificationSettings.wecomKey}
                      onChange={(e) => setNotificationSettings({
                        ...notificationSettings,
                        wecomKey: e.target.value
                      })}
                      className="notification-input"
                    />
                  )}
                </div>
              </div>
              <div className="modal-actions">
                <button 
                  onClick={() => setShowNotificationModal(false)}
                  className="cancel-button"
                >
                  取消
                </button>
                <button 
                  onClick={handleSaveNotificationSettings}
                  className="save-button"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        )}

        {isModalVisible && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2>添加信号</h2>
              <form onSubmit={handleAddSignal}>
                <div className="form-group">
                  <label>时间</label>
                  <input
                    type="datetime-local"
                    name="date"
                    value={formData.date}
                    onChange={handleInputChange}
                    step="1"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>品种类型</label>
                  <select
                    name="symbol_type"
                    value={formData.symbol_type}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="stock">股票</option>
                    <option value="futures">期货</option>
                    <option value="options">期权</option>
                    <option value="etf">ETF</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>品种代码</label>
                  <input
                    type="text"
                    name="symbol"
                    value={formData.symbol}
                    onChange={handleInputChange}
                    placeholder="请输入品种代码"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>交易类型</label>
                  <select
                    name="type"
                    value={formData.type}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="BUY_OPEN">买入开仓</option>
                    <option value="SELL_OPEN">卖出开仓</option>
                    <option value="BUY_CLOSE">买入平仓</option>
                    <option value="SELL_CLOSE">卖出平仓</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>价格</label>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleInputChange}
                    min="0"
                    step="0.01"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>数量</label>
                  <input
                    type="number"
                    name="quantity"
                    value={formData.quantity}
                    onChange={handleInputChange}
                    min="1"
                    step="1"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>开仓原因</label>
                  <textarea
                    name="reason"
                    value={formData.reason}
                    onChange={handleInputChange}
                    rows={4}
                    placeholder="请输入开仓原因"
                    required
                  />
                </div>

                <div className="modal-actions">
                  <button type="submit" className="save-button">
                    提交
                  </button>
                  <button 
                    type="button" 
                    onClick={() => setIsModalVisible(false)}
                    className="cancel-button"
                  >
                    取消
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

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

export default Signals; 