<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-3xl font-bold mb-8">{{ $t(`categories.${categoryId}`) }}</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div v-for="strategy in categoryStrategies" :key="strategy.id">
        <StrategyCard :strategy="strategy" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import StrategyCard from '@/components/StrategyCard.vue'

const route = useRoute()
const categoryId = computed(() => route.params.id)

// 这里添加获取分类策略的逻辑
const categoryStrategies = ref([
  // 示例数据，实际应该从API获取
  {
    id: 'strategy1',
    name: 'Strategy 1',
    description: 'Description 1',
    updatedAt: '2024-03-20',
    tags: ['trend'],
    usageCount: 100,
    isFavorite: false
  },
  // ... more strategies
])
</script> 