<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <router-link to="/" class="flex items-center space-x-2">
              <img 
                src="@/assets/img/logo.png" 
                alt="Logo" 
                class="w-8 h-8 object-contain"
              />
              <span class="text-xl font-bold text-gray-900">{{ $t('home.title') }}</span>
            </router-link>
            <div class="ml-10 flex items-center space-x-4">
              <router-link to="/" class="nav-link">{{ $t('nav.home') }}</router-link>
              <router-link to="/stocks" class="nav-link">{{ $t('nav.stocks') }}</router-link>
              <router-link to="/backtest" class="nav-link">{{ $t('nav.backtest') }}</router-link>
              <router-link to="/ai" class="nav-link">{{ $t('nav.ai') }}</router-link>
              <router-link to="/trading" class="nav-link">{{ $t('nav.trading') }}</router-link>
              <router-link to="/blog" class="nav-link">{{ $t('nav.blog') }}</router-link>
              <router-link to="/about" class="nav-link">{{ $t('nav.about') }}</router-link>
            </div>
          </div>
          <div class="flex items-center">
            <LanguageSwitch />
          </div>
        </div>
      </div>
    </nav>
    <Suspense>
      <template #default>
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </template>
      <template #fallback>
        <div class="flex justify-center items-center h-64">
          <p>Loading...</p>
        </div>
      </template>
    </Suspense>
  </div>
</template>

<script setup>
import LanguageSwitch from './components/LanguageSwitch.vue'
</script>

<style>
.nav-link {
  @apply px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100;
}
.nav-link.router-link-active {
  @apply bg-gray-100 text-gray-900;
}
</style>