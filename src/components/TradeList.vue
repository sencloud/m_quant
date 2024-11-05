<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th v-for="header in headers" :key="header.key" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            {{ $t(`backtest.results.trades.${header.key}`) }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="trade in trades" :key="trade.entryDate" :class="getTradeRowClass(trade)">
          <td class="px-6 py-4 whitespace-nowrap">{{ formatDate(trade.entryDate) }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ formatDate(trade.exitDate) }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ trade.type }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ trade.quantity }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ formatPrice(trade.entryPrice) }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ formatPrice(trade.exitPrice) }}</td>
          <td class="px-6 py-4 whitespace-nowrap" :class="getProfitClass(trade.profit)">
            {{ formatProfit(trade.profit) }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap" :class="getProfitClass(trade.returnPct)">
            {{ formatPercentage(trade.returnPct) }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span :class="getStatusClass(trade.status)">
              {{ trade.status }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  trades: {
    type: Array,
    required: true
  }
})

const headers = [
  { key: 'entryDate' },
  { key: 'exitDate' },
  { key: 'type' },
  { key: 'quantity' },
  { key: 'entryPrice' },
  { key: 'exitPrice' },
  { key: 'profit' },
  { key: 'return' },
  { key: 'status' }
]

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

const formatPrice = (price) => {
  if (!price) return '-'
  return price.toFixed(2)
}

const formatProfit = (profit) => {
  if (!profit) return '-'
  return profit > 0 ? `+${profit.toFixed(2)}` : profit.toFixed(2)
}

const formatPercentage = (value) => {
  if (!value) return '-'
  return value > 0 ? `+${value.toFixed(2)}%` : `${value.toFixed(2)}%`
}

const getProfitClass = (value) => {
  if (!value) return ''
  // 盈利显示红色，亏损显示绿色
  return value > 0 ? 'text-red-600' : value < 0 ? 'text-green-600' : ''
}

const getStatusClass = (status) => {
  return {
    'px-2 py-1 text-xs font-medium rounded-full': true,
    'bg-green-100 text-green-800': status === 'CLOSED',
    'bg-yellow-100 text-yellow-800': status === 'OPEN'
  }
}

const getTradeRowClass = (trade) => {
  return {
    'hover:bg-gray-50': true,
    // 盈利显示浅红色背景，亏损显示浅绿色背景
    'bg-red-50': trade.profit > 0,
    'bg-green-50': trade.profit < 0
  }
}
</script>
