<template>
  <div class="flex justify-end mt-4 gap-3">
    <el-button @click="$emit('reset')" plain>
      {{ t('stocks.pool.factors.reset') }}
    </el-button>
    <el-button 
      type="primary" 
      @click="$emit('apply')"
      :loading="loading"
    >
      {{ t('stocks.pool.factors.apply') }}
    </el-button>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['reset', 'apply'])

const { t } = useI18n()
</script> 