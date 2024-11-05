<template>
  <div>
    <h2 class="text-lg font-semibold mb-4">{{ $t('ai.modelConfig') }}</h2>
    <div class="space-y-4">
      <el-form :model="formData">
        <el-form-item :label="$t('ai.stockSymbol')">
          <el-cascader
            v-model="formData.stockSymbol"
            :options="stockOptions"
            :props="cascaderProps"
            :placeholder="$t('stocks.selectStock')"
            class="w-full"
            filterable
            :loading="loadingStocks"
          />
        </el-form-item>

        <el-form-item :label="$t('ai.selectModels')">
          <el-select
            v-model="formData.modelType"
            multiple
            class="w-full"
          >
            <el-option
              v-for="model in modelTypes"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('ai.trainingPeriod')">
          <el-slider
            v-model="formData.timePeriod"
            :min="300"
            :max="1800"
            :step="100"
            show-stops
          />
        </el-form-item>

        <el-form-item :label="$t('ai.predictionPeriod')">
          <el-date-picker
            v-model="formData.predictionDate"
            type="date"
            :placeholder="$t('common.selectDate')"
            value-format="YYYY-MM-DD"
            class="w-full"
          />
        </el-form-item>

        <el-form-item>
          <div class="flex space-x-4">
            <el-button 
              type="primary" 
              @click="handleTrain"
              :loading="loading"
            >
              {{ $t('ai.trainModel') }}
            </el-button>
            <el-button 
              type="success" 
              @click="handlePredict"
              :loading="predicting"
            >
              {{ $t('ai.predict') }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'

const { t } = useI18n()

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  predicting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['train', 'predict'])

const modelTypes = [
  { value: 'lstm', label: 'LSTM (Long Short-Term Memory)' },
  { value: 'gru', label: 'GRU (Gated Recurrent Unit)' },
  { value: 'rnn', label: 'RNN (Recurrent Neural Network)' }
]

const stocks = ref({})
const stockOptions = ref([])
const loadingStocks = ref(false)

const cascaderProps = ref({
  expandTrigger: 'hover',
  checkStrictly: true,
  multiple: false,
  emitPath: false,
  value: 'code',
  label: 'label'
})

const dateShortcuts = [
  {
    text: t('common.tomorrow'),
    value: () => {
      return dayjs().add(1, 'day').toDate()
    },
  },
  {
    text: t('common.nextWeek'),
    value: () => {
      return dayjs().add(7, 'day').toDate()
    },
  },
  {
    text: t('common.nextMonth'),
    value: () => {
      return dayjs().add(30, 'day').toDate()
    },
  },
]

const formData = ref({
  stockSymbol: '',
  modelType: [],
  timePeriod: 600,
  predictionDate: dayjs().add(1, 'day').format('YYYY-MM-DD')
})

const updateStockOptions = () => {
  stockOptions.value = Object.entries(stocks.value).map(([exchange, industries]) => ({
    value: exchange,
    label: t(`stocks.exchanges.${exchange.toLowerCase()}`),
    children: Object.entries(industries).map(([industry, stockList]) => ({
      value: industry,
      label: industry,
      children: stockList.map(stock => ({
        value: stock.code,
        label: `${stock.name} (${stock.code})`,
        code: stock.code,
        name: stock.name
      }))
    }))
  }))
}

const loadStocks = async () => {
  loadingStocks.value = true
  try {
    const response = await fetch('/api/stocks')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    stocks.value = await response.json()
    updateStockOptions()
  } catch (err) {
    console.error('Failed to load stocks:', err)
  } finally {
    loadingStocks.value = false
  }
}

onMounted(() => {
  loadStocks()
})

const handleTrain = () => {
  if (!formData.value.stockSymbol) {
    ElMessage.warning(t('ai.pleaseSelectStock'))
    return
  }
  if (formData.value.modelType.length === 0) {
    ElMessage.warning(t('ai.pleaseSelectModel'))
    return
  }
  if (!formData.value.predictionDate) {
    ElMessage.warning(t('ai.pleasePredictionDate'))
    return
  }

  emit('train', {
    symbol: formData.value.stockSymbol,
    models: formData.value.modelType,
    timePeriod: formData.value.timePeriod,
    predictionDate: formData.value.predictionDate
  })
}

const handlePredict = () => {
  if (!formData.value.stockSymbol) {
    ElMessage.warning(t('ai.pleaseSelectStock'))
    return
  }
  if (formData.value.modelType.length === 0) {
    ElMessage.warning(t('ai.pleaseSelectModel'))
    return
  }
  if (!formData.value.predictionDate) {
    ElMessage.warning(t('ai.pleasePredictionDate'))
    return
  }

  emit('predict', {
    symbol: formData.value.stockSymbol,
    models: formData.value.modelType,
    timePeriod: formData.value.timePeriod,
    predictionDate: formData.value.predictionDate
  })
}
</script>

<style scoped>
.el-form {
  max-width: 500px;
  margin: 0 auto;
}
</style> 