<template>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center space-x-4">
      <!-- 股票选择 - 修改为级联选择器 -->
      <el-cascader
        v-model="stockValue"
        :options="stockOptions"
        :props="cascaderProps"
        :placeholder="t('stocks.selectStock')"
        class="w-96"
        @change="handleStockChange"
        :loading="loading"
        filterable
        :filter-method="filterStocks"
      />
      
      <!-- 时间粒度切换 -->
      <el-radio-group 
        v-model="granularityValue" 
        @change="handleGranularityChange"
      >
        <el-radio-button 
          v-for="option in granularityOptions" 
          :key="option.value"
          :label="option.value"
        >
          {{ t(`stocks.granularity.${option.value}`) }}
        </el-radio-button>
      </el-radio-group>

      <!-- 时间选择器 -->
      <template v-if="['minute', 'hour', 'day'].includes(granularityValue)">
        <el-date-picker
          v-model="dateValue"
          type="daterange"
          :start-placeholder="t('calendar.range.startDate')"
          :end-placeholder="t('calendar.range.endDate')"
          :range-separator="t('calendar.range.separator')"
          @change="handleDateChange"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStocksStore } from '@/stores/stocks'
import axios from 'axios'

const props = defineProps({
  stock: String,
  timeGranularity: String,
  dateRange: Array
})

const emit = defineEmits(['update:stock', 'update:timeGranularity', 'update:dateRange', 'change'])

const { t } = useI18n()
const store = useStocksStore()

const stockValue = ref(props.stock)
const granularityValue = ref(props.timeGranularity)
const dateValue = ref(props.dateRange)
const loading = ref(false)
const stocks = ref({})
const stockOptions = ref([])

// 级联选择器配置
const cascaderProps = {
  expandTrigger: 'hover',
  checkStrictly: true,
  multiple: false,
  emitPath: false,
  value: 'code',
  label: 'label'
}

const granularityOptions = [
  { value: 'minute' },
  { value: 'hour' },
  { value: 'day' }
]

// 加载股票数据
const loadStocks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/stocks')
    stocks.value = response.data
    updateStockOptions()
  } catch (err) {
    console.error('Failed to load stocks:', err)
  } finally {
    loading.value = false
  }
}

// 更新股票选项
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

const handleStockChange = (value) => {
  emit('update:stock', value)
  emit('change')
}

const handleGranularityChange = (value) => {
  emit('update:timeGranularity', value)
  // 重置日期范围
  const now = new Date()
  let start = new Date()
  
  switch (value) {
    case 'minute':
      start.setDate(start.getDate() - 1)
      break
    case 'hour':
      start.setDate(start.getDate() - 7)
      break
    case 'day':
      start.setFullYear(start.getFullYear() - 1)
      break
  }
  
  dateValue.value = [start, now]
  emit('update:dateRange', [start, now])
  emit('change')
}

const handleDateChange = (value) => {
  emit('update:dateRange', value)
  emit('change')
}

// 股票过滤方法
const filterStocks = (node, keyword) => {
  const { value, label, children } = node
  return (
    value.toLowerCase().indexOf(keyword.toLowerCase()) !== -1 ||
    label.toLowerCase().indexOf(keyword.toLowerCase()) !== -1 ||
    (children && children.some(child => filterStocks(child, keyword)))
  )
}

watch(() => props.stock, (newVal) => {
  stockValue.value = newVal
})

watch(() => props.timeGranularity, (newVal) => {
  granularityValue.value = newVal
})

watch(() => props.dateRange, (newVal) => {
  dateValue.value = newVal
})

// 组件挂载时加载股票数据
onMounted(() => {
  loadStocks()
})
</script> 