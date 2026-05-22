<script setup>
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '点击编辑' },
  type: { type: String, default: 'text' }, // text | number | date
  disabled: { type: Boolean, default: false },
  emptyLabel: { type: String, default: '—' },
  width: { type: String, default: '100%' },
})
const emit = defineEmits(['update:modelValue', 'commit'])

const editing = ref(false)
const draft = ref(props.modelValue ?? '')
const inputRef = ref(null)

watch(() => props.modelValue, v => { if (!editing.value) draft.value = v ?? '' })

async function enter() {
  if (props.disabled) return
  editing.value = true
  draft.value = props.modelValue ?? ''
  await nextTick()
  inputRef.value?.focus()
  inputRef.value?.select?.()
}

function commit() {
  if (!editing.value) return
  editing.value = false
  let val = draft.value
  if (props.type === 'number' && val !== '' && val !== null) val = Number(val)
  if (val !== props.modelValue) {
    emit('update:modelValue', val)
    emit('commit', val)
  }
}

function cancel() {
  editing.value = false
  draft.value = props.modelValue ?? ''
}

function onKey(e) {
  if (e.key === 'Enter') { e.preventDefault(); commit() }
  else if (e.key === 'Escape') { cancel() }
}
</script>

<template>
  <span class="inline-edit" :style="{ width }" :class="{ disabled }">
    <input
      v-if="editing"
      ref="inputRef"
      v-model="draft"
      :type="type"
      :placeholder="placeholder"
      @blur="commit"
      @keydown="onKey"
    />
    <span v-else class="display" @click="enter" v-tooltip="disabled ? '' : '点击编辑'">
      {{ modelValue === '' || modelValue === null || modelValue === undefined ? emptyLabel : modelValue }}
    </span>
  </span>
</template>

<style scoped>
.inline-edit { display: inline-block; }
.inline-edit .display { cursor: pointer; padding: 2px 4px; border-radius: var(--radius-sm); }
.inline-edit .display:hover { background: #f3f4f6; }
.inline-edit.disabled .display { cursor: default; color: var(--text-muted); }
.inline-edit input { width: 100%; padding: 2px 6px; font-size: inherit; }
</style>
