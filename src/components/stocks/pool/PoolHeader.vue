<template>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <h2 class="text-2xl font-bold">{{ t('stocks.pool.title') }}</h2>
      <el-select v-model="selectedGroup" class="w-40">
        <el-option label="全部" value="all" />
        <el-option
          v-for="group in stockGroups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>
      <el-input
        v-model="searchQuery"
        :placeholder="t('stocks.pool.search')"
        prefix-icon="Search"
        class="w-60"
      />
    </div>
    <div class="flex gap-3">
      <el-button @click="openAddGroupDialog">
        {{ t('stocks.pool.addGroup') }}
      </el-button>
      <el-button type="primary" @click="openAddStockDialog">
        <el-icon class="mr-1"><Plus /></el-icon>
        {{ t('stocks.pool.addToPool') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
import { useStocksStore } from '@/stores/stocks'

const { t } = useI18n()
const store = useStocksStore()

const selectedGroup = ref('all')
const searchQuery = ref('')

const stockGroups = computed(() => store.groups)

const openAddGroupDialog = () => {
  store.openDialog('addGroup')
}

const openAddStockDialog = () => {
  store.openDialog('addStock')
}

watch([selectedGroup, searchQuery], () => {
  store.updateFilters({
    group: selectedGroup.value,
    search: searchQuery.value
  })
})
</script> 