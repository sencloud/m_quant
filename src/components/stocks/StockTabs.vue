<template>
  <el-tabs v-model="activeTab" class="custom-tabs" type="border-card">
    <el-tab-pane name="pool">
      <template #label>
        <div class="tab-label">
          <el-icon><Collection /></el-icon>
          <span>{{ t('stocks.tabs.pool') }}</span>
        </div>
      </template>
      <StockPool />
    </el-tab-pane>

    <el-tab-pane name="stocks">
      <template #label>
        <div class="tab-label">
          <el-icon><DataLine /></el-icon>
          <span>{{ t('stocks.tabs.stocks') }}</span>
        </div>
      </template>
      <StockAnalysis />
    </el-tab-pane>

    <el-tab-pane name="futures">
      <template #label>
        <div class="tab-label">
          <el-icon><TrendCharts /></el-icon>
          <span>{{ t('stocks.tabs.futures') }}</span>
        </div>
      </template>
      <FuturesAnalysis />
    </el-tab-pane>
  </el-tabs>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Collection, DataLine, TrendCharts } from '@element-plus/icons-vue'
import StockPool from './StockPool.vue'
import StockAnalysis from './StockAnalysis.vue'
import FuturesAnalysis from './FuturesAnalysis.vue'

const { t } = useI18n()
const activeTab = ref('pool')
</script>

<style scoped>
.custom-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.custom-tabs :deep(.el-tabs__nav) {
  border: none;
}

.custom-tabs :deep(.el-tabs__item) {
  height: 50px;
  line-height: 50px;
  padding: 0 25px;
  font-size: 15px;
  border: none;
  transition: all 0.3s;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  background-color: white;
  border-bottom: 2px solid #409eff;
  color: #409eff;
  font-weight: 600;
}

.custom-tabs :deep(.el-tabs__item:hover) {
  color: #409eff;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style> 