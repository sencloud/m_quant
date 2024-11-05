<template>
  <div class="p-4">
    <div class="mb-3">
      <span class="font-bold mr-2">{{ t('stocks.pool.table.notes') }}:</span>
      <span>{{ stock.notes || t('stocks.pool.noNotes') }}</span>
    </div>
    <div class="flex gap-4">
      <div>
        <span class="font-bold mr-2">{{ t('stocks.pool.table.addedDate') }}:</span>
        <span>{{ formatDate(stock.addedDate) }}</span>
      </div>
      <div>
        <span class="font-bold mr-2">{{ t('stocks.pool.table.lastUpdated') }}:</span>
        <span>{{ formatDate(stock.lastUpdated) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/date'

defineProps({
  stock: {
    type: Object,
    required: true
  }
})

const { t } = useI18n()
</script> 