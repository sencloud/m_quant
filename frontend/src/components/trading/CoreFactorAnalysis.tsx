import React, { useState } from 'react';

interface AnalysisData {
  inventoryCycle: {
    current: number;
    historical: number[];
    trend: string;
  };
  technicalSignals: {
    macd: string;
    rsi: string;
    kdj: string;
  };
  historicalPrice: {
    current: number;
    average: number;
    deviation: number;
  };
  newsPolicy: {
    impact: string;
    sentiment: string;
    events: string[];
  };
  hogMarket: {
    correlation: number;
    trend: string;
    impact: string;
  };
}

const CoreFactorAnalysis: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);

  const renderInventoryCycle = () => {
    if (!analysisData) return null;
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">当前库存</p>
            <p className="text-lg font-semibold">{analysisData.inventoryCycle.current}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">历史均值</p>
            <p className="text-lg font-semibold">
              {(analysisData.inventoryCycle.historical.reduce((a, b) => a + b, 0) / analysisData.inventoryCycle.historical.length).toFixed(2)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">趋势</p>
            <p className="text-lg font-semibold">{analysisData.inventoryCycle.trend}</p>
          </div>
        </div>
      </div>
    );
  };

  const renderTechnicalSignals = () => {
    if (!analysisData) return null;
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">MACD</p>
            <p className="text-lg font-semibold">{analysisData.technicalSignals.macd}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">RSI</p>
            <p className="text-lg font-semibold">{analysisData.technicalSignals.rsi}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">KDJ</p>
            <p className="text-lg font-semibold">{analysisData.technicalSignals.kdj}</p>
          </div>
        </div>
      </div>
    );
  };

  const renderHistoricalPrice = () => {
    if (!analysisData) return null;
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">当前价格</p>
            <p className="text-lg font-semibold">{analysisData.historicalPrice.current}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">历史均价</p>
            <p className="text-lg font-semibold">{analysisData.historicalPrice.average}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">偏离度</p>
            <p className="text-lg font-semibold">{analysisData.historicalPrice.deviation}%</p>
          </div>
        </div>
      </div>
    );
  };

  const renderNewsPolicy = () => {
    if (!analysisData) return null;
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-500">影响程度</p>
              <p className="text-lg font-semibold">{analysisData.newsPolicy.impact}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">市场情绪</p>
              <p className="text-lg font-semibold">{analysisData.newsPolicy.sentiment}</p>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-2">重要事件</p>
            <ul className="list-disc list-inside space-y-1">
              {analysisData.newsPolicy.events.map((event, index) => (
                <li key={index} className="text-sm">{event}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  };

  const renderHogMarket = () => {
    if (!analysisData) return null;
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-500">相关性</p>
            <p className="text-lg font-semibold">{analysisData.hogMarket.correlation}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">趋势</p>
            <p className="text-lg font-semibold">{analysisData.hogMarket.trend}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">影响</p>
            <p className="text-lg font-semibold">{analysisData.hogMarket.impact}</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* 核心因子分析区域 */}
      <div className="bg-white rounded-lg overflow-hidden mb-6">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">核心因子分析</h2>
              <p className="text-sm text-gray-500 mt-1">多维度分析豆粕市场核心因子</p>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          {isLoading ? (
            <div className="flex justify-center items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="text-center text-red-500 py-4">{error}</div>
          ) : !analysisData ? (
            <div className="text-center text-gray-500 py-4">暂无数据</div>
          ) : (
            <>
              {/* 库存周期验证 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  库存周期验证
                </h3>
                {renderInventoryCycle()}
              </div>
              
              {/* 技术信号 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  技术信号
                </h3>
                {renderTechnicalSignals()}
              </div>
              
              {/* 历史价格锚定 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  历史价格锚定
                </h3>
                {renderHistoricalPrice()}
              </div>
              
              {/* 新闻政策扰动 */}
              <div className="mb-8">
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-.5-1.5L16 5.5A2 2 0 0014.5 5H14a2 2 0 00-2 2v10a2 2 0 002 2h5a2 2 0 002-2z" />
                  </svg>
                  新闻政策扰动
                </h3>
                {renderNewsPolicy()}
              </div>
              
              {/* 生猪市场联动 */}
              <div>
                <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  生猪市场联动
                </h3>
                {renderHogMarket()}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoreFactorAnalysis; 