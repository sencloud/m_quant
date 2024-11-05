import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useStocksStore = defineStore('stocks', () => {
  const stocks = ref([])
  const loading = ref(false)
  const error = ref(null)
  const dialogs = ref({
    addStock: false,
    addGroup: false
  })

  // 预设的因子组合
  const factorPresets = {
    value: {
      pe_ttm: 30,
      pb: 30,
      dv_ttm: 40
    },
    growth: {
      revenue_growth: 40,
      profit_growth: 40,
      ps_ttm: 20
    },
    momentum: {
      macd: 40,
      rsi: 30,
      volume_ratio: 30
    },
    quality: {
      roe: 40,
      debt_ratio: 30,
      turnover_rate: 30
    }
  }

  // 更新股票列表
  const updateStocks = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/stocks')
      if (response.data) {
        // 保持原有的数据处理逻辑
        if (Array.isArray(response.data)) {
          stocks.value = response.data.map(stock => ({
            ...stock,
            code: stock.ts_code || stock.code,
          }))
        } else if (typeof response.data === 'object') {
          stocks.value = response.data
        }
      }
    } catch (err) {
      console.error('Failed to update stocks:', err)
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  // 获取股票历史数据
  const fetchStockData = async (params) => {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/stock/history', {
        params: {
          code: params.code,
          granularity: params.granularity,
          startDate: params.startDate,
          endDate: params.endDate
        }
      })
      return response.data
    } catch (err) {
      console.error('Failed to fetch stock data:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 同步股票数据
  const syncStockData = async (params) => {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post('/api/stock/sync', params)
      return response.data
    } catch (err) {
      console.error('Failed to sync stock data:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取因子预设
  const getFactorPreset = (presetName) => {
    if (!factorPresets[presetName]) {
      console.warn(`Preset "${presetName}" not found`)
      return null
    }
    return factorPresets[presetName]
  }

  // 打开对话框
  const openDialog = (dialogName) => {
    dialogs.value[dialogName] = true
  }

  // 关闭对话框
  const closeDialog = (dialogName) => {
    dialogs.value[dialogName] = false
  }

  // 获取筛选后的股票列表
  const filteredStocks = computed(() => stocks.value)

  return {
    stocks,
    loading,
    error,
    dialogs,
    filteredStocks,
    updateStocks,
    fetchStockData,
    syncStockData,
    getFactorPreset,
    factorPresets,
    openDialog,
    closeDialog
  }
}) 