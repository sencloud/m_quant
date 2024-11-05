<template>
  <div ref="chartRef" style="width: 100%; height: 100%"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  trades: {
    type: Array,
    required: true,
    default: () => []
  }
})

const chartRef = ref(null)
let chart = null

const updateChart = () => {
  if (!chart || !props.data || props.data.length === 0) return

  // 准备交易信号标记
  const buyMarkers = []
  const sellMarkers = []
  
  props.trades.forEach(trade => {
    if (trade.entryDate) {
      const entryIndex = props.data.findIndex(item => item.date === trade.entryDate)
      if (entryIndex !== -1) {
        const marker = {
          name: 'Buy',
          coord: [entryIndex, trade.entryPrice],
          value: trade.entryPrice,
          itemStyle: {
            // 买入点使用绿色
            color: '#91cc75'
          },
          symbol: 'arrow',
          symbolSize: 10,
          label: {
            show: true,
            position: 'bottom',
            formatter: `开仓\n¥${trade.entryPrice}`
          }
        }
        buyMarkers.push(marker)
      }
    }
    
    if (trade.exitDate) {
      const exitIndex = props.data.findIndex(item => item.date === trade.exitDate)
      if (exitIndex !== -1) {
        const marker = {
          name: 'Sell',
          coord: [exitIndex, trade.exitPrice],
          value: trade.exitPrice,
          itemStyle: {
            // 卖出点使用红色
            color: '#ee6666'
          },
          symbol: 'arrow',
          symbolSize: 10,
          label: {
            show: true,
            position: 'top',
            formatter: `平仓\n¥${trade.exitPrice}`
          }
        }
        sellMarkers.push(marker)
      }
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: [
        t('backtest.results.chart.price'),
        t('backtest.results.chart.ma5'),
        t('backtest.results.chart.ma10'),
        t('backtest.results.chart.ma20'),
        t('backtest.results.chart.equity')
      ]
    },
    grid: [{
      left: '3%',
      right: '3%',
      height: '60%'  // 上方K线图占60%
    }, {
      left: '3%',
      right: '3%',
      top: '75%',    // 下方成交量图起始位置
      height: '20%'  // 下方成交量图占20%
    }],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],  // 同时控制两个图表
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],  // 同时控制两个图表
        type: 'slider',
        bottom: '0%',
        start: 0,
        end: 100
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: props.data.map(item => item.date),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        gridIndex: 0
      },
      {
        type: 'category',
        gridIndex: 1,
        data: props.data.map(item => item.date),
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: t('backtest.results.chart.price'),
        position: 'left',
        scale: true,
        splitLine: {
          show: true,
          lineStyle: { type: 'dashed' }
        },
        gridIndex: 0
      },
      {
        type: 'value',
        name: t('backtest.results.chart.equity'),
        position: 'right',
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: {
          formatter: (value) => `${value.toFixed(0)}`
        }
      }
    ],
    series: [
      {
        name: t('backtest.results.chart.price'),
        type: 'line',
        data: props.data.map(item => item.close),
        markPoint: {
          data: [...buyMarkers, ...sellMarkers]
        },
        xAxisIndex: 0,
        yAxisIndex: 0
      },
      {
        name: t('backtest.results.chart.ma5'),
        type: 'line',
        data: props.data.map(item => item.ma5),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        xAxisIndex: 0,
        yAxisIndex: 0
      },
      {
        name: t('backtest.results.chart.ma10'),
        type: 'line',
        data: props.data.map(item => item.ma10),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        xAxisIndex: 0,
        yAxisIndex: 0
      },
      {
        name: t('backtest.results.chart.ma20'),
        type: 'line',
        data: props.data.map(item => item.ma20),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        xAxisIndex: 0,
        yAxisIndex: 0
      },
      {
        name: t('backtest.results.chart.equity'),
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: props.data.map(item => item.equity),
        itemStyle: {
          color: '#91cc75'  // 使用绿色表示资金曲线
        },
        barWidth: '60%',
        emphasis: {
          itemStyle: {
            color: '#5fb44d'  // 鼠标悬停时的颜色
          }
        }
      }
    ]
  }

  chart.setOption(option)
}

// 监听数据变化
watch(() => props.data, updateChart, { deep: true })
watch(() => props.trades, updateChart, { deep: true })

// 监听窗口大小变化
const handleResize = () => {
  chart?.resize()
}

window.addEventListener('resize', handleResize)

onMounted(() => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateChart()
})

// 组件卸载时清理
onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>
