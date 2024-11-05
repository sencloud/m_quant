<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="space-y-6">
      <!-- 标题和Logo -->
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 flex items-center justify-center bg-blue-100 rounded-lg">
          <el-icon class="text-2xl text-blue-600">
            <Cpu />
          </el-icon>
        </div>
        <h1 class="text-2xl font-semibold">{{ $t('ai.title') }}</h1>
      </div>

      <!-- 主要内容区域 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 左侧配置区域 -->
        <div class="space-y-6">
          <!-- 模型配置卡片 -->
          <div class="bg-white rounded-lg shadow p-6">
            <AIModelConfig
              :loading="isTraining"
              :predicting="isPredicting"
              @train="trainModel"
              @predict="handlePredict"
            />
          </div>

          <!-- 模型指标卡片 -->
          <div class="bg-white rounded-lg shadow p-6">
            <AIMetrics :metrics="modelMetrics" class="mt-4" />
          </div>
        </div>

        <!-- 右侧图表和结果区域 -->
        <div class="md:col-span-2 space-y-6">
          <!-- 预测图表卡片 -->
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4">{{ $t('ai.predictionChart') }}</h2>
            <div class="h-96">
              <AIPredictionChart
                v-if="chartData"
                :actual-data="chartData.actualData"
                :predicted-data="chartData.predictedData"
                :dates="chartData.dates"
                :technical-indicators="chartData.technicalIndicators"
              />
              <div 
                v-else 
                class="h-full flex items-center justify-center text-gray-500"
              >
                {{ $t('ai.noPredictions') }}
              </div>
            </div>
          </div>

          <!-- 回测结果卡片 -->
          <div class="bg-white rounded-lg shadow p-6">
            <AIBacktestResults :results="backtestResults" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { format } from 'date-fns'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import AIModelConfig from '@/components/AIModelConfig.vue'
import AIPredictionChart from '@/components/AIPredictionChart.vue'
import AIMetrics from '@/components/AIMetrics.vue'
import AIBacktestResults from '@/components/AIBacktestResults.vue'
import { Cpu } from '@element-plus/icons-vue'
import { predictStock, trainStockModel, predictStockPrice } from '@/api/backtest'

const { t } = useI18n()

const isTraining = ref(false)
const isPredicting = ref(false)
const modelMetrics = ref({})
const chartData = ref(null)
const backtestResults = ref({})

const trainModel = async (config) => {
  if (isTraining.value) return
  
  isTraining.value = true
  try {
    const data = await trainStockModel({
      symbol: config.symbol,
      models: config.models,
      timePeriod: config.timePeriod,
      predictionDate: config.predictionDate
    })
    
    if (!data || data.status !== 'success') {
      throw new Error(data?.message || t('ai.trainingFailed'))
    }

    // 更新模型指标
    modelMetrics.value = data.model_metrics || {}
    
    ElMessage.success(t('ai.messages.trainingSuccess'))
  } catch (error) {
    console.error('Training failed:', error)
    ElMessage.error(error.message || t('ai.messages.trainingFailed'))
    modelMetrics.value = {}
  } finally {
    isTraining.value = false
  }
}

const handlePredict = async (config) => {
  if (isPredicting.value) return
  
  isPredicting.value = true
  try {
    const data = await predictStockPrice(config)
    console.log('Received prediction data:', data)

    if (!data || data.status !== 'success') {
      throw new Error(data?.message || t('ai.messages.predictionFailed'))
    }
    
    // 更新图表数据
    if (data.historical_dates && data.historical_prices && data.predictions) {
      chartData.value = {
        dates: data.historical_dates,
        actualData: data.historical_prices,
        predictedData: data.predictions,
        technicalIndicators: data.technical_indicators
      }
      
      console.log('Updated chart data:', chartData.value)
    }

    // 更新预测结果
    backtestResults.value = {
      predictionDate: config.predictionDate,
      predictions: Object.entries(data.predictions).map(([modelType, prediction]) => ({
        modelType: modelType.toUpperCase(),
        actualPrice: data.historical_prices[data.historical_prices.length - 1].close,
        predictedPrice: prediction,
        confidence: data.model_metrics[modelType]?.confidence || null
      }))
    }

    ElMessage.success(t('ai.messages.predictionSuccess'))
  } catch (error) {
    console.error('Prediction failed:', error)
    ElMessage.error(error.message || t('ai.messages.predictionFailed'))
    chartData.value = null
    backtestResults.value = {}
  } finally {
    isPredicting.value = false
  }
}
</script>