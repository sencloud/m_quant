<template>
  <span :class="getPriceClass(value)">
    {{ formatPrice(value) }}
  </span>
</template>

<script setup>
import { formatPrice } from '@/utils/number'

defineProps({
  value: {
    type: Number,
    required: true
  }
})

const getPriceClass = (value) => {
  if (value > 0) return 'text-red-600'
  if (value < 0) return 'text-green-600'
  return 'text-gray-600'
}
</script> 