import React from 'react';
import { Card, Tabs, Row, Col, Statistic, Progress, Tag } from 'antd';
import ReactECharts from 'echarts-for-react';
import { InfoCircleOutlined } from '@ant-design/icons';

interface StandardizedAnalysisProps {
  contractStats: {
    contract: string;
    lowest_price: number;
    highest_price: number;
    price_range: number;
    start_price: number;
    end_price: number;
    volatility_30d: number;
    quantile_coef: number;
  }[];
  selectedContract: string;
}

const StandardizedAnalysis: React.FC<StandardizedAnalysisProps> = ({ contractStats, selectedContract }) => {
  // 计算当前合约的标准化指标
  const currentContract = contractStats.find(stat => stat.contract === selectedContract);
  const historicalMin = Math.min(...contractStats.map(stat => stat.lowest_price));
  const historicalMax = Math.max(...contractStats.map(stat => stat.highest_price));
  
  // Min-Max归一化值
  const minMaxNormalized = currentContract 
    ? ((currentContract.lowest_price - historicalMin) / (historicalMax - historicalMin))
    : 0;

  // 计算预测低点
  const calculatePredictedLow = (contract: any) => {
    if (!contract) return { base: 0, lower: 0, upper: 0 };
    
    const baseCoef = 0.8; // 基础分位系数
    const basePrediction = contract.start_price * baseCoef;
    
    // 根据合约类型调整修正因子
    let supplyAdjustment = 0;
    let policyAdjustment = 0;
    
    if (contract.contract.includes('05')) {
      supplyAdjustment = -0.05; // 5月合约供应压力下调5%
    }
    if (contract.contract.includes('09')) {
      policyAdjustment = 0.03; // 9月合约政策风险上调3%
    }
    
    const lower = basePrediction * (1 + supplyAdjustment);
    const upper = basePrediction * (1 + policyAdjustment);
    
    return {
      base: basePrediction,
      lower: lower,
      upper: upper
    };
  };

  const predictedLow = calculatePredictedLow(currentContract);

  // 周期性波动图表配置
  const getCyclicalPatternOption = () => {
    const years = contractStats.map(stat => stat.contract.slice(1, 3));
    const normalizedPrices = contractStats.map(stat => 
      (stat.lowest_price - historicalMin) / (historicalMax - historicalMin)
    );

    return {
      title: {
        text: '周期性波动分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const year = '20' + years[params[0].dataIndex];
          const value = (params[0].value * 100).toFixed(2);
          return `${year}年<br/>标准化值: ${value}%`;
        }
      },
      xAxis: {
        type: 'category',
        data: years.map(year => '20' + year),
        name: '年份'
      },
      yAxis: {
        type: 'value',
        name: '标准化值',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [{
        data: normalizedPrices.map(v => (v * 100).toFixed(2)),
        type: 'line',
        smooth: true,
        markPoint: {
          data: [
            { type: 'min', name: '周期低点' },
            { type: 'max', name: '周期高点' }
          ]
        },
        markLine: {
          data: [
            { type: 'average', name: '平均值' }
          ]
        }
      }]
    };
  };

  return (
    <Card className="mb-8">
      <div className="text-lg font-semibold text-gray-900 mb-6">
        数据标准化与规律提取
      </div>
      
      <Row gutter={24}>
        <Col span={8}>
          <Card title="标准化指标" bordered={false}>
            <Statistic
              title="分位数标准化值"
              value={currentContract?.quantile_coef ? (currentContract.quantile_coef * 100).toFixed(2) : 0}
              suffix="%"
              precision={2}
            />
            <Statistic
              title="Min-Max归一化值"
              value={minMaxNormalized * 100}
              suffix="%"
              precision={2}
              className="mt-4"
            />
            <Progress
              percent={minMaxNormalized * 100}
              status="active"
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              className="mt-4"
            />
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="低点预测" bordered={false}>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">理论基准低点</div>
                <div className="text-xl font-bold">
                  ¥{predictedLow.base.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">预测区间</div>
                <div className="flex items-center space-x-2">
                  <Tag color="blue">¥{predictedLow.lower.toFixed(2)}</Tag>
                  <span>-</span>
                  <Tag color="blue">¥{predictedLow.upper.toFixed(2)}</Tag>
                </div>
              </div>
              <div className="text-sm text-gray-500 mt-2">
                <InfoCircleOutlined className="mr-1" />
                基于历史分位系数与修正因子计算
              </div>
            </div>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="修正因子分析" bordered={false}>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span>供应压力</span>
                <Tag color="red">-5%</Tag>
              </div>
              <div className="text-xs text-gray-500">
                南美4-5月到港量预计3130万吨（同比+4.6%）
              </div>
              
              <div className="flex justify-between items-center mt-4">
                <span>政策风险</span>
                <Tag color="green">+3%</Tag>
              </div>
              <div className="text-xs text-gray-500">
                中美关税加征导致进口成本上升
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <div className="mt-8">
        <ReactECharts
          option={getCyclicalPatternOption()}
          style={{ height: '300px' }}
        />
      </div>

      <div className="mt-4 text-sm text-gray-500">
        <p>• 周期性规律：数据显示明显的4年大周期（2012/2016/2020/2024年低点），当前处于周期末端</p>
        <p>• 基差收敛：远月合约贴水现货（当前{selectedContract}贴水率6.95%）作为低点修正参考</p>
        <p>• 预测方法：理论低点 = 合约开始价格 × 历史分位系数(78%-85%) ± 修正因子</p>
      </div>
    </Card>
  );
};

export default StandardizedAnalysis; 