<template>
  <div>
    <h2 class="text-lg font-semibold mb-4">{{ t('ai.modelMetrics') }}</h2>    
    <div v-if="metrics && Object.keys(metrics).length > 0" class="space-y-6">
      <div v-for="(modelMetrics, modelType) in metrics" :key="modelType" class="border-t pt-4">
        <template v-if="modelMetrics && typeof modelMetrics === 'object'">
          <h4 class="text-md font-medium text-gray-700 mb-3">
            {{ t(`ai.models.${modelType}`) }}
          </h4>
          
          <!-- 基础指标 -->
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-gray-50 p-3 rounded">
              <div class="text-sm text-gray-500">{{ t('ai.metrics.mse') }}</div>
              <div class="text-lg font-medium">
                {{ formatNumber(modelMetrics.mse) }}
              </div>
            </div>
            <div class="bg-gray-50 p-3 rounded">
              <div class="text-sm text-gray-500">{{ t('ai.metrics.rmse') }}</div>
              <div class="text-lg font-medium">
                {{ formatNumber(modelMetrics.rmse) }}
              </div>
            </div>
            <div class="bg-gray-50 p-3 rounded">
              <div class="text-sm text-gray-500">{{ t('ai.metrics.mae') }}</div>
              <div class="text-lg font-medium">
                {{ formatNumber(modelMetrics.mae) }}
              </div>
            </div>
            <div class="bg-gray-50 p-3 rounded">
              <div class="text-sm text-gray-500">{{ t('ai.metrics.r2') }}</div>
              <div class="text-lg font-medium">
                {{ formatNumber(modelMetrics.r2) }}
              </div>
            </div>
          </div>

          <!-- 预测准确度 -->
          <div v-if="modelMetrics.prediction_accuracy" class="mt-4">
            <h5 class="text-sm font-medium text-gray-600 mb-2">
              {{ t('ai.metrics.predictionAccuracy') }}
            </h5>
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-gray-50 p-3 rounded">
                <div class="text-sm text-gray-500">{{ t('ai.metrics.directionAccuracy') }}</div>
                <div class="text-lg font-medium">
                  {{ formatPercent(modelMetrics.prediction_accuracy.direction_accuracy) }}
                </div>
              </div>
              <div class="bg-gray-50 p-3 rounded">
                <div class="text-sm text-gray-500">{{ t('ai.metrics.mape') }}</div>
                <div class="text-lg font-medium">
                  {{ formatPercent(modelMetrics.prediction_accuracy.mape / 100) }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
    
    <div v-else class="text-gray-500 text-center py-4">
      {{ t('ai.noMetrics') }}
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  metrics: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 格式化数字，保留4位小数
const formatNumber = (value) => {
  if (value === undefined || value === null || !isFinite(value)) {
    return '-'
  }
  const num = Number(value)
  if (Math.abs(num) < 0.0001) {
    return num.toExponential(4)
  }
  return num.toFixed(4)
}

// 格式化百分比，保留2位小数
const formatPercent = (value) => {
  if (value === undefined || value === null || !isFinite(value)) {
    return '-'
  }
  return `${(Number(value) * 100).toFixed(2)}%`
}

// 监听指标变化
watch(() => props.metrics, (newMetrics) => {
  console.log('Metrics updated:', newMetrics)
}, { deep: true })
</script> 