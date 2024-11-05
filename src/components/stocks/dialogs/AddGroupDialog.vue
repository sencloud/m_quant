<template>
  <el-dialog
    v-model="visible"
    :title="t('stocks.pool.addGroupDialog.title')"
    width="30%"
  >
    <el-form :model="form" :rules="rules" ref="formRef">
      <el-form-item 
        :label="t('stocks.pool.addGroupDialog.name')"
        prop="name"
      >
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item 
        :label="t('stocks.pool.addGroupDialog.description')"
        prop="description"
      >
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="3"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">
          {{ t('common.cancel') }}
        </el-button>
        <el-button type="primary" @click="handleConfirm">
          {{ t('stocks.pool.addGroupDialog.confirm') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStocksStore } from '@/stores/stocks'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'added'])

const { t } = useI18n()
const store = useStocksStore()
const formRef = ref(null)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const form = ref({
  name: '',
  description: ''
})

const rules = {
  name: [
    { required: true, message: t('stocks.pool.addGroupDialog.nameRequired'), trigger: 'blur' },
    { min: 2, max: 20, message: t('stocks.pool.addGroupDialog.nameLength'), trigger: 'blur' }
  ]
}

const handleCancel = () => {
  visible.value = false
  resetForm()
}

const handleConfirm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    await store.addGroup(form.value)
    
    ElMessage.success(t('stocks.pool.addGroupDialog.success'))
    emit('added')
    visible.value = false
    resetForm()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  }
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.value = {
    name: '',
    description: ''
  }
}
</script> 