<template>
  <el-table 
    :data="filteredPoolData" 
    style="width: 100%"
    :row-class-name="tableRowClassName"
  >
    <el-table-column type="expand">
      <template #default="props">
        <StockExpandedRow :stock="props.row" />
      </template>
    </el-table-column>
    
    <el-table-column 
      prop="code"
      :label="t('stocks.pool.table.code')"
      width="120"
    />
    
    <el-table-column 
      prop="name"
      :label="t('stocks.pool.table.name')"
      width="150"
    />

    <el-table-column 
      prop="industry"
      :label="t('stocks.pool.table.industry')"
      width="150"
    />

    <el-table-column 
      prop="score"
      :label="t('stocks.pool.table.score')"
      width="120"
    >
      <template #default="{ row }">
        <span :class="{ 
          'text-green-500': row.score > 0,
          'text-red-500': row.score < 0 
        }">
          {{ row.score?.toFixed(2) || '-' }}
        </span>
      </template>
    </el-table-column>

    <!-- 因子值列 -->
    <el-table-column 
      v-for="(value, key) in firstRow?.factors" 
      :key="key"
      :prop="`factors.${key}`"
      :label="t(`stocks.pool.factors.items.${key}`)"
      width="120"
    >
      <template #default="{ row }">
        <template v-if="key === 'total_mv' && row.factors?.[key]">
          {{ (row.factors[key] / 10000).toFixed(2) }}
        </template>
        <template v-else>
          {{ row.factors?.[key]?.toFixed(2) || '-' }}
        </template>
      </template>
    </el-table-column>

    <el-table-column :label="t('stocks.pool.table.actions')" fixed="right">
      <template #default="{ row }">
        <StockActions 
          :stock="row" 
          @view="viewStockDetails"
          @edit="editStockNotes"
          @remove="removeFromPool"
        />
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStocksStore } from '@/stores/stocks'
import StockExpandedRow from './StockExpandedRow.vue'
import StockActions from './StockActions.vue'

const { t } = useI18n()
const store = useStocksStore()

// 获取第一行数据用于动态生成因子列
const firstRow = computed(() => store.filteredStocks[0] || {})

const filteredPoolData = computed(() => store.filteredStocks)

const tableRowClassName = ({ row }) => {
  return row.isHighlighted ? 'highlighted-row' : ''
}

const viewStockDetails = (stock) => {
  store.setSelectedStock(stock)
}

const editStockNotes = (stock) => {
  store.openEditNotesDialog(stock)
}

const removeFromPool = async (stock) => {
  await store.removeStockFromPool(stock)
}
</script>

<style scoped>
.highlighted-row {
  background-color: var(--el-color-primary-light-9);
}
</style> 