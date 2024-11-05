<template>
  <el-collapse v-model="activeFactorPanels" class="mb-6">
    <el-collapse-item name="factors">
      <template #title>
        <div class="flex items-center gap-2">
          <el-icon><DataAnalysis /></el-icon>
          <span class="text-lg font-medium">{{ t('stocks.pool.factors.title') }}</span>
        </div>
      </template>
      
      <div class="grid grid-cols-3 gap-4 mt-4">
        <FactorGroup 
          title="fundamental"
          :factors="fundamentalFactors"
          v-model:selected="selectedFactors.fundamental"
          v-model:weights="factorWeights"
        />
        <FactorGroup 
          title="technical"
          :factors="technicalFactors"
          v-model:selected="selectedFactors.technical"
          v-model:weights="factorWeights"
        />
        <FactorGroup 
          title="volume"
          :factors="volumeFactors"
          v-model:selected="selectedFactors.volume"
          v-model:weights="factorWeights"
        />
      </div>

      <FactorPresets @apply="applyPreset" />
      <FactorActions 
        @reset="resetFactors" 
        @apply="handleFactorFilter"
        :loading="loading"
      />
    </el-collapse-item>
  </el-collapse>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useStocksStore } from '@/stores/stocks'
import FactorGroup from './FactorGroup.vue'
import FactorPresets from './FactorPresets.vue'
import FactorActions from './FactorActions.vue'
import { 
  fundamentalFactors, 
  technicalFactors, 
  volumeFactors 
} from '@/constants/factors'
import { applyFactorFilter } from '@/api/stocks'

const { t } = useI18n()
const store = useStocksStore()

const activeFactorPanels = ref(['factors'])
const loading = ref(false)

const selectedFactors = reactive({
  fundamental: [],
  technical: [],
  volume: []
})

const factorWeights = ref({})

const resetFactors = () => {
  selectedFactors.fundamental = []
  selectedFactors.technical = []
  selectedFactors.volume = []
  factorWeights.value = {}
}

// 添加辅助函数来检查因子属于哪个分组
const findFactorGroup = (factorCode) => {
  if (fundamentalFactors.some(f => f.code === factorCode)) {
    return 'fundamental'
  }
  if (technicalFactors.some(f => f.code === factorCode)) {
    return 'technical'
  }
  if (volumeFactors.some(f => f.code === factorCode)) {
    return 'volume'
  }
  return null
}

const applyPreset = (presetName) => {
  console.log('Applying preset:', presetName)
  const preset = store.getFactorPreset(presetName)
  if (preset) {
    console.log('Found preset:', preset)
    updateFactors(preset)
  } else {
    console.warn('No preset found for:', presetName)
  }
}

const handleFactorFilter = async () => {
  loading.value = true
  try {
    const response = await applyFactorFilter({
      factors: selectedFactors,
      weights: factorWeights.value
    })
    
    const stocksData = typeof response === 'string' ? JSON.parse(response) : response
    
    console.log('Parsed stocks data:', stocksData)
    
    if (Array.isArray(stocksData)) {
      store.updateStocks(stocksData)
      ElMessage.success(t('stocks.pool.factors.filterSuccess'))
    } else {
      console.error('Invalid response format:', stocksData)
      ElMessage.error(t('stocks.pool.factors.filterError'))
    }
  } catch (error) {
    console.error('Factor filter error:', error)
    ElMessage.error(t('stocks.pool.factors.filterError'))
  } finally {
    loading.value = false
  }
}

const updateFactors = (factors) => {
  console.log('Updating factors with:', factors)
  
  // Reset current selections
  resetFactors()
  
  // Update factor weights and selections
  Object.entries(factors).forEach(([factorCode, weight]) => {
    // Update weights
    factorWeights.value[factorCode] = weight
    
    // Update selections based on factor group
    const group = findFactorGroup(factorCode)
    if (group) {
      selectedFactors[group].push(factorCode)
    } else {
      console.warn(`Factor ${factorCode} not found in any group`)
    }
  })
  
  console.log('Updated selections:', selectedFactors)
  console.log('Updated weights:', factorWeights.value)
}

// Add defineExpose to make updateFactors available to parent
defineExpose({
  updateFactors,
  presets: store.factorPresets // Assuming presets are stored in the store
})
</script>

<style scoped>
.factor-group {
  @apply p-4 border rounded-lg bg-gray-50;
}
</style> 