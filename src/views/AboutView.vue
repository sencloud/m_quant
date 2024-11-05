<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="max-w-4xl mx-auto">
        <!-- 头部区域 -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('about.title') }}</h2>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="prose dark:prose-invert max-w-none">
          <section class="mb-8">
            <h3 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              {{ $t('about.introduction') }}
            </h3>
            <p class="text-gray-600 dark:text-gray-400">{{ $t('about.introText') }}</p>
          </section>

          <section class="mb-8">
            <h3 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              {{ $t('about.features') }}
            </h3>
            <ul class="space-y-2">
              <li v-for="(feature, index) in $t('about.featureList')" 
                :key="index"
                class="text-gray-600 dark:text-gray-400 flex items-center">
                <svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {{ feature }}
              </li>
            </ul>
          </section>

          <section class="mb-8">
            <h3 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              {{ $t('about.contact') }}
            </h3>
            <p class="text-gray-600 dark:text-gray-400">{{ $t('about.contactText') }}</p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template> 