<script setup>
import { useStocksStore } from '@/stores/stocks'

const store = useStocksStore()

const openAddStockDialog = () => {
  store.openDialog()
}
</script>

<template>
  <div class="pool-header">
    <el-button @click="openAddStockDialog">
      {{ $t('stocks.addStock') }}
    </el-button>
  </div>
</template> 