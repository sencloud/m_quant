<template>
  <el-table 
    :data="data"
    style="width: 100%"
    :default-sort="{ prop: 'date', order: 'descending' }"
    height="400"
  >
    <el-table-column 
      prop="date" 
      :label="t('stocks.table.date')" 
      sortable 
      width="180" 
    />
    <el-table-column 
      prop="open" 
      :label="t('stocks.table.open')" 
      :formatter="formatPrice" 
    />
    <el-table-column 
      prop="high" 
      :label="t('stocks.table.high')" 
      :formatter="formatPrice" 
    />
    <el-table-column 
      prop="low" 
      :label="t('stocks.table.low')" 
      :formatter="formatPrice" 
    />
    <el-table-column 
      prop="close" 
      :label="t('stocks.table.close')" 
      :formatter="formatPrice" 
    />
    <el-table-column 
      prop="volume" 
      :label="t('stocks.table.volume')" 
      :formatter="formatVolume" 
    />
    <el-table-column 
      prop="change" 
      :label="t('stocks.table.change')" 
    >
      <template #default="{ row }">
        <span :class="getPriceChangeClass(row.change)">
          {{ formatChange(row.change) }}
        </span>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { formatPrice, formatVolume, formatChange } from '@/utils/formatters'

defineProps({
  data: {
    type: Array,
    required: true
  }
})

const { t } = useI18n()

const getPriceChangeClass = (change) => {
  if (change > 0) return 'text-red-600'
  if (change < 0) return 'text-green-600'
  return 'text-gray-600'
}
</script> 