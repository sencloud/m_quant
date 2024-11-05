<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="space-y-6">
      <!-- 交易模式选择卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- SimNow模拟配置卡片 -->
        <div class="bg-white rounded-lg shadow p-6 hover:shadow-md cursor-pointer"
             :class="{ 'border-2 border-blue-500': selectedMode === 'simnow' }"
             @click="selectedMode = 'simnow'">
          <h2 class="text-lg font-semibold mb-4">{{ $t('trading.simnow.title') }}</h2>
          <div class="space-y-4">
            <!-- SimNow配置表单 -->
            <el-form v-if="selectedMode === 'simnow'" label-position="top">
              <el-form-item :label="$t('trading.simnow.account')">
                <el-input v-model="simnowConfig.account"></el-input>
              </el-form-item>
              <el-form-item :label="$t('trading.simnow.password')">
                <el-input v-model="simnowConfig.password" type="password"></el-input>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 实盘配置卡片 -->
        <div class="bg-white rounded-lg shadow p-6 hover:shadow-md cursor-pointer"
             :class="{ 'border-2 border-blue-500': selectedMode === 'live' }"
             @click="selectedMode = 'live'">
          <h2 class="text-lg font-semibold mb-4">{{ $t('trading.live.title') }}</h2>
          <div class="space-y-4">
            <!-- 实盘配置表单 -->
            <el-form v-if="selectedMode === 'live'" label-position="top">
              <el-form-item :label="$t('trading.live.account')">
                <el-input v-model="liveConfig.account"></el-input>
              </el-form-item>
              <el-form-item :label="$t('trading.live.password')">
                <el-input v-model="liveConfig.password" type="password"></el-input>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>

      <!-- 开始交易按钮 -->
      <div class="flex justify-center">
        <el-button type="primary" :disabled="!selectedMode" @click="startTrading">
          {{ $t('trading.startButton') }}
        </el-button>
      </div>

      <!-- 日志显示区域 -->
      <div v-if="logs.length" class="bg-white rounded-lg shadow p-4">
        <h3 class="text-lg font-semibold mb-2">{{ $t('trading.logs') }}</h3>
        <div class="h-60 overflow-y-auto bg-gray-50 p-4 rounded">
          <div v-for="(log, index) in logs" :key="index" class="text-sm">
            <span class="text-gray-500">{{ log.timestamp }}</span>
            <span class="ml-2">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedMode = ref('')
const simnowConfig = ref({
  account: '',
  password: ''
})
const liveConfig = ref({
  account: '',
  password: ''
})
const logs = ref([])

const startTrading = () => {
  // 添加开始交易的时间戳
  logs.value.push({
    timestamp: new Date().toLocaleTimeString(),
    message: `开始${selectedMode.value === 'simnow' ? 'SimNow模拟' : '实盘'}交易`
  })
  
  // 这里添加实际的交易逻辑
}
</script> 