import React from 'react';
import { TechnicalIndicators as TechnicalIndicatorsType } from '../../types/market';

interface TechnicalIndicatorsProps {
  data: TechnicalIndicatorsType;
}

const TechnicalIndicators: React.FC<TechnicalIndicatorsProps> = ({ data }) => {
  const getTrendColor = (trend: string) => {
    switch (trend.toLowerCase()) {
      case 'up':
        return 'text-red-500';
      case 'down':
        return 'text-green-500';
      default:
        return 'text-gray-500';
    }
  };

  const getTrendText = (trend: string) => {
    switch (trend.toLowerCase()) {
      case 'up':
        return '上涨';
      case 'down':
        return '下跌';
      case 'neutral':
        return '中性';
      default:
        return trend;
    }
  };

  return (
    <div className="bg-white rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">技术分析指标</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 价格目标 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">价格目标</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">支撑位 S1:</span>
              <span className="font-medium">{data.price_targets.support_levels.s1.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">支撑位 S2:</span>
              <span className="font-medium">{data.price_targets.support_levels.s2.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">阻力位 R1:</span>
              <span className="font-medium">{data.price_targets.resistance_levels.r1.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">阻力位 R2:</span>
              <span className="font-medium">{data.price_targets.resistance_levels.r2.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.price_targets.trend)}`}>
                {getTrendText(data.price_targets.trend)}
              </span>
            </div>
          </div>
        </div>

        {/* EMA指标 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">EMA指标</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">EMA12:</span>
              <span className="font-medium">{data.ema.ema12.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">EMA26:</span>
              <span className="font-medium">{data.ema.ema26.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.ema.trend)}`}>
                {getTrendText(data.ema.trend)}
              </span>
            </div>
          </div>
        </div>

        {/* MACD指标 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">MACD指标</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">DIF:</span>
              <span className="font-medium">{data.macd.diff.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">DEA:</span>
              <span className="font-medium">{data.macd.dea.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">BAR:</span>
              <span className="font-medium">{data.macd.bar.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.macd.trend)}`}>
                {getTrendText(data.macd.trend)}
              </span>
            </div>
          </div>
        </div>

        {/* RSI指标 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">RSI指标</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">RSI:</span>
              <span className="font-medium">{data.rsi.value.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.rsi.trend)}`}>
                {getTrendText(data.rsi.trend)}
              </span>
            </div>
          </div>
        </div>

        {/* KDJ指标 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">KDJ指标</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">K:</span>
              <span className="font-medium">{data.kdj.k.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">D:</span>
              <span className="font-medium">{data.kdj.d.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">J:</span>
              <span className="font-medium">{data.kdj.j.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.kdj.trend)}`}>
                {getTrendText(data.kdj.trend)}
              </span>
            </div>
          </div>
        </div>

        {/* 布林带 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">布林带</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">上轨:</span>
              <span className="font-medium">{data.bollinger_bands.upper.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">中轨:</span>
              <span className="font-medium">{data.bollinger_bands.middle.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">下轨:</span>
              <span className="font-medium">{data.bollinger_bands.lower.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.bollinger_bands.trend)}`}>
                {getTrendText(data.bollinger_bands.trend)}
              </span>
            </div>
          </div>
        </div>

        {/* 成交量 */}
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">成交量</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">当前成交量:</span>
              <span className="font-medium">{data.volume.current.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">变化率:</span>
              <span className="font-medium">{data.volume.change_percent.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">趋势:</span>
              <span className={`font-medium ${getTrendColor(data.volume.trend)}`}>
                {getTrendText(data.volume.trend)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TechnicalIndicators; 