<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold">{{ t('stocks.futures.title') }}</h2>
      <div class="space-x-2">
        <el-button @click="exportData" :loading="exporting">
          {{ t('stocks.futures.export') }}
        </el-button>
        <el-button type="primary" @click="syncData" :loading="syncing">
          {{ t('stocks.futures.sync') }}
        </el-button>
      </div>
    </div>

    <!-- 合约选择和配置区域 -->
    <el-form :inline="true" class="mb-6 flex flex-wrap items-center gap-4">
      <!-- 交易所选择 -->
      <el-form-item :label="t('stocks.futures.market')" class="mb-2">
        <el-select 
          v-model="selectedMarket"
          :loading="marketLoading"
          @change="handleMarketChange"
          style="width: 220px"
        >
          <el-option 
            v-for="market in markets" 
            :key="market.value"
            :label="market.label"
            :value="market.value"
          >
            <div class="flex items-center justify-between">
              <span>{{ market.label }}</span>
              <span class="text-gray-400 text-sm">({{ market.value }})</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 合约选择 -->
      <el-form-item :label="t('stocks.futures.contract')" class="mb-2">
        <el-select 
          v-model="selectedContract"
          :loading="contractsLoading"
          filterable
          :placeholder="t('stocks.futures.selectContract')"
          style="width: 280px"
          :disabled="!selectedMarket"
        >
          <el-option-group
            v-for="group in groupedContracts"
            :key="group.label"
            :label="group.label"
          >
            <el-option
              v-for="contract in group.options"
              :key="contract.code"
              :label="contract.name"
              :value="contract.code"
            >
              <div class="flex justify-between items-center">
                <span class="font-medium">{{ contract.code }}</span>
                <span class="text-gray-500 ml-4">{{ contract.name }}</span>
              </div>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <!-- 时间粒度选择 -->
      <el-form-item :label="t('stocks.futures.period')" class="mb-2">
        <el-select 
          v-model="timeGranularity"
          style="width: 160px"
        >
          <el-option-group :label="t('stocks.futures.minutes')">
            <el-option label="1分钟" value="1m">
              <div class="flex justify-between items-center">
                <span>1分钟</span>
                <span class="text-gray-400 text-sm">1m</span>
              </div>
            </el-option>
            <el-option label="5分钟" value="5m">
              <div class="flex justify-between items-center">
                <span>5分钟</span>
                <span class="text-gray-400 text-sm">5m</span>
              </div>
            </el-option>
            <el-option label="15分钟" value="15m">
              <div class="flex justify-between items-center">
                <span>15分钟</span>
                <span class="text-gray-400 text-sm">15m</span>
              </div>
            </el-option>
            <el-option label="30分钟" value="30m">
              <div class="flex justify-between items-center">
                <span>30分钟</span>
                <span class="text-gray-400 text-sm">30m</span>
              </div>
            </el-option>
          </el-option-group>
          <el-option-group :label="t('stocks.futures.other')">
            <el-option label="1小时" value="1h">
              <div class="flex justify-between items-center">
                <span>1小时</span>
                <span class="text-gray-400 text-sm">1h</span>
              </div>
            </el-option>
            <el-option label="日线" value="1d">
              <div class="flex justify-between items-center">
                <span>日线</span>
                <span class="text-gray-400 text-sm">1d</span>
              </div>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>

      <!-- 日期范围选择 -->
      <el-form-item :label="t('stocks.futures.dateRange')" class="mb-2">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          :start-placeholder="t('calendar.range.startDate')"
          :end-placeholder="t('calendar.range.endDate')"
          :range-separator="t('calendar.range.separator')"
          value-format="YYYY-MM-DD"
          style="width: 360px"
        />
      </el-form-item>
    </el-form>

    <!-- 合约详情 -->
    <FuturesDetail
      v-if="selectedContractInfo"
      :contract="selectedContractInfo"
      class="mb-6"
    />

    <!-- 图表配置 -->
    <FuturesChartConfig
      v-model:config="chartConfig"
      class="mb-4"
    />

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center py-12">
      <el-loading />
    </div>

    <!-- 数据展示区域 -->
    <template v-else-if="futuresData">
      <!-- K线图 -->
      <div class="h-[600px] mb-8 bg-white rounded-lg shadow p-4">
        <KLineChart 
          :data="futuresData.klineData"
          :indicators="chartConfig.indicators"
          :ma-lines="chartConfig.maLines"
          @range-select="handleRangeSelect"
        />
      </div>

      <!-- 数据表格 -->
      <div class="bg-white rounded-lg shadow p-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium">{{ t('stocks.futures.tradeData') }}</h3>
          <el-radio-group v-model="tableView" size="small">
            <el-radio-button label="normal">{{ t('stocks.futures.normalView') }}</el-radio-button>
            <el-radio-button label="technical">{{ t('stocks.futures.technicalView') }}</el-radio-button>
          </el-radio-group>
        </div>
        <FuturesDataTable 
          :data="futuresData.tableData"
          :view="tableView"
          :loading="tableLoading"
          @sort-change="handleSortChange"
        />
      </div>
    </template>

    <!-- 错误提示 -->
    <div v-else-if="error" class="text-center py-12">
      <el-alert 
        :title="t(error)"
        type="error" 
        show-icon 
        :closable="false"
        class="mb-4"
      />
      <el-button @click="retryLoad">{{ t('stocks.futures.retry') }}</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { format } from 'date-fns'
import KLineChart from './analysis/KLineChart.vue'
import FuturesDataTable from './analysis/FuturesDataTable.vue'
import FuturesDetail from './futures/FuturesDetail.vue'
import FuturesChartConfig from './futures/FuturesChartConfig.vue'
import { useFuturesStore } from '@/stores/futures'
import { exportToCSV } from '@/utils/export'

const { t } = useI18n()
const store = useFuturesStore()

// 状态变量
const loading = ref(false)
const tableLoading = ref(false)
const error = ref(null)
const exporting = ref(false)
const syncing = ref(false)

// 选择和配置
const selectedMarket = ref('CFFEX')
const selectedContract = ref('')
const timeGranularity = ref('1d')
const dateRange = ref([])
const chartConfig = ref({
  indicators: ['MA', 'VOL'],
  maLines: [5, 10, 20]
})
const tableView = ref('normal')

// 数据
const futuresData = ref(null)

// 计算属性
const markets = [
  { value: 'CFFEX', label: '中国金融期货交易所' },
  { value: 'SHFE', label: '上海期货交易所' },
  { value: 'DCE', label: '大连商品交易所' },
  { value: 'CZCE', label: '郑州商品交易所' },
]

const contracts = computed(() => store.getContractsByMarket(selectedMarket.value))

const selectedContractInfo = computed(() => {
  if (!selectedContract.value) return null
  return contracts.value.find(c => c.code === selectedContract.value)
})

// 按品种分组的合约列表
const groupedContracts = computed(() => {
  if (!contracts.value.length) return []
  
  const groups = {}
  contracts.value.forEach(contract => {
    const category = contract.category || '其他'
    if (!groups[category]) {
      groups[category] = {
        label: t(`stocks.futures.categories.${category}`),
        options: []
      }
    }
    groups[category].options.push(contract)
  })
  
  return Object.values(groups).sort((a, b) => a.label.localeCompare(b.label))
})

// 日期快捷选项
const dateShortcuts = [
  {
    text: t('calendar.shortcuts.lastWeek'),
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: t('calendar.shortcuts.lastMonth'),
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 1)
      return [start, end]
    }
  },
  {
    text: t('calendar.shortcuts.lastThreeMonths'),
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setMonth(start.getMonth() - 3)
      return [start, end]
    }
  },
  {
    text: t('calendar.shortcuts.thisYear'),
    value: () => {
      const end = new Date()
      const start = new Date(end.getFullYear(), 0, 1)
      return [start, end]
    }
  }
]

// 方法
const loadFuturesData = async () => {
  if (!selectedContract.value || !dateRange.value?.length) {
    console.log('Missing required values:', {
      contract: selectedContract.value,
      range: dateRange.value
    });
    return;
  }
  
  loading.value = true;
  error.value = null;
  
  try {
    console.log('Calling getFuturesData with:', {
      code: selectedContract.value,
      granularity: timeGranularity.value,
      startDate: dateRange.value[0],
      endDate: dateRange.value[1]
    });

    const data = await store.getFuturesData({
      code: selectedContract.value,
      granularity: timeGranularity.value,
      startDate: dateRange.value[0],
      endDate: dateRange.value[1]
    });
    
    futuresData.value = {
      klineData: data.map(formatKLineData),
      tableData: data.map(formatTableData)
    };
  } catch (err) {
    console.error('Failed to load futures data:', err);
    error.value = err.message || 'stocks.futures.loadError';
  } finally {
    loading.value = false;
  }
};

const handleMarketChange = async () => {
  selectedContract.value = ''
  try {
    await store.loadContracts(selectedMarket.value)
  } catch (err) {
    ElMessage.error(t('stocks.futures.loadContractsError'))
  }
}

const handleRangeSelect = (range) => {
  if (range && range.length === 2) {
    dateRange.value = [
      format(range[0], 'yyyy-MM-dd'),
      format(range[1], 'yyyy-MM-dd')
    ]
  }
}

const handleSortChange = ({ prop, order }) => {
  if (!futuresData.value) return
  
  tableLoading.value = true
  try {
    const sorted = [...futuresData.value.tableData].sort((a, b) => {
      if (order === 'ascending') {
        return a[prop] - b[prop]
      } else {
        return b[prop] - a[prop]
      }
    })
    futuresData.value.tableData = sorted
  } finally {
    tableLoading.value = false
  }
}

const exportData = async () => {
  if (!futuresData.value?.tableData.length) return
  
  exporting.value = true
  try {
    await exportToCSV({
      data: futuresData.value.tableData,
      filename: `${selectedContract.value}_${timeGranularity.value}_${dateRange.value[0]}_${dateRange.value[1]}`,
      sheetName: 'Futures Data'
    })
    ElMessage.success(t('common.exportSuccess'))
  } catch (err) {
    ElMessage.error(t('common.exportError'))
  } finally {
    exporting.value = false
  }
}

const syncData = async () => {
  if (!selectedContract.value) return
  
  syncing.value = true
  try {
    await store.syncFuturesData(selectedContract.value)
    ElMessage.success(t('stocks.futures.syncSuccess'))
    loadFuturesData()
  } catch (err) {
    ElMessage.error(t('stocks.futures.syncError'))
  } finally {
    syncing.value = false
  }
}

const retryLoad = () => {
  error.value = null
  loadFuturesData()
}

const formatKLineData = (item) => ({
  date: item.date,
  open: item.open,
  high: item.high,
  low: item.low,
  close: item.close,
  volume: item.volume,
  openInterest: item.openInterest
})

const formatTableData = (item, index, arr) => ({
  ...item,
  change: index > 0 
    ? ((item.close - arr[index-1].close) / arr[index-1].close * 100).toFixed(2)
    : '0.00'
})

// 监听器
watch(
  [selectedContract, timeGranularity, dateRange],
  async (newValues, oldValues) => {
    const [newContract, newGranularity, newRange] = newValues;
    console.log('Watch triggered:', {
      contract: newContract,
      granularity: newGranularity,
      range: newRange
    });

    if (newContract && newRange?.length === 2) {
      try {
        // 确保 store 已正确初始化
        if (!store || typeof store.getFuturesData !== 'function') {
          console.error('Store not properly initialized:', store);
          error.value = 'Store initialization error';
          return;
        }

        await loadFuturesData();
      } catch (err) {
        console.error('Watch error:', err);
        error.value = err.message;
      }
    }
  },
  {
    deep: true,  // 深度监听
    immediate: false  // 不立即触发
  }
);

// 确保 store 正确初始化
console.log('Store initialized:', store);

// 初始化
onMounted(async () => {
  try {
    await store.loadContracts(selectedMarket.value)
  } catch (err) {
    error.value = 'stocks.futures.initError'
  }
})
</script>

<style scoped>
/* 调整下拉菜单最大高度 */
:deep(.el-select-dropdown__wrap) {
  max-height: 400px;
}

/* 调整选项内容样式 */
:deep(.el-select-dropdown__item) {
  padding: 8px 12px;
}

/* 调整分组标题样式 */
:deep(.el-select-group__title) {
  padding: 8px 12px;
  font-weight: bold;
  background-color: #f5f7fa;
}

/* 调整表单项间距 */
:deep(.el-form-item) {
  margin-right: 16px;
}

/* 调整标签宽度，保持对齐 */
:deep(.el-form-item__label) {
  min-width: 80px;
}
</style>