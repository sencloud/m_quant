<template>
  <div class="mt-4 mb-4 flex items-center gap-4">
    <span class="font-medium">{{ t('stocks.pool.factors.presets.title') }}</span>
    <el-button-group>
      <el-button 
        v-for="preset in presets" 
        :key="preset.key"
        size="small" 
        @click="$emit('apply', preset.key)"
      >
        {{ t(`stocks.pool.factors.presets.${preset.key}`) }}
      </el-button>
    </el-button-group>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const presets = [
  { 
    key: 'value',
    factors: {
      'pe_ttm': 1,
      'pb': 1,
      'ps_ttm': 1,
      'dv_ratio': 1
    }
  },
  { 
    key: 'growth',
    factors: {
      'profit_yoy': 1,
      'income_yoy': 1,
      'roe': 1
    }
  },
  { 
    key: 'momentum',
    factors: {
      'momentum_1m': 1,
      'momentum_3m': 1,
      'momentum_6m': 1,
      'volatility': -1
    }
  },
  { 
    key: 'quality',
    factors: {
      'roe': 1,
      'roa': 1,
      'grossprofit_margin': 1,
      'debt_to_assets': -1
    }
  }
]

defineEmits(['apply'])
// Add this line to export presets
defineExpose({ presets })
</script> 