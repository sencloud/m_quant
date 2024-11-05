<template>
  <div class="p-6">
    <PoolHeader />
    <FactorAnalysis 
      ref="factorAnalysisRef"
    />
    <StockPoolTable :stocks="stocks" />
    <AddStockDialog />
    <AddGroupDialog />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import PoolHeader from './pool/PoolHeader.vue'
import FactorAnalysis from './pool/FactorAnalysis.vue'
import StockPoolTable from './pool/StockPoolTable.vue'
import AddStockDialog from './dialogs/AddStockDialog.vue'
import AddGroupDialog from './dialogs/AddGroupDialog.vue'
import { useStocksStore } from '@/stores/stocks'

const factorAnalysisRef = ref(null)
const store = useStocksStore()
const { stocks } = storeToRefs(store)

const handlePresetApply = (presetKey) => {
  const preset = factorAnalysisRef.value?.presets.find(p => p.key === presetKey)
  if (preset) {
    factorAnalysisRef.value.updateFactors(preset.factors)
  }
}
</script> 