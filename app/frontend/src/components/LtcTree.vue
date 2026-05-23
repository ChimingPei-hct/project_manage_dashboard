<script setup>
import { computed } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'

const props = defineProps({
  currentLtcId: { type: String, default: '' },
})
const emit = defineEmits(['select-pdt', 'select-ltc'])

const { pdt, ltcs, modulesByScope } = useDashboard()

const sortedLtcs = computed(() =>
  (ltcs.value || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
)

function ltcModuleCount(ltcId) {
  const tpl = (modulesByScope.value.ltc_template || []).length
  const own = (modulesByScope.value.ltc[ltcId] || []).length
  return tpl + own
}
</script>

<template>
  <aside class="ltc-tree">
    <div
      class="node root"
      v-tooltip="'返回 PDT 总览页'"
      @click="emit('select-pdt')"
    >
      <span class="icon">📦</span>
      <span class="lbl">{{ pdt?.name || 'PDT' }}</span>
      <span class="badge">PDT</span>
    </div>
    <div class="section-label">LTC 子项目</div>
    <div v-if="!sortedLtcs.length" class="empty">尚未创建 LTC</div>
    <div
      v-for="l in sortedLtcs"
      :key="l.id"
      class="node ltc"
      :class="{ active: l.id === currentLtcId }"
      v-tooltip="'切换查看该 LTC 子项目'"
      @click="emit('select-ltc', l.id)"
    >
      <span class="icon">🔹</span>
      <span class="lbl">{{ l.name }}</span>
      <span class="count" v-tooltip="'该 LTC 下可见模块数(模板 + 自有)'">{{ ltcModuleCount(l.id) }}</span>
    </div>
  </aside>
</template>

<style scoped>
.ltc-tree {
  border-right: 1px solid var(--border);
  background: var(--panel-soft);
  padding: 10px 8px;
  overflow-y: auto;
  height: 100%;
  font-size: 13px;
}
.node {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  user-select: none;
  margin-bottom: 2px;
}
.node:hover { background: var(--panel); }
.node.active {
  background: color-mix(in srgb, var(--accent) 12%, var(--panel));
  color: var(--accent);
  font-weight: 600;
}
.node.root { font-weight: 700; }
.lbl { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.icon { width: 16px; text-align: center; }
.badge {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--panel);
  border: 1px solid var(--border-subtle);
  padding: 1px 6px;
  border-radius: 6px;
}
.count {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--panel);
  border: 1px solid var(--border-subtle);
  padding: 1px 6px;
  border-radius: 6px;
  min-width: 22px;
  text-align: center;
}
.section-label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  padding: 10px 10px 4px;
  letter-spacing: 0.5px;
}
.empty { color: var(--text-muted); font-size: 12px; padding: 8px 10px; }
</style>
