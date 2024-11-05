@ -1,587 +1,14 @@
<template>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold">{{ t('stocks.title') }}</h2>
        </div>
        
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-4">
            <!-- 股票选择 -->
            <el-cascader
              v-model="selectedStock"
              :options="stockOptions"
              :props="cascaderProps"
              :placeholder="t('stocks.selectStock')"
              class="w-96"
              @change="handleStockChange"
              :loading="loadingStocks"
              filterable
              :filter-method="filterStocks"
            />
            
            <!-- 时间粒度切换 -->
            <el-radio-group v-model="timeGranularity" @change="handleGranularityChange">
              <el-radio-button label="minute">{{ t('stocks.granularity.minute') }}</el-radio-button>
              <el-radio-button label="hour">{{ t('stocks.granularity.hour') }}</el-radio-button>
              <el-radio-button label="day">{{ t('stocks.granularity.day') }}</el-radio-button>
              <!-- <el-radio-button label="week">{{ t('stocks.granularity.week') }}</el-radio-button>
              <el-radio-button label="month">{{ t('stocks.granularity.month') }}</el-radio-button>
              <el-radio-button label="year">{{ t('stocks.granularity.year') }}</el-radio-button> -->
            </el-radio-group>
  
            <!-- 时间选择器 -->
            <template v-if="['minute', 'hour', 'day'].includes(timeGranularity)">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                :start-placeholder="t('calendar.range.startDate')"
                :end-placeholder="t('calendar.range.endDate')"
                :range-separator="t('calendar.range.separator')"
                @change="loadStockData"
              />
            </template>
  
            <template v-else-if="timeGranularity === 'week'">
              <el-date-picker
                v-model="selectedWeek"
                type="week"
                :format="'[' + t('stocks.week') + '] w'"
                :placeholder="t('stocks.selectWeek')"
                @change="loadStockData"
              />
            </template>
  
            <template v-else-if="timeGranularity === 'month'">
              <el-date-picker
                v-model="selectedMonth"
                type="month"
                :placeholder="t('stocks.selectMonth')"
                @change="loadStockData"
              />
            </template>
  
            <template v-else-if="timeGranularity === 'year'">
              <el-date-picker
                v-model="selectedYear"
                type="year"
                :placeholder="t('stocks.selectYear')"
                @change="loadStockData"
              />
            </template>
            <el-button @click="showSyncDialog = true">{{ t('stocks.syncDataDialog.title') }}</el-button>
          </div>  
        </div>
  
        <div v-if="loading" class="flex justify-center py-12">
          <el-loading />
        </div>
  
        <template v-else-if="stockData">
          <div class="h-[500px] mb-8">
            <k-line-chart 
              :data="stockData.klineData"
              :ma-lines="[5, 10, 20]"
            />
          </div>
  
          <el-table 
            :data="stockData.tableData"
            style="width: 100%"
            :default-sort="{ prop: 'date', order: 'descending' }"
            height="400"
          >
            <el-table-column prop="date" :label="t('stocks.table.date')" sortable width="180" />
            <el-table-column prop="open" :label="t('stocks.table.open')" :formatter="formatPrice" />
            <el-table-column prop="high" :label="t('stocks.table.high')" :formatter="formatPrice" />
            <el-table-column prop="low" :label="t('stocks.table.low')" :formatter="formatPrice" />
            <el-table-column prop="close" :label="t('stocks.table.close')" :formatter="formatPrice" />
            <el-table-column prop="volume" :label="t('stocks.table.volume')" :formatter="formatVolume" />
            <el-table-column prop="change" :label="t('stocks.table.change')" :formatter="formatChange">
              <template #default="{ row }">
                <span :class="row.change >= 0 ? 'text-red-600' : 'text-green-600'">
                  {{ formatChange(null, null, row.change) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </template>
  
        <div v-else-if="error" class="text-center py-12">
          <el-alert :title="t(error)" type="error" show-icon />
        </div>
      </div>
    </div>
  
    <!-- Sync Data Dialog -->
    <el-dialog
      v-model="showSyncDialog"
      :title="t('stocks.syncDataDialog.title')"
      width="30%"
    >
      <el-form>
        <el-form-item :label="t('stocks.syncDataDialog.dateRange')">
          <el-date-picker
            v-model="syncDateRange"
            type="daterange"
            :start-placeholder="t('calendar.range.startDate')"
            :end-placeholder="t('calendar.range.endDate')"
            :range-separator="t('calendar.range.separator')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSyncDialog = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="syncStockData">
            {{ t('stocks.syncDataDialog.confirm') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  
    <!-- Add Stock Dialog -->
    <el-dialog
      v-model="showAddStockDialog"
      :title="t('stocks.addStockDialog.title')"
      width="30%"
    >
      <el-form>
        <el-form-item :label="t('stocks.addStockDialog.selectMarket')">
          <el-select v-model="newStockMarket">
            <el-option label="上海证券交易所" value="SH" />
            <el-option label="深圳证券交易所" value="SZ" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('stocks.addStockDialog.selectStock')">
          <el-select 
            v-model="newStock" 
            filterable
            :loading="loadingAvailableStocks"
          >
            <el-option
              v-for="stock in filteredAvailableStocks"
              :key="stock.value"
              :label="stock.label"
              :value="stock.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddStockDialog = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="addNewStock">
            {{ t('stocks.addStockDialog.add') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </template>
  
  <script>
  import { ref, onMounted, watch, computed } from 'vue'
  import { useI18n } from 'vue-i18n'  // 添加这一行
  import dayjs from 'dayjs'
  import KLineChart from '../components/KLineChart.vue'
  import { fetchStocks, syncStockData as apiSyncStockData, addStock as apiAddStock, fetchAvailableStocks } from '../api/backtest'
  import { ElMessage, ElMessageBox } from 'element-plus'
  
  export default {
    components: {
      KLineChart
    },
  
    setup() {
      const { t } = useI18n()  // 添加这一行
  
      const stocks = ref({})
      const selectedStock = ref('')
      const stockData = ref(null)
      const loading = ref(false)
      const error = ref(null)
      const timeGranularity = ref('day')
      const dateRange = ref([])
      const selectedWeek = ref('')
      const selectedMonth = ref('')
      const selectedYear = ref('')
  
      // New refs for dialogs and new functionality
      const showSyncDialog = ref(false)
      const showAddStockDialog = ref(false)
      const syncDateRange = ref([])
      const newStock = ref('')
      const newStockMarket = ref('SH')
      const availableStocks = ref([])
      const loadingAvailableStocks = ref(false)
      const loadingStocks = ref(false)  // Add this line
  
      const stockOptions = ref([])
  
      const cascaderProps = ref({
        expandTrigger: 'hover',
        checkStrictly: true,
        multiple: false,
        emitPath: false,
        value: 'code',
        label: 'label'
      })
  
      const filteredAvailableStocks = computed(() => {
        return availableStocks.value.filter(stock => stock.market === newStockMarket.value)
      })
  
      const handleGranularityChange = () => {
        // 重置所有时间选择
        dateRange.value = []
        selectedWeek.value = ''
        selectedMonth.value = ''
        selectedYear.value = ''
        
        // 设置认时间范围
        if (['minute', 'hour', 'day'].includes(timeGranularity.value)) {
          const end = dayjs()
          const start = timeGranularity.value === 'minute' ? end.subtract(1, 'day')
            : timeGranularity.value === 'hour' ? end.subtract(7, 'day')
            : end.subtract(1, 'year')
          dateRange.value = [start.toDate(), end.toDate()]
        }
        
        loadStockData()
      }
  
      const getTimeParams = () => {
        const params = {
          granularity: timeGranularity.value
        }
        
        if (['minute', 'hour', 'day'].includes(timeGranularity.value) && dateRange.value?.length === 2) {
          params.startDate = dayjs(dateRange.value[0]).format('YYYY-MM-DD HH:mm')
          params.endDate = dayjs(dateRange.value[1]).format('YYYY-MM-DD HH:mm')
        } else if (timeGranularity.value === 'week' && selectedWeek.value) {
          const weekStart = dayjs(selectedWeek.value).startOf('week')
          params.startDate = weekStart.format('YYYY-MM-DD')
          params.endDate = weekStart.add(6, 'day').format('YYYY-MM-DD')
        } else if (timeGranularity.value === 'month' && selectedMonth.value) {
          const monthDate = dayjs(selectedMonth.value)
          params.startDate = monthDate.startOf('month').format('YYYY-MM-DD')
          params.endDate = monthDate.endOf('month').format('YYYY-MM-DD')
        } else if (timeGranularity.value === 'year' && selectedYear.value) {
          const yearDate = dayjs(selectedYear.value)
          params.startDate = yearDate.startOf('year').format('YYYY-MM-DD')
          params.endDate = yearDate.endOf('year').format('YYYY-MM-DD')
        } else {
          // 如果没有选择日期，使用默认的日期范围
          const end = dayjs()
          const start = end.subtract(1, 'year')
          params.startDate = start.format('YYYY-MM-DD')
          params.endDate = end.format('YYYY-MM-DD')
        }
  
        console.log('Time params:', params)  // 添加这行来检查参数
        return params
      }
  
      const loadStocks = async () => {
        loadingStocks.value = true
        error.value = null
        try {
          const response = await fetch('/api/stocks')
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
          stocks.value = await response.json()
          updateStockOptions()
          
          if (!selectedStock.value && stockOptions.value.length > 0) {
            const firstStock = stockOptions.value[0].children[0].children[0]
            selectedStock.value = firstStock.value
            
            // 设置默认的日期范围
            const end = dayjs()
            const start = end.subtract(1, 'year')
            dateRange.value = [start.toDate(), end.toDate()]
            
            await loadStockData()
          }
        } catch (err) {
          console.error('Failed to load stocks:', err)
          error.value = 'stocks.error.loadStocks'
          ElMessage.error(t('stocks.error.loadStocks'))
        } finally {
          loadingStocks.value = false
        }
      }
  
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
  
      const getExchangeLabel = (exchange) => {
        switch (exchange) {
          case 'SH':
            return t('stocks.exchanges.sh')  // 使用 t 替换 $t
          case 'SZ':
            return t('stocks.exchanges.sz')  // 使用 t 替换 $t
          default:
            return t('stocks.exchanges.bj')  // 使用 t 替换 $t
        }
      }
  
      const loadStockData = async () => {
        if (!selectedStock.value) return

        loading.value = true
        error.value = null

        try {
          const params = getTimeParams()
          const queryString = new URLSearchParams(params).toString()
          const response = await fetch(`/api/stocks/${selectedStock.value}?${queryString}`)
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const data = await response.json()

          if (!data || data.length === 0) {
            error.value = 'stocks.noData'
            stockData.value = null
            ElMessage.warning(t('stocks.noData'))
            return
          }

          stockData.value = {
            klineData: data.map(item => ({
              date: item.date,
              open: item.open,
              high: item.high,
              low: item.low,
              close: item.close,
              volume: item.volume
            })),
            tableData: data.map((item, index, arr) => ({
              ...item,
              change: index > 0 
                ? ((item.close - arr[index-1].close) / arr[index-1].close * 100)
                : 0
            }))
          }
        } catch (err) {
          console.error('Failed to load stock data:', err)
          error.value = 'stocks.error.loadFailed'
          ElMessage.error(t('stocks.error.loadFailed'))
          stockData.value = null
        } finally {
          loading.value = false
        }
      }
  
      const formatPrice = (row, column, value) => {
        return value?.toFixed(2) || '0.00'
      }
  
      const formatVolume = (row, column, value) => {
        return value?.toLocaleString() || '0'
      }
  
      const formatChange = (row, column, value) => {
        return `${value?.toFixed(2) || '0.00'}%`
      }
  
      // Function to sync stock data
      const syncStockData = async () => {
        if (!syncDateRange.value || syncDateRange.value.length !== 2) {
          ElMessage.error('Please select a valid date range')
          return
        }

        try {
          const startDate = dayjs(syncDateRange.value[0]).format('YYYY-MM-DD')
          const endDate = dayjs(syncDateRange.value[1]).format('YYYY-MM-DD')

          // Fetch available stocks
          const availableStocksResponse = await fetch('/api/stocks/available')
          const availableStocks = await availableStocksResponse.json()

          if (!Array.isArray(availableStocks) || availableStocks.length === 0) {
            ElMessage.error('No available stocks found')
            return
          }

          // Show progress dialog
          const messageBoxInstance = ElMessageBox.alert('Syncing stock data...', 'Progress', {
            showClose: false,
            closeOnClickModal: false,
            closeOnPressEscape: false,
            showCancelButton: false,
            showConfirmButton: false,
          })

          // Sync data for each stock
          for (const stock of availableStocks) {
            try {
              const response = await fetch('/api/stocks/sync', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  ts_code: stock.ts_code,
                  startDate,
                  endDate,
                }),
              })

              if (!response.ok) {
                throw new Error(`Failed to sync data for ${stock.ts_code}`)
              }

              // Update progress message
              ElMessageBox.close()
              ElMessageBox.alert(`Synced data for ${stock.ts_code}`, 'Progress', {
                showClose: false,
                closeOnClickModal: false,
                closeOnPressEscape: false,
                showCancelButton: false,
                showConfirmButton: false,
              })
            } catch (error) {
              console.error(`Error syncing data for ${stock.ts_code}:`, error)
            }
          }

          // Close progress dialog
          ElMessageBox.close()

          ElMessage.success('Stock data synced successfully')
          showSyncDialog.value = false
          loadStocks() // Reload stocks after syncing
        } catch (error) {
          console.error('Error syncing stock data:', error)
          ElMessage.error('Failed to sync stock data')
        }
      }
  
      // Function to add a new stock
      const addNewStock = async () => {
        if (!newStock.value) {
          // Show an error message
          return
        }

        try {
          await apiAddStock(newStock.value)
          // Show success message
          showAddStockDialog.value = false
          loadStocks() // Reload stocks after adding
        } catch (error) {
          // Show error message
        }
      }
  
      // Load available stocks for adding
      const loadAvailableStocks = async () => {
        loadingAvailableStocks.value = true
        try {
          availableStocks.value = await fetchAvailableStocks()
        } catch (error) {
          // Handle error (e.g., show error message)
        } finally {
          loadingAvailableStocks.value = false
        }
      }
  
      const handleStockChange = async (value) => {
        selectedStock.value = value
        if (value) {
          // 找到选中的股票对象
          const selectedStockObj = stockOptions.value
            .flatMap(exchange => exchange.children)
            .flatMap(industry => industry.children)
            .find(stock => stock.code === value)

          if (selectedStockObj) {
            console.log('Selected stock:', selectedStockObj)
            await loadStockData(selectedStockObj.code)
          }
        } else {
          stockData.value = null
        }
      }
  
      const filterStocks = computed(() => {
        // Your filtering logic here
        return stocks.value
      })
  
      onMounted(() => {
        loadStocks()
      })
  
      watch(stocks, (newStocks) => {
        if (newStocks.length > 0 && !selectedStock.value) {
          selectedStock.value = newStocks[0].code
          handleGranularityChange()
        }
      })
  
      // Call loadAvailableStocks when the dialog is opened
      watch(showAddStockDialog, (newValue) => {
        if (newValue) {
          loadAvailableStocks()
        }
      })
  
      return {
        stocks,
        selectedStock,
        stockData,
        loading,
        error,
        timeGranularity,
        dateRange,
        selectedWeek,
        selectedMonth,
        selectedYear,
        handleGranularityChange,
        loadStockData,
        formatPrice,
        formatVolume,
        formatChange,
        showSyncDialog,
        showAddStockDialog,
        syncDateRange,
        newStock,
        newStockMarket,
        filteredAvailableStocks,
        loadingAvailableStocks,
        syncStockData,
        addNewStock,
        stockOptions,
        cascaderProps,
        handleStockChange,
        loadingStocks,
        t  // 将 t 函数添加到返回对象中
      }
    }
  }
  </script>
