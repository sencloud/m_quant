<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Main Strategy Form -->
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-2xl font-bold mb-6">{{ $t('backtest.title') }}</h2>
      
      <el-form :model="form" label-position="top" ref="formRef">
        <!-- Main inputs in one row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <el-form-item 
            :label="$t('backtest.form.strategy')" 
            prop="strategy"
            :rules="[{ required: true, message: $t('backtest.validation.selectStrategy') }]"
          >
            <el-select v-model="form.strategy" :placeholder="$t('backtest.form.strategy')" class="w-full">
              <el-option
                v-for="strategy in strategies"
                :key="strategy.value"
                :label="$t(strategy.label)"
                :value="strategy.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item 
            :label="$t('backtest.form.stock')" 
            prop="stock"
            :rules="[{ required: true, message: $t('backtest.validation.selectStock') }]"
          >
            <el-cascader
              v-model="form.stock"
              :options="stockOptions"
              :props="cascaderProps"
              :placeholder="$t('backtest.form.stock')"
              class="w-full"
              @change="handleStockChange"
              :loading="loadingStocks"
              filterable
              :filter-method="filterStocks"
            />
          </el-form-item>

          <el-form-item 
            :label="$t('backtest.form.dateRange')" 
            prop="dateRange"
            :rules="[{ required: true, message: $t('backtest.validation.selectDateRange') }]"
          >
            <el-date-picker
              v-model="form.dateRange"
              type="daterange"
              :range-separator="$t('calendar.range.separator')"
              :start-placeholder="$t('calendar.range.startDate')"
              :end-placeholder="$t('calendar.range.endDate')"
              value-format="YYYY-MM-DD"
              class="w-full"
            />
          </el-form-item>
        </div>
      </el-form>
    </div>

    <!-- Backtest Settings in a separate card -->
    <div class="bg-white rounded-lg shadow p-4 mt-4">
      <h2 class="text-xl font-bold mb-4">{{ $t('backtest.form.settings') }}</h2>
      
      <el-form :model="form" label-position="top">
        <!-- Capital and Fees Settings -->
        <div class="mb-4">
          <h3 class="text-base font-semibold mb-2">{{ $t('backtest.form.capitalAndFees') }}</h3>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <el-form-item 
              :label="$t('backtest.form.initialCapital')" 
              prop="initialCapital"
              :rules="[{ required: true, message: $t('backtest.validation.initialCapital') }]"
            >
              <el-input-number 
                v-model="form.initialCapital" 
                :min="1000" 
                :step="1000" 
                class="w-full"
              />
            </el-form-item>

            <el-form-item 
              :label="$t('backtest.form.commission')" 
              prop="commission"
            >
              <el-input-number 
                v-model="form.commission" 
                :min="0" 
                :max="1" 
                :step="0.001" 
                :precision="3"
                class="w-full"
              />
            </el-form-item>

            <el-form-item 
              :label="$t('backtest.form.slippage')" 
              prop="slippage"
            >
              <el-input-number 
                v-model="form.slippage" 
                :min="0" 
                :max="1" 
                :step="0.001" 
                :precision="3"
                class="w-full"
              />
            </el-form-item>
          </div>
        </div>

        <!-- Position and Risk Management Settings in one row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Position Settings -->
          <div class="mb-4">
            <h3 class="text-base font-semibold mb-2">{{ $t('backtest.form.position.title') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <el-form-item :label="$t('backtest.form.position.sizeType')">
                <el-select v-model="form.positionSizeType" class="w-full">
                  <el-option :label="$t('backtest.form.position.fixedSize')" value="fixed" />
                  <el-option :label="$t('backtest.form.position.percentageSize')" value="percentage" />
                </el-select>
              </el-form-item>

              <el-form-item :label="$t('backtest.form.position.size')">
                <el-input-number 
                  v-model="form.positionSize" 
                  :min="1"
                  :step="form.positionSizeType === 'fixed' ? 100 : 0.1"
                  :precision="form.positionSizeType === 'fixed' ? 0 : 2"
                  class="w-full"
                />
              </el-form-item>
            </div>
          </div>

          <!-- Risk Management Settings -->
          <div class="mb-4">
            <h3 class="text-base font-semibold mb-2">{{ $t('backtest.form.risk.title') }}</h3>
            <div class="grid grid-cols-3 gap-4">
              <el-form-item :label="$t('backtest.form.risk.stopLoss')">
                <el-input-number 
                  v-model="form.stopLoss" 
                  :min="0"
                  :max="100"
                  :step="0.1"
                  class="w-full"
                />
              </el-form-item>

              <el-form-item :label="$t('backtest.form.risk.takeProfit')">
                <el-input-number 
                  v-model="form.takeProfit" 
                  :min="0"
                  :max="100"
                  :step="0.1"
                  class="w-full"
                />
              </el-form-item>

              <el-form-item :label="$t('backtest.form.risk.trailingStop')">
                <el-input-number 
                  v-model="form.trailingStop" 
                  :min="0"
                  :max="100"
                  :step="0.1"
                  class="w-full"
                />
              </el-form-item>
            </div>
          </div>
        </div>

        <div class="flex justify-end">
          <el-button 
            type="primary" 
            @click="handleBacktest"
            :loading="loading"
          >
            {{ $t('backtest.form.runBacktest') }}
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 添加调试信息显示 -->
    <!-- <div v-if="results" class="bg-white rounded-lg shadow p-6 mb-4">
      <h3>Debug Info:</h3>
      <pre class="whitespace-pre-wrap">{{ JSON.stringify(results, null, 2) }}</pre>
    </div> -->

    <div v-if="results" class="mt-8 space-y-8">
      <!-- Performance Summary -->
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-xl font-semibold mb-6">{{ $t('backtest.results.performance') }}</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <metric-card
            :title="$t('backtest.results.metrics.totalReturn')"
            :value="results.metrics?.totalReturn"
            format="decimal"
          />
          <metric-card
            :title="$t('backtest.results.metrics.winRate')"
            :value="results.metrics?.winRate"
            format="decimal"
          />
          <metric-card
            :title="$t('backtest.results.metrics.sharpeRatio')"
            :value="results.metrics?.sharpeRatio"
            format="decimal"
          />
          <metric-card
            :title="$t('backtest.results.metrics.profitFactor')"
            :value="results.metrics?.profitFactor"
            format="decimal"
          />
        </div>
      </div>

      <!-- Charts -->
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-xl font-semibold mb-6">{{ $t('backtest.results.chart.title') }}</h3>
        <div class="h-96">
          <price-chart 
            :data="results.chartData"
            :trades="results.trades"
          />
        </div>
      </div>

      <!-- Trade List -->
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="text-xl font-semibold mb-6">{{ $t('backtest.results.trades.title') }}</h3>
        <trade-list :trades="results.trades" />
      </div>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      class="mt-4"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import PriceChart from '../components/PriceChart.vue'
import MetricCard from '../components/MetricCard.vue'
import TradeList from '../components/TradeList.vue'

const { t } = useI18n()
const route = useRoute()
const formRef = ref(null)

const form = ref({
  strategy: route.query.strategy || '',
  stock: '',
  dateRange: [],
  // Capital and Fees
  initialCapital: 100000,
  commission: 0.003,
  slippage: 0.001,
  // Position Settings
  positionSizeType: 'fixed',
  positionSize: 100,
  // Risk Management
  stopLoss: 5,
  takeProfit: 10,
  trailingStop: 0
})

const loading = ref(false)
const loadingStocks = ref(false)
const error = ref(null)
const results = ref(null)
const stocks = ref({})
const stockOptions = ref([])

const strategies = [
  { label: 'home.strategies.shortTerm.name', value: 'short_term' },
  { label: 'home.strategies.mediumTerm.name', value: 'medium_term' },
  { label: 'home.strategies.longTerm.name', value: 'long_term' }
]

const cascaderProps = {
  expandTrigger: 'hover',
  checkStrictly: true,
  multiple: false,
  emitPath: false,
  value: 'code',
  label: 'label'
}

const handleBacktest = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    error.value = null
    
    const [startDate, endDate] = form.value.dateRange
    
    const response = await axios.post('/api/backtest', {
      strategy: form.value.strategy,
      stock: form.value.stock,
      startDate,
      endDate,
      initialCapital: form.value.initialCapital,
      commission: form.value.commission,
      slippage: form.value.slippage,
      positionSizeType: form.value.positionSizeType,
      positionSize: form.value.positionSize,
      stopLoss: form.value.stopLoss,
      takeProfit: form.value.takeProfit,
      trailingStop: form.value.trailingStop
    })
    
    // Parse response data if it's a string and handle NaN values
    if (typeof response.data === 'string') {
      try {
        // Replace NaN values with null before parsing
        const cleanedData = response.data.replace(/:\s*NaN\b/g, ': null')
        response.data = JSON.parse(cleanedData)
      } catch (err) {
        console.error('Failed to parse response data:', err)
        console.error('Raw response data:', response.data)
        throw new Error('Invalid response data format')
      }
    }

    // console.log('Parsed response data:', response.data)
    // 检查响应数据结构
    if (!response.data) {
      throw new Error('No data received from server')
    }
    
    // 使用可选链和默认值来安全地处理数据
    const metrics = response.data.metrics || {}
    // console.log('Metrics:', metrics)
    const chartData = response.data.chartData || []
    // console.log('Chart Data:', chartData)
    const trades = response.data.trades || []
    // console.log('Trades:', trades)
    
    // 确保数据格式正确
    results.value = {
      metrics: {
        totalReturn: Number(metrics.totalReturn || 0),
        winRate: Number(metrics.winRate || 0),
        sharpeRatio: Number(metrics.sharpeRatio || 0),
        profitFactor: Number(metrics.profitFactor || 0),
        totalTrades: Number(metrics.totalTrades || 0),
        wonTrades: Number(metrics.wonTrades || 0),
        lostTrades: Number(metrics.lostTrades || 0),
        maxDrawdown: Number(metrics.maxDrawdown || 0)
      },
      chartData: chartData.map(point => ({
        date: point.date,
        close: Number(point.close || 0),
        ma5: point.ma5 ? Number(point.ma5) : null,
        ma10: point.ma10 ? Number(point.ma10) : null,
        ma20: point.ma20 ? Number(point.ma20) : null,
        equity: point.equity ? Number(point.equity) : null
      })),
      trades: trades
    }
    
    // console.log('Processed results:', results.value)
  } catch (err) {
    console.error('Backtest error:', err)
    console.error('Response data:', err.response?.data) // 添加更多错误信息
    if (err.response) {
      error.value = err.response.data.error || t('backtest.error.failed')
    } else {
      error.value = err.message || t('backtest.error.validation')
    }
  } finally {
    loading.value = false
  }
}

const loadStocks = async () => {
  loadingStocks.value = true
  error.value = null
  try {
    const response = await axios.get('/api/stocks')
    stocks.value = response.data
    updateStockOptions()
  } catch (err) {
    console.error('Failed to load stocks:', err)
    error.value = t('backtest.error.loadStocks')
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

const handleStockChange = (value) => {
  form.value.stock = value
}

const filterStocks = (node, keyword) => {
  const { value, label, children } = node
  return (
    value.toLowerCase().indexOf(keyword.toLowerCase()) !== -1 ||
    label.toLowerCase().indexOf(keyword.toLowerCase()) !== -1 ||
    (children && children.some(child => filterStocks(child, keyword)))
  )
}

onMounted(() => {
  loadStocks()
})
</script>



