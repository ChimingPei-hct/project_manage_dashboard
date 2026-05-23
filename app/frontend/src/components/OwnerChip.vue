<script setup>
/* Owner 头像 + 姓名 chip;参考 oversea_projects 的 admin-avatar 模式。
   头像缺失时降级首字符圆点。 */
import { computed, onMounted } from 'vue'
import { useContactCache, displayName } from '../composables/useContactCache.js'

const props = defineProps({
  openId: { type: String, default: '' },
  fallback: { type: String, default: '未指派' },
  prefix: { type: String, default: '' },          // e.g. "Owner: "
  size: { type: Number, default: 20 },            // px
})

const { ensureContacts, contacts } = useContactCache()
onMounted(() => { ensureContacts() })

const name = computed(() => (props.openId ? displayName(props.openId) : ''))
const avatar = computed(() => {
  if (!props.openId) return ''
  const u = (contacts.value || []).find(x => x.open_id === props.openId)
  return u?.avatar_url || ''
})
const initial = computed(() => (name.value || props.openId || '?').charAt(0))
</script>

<template>
  <span class="owner-chip" v-if="openId">
    <span v-if="prefix" class="prefix">{{ prefix }}</span>
    <span class="avatar" :style="{ width: size + 'px', height: size + 'px' }">
      <img v-if="avatar" :src="avatar" :alt="name" />
      <span v-else class="avatar-fallback">{{ initial }}</span>
    </span>
    <span class="name">{{ name }}</span>
  </span>
  <span v-else class="owner-chip empty">{{ fallback }}</span>
</template>

<style scoped>
.owner-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}
.owner-chip.empty { color: var(--text-muted); font-style: italic; }
.prefix { color: var(--text-muted); }
.avatar {
  display: inline-block;
  border-radius: 6px;
  overflow: hidden;
  background: var(--panel-soft);
  flex-shrink: 0;
  border: 1px solid var(--border-subtle);
}
.avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
.avatar-fallback {
  display: flex; align-items: center; justify-content: center;
  width: 100%; height: 100%;
  font-size: 11px; color: var(--text); background: var(--panel-soft);
}
.name { color: var(--text); font-weight: 500; }
</style>
