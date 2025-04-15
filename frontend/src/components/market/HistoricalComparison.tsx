import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Button, Tag } from 'antd';
import { ContractPrice } from '../../types/market';
import dayjs from 'dayjs';
import { Link } from 'react-router-dom';
import { CrownOutlined } from '@ant-design/icons';

interface HistoricalComparisonProps {
  currentContract: ContractPrice;
  historicalContracts: ContractPrice[];
}

const HistoricalComparison: React.FC<HistoricalComparisonProps> = ({
  currentContract,
  historicalContracts,
}) => {
  const option = useMemo(() => {
    // 获取当前合约的月份
    const currentMonth = currentContract.contract.slice(-2);
    
    // 对当前合约数据进行处理
    const currentPrices = currentContract.historicalPrices
      .sort((a, b) => dayjs(a.date).diff(dayjs(b.date)))
      .map(price => [
        dayjs(price.date).format('MM-DD'),
        price.close
      ]);

    const historicalSeries = historicalContracts
      .filter(contract => {
        // 只选择相同月份的合约
        const contractMonth = contract.contract.slice(-2);
        return contractMonth === currentMonth;
      })
      .map((contract) => {
        const prices = contract.historicalPrices
          .sort((a, b) => dayjs(a.date).diff(dayjs(b.date)))
          .map(price => [
            dayjs(price.date).format('MM-DD'),
            price.close
          ]);

        // 从合约代码中提取年份
        const year = contract.contract.slice(-4, -2);
        
        return {
          name: `20${year}年`,
          type: 'line',
          data: prices,
          lineStyle: {
            opacity: 0.3
          }
        };
      })
      .filter(series => series.data.length > 0);

    // 获取所有日期并排序
    const allDates = Array.from(new Set([
      ...currentPrices.map(p => p[0]),
      ...historicalSeries.flatMap(s => s.data.map(d => d[0]))
    ])).sort((a, b) => {
      // 将MM-DD转换为虚拟的完整日期进行排序
      const [monthA, dayA] = String(a).split('-').map(Number);
      const [monthB, dayB] = String(b).split('-').map(Number);
      
      // 如果月份大于等于9，使用前一年，这样9-12月会排在1-8月前面
      const yearA = monthA >= 9 ? 2000 : 2001;
      const yearB = monthB >= 9 ? 2000 : 2001;
      
      const dateA = new Date(yearA, monthA - 1, dayA);
      const dateB = new Date(yearB, monthB - 1, dayB);
      
      return dateA.getTime() - dateB.getTime();
    });

    return {
      title: {
        text: `主力合约历史走势比对`,
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `${params[0].axisValue}<br/>`;
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${param.value[1].toFixed(2)}<br/>`;
          });
          return result;
        }
      },
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: 0,
          end: 100,
          bottom: 60
        },
        {
          type: 'inside',
          xAxisIndex: [0],
          start: 0,
          end: 100
        }
      ],
      legend: {
        data: [`${currentContract.contract}(当前)`, ...historicalSeries.map(s => s.name)],
        bottom: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '25%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: allDates,
        axisLabel: {
          formatter: (value: string) => value
        }
      },
      yAxis: {
        type: 'value',
        scale: true
      },
      series: [
        {
          name: `${currentContract.contract}(当前)`,
          type: 'line',
          data: currentPrices,
          lineStyle: {
            width: 2
          },
          emphasis: {
            lineStyle: {
              width: 3
            }
          },
          smooth: true,
          showSymbol: false
        },
        ...historicalSeries.map(series => ({
          ...series,
          smooth: true,
          showSymbol: false
        }))
      ]
    };
  }, [currentContract, historicalContracts]);

  return (
    <Card 
      className="mb-8"
      title={
        <div className="flex justify-between items-center">
          <span>历史走势比对</span>
          <Tag 
            className="cursor-pointer px-3 py-1 text-base bg-gradient-to-r from-yellow-400 to-yellow-600 text-white font-bold rounded-full shadow-md transform rotate-12"
            onClick={() => window.location.href = '/pro-analysis'}
          >
            PRO
          </Tag>
        </div>
      }
    >
      <ReactECharts 
        option={option}
        style={{ height: '400px' }}
      />
    </Card>
  );
};

export default HistoricalComparison; 