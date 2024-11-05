<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold mb-4">{{ t('ai.predictions') }}</h2>    
    
    <!-- 预测结果表格 -->
    <div v-if="predictions.length">
      <el-table 
        :data="predictions"
        class="w-full"
      >
        <el-table-column
          prop="modelType"
          :label="t('ai.backtest.model')"
        >
          <template #default="{ row }">
            <el-tag :type="getModelTagType(row.modelType)" size="small">
              {{ row.modelType }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="actualPrice"
          :label="t('ai.backtest.actual')"
          align="right"
          width="120"
        >
          <template #default="{ row }">
            {{ formatPrice(row.actualPrice) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="predictedPrice"
          :label="t('ai.backtest.predicted')"
          align="right"
          width="120"
        >
          <template #default="{ row }">
            {{ formatPrice(row.predictedPrice) }}
          </template>
        </el-table-column>
        
        <el-table-column
          prop="confidence"
          :label="t('ai.backtest.confidence')"
          align="right"
          width="120"
        >
          <template #default="{ row }">
            <span :class="getConfidenceClass(row.confidence)">
              {{ formatPercentage(row.confidence * 100) }}
            </span>
          </template>
        </el-table-column>

        <!-- 添加误差百分比列 -->
        <el-table-column
          prop="errorRate"
          :label="t('ai.backtest.error')"
          align="right"
          width="120"
        >
          <template #default="{ row }">
            <span :class="getErrorClass(row.actualPrice, row.predictedPrice)">
              {{ formatErrorRate(row.actualPrice, row.predictedPrice) }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 预测日期显示 -->
      <div class="mt-4 p-4 bg-gray-50 rounded-lg">
        <div class="flex items-center justify-between">
          <span class="text-gray-600">{{ t('ai.backtest.predictionDate') }}:</span>
          <span class="font-medium">{{ formatDate(predictionDate) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="text-center text-gray-500 py-4">
      {{ t('ai.noPredictions') }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'

const { t } = useI18n()

const props = defineProps({
  results: {
    type: Object,
    default: () => ({})
  }
})

// 从 results 中提取预测数据
const predictions = computed(() => props.results.predictions || [])
const predictionDate = computed(() => props.results.predictionDate)

// 格式化日期
const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD') : '-'
}

// 格式化价格
const formatPrice = (price) => {
  return price ? Number(price).toFixed(2) : '-'
}

// 格式化百分比
const formatPercentage = (value) => {
  return value ? `${Number(value).toFixed(1)}%` : '-'
}

// 计算并格式化误差率
const formatErrorRate = (actual, predicted) => {
  if (!actual || !predicted) return '-'
  const error = Math.abs((predicted - actual) / actual * 100)
  return `${error.toFixed(2)}%`
}

// 获取误差样式类
const getErrorClass = (actual, predicted) => {
  if (!actual || !predicted) return 'text-gray-500'
  
  const error = Math.abs((predicted - actual) / actual * 100)
  if (error <= 3) return 'text-green-600 font-medium'
  if (error <= 5) return 'text-yellow-600 font-medium'
  return 'text-red-600 font-medium'
}

// 获取模型标签类型
const getModelTagType = (modelType) => {
  const types = {
    'RNN': '',
    'LSTM': 'success',
    'GRU': 'warning'
  }
  return types[modelType] || 'info'
}

// 获取置信度样式类
const getConfidenceClass = (confidence) => {
  if (!confidence) return 'text-gray-500'
  
  const value = confidence * 100
  if (value >= 80) return 'text-green-600 font-medium'
  if (value >= 60) return 'text-yellow-600 font-medium'
  return 'text-red-600 font-medium'
}
</script> 