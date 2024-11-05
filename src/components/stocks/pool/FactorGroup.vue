<template>
  <div class="factor-group">
    <h3 class="text-lg font-medium mb-3">
      {{ t(`stocks.pool.factors.${title}`) }}
    </h3>
    <div class="space-y-2">
      <template v-for="factor in factors" :key="factor.code">
        <el-tooltip
          :content="factor.description"
          placement="right"
          effect="light"
          :show-after="200"
        >
          <div class="flex items-center justify-between p-2 hover:bg-gray-100 rounded">
            <el-checkbox 
              :model-value="selectedValue.includes(factor.code)"
              :label="factor.code"
              @update:model-value="handleCheckboxChange($event, factor.code)"
            >
              {{ factor.name }}
            </el-checkbox>
            <el-input-number 
              v-if="selectedValue.includes(factor.code)"
              v-model="weights[factor.code]"
              :min="0"
              :max="100"
              size="small"
              class="w-20"
              @change="emitWeightUpdate"
            />
          </div>
        </el-tooltip>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  factors: {
    type: Array,
    required: true
  },
  selected: {
    type: Array,
    default: () => []
  },
  weights: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:selected', 'update:weights'])
const { t } = useI18n()

const selectedValue = ref(props.selected)
const weights = ref(props.weights)

const handleCheckboxChange = (checked, code) => {
  const newSelected = [...selectedValue.value]
  if (checked) {
    newSelected.push(code)
    // 设置默认权重
    weights.value[code] = 50
  } else {
    const index = newSelected.indexOf(code)
    if (index > -1) {
      newSelected.splice(index, 1)
      // 移除权重
      delete weights.value[code]
    }
  }
  selectedValue.value = newSelected
  emitUpdate()
  emitWeightUpdate()
}

const emitUpdate = () => {
  emit('update:selected', selectedValue.value)
}

const emitWeightUpdate = () => {
  emit('update:weights', weights.value)
}

watch(() => props.selected, (newVal) => {
  selectedValue.value = newVal
})

watch(() => props.weights, (newVal) => {
  weights.value = newVal
})
</script> 