<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <!-- 头部区域 -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('blog.title') }}</h2>
          <p class="mt-2 text-gray-600 dark:text-gray-400">{{ $t('blog.subtitle') }}</p>
        </div>
        <router-link 
          :to="{ name: 'CreateBlog' }" 
          class="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md shadow-sm transition-colors duration-200"
        >
          <i class="fas fa-plus mr-2"></i>
          {{ $t('blog.createNew') }}
        </router-link>
      </div>

      <!-- 文章列表区域 -->
      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div v-for="post in posts" :key="post.id" 
          class="bg-gray-50 dark:bg-gray-700 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <router-link :to="{ name: 'BlogPost', params: { id: post.id }}" 
            class="block h-full">
            <div class="p-6">
              <!-- 文章类别标签 -->
              <div class="flex gap-2 mb-4">
                <span v-for="tag in post.tags" :key="tag"
                  class="px-2 py-1 text-xs rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100">
                  {{ tag }}
                </span>
              </div>
              
              <!-- 文章标题和摘要 -->
              <h2 class="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                {{ post.title }}
              </h2>
              <p class="text-gray-600 dark:text-gray-400 text-sm mb-4">
                {{ post.summary }}
              </p>
              
              <!-- 文章信息 -->
              <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                <div class="flex items-center">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {{ new Date(post.date).toLocaleDateString() }}
                </div>
                <div class="flex items-center">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  {{ post.readTime }} {{ $t('blog.minuteRead') }}
                </div>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const posts = ref([
  {
    id: 1,
    title: '量化交易策略优化指南',
    date: '2024-03-20',
    summary: '探讨如何优化您的量化交易策略，提高回测效果和实盘表现...',
    tags: ['量化交易', '策略优化'],
    readTime: 5
  },
  {
    id: 2,
    title: 'AI在股票市场中的应用',
    date: '2024-03-19',
    summary: '深入分析人工智能技术如何改变传统的股票市场交易方式...',
    tags: ['AI', '市场分析'],
    readTime: 8
  },
  {
    id: 3,
    title: '技术分析基础入门',
    date: '2024-03-18',
    summary: '从零开始学习股票技术分析，掌握基本的图表分析方法...',
    tags: ['技术分析', '入门指南'],
    readTime: 6
  }
])

onMounted(async () => {
  // 后续从API获取文章列表
})
</script> 