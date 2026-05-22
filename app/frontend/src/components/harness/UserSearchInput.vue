<template>
  <!--
    harness/UserSearchInput — 纯哑通用用户搜索输入框
    Props: modelValue, users(必传), placeholder, disabled, autofocus, loading
    Events: update:modelValue, select(user)
    搜索:中文/英文子串 + 全拼 + 拼音首字母 + 部门子串
  -->
  <div class="user-search-wrap" @click.stop>
    <input
      ref="inputRef"
      v-model="query"
      :placeholder="placeholder"
      :disabled="disabled"
      type="text"
      autocomplete="off"
      class="user-search-input"
      @input="onInput"
      @focus="onFocus"
      @keydown="onKeydown"
    />
    <div v-if="showDropdown && results.length" class="user-search-dropdown">
      <div
        v-for="(u, i) in results"
        :key="u.open_id || u.id || i"
        class="user-search-item"
        :class="{ active: i === activeIdx }"
        @mousedown.prevent="select(u)"
        @mouseenter="activeIdx = i"
      >
        <img v-if="u.avatar_url" :src="u.avatar_url" class="user-avatar-sm" />
        <div v-else class="user-avatar-fallback">{{ (u.name || '?').charAt(0) }}</div>
        <div class="user-info">
          <div class="user-name">{{ u.name }}</div>
          <div v-if="u.department" class="user-dept">{{ u.department }}</div>
        </div>
      </div>
    </div>
    <div v-else-if="showDropdown && query && !loading" class="user-search-dropdown">
      <div class="user-search-empty">未找到匹配用户</div>
    </div>
    <div v-else-if="showDropdown && loading && !users.length" class="user-search-dropdown">
      <div class="user-search-empty">加载中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { pinyin } from 'pinyin-pro'

const props = defineProps({
  modelValue: { type: String, default: '' },
  users: { type: Array, required: true },
  placeholder: { type: String, default: '搜索用户姓名...' },
  disabled: { type: Boolean, default: false },
  autofocus: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'select', 'request-load'])

const query = ref(props.modelValue || '')
const showDropdown = ref(false)
const activeIdx = ref(0)
const inputRef = ref(null)
const userNavigated = ref(false)  // 用户是否用方向键浏览过(决定 Enter 是否敢自动选)

function matchPinyin(text, q) {
  if (!text) return false
  const lower = text.toLowerCase()
  if (lower.includes(q)) return true
  if (!/[一-龥]/.test(text)) return false
  const full = pinyin(text, { toneType: 'none', type: 'array', nonZh: 'consecutive' }).join('').toLowerCase()
  if (full.includes(q)) return true
  const initials = pinyin(text, { pattern: 'first', toneType: 'none', type: 'array', nonZh: 'consecutive' }).join('').toLowerCase()
  return initials.includes(q)
}

const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.users.slice(0, 20)
  return props.users.filter(u => {
    if (matchPinyin(u.name || '', q)) return true
    if ((u.department || '').toLowerCase().includes(q)) return true
    return false
  }).slice(0, 30)
})

watch(() => props.modelValue, v => { if (v !== query.value) query.value = v || '' })

function onInput() {
  emit('update:modelValue', query.value)
  showDropdown.value = true
  activeIdx.value = 0
  userNavigated.value = false  // 输入新内容,清空"已浏览"标记
  emit('request-load')
}

function onFocus() {
  showDropdown.value = true
  emit('request-load')
}

function onKeydown(e) {
  if (!showDropdown.value || !results.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault(); userNavigated.value = true
    activeIdx.value = (activeIdx.value + 1) % results.value.length
  }
  else if (e.key === 'ArrowUp') {
    e.preventDefault(); userNavigated.value = true
    activeIdx.value = (activeIdx.value - 1 + results.value.length) % results.value.length
  }
  else if (e.key === 'Enter') {
    const q = query.value.trim()
    const item = results.value[activeIdx.value]
    if (!item) return
    // 安全开关:防止用户没浏览/没明确意图时,Enter 误选第一条
    //  - query 为空 → 永远不自动选(避免聚焦后随手回车把第一个通讯录人填进去)
    //  - 用户没用过方向键 → 仅当(精确名字命中) OR (结果只剩 1 条)时才视为"明确选这个"
    //  - 用过方向键 → 信任 activeIdx
    const exactMatch = item.name && item.name.toLowerCase() === q.toLowerCase()
    const onlyOne = results.value.length === 1
    if (!q) return  // 空 query 时 Enter 让浏览器/外层处理(比如提交表单),不抢
    if (!userNavigated.value && !exactMatch && !onlyOne) return
    e.preventDefault(); select(item)
  }
  else if (e.key === 'Escape') { showDropdown.value = false }
}

function select(u) {
  if (!u || !u.name) return
  query.value = u.name
  emit('update:modelValue', u.name)
  emit('select', u)
  showDropdown.value = false
}

function hide() { showDropdown.value = false }

onMounted(() => {
  document.addEventListener('click', hide)
  if (props.autofocus && inputRef.value) inputRef.value.focus()
})
onUnmounted(() => document.removeEventListener('click', hide))

defineExpose({ focus: () => inputRef.value?.focus() })
</script>

<style scoped>
.user-search-wrap { position: relative; }
.user-search-input { width: 100%; padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; box-sizing: border-box; }
.user-search-input:focus { outline: none; border-color: #4f6ef7; box-shadow: 0 0 0 2px rgba(79,110,247,0.15); }
.user-search-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0; max-height: 260px; overflow-y: auto;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08); z-index: 1000;
}
.user-search-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; cursor: pointer; transition: background 0.12s; }
.user-search-item.active, .user-search-item:hover { background: #f3f4f6; }
.user-avatar-sm { width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0; }
.user-avatar-fallback {
  width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #60a5fa, #8b5cf6);
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 13px; color: #111827; line-height: 1.3; }
.user-dept { font-size: 11px; color: #6b7280; line-height: 1.3; margin-top: 1px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-search-empty { padding: 12px; text-align: center; color: #9ca3af; font-size: 12px; }
</style>
