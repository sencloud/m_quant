<template>
  <el-table
    :data="data"
    style="width: 100%"
    height="500"
    border
    :loading="loading"
    @sort-change="$emit('sort-change', $event)"
  >
    <!-- 日期列 -->
    <el-table-column
      prop="date"
      :label="t('stocks.futures.date')"
      min-width="160"
      fixed="left"
      sortable
    >
      <template #default="{ row }">
        {{ formatTimestamp(row.date) }}
      </template>
    </el-table-column>

    <!-- 价格相关列 -->
    <el-table-column label="价格信息" min-width="500">
      <el-table-column
        prop="preClose"
        :label="t('stocks.futures.preClose')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.preClose) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="preSettle"
        :label="t('stocks.futures.preSettle')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.preSettle) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="open"
        :label="t('stocks.futures.open')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.open) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="high"
        :label="t('stocks.futures.high')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.high) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="low"
        :label="t('stocks.futures.low')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.low) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="close"
        :label="t('stocks.futures.close')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.close) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="settle"
        :label="t('stocks.futures.settle')"
        min-width="100"
        align="right"
      >
        <template #default="{ row }">
          {{ formatPriceWithPrecision(row.settle) }}
        </template>
      </el-table-column>
    </el-table-column>

    <!-- 涨跌幅列 -->
    <el-table-column
      prop="change1"
      :label="t('stocks.futures.priceChange')"
      min-width="120"
      align="right"
      sortable
    >
      <template #default="{ row }">
        <span :class="row.change1 >= 0 ? 'text-red-500' : 'text-green-500'">
          {{ formatPercent(row.change1) }}
        </span>
      </template>
    </el-table-column>

    <!-- 成交量和持仓量列 -->
    <el-table-column label="交易信息" min-width="360">
      <el-table-column
        prop="volume"
        :label="t('stocks.futures.volume')"
        min-width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          {{ formatNumber(row.volume) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="amount"
        :label="t('stocks.futures.amount')"
        min-width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          {{ formatNumber(row.amount, 2) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="openInterest"
        :label="t('stocks.futures.openInterest')"
        min-width="120"
        align="right"
        sortable
      >
        <template #default="{ row }">
          {{ formatNumber(row.openInterest) }}
        </template>
      </el-table-column>
    </el-table-column>

    <!-- 技术视图额外列 -->
    <template v-if="view === 'technical'">
      <el-table-column label="技术指标" min-width="360">
        <el-table-column
          prop="ma5"
          label="MA5"
          min-width="100"
          align="right"
        >
          <template #default="{ row }">
            {{ formatPriceWithPrecision(row.ma5) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="ma10"
          label="MA10"
          min-width="100"
          align="right"
        >
          <template #default="{ row }">
            {{ formatPriceWithPrecision(row.ma10) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="ma20"
          label="MA20"
          min-width="100"
          align="right"
        >
          <template #default="{ row }">
            {{ formatPriceWithPrecision(row.ma20) }}
          </template>
        </el-table-column>
      </el-table-column>
    </template>
  </el-table>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { 
  formatNumber, 
  formatPriceWithPrecision, 
  formatPercent,
  formatTimestamp 
} from '@/utils/formatters'

defineProps({
  data: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  view: {
    type: String,
    default: 'normal'
  }
})

const { t } = useI18n()
</script>

<style scoped>
:deep(.el-table) {
  /* 设置表格最大高度，超出显示滚动条 */
  max-height: calc(100vh - 400px);
}

:deep(.el-table__header) {
  /* 确保表头始终可见 */
  position: sticky;
  top: 0;
  z-index: 1;
}

:deep(.el-table__fixed) {
  /* 确保固定列正确显示 */
  height: 100%;
}

/* 调整列宽度样式 */
:deep(.el-table .cell) {
  white-space: nowrap;
  padding-right: 10px;
  padding-left: 10px;
}

/* 数字列右对齐 */
:deep(.el-table .is-right) {
  text-align: right;
}

/* 表头样式 */
:deep(.el-table__header th) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: bold;
  padding: 8px 0;
}

/* 分组表头样式 */
:deep(.el-table__header .el-table__cell--level-0) {
  background-color: #ebeef5;
}
</style> 