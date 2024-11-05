<template>
  <el-dialog
    v-model="visible"
    :title="t('stocks.addStockDialog.title')"
    width="30%"
  >
    <el-form>
      <el-form-item :label="t('stocks.addStockDialog.selectMarket')">
        <el-select v-model="market">
          <el-option label="上海证券交易所" value="SH" />
          <el-option label="深圳证券交易所" value="SZ" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('stocks.addStockDialog.selectStock')">
        <el-select 
          v-model="selectedStock" 
          filterable
          :loading="loading"
        >
          <el-option
            v-for="stock in filteredStocks"
            :key="stock.value"
            :label="stock.label"
            :value="stock.value"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleConfirm">
          {{ t('stocks.addStockDialog.add') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStocksStore } from '@/stores/stocks'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'added'])

const { t } = useI18n()
const store = useStocksStore()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const market = ref('SH')
const selectedStock = ref('')
const loading = ref(false)

const filteredStocks = computed(() => {
  return store.availableStocks.filter(stock => stock.market === market.value)
})

const handleCancel = () => {
  visible.value = false
  resetForm()
}

const handleConfirm = async () => {
  if (!selectedStock.value) {
    ElMessage.warning(t('stocks.addStockDialog.selectRequired'))
    return
  }

  try {
    await store.addStock({
      market: market.value,
      code: selectedStock.value
    })
    
    ElMessage.success(t('stocks.addStockDialog.success'))
    emit('added')
    visible.value = false
    resetForm()
  } catch (error) {
    ElMessage.error(t('stocks.addStockDialog.error'))
  }
}

const resetForm = () => {
  market.value = 'SH'
  selectedStock.value = ''
}

watch(visible, async (newVal) => {
  if (newVal) {
    loading.value = true
    try {
      await store.fetchAvailableStocks()
    } catch (error) {
      ElMessage.error(t('stocks.addStockDialog.loadError'))
    } finally {
      loading.value = false
    }
  }
})
</script> 