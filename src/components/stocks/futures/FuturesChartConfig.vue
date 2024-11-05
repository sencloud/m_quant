<template>
  <div class="mb-4">
    <el-form :inline="true">
      <el-form-item :label="t('stocks.futures.indicators')">
        <el-checkbox-group v-model="selectedIndicators" @change="updateConfig">
          <el-checkbox label="MA">MA</el-checkbox>
          <el-checkbox label="MACD">MACD</el-checkbox>
          <el-checkbox label="KDJ">KDJ</el-checkbox>
          <el-checkbox label="RSI">RSI</el-checkbox>
          <el-checkbox label="VOL">{{ t('stocks.futures.volume') }}</el-checkbox>
          <el-checkbox label="OI">{{ t('stocks.futures.openInterest') }}</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      
      <el-form-item :label="t('stocks.futures.maLines')" v-if="selectedIndicators.includes('MA')">
        <el-select v-model="maLines" multiple collapse-tags @change="updateConfig">
          <el-option v-for="n in [5,10,20,30,60]" :key="n" :label="n" :value="n" />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:config'])

const { t } = useI18n()

const selectedIndicators = ref(['MA', 'VOL'])
const maLines = ref([5, 10, 20])

const updateConfig = () => {
  emit('update:config', {
    indicators: selectedIndicators.value,
    maLines: maLines.value
  })
}

watch(() => props.config, (newConfig) => {
  if (newConfig) {
    selectedIndicators.value = newConfig.indicators || ['MA', 'VOL']
    maLines.value = newConfig.maLines || [5, 10, 20]
  }
}, { deep: true })
</script> 