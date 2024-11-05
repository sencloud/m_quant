<template>
    <div ref="chartRef" class="w-full h-full"></div>
  </template>
  
  <script>
  import { ref, onMounted, watch, onUnmounted } from 'vue'
  import { useI18n } from 'vue-i18n'
  import * as echarts from 'echarts'
  
  export default {
    props: {
      data: {
        type: Array,
        required: true
      },
      maLines: {
        type: Array,
        default: () => []
      }
    },
  
    setup(props) {
      const { t } = useI18n()
      const chartRef = ref(null)
      let chart = null
  
      const calculateMA = (dayCount) => {
        const result = []
        for (let i = 0; i < props.data.length; i++) {
          if (i < dayCount - 1) {
            result.push(null)
            continue
          }
          let sum = 0
          for (let j = 0; j < dayCount; j++) {
            sum += props.data[i - j].close
          }
          result.push(sum / dayCount)
        }
        return result
      }
  
      const initChart = () => {
        if (!chartRef.value) return
  
        chart = echarts.init(chartRef.value)
        updateChart()
      }
  
      const updateChart = () => {
        if (!chart || !props.data.length) return
  
        const dates = props.data.map(item => item.date)
        const values = props.data.map(item => [item.open, item.close, item.low, item.high])
        const volumes = props.data.map(item => item.volume)
  
        const option = {
          animation: false,
          legend: {
            top: 10,
            left: 'center',
            data: [t('stocks.chart.kline'), ...props.maLines.map(d => `${t('stocks.chart.ma')}${d}`)]
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross'
            },
            borderWidth: 1,
            borderColor: '#ccc',
            padding: 10,
            textStyle: {
              color: '#000'
            }
          },
          axisPointer: {
            link: [{ xAxisIndex: 'all' }]
          },
          grid: [
            {
              left: '10%',
              right: '8%',
              height: '60%'
            },
            {
              left: '10%',
              right: '8%',
              top: '75%',
              height: '20%'
            }
          ],
          xAxis: [
            {
              type: 'category',
              data: dates,
              scale: true,
              boundaryGap: false,
              axisLine: { onZero: false },
              splitLine: { show: false },
              splitNumber: 20
            },
            {
              type: 'category',
              gridIndex: 1,
              data: dates,
              scale: true,
              boundaryGap: false,
              axisLine: { onZero: false },
              axisTick: { show: false },
              splitLine: { show: false },
              axisLabel: { show: false },
              splitNumber: 20
            }
          ],
          yAxis: [
            {
              scale: true,
              splitArea: {
                show: true
              }
            },
            {
              scale: true,
              gridIndex: 1,
              splitNumber: 2,
              axisLabel: { show: false },
              axisLine: { show: false },
              axisTick: { show: false },
              splitLine: { show: false }
            }
          ],
          dataZoom: [
            {
              type: 'inside',
              xAxisIndex: [0, 1],
              start: 0,
              end: 100
            },
            {
              show: true,
              xAxisIndex: [0, 1],
              type: 'slider',
              top: '97%',
              start: 0,
              end: 100
            }
          ],
          series: [
            {
              name: t('stocks.chart.kline'),
              type: 'candlestick',
              data: values,
              itemStyle: {
                color: '#F54640', // Red for rising
                color0: '#2DC08C', // Green for falling
                borderColor: '#F54640', // Red border for rising
                borderColor0: '#2DC08C' // Green border for falling
              }
            },
            ...props.maLines.map(d => ({
              name: `${t('stocks.chart.ma')}${d}`,
              type: 'line',
              data: calculateMA(d),
              smooth: true,
              showSymbol: false,
              lineStyle: {
                opacity: 0.5
              }
            })),
            {
              name: t('stocks.table.volume'),
              type: 'bar',
              xAxisIndex: 1,
              yAxisIndex: 1,
              data: volumes,
              itemStyle: {
                color: (params) => {
                  const item = props.data[params.dataIndex]
                  return item.close > item.open ? '#F54640' : '#2DC08C'
                }
              }
            }
          ]
        }
  
        chart.setOption(option)
      }
  
      const handleResize = () => {
        chart?.resize()
      }
  
      onMounted(() => {
        initChart()
        window.addEventListener('resize', handleResize)
      })
  
      onUnmounted(() => {
        window.removeEventListener('resize', handleResize)
        chart?.dispose()
      })
  
      watch(() => [props.data, props.maLines], updateChart, { deep: true })
  
      return {
        chartRef
      }
    }
  }
  </script>