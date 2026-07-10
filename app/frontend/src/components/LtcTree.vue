<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useAuth } from '../composables/useAuth.js'
import LtcCreateDialog from './admin/LtcCreateDialog.vue'

const props = defineProps({
  currentLtcId: { type: String, default: '' },
})
const emit = defineEmits(['select-ltc'])

const { ltcs, modulesByScope, refresh } = useDashboard()
const { me, refresh: refreshMe } = useAuth()

onMounted(() => { if (!me.value) refreshMe() })

const sortedLtcs = computed(() =>
  (ltcs.value || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
)

const canCreateLtc = computed(() => !!(me.value && (me.value.is_super || me.value.is_pdt_admin)))

function ltcModuleCount(ltcId) {
  // 仅统计本 LTC 自有副本(scope=ltc & ltc_id),与主视图 ltcVisibleModules 一致。
  // 模板池(scope=ltc_template)不再混入。
  return (modulesByScope.value.ltc[ltcId] || []).length
}

const showCreate = ref(false)
const toast = ref('')
function flashToast(msg) { toast.value = msg; setTimeout(() => { toast.value = '' }, 3500) }

async function onCreated({ id, templateCopied, templateErr }) {
  showCreate.value = false
  await refresh()
  emit('select-ltc', id)
  if (templateErr) flashToast(`LTC 已创建,模板拷贝失败:${templateErr}`)
  else if (templateCopied) flashToast('LTC 已创建,模板已拷贝')
  else flashToast('LTC 已创建(未拷贝模板)')
}
</script>

<template>
  <aside class="ltc-tree">
    <div class="section-label">
      <span class="lbl-text">LTC 子项目</span>
      <span class="lbl-count" v-if="sortedLtcs.length">{{ sortedLtcs.length }}</span>
    </div>
    <div v-if="!sortedLtcs.length" class="empty">尚未创建 LTC</div>
    <button
      v-for="l in sortedLtcs"
      :key="l.id"
      type="button"
      class="node ltc"
      :class="{ active: l.id === currentLtcId }"
      v-tooltip="'切换查看该 LTC 子项目'"
      @click="emit('select-ltc', l.id)"
    >
      <span class="node-dot" aria-hidden="true"></span>
      <span class="lbl">{{ l.name }}</span>
      <span class="count" v-tooltip="'该 LTC 下可见模块数(模板 + 自有)'">{{ ltcModuleCount(l.id) }}</span>
    </button>
    <button
      v-if="canCreateLtc"
      type="button"
      class="node create"
      v-tooltip="'创建一个新 LTC,可选从模板复制 6 大类 + 18 示例模块'"
      @click="showCreate = true"
    >
      <span class="icon" aria-hidden="true">+</span>
      <span class="lbl">新建 LTC</span>
    </button>
    <p v-if="toast" class="toast" role="status" aria-live="polite">{{ toast }}</p>

    <LtcCreateDialog
      :open="showCreate"
      @close="showCreate = false"
      @created="onCreated"
    />
  </aside>
</template>

<style scoped>
.ltc-tree {
  border-right: 1px solid var(--border);
  background: var(--panel-soft);
  padding: 16px 10px 12px;
  overflow-y: auto;
  height: 100%;
  font-family: var(--font-sans);
  font-size: 14px;
}

/* ── 节标题 ── */
.section-label {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
  font-family: var(--font-sans);
  font-size: 11.5px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 4px 10px 12px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 10px;
}
.lbl-count {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 1px 7px;
  border-radius: var(--radius-sm);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
  text-transform: none;
}

/* ── LTC 节点:左侧 indicator bar + 微浮起 ── */
.node {
  position: relative;
  display: flex; align-items: center; gap: 9px;
  padding: 8px 10px 8px 14px;
  border-radius: var(--radius);
  cursor: pointer;
  user-select: none;
  margin-bottom: 3px;
  color: var(--text);
  font-weight: 500;
  letter-spacing: 0.01em;
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  font-family: inherit;
  font-size: inherit;
  transition:
    background var(--transition),
    color var(--transition),
    transform 140ms cubic-bezier(0.16, 1, 0.3, 1);
}
.node:focus-visible {
  outline: 2px solid var(--accent-ring);
  outline-offset: -2px;
}
.node::before {
  content: '';
  position: absolute;
  left: 4px; top: 8px; bottom: 8px;
  width: 3px;
  background: transparent;
  border-radius: 2px;
  transition: background var(--transition);
}
.node:hover {
  background: var(--panel);
  transform: translateX(2px);
}
.node:hover::before { background: var(--border-strong); }
.node.active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 700;
}
.node.active::before { background: var(--accent); }

.lbl {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}
.node-dot {
  width: 6px; height: 6px;
  border-radius: 2px;
  background: var(--text-dim);
  flex-shrink: 0;
  transition: background var(--transition), transform var(--transition);
}
.node:hover .node-dot { background: var(--accent); }
.node.active .node-dot { background: var(--accent); transform: scale(1.15); }

.count {
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--panel);
  border: 1px solid var(--border-subtle);
  padding: 2px 8px;
  border-radius: var(--radius);
  min-width: 26px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  transition: color var(--transition), border-color var(--transition), background var(--transition);
}
.node:hover .count { border-color: var(--border); }
.node.active .count {
  color: var(--accent);
  border-color: var(--accent-soft-strong);
  background: var(--panel);
  font-weight: 700;
}

.empty { color: var(--text-muted); font-size: 13px; padding: 10px 12px; }

/* ── 新建 LTC dashed 卡片 ── */
.node.create {
  margin-top: 12px;
  border: 1px dashed var(--border);
  color: var(--text-muted);
  padding: 10px 12px;
  background: transparent;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.node.create::before { display: none; }
.node.create:hover {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: var(--accent);
  border-style: dashed;
  transform: translateX(0) translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.node.create .icon {
  font-size: 16px; font-weight: 400;
  width: 16px; text-align: center;
  color: inherit;
}

.toast {
  margin: 10px 4px 0;
  padding: 7px 11px;
  font-size: 12px;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-soft-strong);
  border-radius: var(--radius);
  letter-spacing: 0.02em;
}

@media (prefers-reduced-motion: reduce) {
  .node:hover { transform: none; }
  .node:hover .node-dot { transform: none; }
  .node.create:hover { transform: none; }
}
</style>
