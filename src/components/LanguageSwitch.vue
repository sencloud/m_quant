<template>
  <el-dropdown @command="handleCommand">
    <span class="flex items-center cursor-pointer">
      {{ currentLocale === 'en' ? 'English' : '中文' }}
      <el-icon class="ml-1"><arrow-down /></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="en">English</el-dropdown-item>
        <el-dropdown-item command="zh">中文</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { ElConfigProvider } from 'element-plus'

const { locale } = useI18n()
const currentLocale = computed(() => locale.value)

const handleCommand = (command) => {
  locale.value = command
  // 更新 Element Plus 的语言配置
  ElConfigProvider.config.locale = command === 'zh' ? zhCn : en
}

// 监听语言变化，更新 Element Plus 的语言配置
watch(currentLocale, (newLocale) => {
  ElConfigProvider.config.locale = newLocale === 'zh' ? zhCn : en
})
</script>