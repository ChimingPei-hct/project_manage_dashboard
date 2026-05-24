<script setup>
import { computed } from 'vue'

/**
 * LTC 看板模块卡(三级结构第二层)。
 * 模块名背景按 module_color 上色;下方一排子项色块;点击子项触发 emit('edit-sub', sub)。
 * 与 PDT 看板的 ModuleCardGrid 独立(详见 CLAUDE.md 红线)。
 */
const props = defineProps({
  module: { type: Object, required: true },
  entry: { type: Object, default: () => ({}) },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['edit-sub'])

const moduleColor = computed(() => props.entry?.module_color || 'gray')
const subColors = computed(() => props.entry?.sub_items_color || {})
const subs = computed(() => (props.module.sub_items || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)))

function colorOf(sid) { return subColors.value[sid] || 'gray' }
function tipOf(sub) {
  if (!props.canEdit) return `${sub.name} · 查看状态(无编辑权限)`
  return `编辑「${sub.name}」的状态灯与风险说明`
}
</script>

<template>
  <div class="ltc-mod-card">
    <header class="title" :class="`tone-${moduleColor}`">
      <span class="name">{{ module.name }}</span>
    </header>
    <div v-if="subs.length" class="chips">
      <button
        v-for="s in subs"
        :key="s.id"
        type="button"
        class="chip"
        :class="`tone-${colorOf(s.id)}`"
        :disabled="!canEdit"
        v-tooltip="tipOf(s)"
        @click="emit('edit-sub', s)"
      >{{ s.name }}</button>
    </div>
    <div v-else class="empty">无子项</div>
  </div>
</template>

<style scoped>
.ltc-mod-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--panel);
  overflow: hidden;
  display: flex; flex-direction: column;
}
.title {
  padding: 5px 10px;
  font-size: 12.5px; font-weight: 700;
  color: var(--text);
  border-bottom: 1px solid var(--border-subtle);
}
.title.tone-green { background: var(--status-green-bg); color: var(--status-green); }
.title.tone-yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.title.tone-red { background: var(--status-red-bg); color: var(--status-red); }
.title.tone-gray { background: var(--panel-soft); color: var(--text-muted); }

.chips {
  display: flex; flex-wrap: wrap; gap: 4px;
  padding: 6px 8px 8px;
}
.chip {
  font-size: 11.5px; line-height: 1.2;
  padding: 3px 7px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  cursor: pointer;
  font-weight: 500;
  white-space: nowrap;
}
.chip:disabled { cursor: default; }
.chip.tone-green { background: var(--status-green); color: #fff; border-color: var(--status-green); }
.chip.tone-yellow { background: var(--status-yellow); color: #fff; border-color: var(--status-yellow); }
.chip.tone-red { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.chip.tone-gray { background: var(--panel-soft); color: var(--text-muted); border-color: var(--border); }
.chip:not(:disabled):hover { filter: brightness(0.92); }

.empty {
  font-size: 11.5px; color: var(--text-dim);
  padding: 6px 10px 8px;
}
</style>
