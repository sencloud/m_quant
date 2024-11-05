<template>
  <div class="flex items-center justify-between mb-6">
    <h2 class="text-2xl font-bold">{{ t('stocks.title') }}</h2>
    <el-button @click="showSyncDialog = true">
      {{ t('stocks.actions.sync') }}
    </el-button>
    
    <!-- 添加同步数据对话框 -->
    <SyncDataDialog
      v-model="showSyncDialog"
      @sync="handleSync"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import SyncDataDialog from '../dialogs/SyncDataDialog.vue'

const { t } = useI18n()

// 控制对话框显示
const showSyncDialog = ref(false)

// 处理同步数据
const handleSync = async (dateRange) => {
  try {
    await emit('sync', dateRange)
    ElMessage.success(t('stocks.syncDataDialog.success'))
  } catch (error) {
    ElMessage.error(t('stocks.syncDataDialog.error'))
  }
}

defineEmits(['sync'])
</script> 