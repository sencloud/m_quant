<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <article class="max-w-4xl mx-auto">
        <header class="mb-8">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">{{ post.title }}</h1>
          <div class="flex items-center text-gray-600 dark:text-gray-400">
            <span class="flex items-center">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {{ new Date(post.date).toLocaleDateString() }}
            </span>
          </div>
        </header>

        <img v-if="post.cover" :src="post.cover" :alt="post.title" 
          class="w-full h-64 object-cover rounded-lg mb-8">

        <div class="prose dark:prose-invert max-w-none">
          {{ post.content }}
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const post = ref({})

onMounted(async () => {
  // 后续从API获取文章详情
  // const response = await fetch(`/api/posts/${route.params.id}`)
  // post.value = await response.json()
  
  // 临时测试数据
  post.value = {
    id: route.params.id,
    title: '示例文章详情',
    date: '2024-03-20',
    content: '这里是文章的详细内容...',
    cover: '/images/sample-cover.jpg'
  }
})
</script> 