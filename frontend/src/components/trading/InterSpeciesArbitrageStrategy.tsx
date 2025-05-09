import React, { useEffect, useState, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { getInterSpeciesSpreadData, SpreadData } from '../../api/arbitrage';

interface SpreadAnalysis {
  upperLimit: number;
  lowerLimit: number;
  mean: number;
  std: number;
  zScore: number;
}

const InterSpeciesArbitrageStrategy: React.FC = () => {
  const [spreadDataM2509_RM2509, setSpreadDataM2509_RM2509] = useState<SpreadData[]>([]);
  const [loading, setLoading] = useState(true);
  const [stdMultiplier, setStdMultiplier] = useState(1.3);
  const [windowSize, setWindowSize] = useState(60);

  // 计算价差统计分析
  const calculateSpreadAnalysis = (data: SpreadData[]): SpreadAnalysis => {
    if (data.length === 0) return { upperLimit: 0, lowerLimit: 0, mean: 0, std: 0, zScore: 0 };
    
    const recentData = data.slice(-windowSize);
    const spreads = recentData.map(item => item.spread);
    
    const mean = spreads.reduce((a, b) => a + b, 0) / spreads.length;
    const variance = spreads.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / spreads.length;
    const std = Math.sqrt(variance);
    
    const currentSpread = spreads[spreads.length - 1];
    const zScore = (currentSpread - mean) / std;
    
    const upperLimit = mean + stdMultiplier * std;
    const lowerLimit = mean - stdMultiplier * std;
    
    return { mean, std, upperLimit, lowerLimit, zScore };
  };

  const analysisM2509_RM2509 = useMemo(() => calculateSpreadAnalysis(spreadDataM2509_RM2509), 
    [spreadDataM2509_RM2509, stdMultiplier, windowSize]);

  const fetchSpreadData = async () => {
    setLoading(true);
    try {
      // 获取2509豆粕-菜粕价差数据
      const dataM2509_RM2509 = await getInterSpeciesSpreadData(
        undefined, 
        undefined, 
        'M2509.DCE', 
        'RM2509.ZCE'
      );
      setSpreadDataM2509_RM2509([...dataM2509_RM2509].sort((a, b) => a.date.localeCompare(b.date)));
    } catch (error) {
      console.error('获取价差数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpreadData();
  }, []);

  const createChartOption = (data: SpreadData[], title: string, analysis: SpreadAnalysis) => ({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const date = params[0].name;
        const spread = params[0].value;
        const zScore = ((spread - analysis.mean) / analysis.std).toFixed(2);
        return `${date}<br/>价差: ${spread.toFixed(2)}<br/>Z分数: ${zScore}<br/>上限: ${analysis.upperLimit.toFixed(2)}<br/>下限: ${analysis.lowerLimit.toFixed(2)}`;
      }
    },
    legend: {
      data: ['价差', '上限', '下限', '均值'],
      top: 0
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date),
      name: '日期',
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '价差',
      nameLocation: 'middle',
      nameGap: 40,
      scale: true
    },
    series: [
      {
        name: '价差',
        type: 'line',
        data: data.map(item => item.spread),
        symbol: 'diamond',
        symbolSize: 8,
        lineStyle: { width: 2 },
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '上限',
        type: 'line',
        data: new Array(data.length).fill(analysis.upperLimit),
        lineStyle: {
          type: 'dashed',
          width: 2,
          color: '#ff4d4f'
        },
        symbol: 'none'
      },
      {
        name: '下限',
        type: 'line',
        data: new Array(data.length).fill(analysis.lowerLimit),
        lineStyle: {
          type: 'dashed',
          width: 2,
          color: '#52c41a'
        },
        symbol: 'none'
      },
      {
        name: '均值',
        type: 'line',
        data: new Array(data.length).fill(analysis.mean),
        lineStyle: {
          type: 'dashed',
          width: 1,
          color: '#d9d9d9'
        },
        symbol: 'none'
      }
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '5%',
      top: '10%',
      containLabel: true
    }
  });

  const ChartCard = ({ title, data, analysis }: { title: string; data: SpreadData[]; analysis: SpreadAnalysis }) => (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <div className="text-sm text-gray-500">
          均值: {analysis.mean.toFixed(2)} | 标准差: {analysis.std.toFixed(2)} | Z分数: {analysis.zScore.toFixed(2)}
        </div>
      </div>
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : (
        <ReactECharts option={createChartOption(data, title, analysis)} style={{ height: '400px' }} />
      )}
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="prose max-w-none">
        <h2>豆粕-菜粕跨品种套利策略说明</h2>
        <p>
          豆粕-菜粕跨品种套利是利用两个品种之间的价差进行交易的策略。当价差显著偏离历史均值时，可以考虑进行套利操作：
        </p>
        <ul>
          <li>当价差高于上限时，可以考虑做空豆粕同时做多菜粕</li>
          <li>当价差低于下限时，可以考虑做多豆粕同时做空菜粕</li>
        </ul>
        <p>
          策略参数说明：
        </p>
        <ul>
          <li>标准差倍数：{stdMultiplier}（用于计算上下限）</li>
          <li>计算窗口：{windowSize}天</li>
        </ul>
      </div>

      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <label className="text-sm text-gray-600">
            标准差倍数：
            <input
              type="number"
              value={stdMultiplier}
              onChange={(e) => setStdMultiplier(Number(e.target.value))}
              className="ml-2 w-20 px-2 py-1 border rounded"
              step="0.1"
              min="0.1"
            />
          </label>
          <label className="text-sm text-gray-600">
            计算窗口（天）：
            <input
              type="number"
              value={windowSize}
              onChange={(e) => setWindowSize(Number(e.target.value))}
              className="ml-2 w-20 px-2 py-1 border rounded"
              step="1"
              min="1"
            />
          </label>
          <button
            onClick={fetchSpreadData}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            刷新数据
          </button>
        </div>

        <ChartCard
          title="2509豆粕-菜粕价差"
          data={spreadDataM2509_RM2509}
          analysis={analysisM2509_RM2509}
        />
      </div>
    </div>
  );
};

export default InterSpeciesArbitrageStrategy; 