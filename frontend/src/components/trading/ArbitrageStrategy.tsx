import React, { useEffect, useState, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { getSpreadData, SpreadData } from '../../api/arbitrage';
import { Highlight, themes, type Token } from 'prism-react-renderer';

interface SpreadAnalysis {
  upperLimit: number;
  lowerLimit: number;
  mean: number;
  std: number;
  zScore: number; // 当前价差的Z分数
}

type Commodity = 'M' | 'C';

const ArbitrageStrategy: React.FC = () => {
  const [spreadData2509_2601, setSpreadData2509_2601] = useState<SpreadData[]>([]);
  const [spreadData2505_2509, setSpreadData2505_2509] = useState<SpreadData[]>([]);
  const [spreadData2507_2511, setSpreadData2507_2511] = useState<SpreadData[]>([]);
  const [loading, setLoading] = useState(true);
  const [stdMultiplier, setStdMultiplier] = useState(1.3);
  const [windowSize, setWindowSize] = useState(60); // 滚动窗口大小，默认60天
  const [commodity, setCommodity] = useState<Commodity>('M');
  const [showCode, setShowCode] = useState(false);

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

  const fetchSpreadData = async (commodity: Commodity) => {
    setLoading(true);
    try {
      // 获取2509-2601价差数据
      const data2509_2601 = await getSpreadData(
        undefined, 
        undefined, 
        `${commodity}2509.DCE`, 
        `${commodity}2601.DCE`
      );
      const sortedData2509_2601 = [...data2509_2601].sort((a, b) => a.date.localeCompare(b.date));
      setSpreadData2509_2601(sortedData2509_2601);
      
      // 获取2505-2509价差数据
      const data2505_2509 = await getSpreadData(
        undefined, 
        undefined, 
        `${commodity}2505.DCE`, 
        `${commodity}2509.DCE`
      );
      const sortedData2505_2509 = [...data2505_2509].sort((a, b) => a.date.localeCompare(b.date));
      setSpreadData2505_2509(sortedData2505_2509);

      // 获取2507-2511价差数据
      const data2507_2511 = await getSpreadData(
        undefined, 
        undefined, 
        `${commodity}2507.DCE`, 
        `${commodity}2511.DCE`
      );
      const sortedData2507_2511 = [...data2507_2511].sort((a, b) => a.date.localeCompare(b.date));
      setSpreadData2507_2511(sortedData2507_2511);
    } catch (error) {
      console.error('获取价差数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpreadData(commodity);
  }, [commodity]);

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

  const pythonCode = `'''backtest
start: 2025-01-01 09:00:00
end: 2025-04-09 15:00:00
period: 1m
basePeriod: 1m
exchanges: [{"eid":"Futures_CTP","currency":"FUTURES"}]
mode: 1
'''
from datetime import datetime, time

p = ext.NewPositionManager()

def is_trading_time(current_time):
    # 交易时段设置
    trading_sessions = [
        (time(9, 0), time(10, 15)),
        (time(10, 30), time(11, 30)),
        (time(13, 30), time(15, 0)),
        (time(21, 0), time(23, 0)),
    ]
    for session_start, session_end in trading_sessions:
        if session_start < current_time < session_end:
            return True
    return False

def onTick():
    global maxDiff, minDiff
    # 获取合约A行情数据
    infoA = exchange.SetContractType(symbolA)
    tickA = exchange.GetTicker()
    recordsA = exchange.GetRecords()
    
    # 获取合约B行情数据
    infoB = exchange.SetContractType(symbolB)
    tickB = exchange.GetTicker()
    recordsB = exchange.GetRecords()
    
    if not tickA or not tickB or not recordsA or not recordsB:
        return
    
    timestamp_msA = int(tickA['Time'])
    record_datetimeA = datetime.fromtimestamp(timestamp_msA / 1000)
    current_timeA = record_datetimeA.time()
    timestamp_msB = int(tickB['Time'])
    record_datetimeB = datetime.fromtimestamp(timestamp_msB / 1000)
    current_timeB = record_datetimeB.time()
    # 判断是否在交易时段内
    if not is_trading_time(current_timeA) or not is_trading_time(current_timeB):
        return
    
    # 分析持仓
    pos = exchange.GetPosition()
    if pos is None:
        return 
    longPosOfSymbolA = p.GetPosition(symbolA, PD_LONG)
    shortPosOfSymbolA = p.GetPosition(symbolA, PD_SHORT)
    longPosOfSymbolB = p.GetPosition(symbolB, PD_LONG)
    shortPosOfSymbolB = p.GetPosition(symbolB, PD_SHORT)
    
    # 计算价差
    diff = tickA["Last"] - tickB["Last"]
    
    if not longPosOfSymbolA and not shortPosOfSymbolA and not longPosOfSymbolB and not shortPosOfSymbolB:
        if diff > maxDiff:
            # 空A合约，多B合约
            Log("空A合约:", symbolA, "，多B合约:", symbolB, ", diff:", diff, ", maxDiff:", maxDiff, "#FF0000")
            p.OpenShort(symbolA, 2)
            p.OpenLong(symbolB, 2)
        elif diff < minDiff:
            # 多A合约，空B合约
            Log("多A合约:", symbolA, "，空B合约:", symbolB, ", diff:", diff, ", minDiff:", minDiff, "#FF0000")
            p.OpenLong(symbolA, 2)
            p.OpenShort(symbolB, 2)
    
    if longPosOfSymbolA and shortPosOfSymbolB and not shortPosOfSymbolA and not longPosOfSymbolB:
        # 持有A多头、B空头
        if diff > (longPosOfSymbolA["Price"] - shortPosOfSymbolB["Price"]) + stopProfit:
            # 止盈
            Log("持有A多头、B空头，止盈。", "diff:", diff, "持有差价：", (longPosOfSymbolA["Price"] - shortPosOfSymbolB["Price"]))
            p.Cover(symbolA)
            p.Cover(symbolB)
        elif diff < (longPosOfSymbolA["Price"] - shortPosOfSymbolB["Price"]) - stopLoss:
            # 止损
            Log("持有A多头、B空头，止损。", "diff:", diff, "持有差价：", (longPosOfSymbolA["Price"] - shortPosOfSymbolB["Price"]))
            p.Cover(symbolA)
            p.Cover(symbolB)
    elif shortPosOfSymbolA and longPosOfSymbolB and not longPosOfSymbolA and not shortPosOfSymbolB:
        # 持有A空头、B多头
        if diff < (shortPosOfSymbolA["Price"] - longPosOfSymbolB["Price"]) - stopProfit:
            # 止盈
            Log("持有A空头、B多头，止盈。", "diff:", diff, "持有差价：", (shortPosOfSymbolA["Price"] - longPosOfSymbolB["Price"]))
            p.Cover(symbolA)
            p.Cover(symbolB)
        elif diff > (shortPosOfSymbolA["Price"] - longPosOfSymbolB["Price"]) + stopLoss:
            # 止损
            Log("持有A空头、B多头，止损。", "diff:", diff, "持有差价：", (shortPosOfSymbolA["Price"] - longPosOfSymbolB["Price"]))
            p.Cover(symbolA)
            p.Cover(symbolB)
    
    # 画图
    ext.PlotLine("差价", diff)

def main():
    while True:
        if exchange.IO("status"):
            onTick()
            LogStatus(_D(), "已连接")
        else:
            LogStatus(_D(), "未连接")
        Sleep(500)`;

  return (
    <div className="space-y-6">
      <div className="prose max-w-none">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">策略说明</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setCommodity(prev => prev === 'M' ? 'C' : 'M')}
              className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors"
            >
              对比{commodity === 'M' ? '玉米' : '豆粕'}
            </button>
            <button
              onClick={() => setShowCode(true)}
              className="px-3 py-1 text-sm font-medium text-green-600 bg-green-50 rounded-full hover:bg-green-100 transition-colors"
            >
              查看代码
            </button>
          </div>
        </div>
        <p className="text-gray-600">
          {commodity === 'M' ? '豆粕' : '玉米'}近远月套利策略是基于同一品种不同到期月份合约之间的价差进行交易。当两个合约之间的价差出现不合理变动时，通过同时买入低估合约和卖出高估合约来获取套利收益。
        </p>
        
        <h4 className="text-md font-medium text-gray-900 mt-4">交易逻辑</h4>
        
        <ul className="list-disc pl-5 text-gray-600">
          <li>价差计算：近月合约价格 - 远月合约价格</li>
          <li>正套（做空价差）：当价差Z分数 大于{stdMultiplier}或价差高估，卖出近月合约 + 买入远月合约。</li>
          <li>反套（做多价差）：当价差Z分数 小于-{stdMultiplier}或价差低估，买入近月合约 + 卖出远月合约。</li>
        </ul>

        <h4 className="text-md font-medium text-gray-900 mt-4">止盈止损</h4>
        <ul className="list-disc pl-5 text-gray-600">
          <li>正套止盈：价差Z分数回归至0或固定点位。</li>
          <li>正套止损：价差Z分数 大于{stdMultiplier + 1}或固定止损。</li>
          <li>反套止盈：价差Z分数回归至0或固定点位。</li>
          <li>反套止损：价差Z分数 小于-{stdMultiplier + 1}或固定止损。</li>
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
          title={`${commodity}2509-${commodity}2601价差走势`} 
          data={spreadData2509_2601}
          analysis={analysis2509_2601}
        />

        {/* M2505-M2509和M2507-M2511并列一行 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard 
            title={`${commodity}2505-${commodity}2509价差走势`} 
            data={spreadData2505_2509}
            analysis={analysis2505_2509}
          />
          <ChartCard 
            title={`${commodity}2507-${commodity}2511价差走势`} 
            data={spreadData2507_2511}
            analysis={analysis2507_2511}
          />
        </div>
      </div>

      {/* Modal */}
      {showCode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-3/4 max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-lg font-medium">策略代码</h3>
                <p className="text-sm text-gray-500 mt-1">本策略适用于YouQuant量化平台</p>
              </div>
              <button
                onClick={() => setShowCode(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="bg-[#011627] rounded-lg overflow-hidden">
              <Highlight 
                theme={themes.nightOwl} 
                code={pythonCode} 
                language="python"
              >
                {({
                  className,
                  style,
                  tokens,
                  getLineProps,
                  getTokenProps
                }: {
                  className: string;
                  style: React.CSSProperties;
                  tokens: Token[][];
                  getLineProps: (props: { line: Token[]; key: number }) => { className: string };
                  getTokenProps: (props: { token: Token; key: number }) => { className: string };
                }) => (
                  <pre className={`${className} p-4 overflow-auto`} style={style}>
                    {tokens.map((line, lineIndex) => (
                      <div key={lineIndex} {...getLineProps({ line, key: lineIndex })}>
                        <span className="text-gray-500 select-none mr-4 text-right inline-block w-8">
                          {lineIndex + 1}
                        </span>
                        {line.map((token, tokenIndex) => (
                          <span key={tokenIndex} {...getTokenProps({ token, key: tokenIndex })} />
                        ))}
                      </div>
                    ))}
                  </pre>
                )}
              </Highlight>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArbitrageStrategy; 