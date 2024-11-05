<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Favorites Section -->
    <section class="mb-16">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('home.favorites') }}</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div v-for="strategy in favoriteStrategies" :key="strategy.id" class="strategy-card">
          <StrategyCard :strategy="strategy" />
        </div>
      </div>
    </section>

    <!-- Categories Section -->
    <section class="mb-16">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('home.categories') }}</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
        <router-link
          v-for="category in categories"
          :key="category.id"
          :to="{ name: 'Category', params: { id: category.id }}"
          class="group relative overflow-hidden bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-300"
        >
          <div class="aspect-w-16 aspect-h-9 p-6">
            <div class="flex flex-col items-center justify-center space-y-3">
              <div class="w-12 h-12 flex items-center justify-center rounded-full bg-indigo-50 group-hover:bg-indigo-100 transition-colors duration-300">
                <i :class="category.icon" class="text-xl text-indigo-600"></i>
              </div>
              <span class="text-gray-900 font-medium group-hover:text-indigo-600 transition-colors duration-300">
                {{ $t(category.name) }}
              </span>
              <span class="text-sm text-gray-500">
                {{ category.count }} {{ $t('common.strategies') }}
              </span>
            </div>
          </div>
          <div class="absolute inset-0 border-2 border-transparent group-hover:border-indigo-100 rounded-xl transition-colors duration-300"></div>
        </router-link>
      </div>
    </section>

    <!-- All Strategies Section -->
    <section>
      <h2 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('home.allStrategies') }}</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div v-for="strategy in strategies" :key="strategy.id" class="strategy-card">
          <StrategyCard :strategy="strategy" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StrategyCard from '@/components/StrategyCard.vue'

const categories = ref([
  { 
    id: 'trend', 
    name: 'categories.trend',
    icon: 'fas fa-chart-line',
    count: 12
  },
  { 
    id: 'momentum', 
    name: 'categories.momentum',
    icon: 'fas fa-rocket',
    count: 8
  },
  { 
    id: 'value', 
    name: 'categories.value',
    icon: 'fas fa-coins',
    count: 15
  },
  { 
    id: 'volatility', 
    name: 'categories.volatility',
    icon: 'fas fa-chart-bar',
    count: 10
  },
  { 
    id: 'mean_reversion', 
    name: 'categories.mean_reversion',
    icon: 'fas fa-retweet',
    count: 6
  },
  { 
    id: 'arbitrage', 
    name: 'categories.arbitrage',
    icon: 'fas fa-balance-scale',
    count: 9
  },
  { 
    id: 'ml', 
    name: 'categories.ml',
    icon: 'fas fa-brain',
    count: 7
  },
  { 
    id: 'fundamental', 
    name: 'categories.fundamental',
    icon: 'fas fa-search-dollar',
    count: 11
  }
])

const strategies = ref([
  {
    id: 'short_term',
    name: 'home.strategies.shortTerm.name',
    description: 'home.strategies.shortTerm.description',
    updatedAt: '2024-03-20',
    tags: ['trend', 'momentum'],
    usageCount: 1234,
    isFavorite: true
  },
  // ... other strategies
])

const favoriteStrategies = computed(() => 
  strategies.value.filter(strategy => strategy.isFavorite)
)
</script>

<style scoped>
.aspect-w-16 {
  position: relative;
  padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
}

.aspect-w-16 > div {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}
</style>