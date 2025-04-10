import React, { useEffect, useState, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { getSpreadData, SpreadData } from '../../api/arbitrage';

interface SpreadAnalysis {
  upperLimit: number;
  lowerLimit: number;
  mean: number;
  std: number;
  zScore: number; // 当前价差的Z分数
}

const ArbitrageStrategy: React.FC = () => {
  const [spreadData2509_2601, setSpreadData2509_2601] = useState<SpreadData[]>([]);
  const [spreadData2505_2509, setSpreadData2505_2509] = useState<SpreadData[]>([]);
  const [spreadData2507_2511, setSpreadData2507_2511] = useState<SpreadData[]>([]);
  const [loading, setLoading] = useState(true);
  const [stdMultiplier, setStdMultiplier] = useState(2);
  const [windowSize, setWindowSize] = useState(60); // 滚动窗口大小，默认60天

  // 计算价差统计分析
  const calculateSpreadAnalysis = (data: SpreadData[]): SpreadAnalysis => {
    if (data.length === 0) return { upperLimit: 0, lowerLimit: 0, mean: 0, std: 0, zScore: 0 };
    
    // 只取最近windowSize天的数据
    const recentData = data.slice(-windowSize);
    const spreads = recentData.map(item => item.spread);
    
    // 计算均值和标准差
    const mean = spreads.reduce((a, b) => a + b, 0) / spreads.length;
    const variance = spreads.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / spreads.length;
    const std = Math.sqrt(variance);
    
    // 计算当前价差的Z分数
    const currentSpread = spreads[spreads.length - 1];
    const zScore = (currentSpread - mean) / std;
    
    // 计算动态上下限
    const upperLimit = mean + stdMultiplier * std;
    const lowerLimit = mean - stdMultiplier * std;
    
    return {
      mean,
      std,
      upperLimit,
      lowerLimit,
      zScore
    };
  };

  // 使用useMemo缓存分析结果
  const analysis2509_2601 = useMemo(() => calculateSpreadAnalysis(spreadData2509_2601), 
    [spreadData2509_2601, stdMultiplier, windowSize]);
  const analysis2505_2509 = useMemo(() => calculateSpreadAnalysis(spreadData2505_2509), 
    [spreadData2505_2509, stdMultiplier, windowSize]);
  const analysis2507_2511 = useMemo(() => calculateSpreadAnalysis(spreadData2507_2511), 
    [spreadData2507_2511, stdMultiplier, windowSize]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取M2509-M2601价差数据
        const data2509_2601 = await getSpreadData(undefined, undefined, 'M2509.DCE', 'M2601.DCE');
        const sortedData2509_2601 = [...data2509_2601].sort((a, b) => a.date.localeCompare(b.date));
        setSpreadData2509_2601(sortedData2509_2601);
        
        // 获取M2505-M2509价差数据
        const data2505_2509 = await getSpreadData(undefined, undefined, 'M2505.DCE', 'M2509.DCE');
        const sortedData2505_2509 = [...data2505_2509].sort((a, b) => a.date.localeCompare(b.date));
        setSpreadData2505_2509(sortedData2505_2509);

        // 获取M2507-M2511价差数据
        const data2507_2511 = await getSpreadData(undefined, undefined, 'M2507.DCE', 'M2511.DCE');
        const sortedData2507_2511 = [...data2507_2511].sort((a, b) => a.date.localeCompare(b.date));
        setSpreadData2507_2511(sortedData2507_2511);
      } catch (error) {
        console.error('获取价差数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: '#1890ff'
        }
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <ReactECharts 
          option={createChartOption(data, title, analysis)} 
          style={{ height: '400px' }} 
        />
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900">策略说明</h3>
        <p className="text-gray-600">
          近远月套利策略是基于同一品种不同到期月份合约之间的价差进行交易。当两个合约之间的价差出现不合理变动时，通过同时买入低估合约和卖出高估合约来获取套利收益。
        </p>
        
        <h4 className="text-md font-medium text-gray-900 mt-4">交易逻辑</h4>
        <ul className="list-disc pl-5 text-gray-600">
          <li>价差计算：近月合约价格 - 远月合约价格</li>
          <li>正套：当价差Z分数大于{stdMultiplier}时，做空远月合约，做多近月合约</li>
          <li>反套：当价差Z分数小于-{stdMultiplier}时，做多远月合约，做空近月合约</li>
        </ul>

        <h4 className="text-md font-medium text-gray-900 mt-4">止盈止损</h4>
        <ul className="list-disc pl-5 text-gray-600">
          <li>正套止盈：价差Z分数回归到0</li>
          <li>正套止损：价差Z分数继续扩大到{stdMultiplier + 1}</li>
          <li>反套止盈：价差Z分数回归到0</li>
          <li>反套止损：价差Z分数继续扩大到-{stdMultiplier + 1}</li>
        </ul>

        <div className="mt-4 space-y-4">
          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-600">标准差倍数：</label>
            <input
              type="range"
              min="1"
              max="3"
              step="0.1"
              value={stdMultiplier}
              onChange={(e) => setStdMultiplier(parseFloat(e.target.value))}
              className="w-48"
            />
            <span className="text-sm text-gray-600">{stdMultiplier.toFixed(1)}</span>
          </div>
          
          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-600">滚动窗口：</label>
            <input
              type="range"
              min="20"
              max="120"
              step="10"
              value={windowSize}
              onChange={(e) => setWindowSize(parseInt(e.target.value))}
              className="w-48"
            />
            <span className="text-sm text-gray-600">{windowSize}天</span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* M2509-M2601单独一行 */}
        <ChartCard 
          title="M2509-M2601价差走势" 
          data={spreadData2509_2601}
          analysis={analysis2509_2601}
        />

        {/* M2505-M2509和M2507-M2511并列一行 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard 
            title="M2505-M2509价差走势" 
            data={spreadData2505_2509}
            analysis={analysis2505_2509}
          />
          <ChartCard 
            title="M2507-M2511价差走势" 
            data={spreadData2507_2511}
            analysis={analysis2507_2511}
          />
        </div>
      </div>
    </div>
  );
};

export default ArbitrageStrategy; 