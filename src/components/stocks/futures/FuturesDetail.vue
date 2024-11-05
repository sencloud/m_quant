<template>
  <el-descriptions
    :title="t('stocks.futures.contractInfo')"
    :column="3"
    border
  >
    <el-descriptions-item :label="t('stocks.futures.code')">
      {{ contract.code }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('stocks.futures.name')">
      {{ contract.name }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('stocks.futures.market')">
      {{ getMarketName(contract.market) }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('stocks.futures.underlying')">
      {{ contract.underlying }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('stocks.futures.multiplier')">
      {{ contract.multiplier }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('stocks.futures.lastTradeDate')">
      {{ formatDate(contract.lastTradeDate) }}
    </el-descriptions-item>
  </el-descriptions>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/formatters'

const props = defineProps({
  contract: {
    type: Object,
    required: true
  }
})

const { t } = useI18n()

const getMarketName = (market) => {
  const markets = {
    'CFFEX': '中国金融期货交易所',
    'SHFE': '上海期货交易所',
    'DCE': '大连商品交易所',
    'CZCE': '郑州商品交易所'
  }
  return markets[market] || market
}
</script> 