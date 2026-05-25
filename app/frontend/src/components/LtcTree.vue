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
    <div
      v-if="canCreateLtc"
      class="node create"
      v-tooltip="'创建一个新 LTC,可选从模板复制 6 大类 + 18 示例模块'"
      @click="showCreate = true"
    >
      <span class="icon">+</span>
      <span class="lbl">新建 LTC</span>
    </div>
    <p v-if="toast" class="toast">{{ toast }}</p>

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
.node.create {
  margin-top: 8px;
  border: 1px dashed var(--border);
  color: var(--text-muted);
  padding: 8px 10px;
}
.node.create:hover {
  background: var(--panel);
  color: var(--accent);
  border-color: var(--accent);
}
.node.create .icon { font-size: 14px; font-weight: 700; }
.toast {
  margin: 8px 4px 0; padding: 6px 10px;
  font-size: 11.5px; color: var(--accent);
  background: var(--panel); border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
}
</style>
