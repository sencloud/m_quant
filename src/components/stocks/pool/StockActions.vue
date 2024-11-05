<template>
  <el-button-group>
    <el-button 
      size="small" 
      @click="$emit('view', stock)"
      :title="t('stocks.pool.view')"
    >
      <el-icon><View /></el-icon>
    </el-button>
    <el-button 
      size="small" 
      @click="$emit('edit', stock)"
      :title="t('stocks.pool.editNotes')"
    >
      <el-icon><Edit /></el-icon>
    </el-button>
    <el-button 
      size="small" 
      type="danger" 
      @click="confirmRemove"
      :title="t('stocks.pool.remove')"
    >
      <el-icon><Delete /></el-icon>
    </el-button>
  </el-button-group>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { View, Edit, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  stock: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['view', 'edit', 'remove'])
const { t } = useI18n()

const confirmRemove = async () => {
  try {
    await ElMessageBox.confirm(
      t('stocks.pool.removeConfirm', { name: props.stock.name }),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    emit('remove', props.stock)
  } catch {
    // User cancelled
  }
}
</script> 