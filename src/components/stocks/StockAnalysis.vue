<template>
  <div class="p-6">
    <AnalysisHeader />
    <AnalysisControls 
      v-model:stock="selectedStock"
      v-model:timeGranularity="timeGranularity"
      v-model:dateRange="dateRange"
      @change="loadStockData"
    />
    
    <div v-if="loading" class="flex justify-center py-12">
      <el-loading />
    </div>

    <template v-else-if="stockData">
      <div class="h-[500px] mb-8">
        <KLineChart 
          :data="stockData.klineData"
          :ma-lines="[5, 10, 20]"
        />
      </div>

      <StockDataTable :data="stockData.tableData" />
    </template>

    <div v-else-if="error" class="text-center py-12">
      <el-alert :title="t(error)" type="error" show-icon />
    </div>

    <SyncDataDialog 
      v-model="showSyncDialog"
      :stock-symbol="selectedStock"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStocksStore } from '@/stores/stocks'
import AnalysisHeader from './analysis/AnalysisHeader.vue'
import AnalysisControls from './analysis/AnalysisControls.vue'
import KLineChart from './analysis/KLineChart.vue'
import StockDataTable from './analysis/StockDataTable.vue'
import SyncDataDialog from './dialogs/SyncDataDialog.vue'

const { t } = useI18n()
const store = useStocksStore()

const selectedStock = ref('')
const timeGranularity = ref('day')
const dateRange = ref([])
const loading = ref(false)
const error = ref(null)
const showSyncDialog = ref(false)
const stockData = ref(null)

const loadStockData = async () => {
  if (!selectedStock.value) return
  
  loading.value = true
  error.value = null
  
  try {
    const data = await store.fetchStockData({
      code: selectedStock.value,
      granularity: timeGranularity.value,
      startDate: dateRange.value[0],
      endDate: dateRange.value[1]
    })
    
    stockData.value = {
      klineData: data.map(formatKLineData),
      tableData: data.map(formatTableData)
    }
  } catch (err) {
    console.error('Failed to load stock data:', err)
    error.value = 'stocks.error.loadFailed'
  } finally {
    loading.value = false
  }
}

const handleDataSync = async (params) => {
  try {
    await store.syncStockData(params)
    await loadStockData()
  } catch (err) {
    console.error('Failed to sync data:', err)
  }
}

const formatKLineData = (item) => ({
  date: item.date,
  open: item.open,
  high: item.high,
  low: item.low,
  close: item.close,
  volume: item.volume
})

const formatTableData = (item, index, arr) => ({
  ...item,
  change: index > 0 
    ? ((item.close - arr[index-1].close) / arr[index-1].close * 100)
    : 0
})

watch([selectedStock, timeGranularity, dateRange], () => {
  if (selectedStock.value && dateRange.value.length === 2) {
    loadStockData()
  }
})

const handleShowSyncDialog = (stockSymbol) => {
  selectedStock.value = stockSymbol
  showSyncDialog.value = true
}
</script> 