<template>
  <el-dialog
    v-model="visible"
    :title="t('stocks.syncDataDialog.title')"
    width="30%"
  >
    <el-form>
      <el-form-item :label="t('stocks.syncDataDialog.dateRange')">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          :start-placeholder="t('calendar.range.startDate')"
          :end-placeholder="t('calendar.range.endDate')"
          :range-separator="t('calendar.range.separator')"
          :disabled-date="disabledDate"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">
          {{ t('stocks.syncDataDialog.cancel') }}
        </el-button>
        <el-button 
          type="primary" 
          @click="handleConfirm"
          :loading="syncing"
        >
          {{ t('stocks.syncDataDialog.confirm') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { syncStockData } from '@/api/backtest'
import { useStocksStore } from '@/stores/stocks'

const props = defineProps({
  modelValue: Boolean,
  stockSymbol: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()
const store = useStocksStore()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dateRange = ref([])
const syncing = ref(false)

const disabledDate = (date) => {
  return date > dayjs().endOf('day')
}

const handleCancel = () => {
  visible.value = false
  resetForm()
}

const handleConfirm = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning(t('stocks.syncDataDialog.dateRequired'))
    return
  }

  syncing.value = true
  try {
    await syncStockData({
      code: props.stockSymbol,
      startDate: dayjs(dateRange.value[0]).format('YYYY-MM-DD'),
      endDate: dayjs(dateRange.value[1]).format('YYYY-MM-DD')
    })
    
    ElMessage.success(t('stocks.syncDataDialog.success'))
    await store.updateStocks()
    
    visible.value = false
    resetForm()
  } catch (error) {
    console.error('Sync error:', error)
    ElMessage.error(error.message || t('stocks.syncDataDialog.error'))
  } finally {
    syncing.value = false
  }
}

const resetForm = () => {
  dateRange.value = []
}
</script> 