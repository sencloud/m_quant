<template>
  <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
    <h3 class="text-lg font-semibold text-gray-900 mb-2">
      {{ strategy?.name || 'Strategy' }}
    </h3>
    <p class="text-gray-600 mb-4">{{ strategy?.description || 'No description available' }}</p>
    
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="text-center">
        <div class="text-sm text-gray-500">{{ $t('metrics.avgReturn') }}</div>
        <div class="font-semibold text-gray-900">
          {{ formatMetric(strategy?.metrics?.avgReturn, 'percent') }}
        </div>
      </div>
      <div class="text-center">
        <div class="text-sm text-gray-500">{{ $t('metrics.winRate') }}</div>
        <div class="font-semibold text-gray-900">
          {{ formatMetric(strategy?.metrics?.winRate, 'percent') }}
        </div>
      </div>
      <div class="text-center">
        <div class="text-sm text-gray-500">{{ $t('metrics.trades') }}</div>
        <div class="font-semibold text-gray-900">
          {{ strategy?.metrics?.trades || '0' }}
        </div>
      </div>
    </div>

    <button 
      @click="$emit('select', strategy?.id)"
      class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 
             transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
    >
      {{ $t('buttons.tryStrategy') }}
    </button>
  </div>
</template>

<script>
export default {
  props: {
    strategy: {
      type: Object,
      default: () => ({})
    }
  },

  emits: ['select'],

  methods: {
    formatMetric(value, type) {
      if (value === undefined || value === null || isNaN(value)) {
        return type === 'percent' ? '0.00%' : '0.00'
      }

      if (type === 'percent') {
        return typeof value === 'string' ? value : `${(value * 100).toFixed(2)}%`
      }
      return typeof value === 'string' ? value : value.toFixed(2)
    }
  }
}
</script>