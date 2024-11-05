<template>
  <div class="bg-white rounded-lg shadow p-6">
    <div class="text-center">
      <div class="h-12 w-12 mx-auto text-indigo-500">
        <i :class="['fas', `fa-${icon}`]"></i>
      </div>
      <h3 class="mt-4 text-lg font-medium text-gray-900">{{ title || 'Feature' }}</h3>
      <p class="mt-2 text-sm text-gray-500">{{ description || 'No description available' }}</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    title: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    },
    icon: {
      type: String,
      default: 'star'
    }
  }
}
</script>