<template>
  <div class="bg-white rounded-lg shadow p-4">
    <h4 class="text-sm font-medium text-gray-500">{{ title || 'Metric' }}</h4>
    <p class="mt-2 text-2xl font-semibold text-gray-900">
      {{ formattedValue }}
    </p>
  </div>
</template>

<script>
export default {
  props: {
    title: {
      type: String,
      default: ''
    },
    value: {
      type: Number,
      default: 0
    },
    format: {
      type: String,
      default: 'decimal'
    }
  },

  computed: {
    formattedValue() {
      // Handle undefined, null or NaN values
      if (this.value === undefined || this.value === null || isNaN(this.value)) {
        return this.format === 'percent' ? '0.00%' : '0.00'
      }

      if (this.format === 'percent') {
        return `${(this.value * 100).toFixed(2)}%`
      }
      return this.value.toFixed(2)
    }
  }
}
</script>