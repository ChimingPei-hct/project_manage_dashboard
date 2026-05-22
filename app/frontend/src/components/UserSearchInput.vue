<template>
  <!--
    薄壳:把通讯录注入 harness 版纯哑组件。
    业务方零改动,API 与原版一致。新组件请直接用 harness/UserSearchInput。
  -->
  <HarnessUserSearchInput
    ref="inner"
    :modelValue="modelValue"
    :users="contacts"
    :loading="loading"
    :placeholder="placeholder"
    :disabled="disabled"
    :autofocus="autofocus"
    @update:modelValue="v => $emit('update:modelValue', v)"
    @select="u => $emit('select', u)"
    @request-load="ensureContacts"
  />
</template>

<script setup>
import { ref } from 'vue'
import HarnessUserSearchInput from './harness/UserSearchInput.vue'
import { useContactCache } from '../composables/useContactCache.js'

defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '搜索用户姓名...' },
  disabled: { type: Boolean, default: false },
  autofocus: { type: Boolean, default: false },
})
defineEmits(['update:modelValue', 'select'])

const { contacts, loading, ensureContacts } = useContactCache()
const inner = ref(null)
defineExpose({ focus: () => inner.value?.focus() })
</script>
