<template>
  <div class="space-y-4">
    <div class="flex space-x-2">
      <el-checkbox-group v-model="selectedIndicators" size="small">
        <el-checkbox value="EMA">{{ t('ai.chart.ema') }}</el-checkbox>
        <el-checkbox value="VOL">{{ t('ai.chart.volume') }}</el-checkbox>
      </el-checkbox-group>
    </div>
    <div ref="chartRef" class="w-full h-full min-h-[400px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'

const props = defineProps({
  actualData: {
    type: Array,
    required: true
  },
  predictedData: {
    type: Object,
    required: true
  },
  dates: {
    type: Array,
    required: true
  },
  technicalIndicators: {
    type: Object,
    required: true
  }
})

const selectedIndicators = ref(['EMA'])

const { t } = useI18n()
const chartRef = ref(null)
let chart = null

const initChart = async () => {
  if (!chartRef.value) return
  
  await nextTick()
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  const resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartRef.value)
  
  updateChart()
}

const updateChart = () => {
  if (!chart || !props.technicalIndicators) return

  console.log('Updating chart with data:', {
    actualData: props.actualData,
    predictedData: props.predictedData,
    technicalIndicators: props.technicalIndicators
  })

  const series = [
    {
      name: t('ai.chart.kline'),
      type: 'candlestick',
      data: props.actualData.map(item => [
        item.open,
        item.close,
        item.low,
        item.high
      ]),
      itemStyle: {
        color: '#ef4444',
        color0: '#10B981',
        borderColor: '#ef4444',
        borderColor0: '#10B981'
      }
    }
  ]

  Object.entries(props.predictedData).forEach(([modelType, prediction], index) => {
    const colors = ['#3B82F6', '#F59E0B', '#EC4899']  // 蓝色、橙色和粉色
    
    // 创建一个与历史数据长度相同的数组，只在最后一个位置放置预测值
    const predictionData = new Array(props.actualData.length).fill(null)
    predictionData[predictionData.length - 1] = prediction

    series.push({
      name: `${t(`ai.models.${modelType}`)}`,
      type: 'line',
      data: predictionData,
      itemStyle: {
        color: colors[index % colors.length]
      },
      lineStyle: {
        width: 2,
        type: 'dashed'
      },
      symbol: 'circle',
      symbolSize: 8,
      connectNulls: true
    })
  })

  if (selectedIndicators.value.includes('MA')) {
    if (props.technicalIndicators.SMA_5?.length > 0) {
      series.push({
        name: 'MA5',
        type: 'line',
        data: props.technicalIndicators.SMA_5.map((value, index) => ({
          value: value || null,
          coord: [index, value]
        })).filter(item => item.value !== null && item.value !== 0),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        itemStyle: { color: '#60A5FA' },
        connectNulls: true
      })
    }
    
    if (props.technicalIndicators.SMA_20?.length > 0) {
      series.push({
        name: 'MA20',
        type: 'line',
        data: props.technicalIndicators.SMA_20.map((value, index) => ({
          value: value || null,
          coord: [index, value]
        })).filter(item => item.value !== null && item.value !== 0),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        itemStyle: { color: '#F59E0B' },
        connectNulls: true
      })
    }
  }

  if (selectedIndicators.value.includes('EMA')) {
    if (props.technicalIndicators.EMA_5?.length > 0) {
      series.push({
        name: 'EMA5',
        type: 'line',
        data: props.technicalIndicators.EMA_5.map((value, index) => ({
          value: value || null,
          coord: [index, value]
        })).filter(item => item.value !== null && item.value !== 0),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        itemStyle: { color: '#34D399' },
        connectNulls: true
      })
    }
    
    if (props.technicalIndicators.EMA_20?.length > 0) {
      series.push({
        name: 'EMA20',
        type: 'line',
        data: props.technicalIndicators.EMA_20.map((value, index) => ({
          value: value || null,
          coord: [index, value]
        })).filter(item => item.value !== null && item.value !== 0),
        smooth: true,
        lineStyle: { opacity: 0.5 },
        itemStyle: { color: '#A78BFA' },
        connectNulls: true
      })
    }
  }

  if (selectedIndicators.value.includes('VOL')) {
    const volumeData = props.actualData.map(item => 
      item.volume === 0 ? null : item.volume
    )
    
    series.push({
      name: t('ai.chart.volume'),
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: volumeData,
      itemStyle: {
        color: (params) => {
          const item = props.actualData[params.dataIndex]
          return item.close > item.open ? '#ef4444' : '#10B981'
        }
      }
    })
  }

  const option = {
    animation: false,
    grid: [{
      left: 60,
      right: 20,
      top: 40,
      height: selectedIndicators.value.includes('VOL') ? '60%' : '80%'
    }, {
      left: 60,
      right: 20,
      height: '20%',
      bottom: 60,
      show: selectedIndicators.value.includes('VOL')
    }],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: function(params) {
        if (!params || !params.length) return ''
        
        const date = params[0].axisValue
        let result = `<div class="font-medium">${date}</div>`
        
        const klineData = params.find(p => p.seriesName === t('ai.chart.kline'))
        if (klineData?.data) {
          const [open, close, low, high] = klineData.data
          result += `<div class="mt-1">
            ${klineData.marker}
            <span class="font-medium">${t('ai.chart.kline')}</span><br/>
            ${t('ai.chart.open')}: ${Number(open).toFixed(2)}<br/>
            ${t('ai.chart.close')}: ${Number(close).toFixed(2)}<br/>
            ${t('ai.chart.high')}: ${Number(high).toFixed(2)}<br/>
            ${t('ai.chart.low')}: ${Number(low).toFixed(2)}
          </div>`
        }
        
        params.forEach(param => {
          if (param.seriesName !== t('ai.chart.kline') && param.value != null && param.value !== 0) {
            result += `<div class="mt-1">
              ${param.marker} 
              <span class="font-medium">${param.seriesName}</span>: 
              ${Number(param.value).toFixed(2)}
            </div>`
          }
        })
        
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 10,
      selected: {
        'MA5': false,
        'MA20': false,
        'EMA5': true,
        'EMA20': true,
        ...Object.fromEntries(
          Object.keys(props.predictedData).map(model => [
            t(`ai.models.${model}`),
            true
          ])
        )
      }
    },
    xAxis: [{
      type: 'category',
      data: props.dates,
      axisLabel: {
        rotate: 30,
        formatter: (value) => value.substring(5)
      }
    }, {
      type: 'category',
      gridIndex: 1,
      data: props.dates,
      axisLabel: { show: false }
    }],
    yAxis: [{
      type: 'value',
      name: t('ai.chart.price'),
      nameLocation: 'middle',
      nameGap: 40,
      scale: true,
      splitLine: { lineStyle: { type: 'dashed' } }
    }, {
      gridIndex: 1,
      type: 'value',
      name: t('ai.chart.volume'),
      nameLocation: 'middle',
      nameGap: 30,
      show: selectedIndicators.value.includes('VOL')
    }],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
        bottom: 10
      }
    ],
    toolbox: {
      feature: {
        dataZoom: { yAxisIndex: 'none' },
        restore: {},
        saveAsImage: {}
      },
      right: 20,
      top: 10
    },
    series: series
  }

  try {
    chart.setOption(option, { notMerge: true })
  } catch (error) {
    console.error('Error setting chart option:', error)
  }
}

onMounted(async () => {
  await nextTick()
  if (chartRef.value && props.actualData?.length && props.dates?.length) {
    initChart()
  }
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch([
  () => props.actualData,
  () => props.predictedData,
  () => props.dates,
  () => props.technicalIndicators,
  selectedIndicators
], async () => {
  if (props.actualData?.length && props.dates?.length) {
    if (!chart) {
      await initChart()
    } else {
      updateChart()
    }
  }
}, { deep: true })

window.addEventListener('resize', () => {
  chart?.resize()
})
</script>

<style scoped>
.min-h-[400px] {
  min-height: 300px;
}
</style> 