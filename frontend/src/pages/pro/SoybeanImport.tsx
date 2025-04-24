import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { fetchSoybeanImportData } from '../../api/soybean';
import Layout from '../../components/layout/Layout';
import type { EChartsOption } from 'echarts';

// 定义港口详情类型
interface PortDetailType {
  location: string;
  capacity: string;
  features: string[];
  advantages: string[];
  risks: string[];
}

// 定义海关详情类型
interface CustomsDetailType {
  jurisdiction: string;
  features: string[];
  advantages: string[];
  statistics: {
    averageProcessingTime: string;
    inspectionPassRate: string;
    annualProcessingVolume: string;
  };
}

// 定义港口详情数据
const PORT_DETAILS: Record<string, PortDetailType> = {
  '大连港': {
    location: '辽宁省大连市',
    capacity: '年吞吐量2000万吨',
    features: ['深水良港', '东北最大粮食输入口岸', '现代化装卸设施'],
    advantages: [
      '地理位置优越，辐射东北三省',
      '铁路集疏运系统完善',
      '仓储能力强',
      '加工产业链配套完整'
    ],
    risks: [
      '季节性影响较大',
      '腹地经济发展不平衡',
      '竞争港口增多'
    ]
  },
  '青岛港': {
    location: '山东省青岛市',
    capacity: '年吞吐量1800万吨',
    features: ['天然深水港', '现代化粮食专用码头', '智能化操作系统'],
    advantages: [
      '地处环渤海经济圈',
      '多式联运体系成熟',
      '智能化程度高',
      '服务华北、华东市场'
    ],
    risks: [
      '台风等自然灾害影响',
      '腹地竞争激烈',
      '环保要求提高'
    ]
  },
  '天津港': {
    location: '天津市',
    capacity: '年吞吐量1500万吨',
    features: ['人工深水港', '京津冀重要海上门户', '现代物流体系'],
    advantages: [
      '服务京津冀协同发展',
      '铁路运输便捷',
      '保税仓储优势',
      '加工贸易发达'
    ],
    risks: [
      '环保压力大',
      '产能过剩风险',
      '区域竞争加剧'
    ]
  }
};

// 定义海关详情数据
const CUSTOMS_DETAILS: Record<string, CustomsDetailType> = {
  '大连海关': {
    jurisdiction: '辽宁省',
    features: ['东北地区最大海关', '智能通关系统', '专业粮食检验团队'],
    advantages: [
      '通关效率高',
      '检验设备先进',
      '政策支持力度大',
      '服务体系完善'
    ],
    statistics: {
      averageProcessingTime: '24小时',
      inspectionPassRate: '98.5%',
      annualProcessingVolume: '1200万吨'
    }
  },
  '青岛海关': {
    jurisdiction: '山东省',
    features: ['智能化通关改革先行区', '粮食进口重点监管', '质量追溯体系'],
    advantages: [
      '通关自动化程度高',
      '风险防控体系完善',
      '检验标准国际化',
      '服务响应快速'
    ],
    statistics: {
      averageProcessingTime: '20小时',
      inspectionPassRate: '99%',
      annualProcessingVolume: '1000万吨'
    }
  }
};

interface ComparisonData {
  month: string;
  value: number;
  type: string;
}

interface PortDistributionData {
  port: string;
  value: number;
  type: string;
}

interface PortData {
  port: string;
  current: number;
  next_month: number;
  next_two_month: number;
}

interface CustomsData {
  customs: string;
  current: number;
  next_period: number;
  next_month: number;
  next_two_month: number;
}

interface SoybeanImportData {
  date: string;
  current_shipment: number;
  forecast_shipment: number;
  forecast_next_shipment: number;
  current_arrival: number;
  next_arrival: number;
  current_month_arrival: number;
  next_month_arrival: number;
  current_shipment_yoy: number;
  current_shipment_mom: number;
  forecast_shipment_yoy: number;
  forecast_shipment_mom: number;
  current_arrival_yoy: number;
  current_arrival_mom: number;
  next_arrival_yoy: number;
  shipment_forecast_diff: number;
  arrival_forecast_diff: number;
  monthly_comparison: ComparisonData[];
  port_distribution: PortDistributionData[];
  port_details: PortData[];
  customs_details: CustomsData[];
  created_at: string;
  updated_at: string;
}

const SoybeanImport: React.FC = () => {
  const [data, setData] = useState<SoybeanImportData | null>(null);
  const [activeTab, setActiveTab] = useState<'port' | 'customs'>('port');
  const [selectedPort, setSelectedPort] = useState<string | null>(null);
  const [selectedCustoms, setSelectedCustoms] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetchSoybeanImportData();
        setData(response as SoybeanImportData);
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getComparisonChartOption = (): EChartsOption => {
    if (!data?.monthly_comparison) return {};
    
    const months = Array.from(new Set(data.monthly_comparison.map(item => item.month)));
    const actualData = data.monthly_comparison.filter(item => item.type === 'actual');
    const forecastData = data.monthly_comparison.filter(item => item.type === 'forecast');
    
    return {
      tooltip: {
        trigger: 'axis',
        formatter: function(params: any) {
          const month = params[0].axisValue;
          let result = `${month}<br/>`;
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${param.value.toLocaleString()} 万吨<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['实际装船', '预计装船']
      },
      xAxis: {
        type: 'category',
        data: months,
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getFullYear()}年${date.getMonth() + 1}月`;
          }
        }
      },
      yAxis: {
        type: 'value',
        name: '万吨',
        axisLabel: {
          formatter: (value: number) => value.toLocaleString()
        }
      },
      series: [
        {
          name: '实际装船',
          type: 'bar',
          data: actualData.map(item => item.value),
          itemStyle: {
            color: '#3B82F6'
          }
        },
        {
          name: '预计装船',
          type: 'bar',
          data: forecastData.map(item => item.value),
          itemStyle: {
            color: '#10B981'
          }
        }
      ]
    };
  };

  const getPortDistributionOption = (): EChartsOption => {
    if (!data?.port_distribution) return {};
    
    // 按value值降序排序
    const sortedData = [...data.port_distribution].sort((a, b) => b.value - a.value);
    
    return {
      tooltip: {
        trigger: 'axis',
        formatter: function(params: any) {
          return `${params[0].name}<br/>${params[0].value.toLocaleString()} 吨`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '吨',
        axisLabel: {
          formatter: (value: number) => value.toLocaleString()
        }
      },
      yAxis: {
        type: 'category',
        data: sortedData.map(item => item.port),
        axisLabel: {
          interval: 0,
          rotate: 0
        }
      },
      series: [
        {
          name: '港口分布',
          type: 'bar',
          data: sortedData.map(item => item.value),
          itemStyle: {
            color: function(params: any) {
              const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
              return colors[params.dataIndex % colors.length];
            }
          },
          label: {
            show: true,
            position: 'right',
            formatter: (params: any) => params.value.toLocaleString()
          }
        }
      ]
    };
  };

  // 辅助函数：根据数值返回颜色类名
  const getColorClass = (value: number) => {
    return value >= 0 ? 'text-red-600' : 'text-green-600';
  };

  // 辅助函数：格式化百分比
  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">加载中...</div>;
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 relative inline-block">
            大豆进口分析
            <span className="absolute -top-3 -right-12 bg-gradient-to-r from-yellow-400 to-yellow-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-md transform rotate-12">
              PRO
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-500">
            实时监控大豆进口数据，分析港口分布和海关通关情况
          </p>
          <p className="mt-2 text-sm text-gray-400">
            最后更新: {data?.date ? new Date(data.date).toLocaleDateString('zh-CN') : '-'}
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 月度对比图表 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">月度到港对比</h2>
            <ReactECharts option={getComparisonChartOption()} style={{ height: '400px' }} />
          </div>

          {/* 港口分布图表 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">港口分布</h2>
            <ReactECharts option={getPortDistributionOption()} style={{ height: '400px' }} />
          </div>
        </div>

        {/* 数据统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">当前装船量</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{data?.current_shipment?.toLocaleString() || 0} 万吨</p>
            <div className="mt-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">同比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.current_shipment_yoy || 0)}`}>
                  {formatPercentage(data?.current_shipment_yoy || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">环比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.current_shipment_mom || 0)}`}>
                  {formatPercentage(data?.current_shipment_mom || 0)}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">预计装船量</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{data?.forecast_shipment?.toLocaleString() || 0} 万吨</p>
            <div className="mt-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">同比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.forecast_shipment_yoy || 0)}`}>
                  {formatPercentage(data?.forecast_shipment_yoy || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">环比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.forecast_shipment_mom || 0)}`}>
                  {formatPercentage(data?.forecast_shipment_mom || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 pt-1 border-t border-gray-100">
                <span className="text-sm text-gray-500">预期差异</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.shipment_forecast_diff || 0)}`}>
                  {(data?.shipment_forecast_diff || 0).toLocaleString()} 万吨
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">当前到港量</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{data?.current_arrival?.toLocaleString() || 0} 万吨</p>
            <div className="mt-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">同比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.current_arrival_yoy || 0)}`}>
                  {formatPercentage(data?.current_arrival_yoy || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">环比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.current_arrival_mom || 0)}`}>
                  {formatPercentage(data?.current_arrival_mom || 0)}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">预计到港量</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">{data?.next_arrival?.toLocaleString() || 0} 万吨</p>
            <div className="mt-2 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">同比</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.next_arrival_yoy || 0)}`}>
                  {formatPercentage(data?.next_arrival_yoy || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 pt-1 border-t border-gray-100">
                <span className="text-sm text-gray-500">预期差异</span>
                <span className={`text-sm font-semibold ${getColorClass(data?.arrival_forecast_diff || 0)}`}>
                  {(data?.arrival_forecast_diff || 0).toLocaleString()} 万吨
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 详细数据表格 */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('port')}
                className={`${
                  activeTab === 'port'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } w-1/4 py-4 px-1 text-center border-b-2 font-medium text-sm`}
              >
                港口详情
              </button>
              <button
                onClick={() => setActiveTab('customs')}
                className={`${
                  activeTab === 'customs'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } w-1/4 py-4 px-1 text-center border-b-2 font-medium text-sm`}
              >
                海关详情
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'port' && (
              <div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          装运港
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          本期装船数量
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          下月装船数量
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          下下月装船数量
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data?.port_details?.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedPort(item.port)}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                            {item.port}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.current.toLocaleString()} 吨
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.next_month.toLocaleString()} 吨
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.next_two_month.toLocaleString()} 吨
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {activeTab === 'customs' && (
              <div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          海关
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          本期到港数量
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          下期到港数量
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          下月到港数量
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          下下月到港数量
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data?.customs_details?.map((item, index) => (
                        <tr key={index} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedCustoms(item.customs)}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                            {item.customs}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.current.toLocaleString()} 吨
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.next_period.toLocaleString()} 吨
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.next_month.toLocaleString()} 吨
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.next_two_month.toLocaleString()} 吨
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SoybeanImport; 