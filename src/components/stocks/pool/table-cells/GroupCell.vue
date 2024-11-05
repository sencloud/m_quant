<template>
  <el-tag :type="getGroupTagType(value)">
    {{ value }}
  </el-tag>
</template>

<script setup>
defineProps({
  value: {
    type: String,
    required: true
  }
})

const getGroupTagType = (group) => {
  const types = {
    'value': '',
    'growth': 'success',
    'momentum': 'warning',
    'quality': 'info'
  }
  return types[group] || ''
}
</script> 