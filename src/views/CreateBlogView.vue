<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ $t('blog.create.title') }}
        </h1>
      </div>

      <!-- 文章表单 -->
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- 标题输入 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('blog.create.titleLabel') }}
          </label>
          <input
            v-model="formData.title"
            type="text"
            required
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600"
          />
        </div>

        <!-- 标签选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('blog.create.tagsLabel') }}
          </label>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="tag in availableTags"
              :key="tag"
              @click="toggleTag(tag)"
              :class="[
                'px-3 py-1 rounded-full text-sm cursor-pointer transition-colors duration-200',
                formData.tags.includes(tag)
                  ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              ]"
            >
              {{ tag }}
            </div>
          </div>
        </div>

        <!-- Markdown编辑器 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {{ $t('blog.create.contentLabel') }}
          </label>
          <div class="border border-gray-300 rounded-md dark:border-gray-600">
            <div class="flex border-b border-gray-300 dark:border-gray-600">
              <button
                v-for="tab in ['write', 'preview']"
                :key="tab"
                @click="activeTab = tab"
                :class="[
                  'px-4 py-2 text-sm font-medium',
                  activeTab === tab
                    ? 'text-indigo-600 border-b-2 border-indigo-600'
                    : 'text-gray-500 hover:text-gray-700'
                ]"
                type="button"
              >
                {{ $t(`blog.create.${tab}`) }}
              </button>
            </div>
            
            <div class="p-4">
              <textarea
                v-if="activeTab === 'write'"
                v-model="formData.content"
                rows="12"
                class="w-full p-2 border-0 focus:ring-0 dark:bg-gray-700"
                :placeholder="$t('blog.create.contentPlaceholder')"
              ></textarea>
              <div
                v-else
                class="prose dark:prose-invert max-w-none"
                v-html="renderedContent"
              ></div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex justify-end space-x-4">
          <button
            type="button"
            @click="$router.back()"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600"
          >
            {{ $t('common.cancel') }}
          </button>
          <button
            type="submit"
            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
          >
            {{ $t('blog.create.publish') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()
const activeTab = ref('write')

const formData = ref({
  title: '',
  content: '',
  tags: []
})

const availableTags = [
  '量化交易',
  '策略优化',
  'AI',
  '市场分析',
  '技术分析',
  '入门指南'
]

const renderedContent = computed(() => {
  return DOMPurify.sanitize(marked(formData.value.content))
})

const toggleTag = (tag) => {
  const index = formData.value.tags.indexOf(tag)
  if (index === -1) {
    formData.value.tags.push(tag)
  } else {
    formData.value.tags.splice(index, 1)
  }
}

const handleSubmit = async () => {
  try {
    // TODO: 实现文章发布逻辑
    console.log('Publishing:', formData.value)
    // await publishBlog(formData.value)
    router.push({ name: 'Blog' })
  } catch (error) {
    console.error('Failed to publish blog:', error)
  }
}
</script> 