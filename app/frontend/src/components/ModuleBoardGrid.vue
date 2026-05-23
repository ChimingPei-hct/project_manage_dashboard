<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { useContactCache, displayName } from '../composables/useContactCache.js'
import { risksOf, subRiskOf } from '../composables/useStatusHelpers.js'
import ModuleStatusDots from './ModuleStatusDots.vue'
import StatusEditDialog from './StatusEditDialog.vue'
import OwnerChip from './OwnerChip.vue'

const props = defineProps({
  modules: { type: Array, default: () => [] },
  ltcId: { type: String, default: '' },
})

const { status, statusKeyOf } = useDashboard()
const { canEdit } = useEditableModules()
const { ensureContacts } = useContactCache()
onMounted(() => { ensureContacts() })

function statusOf(m) { return status.value?.[statusKeyOf(m, props.ltcId)] || null }
function colorOf(m) { return statusOf(m)?.module_color || 'gray' }
function subColor(m, sid) { return statusOf(m)?.sub_items_color?.[sid] || 'gray' }
function hasMismatch(m) {
  if (colorOf(m) !== 'green') return false
  const subs = statusOf(m)?.sub_items_color || {}
  return Object.values(subs).some(c => c && c !== 'green')
}
function firstRiskText(m) { return (risksOf(statusOf(m))[0] || {}).text || '' }
function subTooltip(m, s) {
  const note = subRiskOf(statusOf(m), s.id) || s.risk_note || ''
  const lbl = { red: 'Delay/Block', yellow: '预警', green: '正常', gray: '未填报' }[subColor(m, s.id)]
  return `${s.name} · ${lbl}${note ? '\n' + note : ''}`
}
function editable(m) { return canEdit(m.id, props.ltcId) }

const groups = computed(() => {
  const g = {}
  for (const m of props.modules) {
    const key = m.group || '其他'
    if (!g[key]) g[key] = []
    g[key].push(m)
  }
  return g
})

const editing = ref(null)
const focusSubId = ref('')
function openEdit(m, subId = '') {
  if (!editable(m)) return
  focusSubId.value = subId
  editing.value = m
}
function closeEdit() { editing.value = null; focusSubId.value = '' }

const editingKey = computed(() => editing.value ? statusKeyOf(editing.value, props.ltcId) : '')
const editingStatus = computed(() => editing.value ? statusOf(editing.value) || {} : {})
</script>

<template>
  <div>
    <div v-if="!modules.length" class="empty">该 LTC 下暂无模块,可在管理后台新增模板模块或本 LTC 增量模块。</div>
    <div v-else class="columns">
      <section v-for="(items, group) in groups" :key="group" class="column">
        <header class="col-head">
          <span class="col-title">{{ group }}</span>
        </header>
        <article
          v-for="m in items"
          :key="m.id"
          class="card"
          :class="`tone-${colorOf(m)}`"
        >
          <header class="card-head">
            <span class="name">
              {{ m.name }}
              <span v-if="m.scope === 'ltc_template'" class="tpl-chip" v-tooltip="'PDT 级模板模块,每个 LTC 独立填报状态'">模板</span>
              <span
                v-if="hasMismatch(m)"
                class="warn"
                v-tooltip="'模块绿但子项非绿,请核对一致性'"
              >⚠</span>
            </span>
            <ModuleStatusDots
              :color="colorOf(m)"
              :editable="editable(m)"
              :note="firstRiskText(m)"
              @edit="openEdit(m)"
            />
          </header>
          <div v-if="m.sub_items?.length" class="subs">
            <button
              v-for="s in m.sub_items"
              :key="s.id"
              type="button"
              class="sub-cell"
              :class="[`tone-${subColor(m, s.id)}`, { editable: editable(m) }]"
              :disabled="!editable(m)"
              v-tooltip="subTooltip(m, s)"
              @click="editable(m) && openEdit(m, s.id)"
            >{{ s.name }}</button>
          </div>
          <div v-else-if="m.owner_open_id" class="owner-line"><OwnerChip :open-id="m.owner_open_id" prefix="Owner: " /></div>
        </article>
      </section>
    </div>

    <StatusEditDialog
      :open="!!editing"
      :module="editing"
      :current="editingStatus"
      :status-key="editingKey"
      :focus-sub-id="focusSubId"
      @close="closeEdit"
    />
  </div>
</template>

<style scoped>
.empty { color: var(--text-muted); padding: 32px; text-align: center; }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.column {
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.col-head { display: flex; justify-content: space-between; align-items: baseline; padding: 0 2px 4px; border-bottom: 2px solid var(--accent-soft); }
.col-title { font-size: 13px; font-weight: 700; color: var(--text); letter-spacing: 0.3px; }

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}
.card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--status-gray);
}
.card.tone-green::before { background: var(--status-green); }
.card.tone-yellow::before { background: var(--status-yellow); }
.card.tone-red::before { background: var(--status-red); }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px; }
.name { font-weight: 600; font-size: 13px; display: inline-flex; align-items: center; gap: 4px; }
.tpl-chip {
  font-size: 10px; font-weight: 600;
  color: var(--text-muted);
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  padding: 1px 6px;
  border-radius: 6px;
}
.warn { color: var(--status-yellow); font-size: 14px; }

.subs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 4px;
}
.sub-cell {
  font-size: 11.5px;
  font-weight: 600;
  color: #fff;
  text-align: center;
  padding: 6px 6px;
  border: none;
  border-radius: 6px;
  background: var(--status-gray);
  min-height: 28px;
  line-height: 1.25;
  letter-spacing: 0.2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}
.sub-cell.tone-green { background: var(--status-green); }
.sub-cell.tone-yellow { background: var(--status-yellow); color: #fff; }
.sub-cell.tone-red { background: var(--status-red); }
.sub-cell.tone-gray { background: var(--status-gray); color: var(--text-muted); }
.sub-cell.editable { cursor: pointer; }
.owner-line { font-size: 11px; color: var(--text-muted); }
</style>
