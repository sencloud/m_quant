<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <div class="flex justify-between items-start mb-4">
      <h3 class="text-lg font-semibold">{{ $t(strategy.name) }}</h3>
      <button @click="toggleFavorite" class="text-yellow-400 hover:text-yellow-500">
        <i class="fas" :class="strategy.isFavorite ? 'fa-star' : 'fa-star-o'"></i>
      </button>
    </div>
    
    <p class="text-gray-600 mb-4">{{ $t(strategy.description) }}</p>
    
    <div class="flex flex-wrap gap-2 mb-4">
      <span v-for="tag in strategy.tags" :key="tag" 
        class="px-2 py-1 bg-gray-100 text-sm rounded-full text-gray-600">
        {{ $t(`tags.${tag}`) }}
      </span>
    </div>
    
    <div class="flex justify-between items-center text-sm text-gray-500 mb-4">
      <span>{{ $t('common.updated') }}: {{ formatDate(strategy.updatedAt) }}</span>
      <span>{{ $t('common.uses') }}: {{ strategy.usageCount }}</span>
    </div>

    <router-link 
      :to="{ name: 'Backtest', query: { strategy: strategy.id }}"
      class="inline-block w-full text-center bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
    >
      {{ $t('home.strategies.tryStrategy') }}
    </router-link>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  strategy: {
    type: Object,
    required: true
  }
})

const formatDate = (date) => {
  return new Date(date).toLocaleDateString()
}

const toggleFavorite = () => {
  // 实现收藏功能
}
</script> 