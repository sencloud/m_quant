import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { ElLoading } from 'element-plus'
import './style.css'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

const app = createApp(App)
const pinia = createPinia()

// 配置 Element Plus 的语言
app.use(ElementPlus, {
  locale: i18n.global.locale.value === 'zh' ? zhCn : en
})

app.use(pinia)
app.use(router)
app.use(i18n)
app.use(ElLoading)
app.mount('#app')