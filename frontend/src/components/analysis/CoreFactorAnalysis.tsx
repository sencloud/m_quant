import React from 'react';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import { Spin } from 'antd';

interface InventoryData {
  mom_change: number;
  yoy_change: number;
}

const CoreFactorAnalysis: React.FC = () => {
  // Mock data for demonstration
  const [inventoryData, setInventoryData] = React.useState<InventoryData[]>([{ mom_change: -2.5, yoy_change: -15.3 }]);
  const [inventoryLoading, setInventoryLoading] = React.useState(false);
  const [inventoryError, setInventoryError] = React.useState<string | null>(null);
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="bg-white rounded-lg overflow-hidden mb-6">
      <div 
        className="p-4 border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors duration-150"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">核心驱动因子分析</h2>
            <p className="text-sm text-gray-500 mt-1">多维度分析豆粕市场核心驱动因素</p>
          </div>
          <svg 
            className={`w-5 h-5 text-gray-500 transform transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      <div className={`transition-all duration-300 ease-in-out ${isExpanded ? 'max-h-[5000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="p-6">
          {/* 库存周期验证 */}
          <div className="mb-8">
            <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              库存周期验证
            </h3>
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• 当前库存水平：截至2025年3月，油厂豆粕库存约60万吨，处于近三年同期低位，短期供应紧张支撑现货价格坚挺。</li>
                  <li>• 库存拐点预判：关注4月后巴西大豆到港量（预计850-1100万吨/月），若实际到港延迟或低于预期，库存压力缓解可能延长反弹窗口。</li>
                </ul>
                <div className="mt-4">
                  {inventoryLoading ? (
                    <div className="flex justify-center items-center h-[200px]">
                      <Spin size="large" />
                    </div>
                  ) : inventoryError ? (
                    <div className="text-center text-red-500 py-4">
                      {inventoryError}
                    </div>
                  ) : inventoryData.length > 0 ? (
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-500">最近库存变化</span>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm">
                            环比: <span className={inventoryData[0].mom_change >= 0 ? "text-red-500" : "text-green-500"}>
                              {inventoryData[0].mom_change >= 0 ? "+" : ""}{inventoryData[0].mom_change}%
                            </span>
                          </span>
                          <span className="text-sm">
                            同比: <span className={inventoryData[0].yoy_change >= 0 ? "text-red-500" : "text-green-500"}>
                              {inventoryData[0].yoy_change >= 0 ? "+" : ""}{inventoryData[0].yoy_change}%
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-4">
                      暂无库存数据
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 技术面信号 */}
          <div className="mb-8">
            <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              技术面信号
            </h3>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• 周线趋势：豆粕指数周线处于第四轮中期宽幅震荡周期，自历史低位1511元起的三波结构显示当前可能处于B浪反弹修复阶段，若突破3050元压力位可确认上行趋势。</li>
                <li>• 日线关键位：日线支撑位2850元（3月6日低点）、压力位3000元；小时线关注2900元分水岭，突破后增仓可作为入场信号。</li>
                <li>• 波动率策略：隐含波动率25%时，可卖出跨式期权组合（如卖出2950看涨+2850看跌）对冲短期震荡风险。</li>
              </ul>
            </div>
          </div>

          {/* 历史价格锚定 */}
          <div className="mb-8">
            <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              历史价格锚定
            </h3>
            <div className="bg-green-50 p-4 rounded-lg">
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• 十年低位均值：过去十年豆粕历史低位均值约2600元/吨，当前价格（2850-2900元）接近支撑区间，结合库存低位，下行空间有限。</li>
                <li>• 季节性规律：3-5月南美天气炒作窗口叠加国内补库需求，历史同期上涨概率达65%。</li>
              </ul>
            </div>
          </div>

          {/* 资讯与政策扰动 */}
          <div className="mb-8">
            <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              资讯与政策扰动
            </h3>
            <div className="bg-purple-50 p-4 rounded-lg">
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• 短期利多：国储抛储规模若低于预期（如150万吨）、阿根廷天气偏离预报（±20mm降雨量波动）可能触发100元/吨级别反弹。</li>
                <li>• 风险事件：中美/中加关税政策变化（如豁免美豆加税）或巴西物流受阻可能引发波动，需实时跟踪海关数据。</li>
              </ul>
            </div>
          </div>

          {/* 生猪市场联动 */}
          <div className="mb-8">
            <h3 className="text-base font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              生猪市场联动
            </h3>
            <div className="bg-red-50 p-4 rounded-lg">
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• 需求端验证：生猪存栏量4亿头（低位区间），但饲料企业开启第二轮补库，若生猪价格指数回升至15元/公斤以上，豆粕添加比例可能提升。</li>
                <li>• 替代效应：豆菜价差若突破800元/吨，菜粕替代增强会压制豆粕涨幅，需同步监测菜粕价格及关税政策。</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoreFactorAnalysis; 