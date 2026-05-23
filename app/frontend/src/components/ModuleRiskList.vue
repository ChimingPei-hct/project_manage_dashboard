<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { useContactCache, displayName } from '../composables/useContactCache.js'
import { risksOf, subRiskOf } from '../composables/useStatusHelpers.js'
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
function editable(m) { return canEdit(m.id, props.ltcId) }

const riskyModules = computed(() => props.modules.filter(m => {
  if (colorOf(m) === 'red' || colorOf(m) === 'yellow') return true
  const subs = statusOf(m)?.sub_items_color || {}
  return Object.values(subs).some(c => c === 'red' || c === 'yellow')
}))

// 1:1 对称:看板区按 group 分列展示了所有模块,风险区也按 group 分列,但只显示非绿
const groups = computed(() => {
  const allGroups = new Map()
  for (const m of props.modules) {
    const k = m.group || '其他'
    if (!allGroups.has(k)) allGroups.set(k, [])
  }
  for (const m of riskyModules.value) {
    const k = m.group || '其他'
    allGroups.get(k).push(m)
  }
  return [...allGroups.entries()]
})

function riskySubs(m) {
  return (m.sub_items || []).filter(s => {
    const c = subColor(m, s.id)
    return c === 'red' || c === 'yellow'
  })
}
function moduleRisks(m) { return risksOf(statusOf(m)) }
function subRiskNote(m, sid) {
  return subRiskOf(statusOf(m), sid) || (m.sub_items.find(x => x.id === sid)?.risk_note || '')
}

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
    <div v-if="!riskyModules.length" class="empty">
      <span class="emoji">🎉</span>
      <div>本周无风险项</div>
      <div class="sub-msg">所有模块与子项均为绿灯</div>
    </div>
    <div v-else class="columns">
      <section v-for="[group, items] in groups" :key="group" class="column">
        <header class="col-head"><span>{{ group }}</span></header>
        <div v-if="!items.length" class="col-empty">本周无风险</div>
        <article
          v-for="m in items"
          :key="m.id"
          class="card"
          :class="`tone-${colorOf(m)}`"
        >
          <header class="card-head">
            <span class="m-name">{{ m.name }}</span>
            <OwnerChip v-if="m.owner_open_id" :open-id="m.owner_open_id" prefix="Owner: " />
          </header>

          <div v-if="moduleRisks(m).length" class="m-risks">
            <div
              v-for="(r, i) in moduleRisks(m)"
              :key="i"
              class="risk-note"
              :class="`sev-${r.severity}`"
            >
              <span class="risk-icon">⚠</span>{{ r.text }}
            </div>
          </div>

          <div v-if="riskySubs(m).length" class="sub-risks">
            <div
              v-for="s in riskySubs(m)"
              :key="s.id"
              class="sub-risk"
            >
              <button
                type="button"
                class="sub-chip"
                :class="`tone-${subColor(m, s.id)}`"
                :disabled="!editable(m)"
                v-tooltip="editable(m) ? '编辑该子项状态与风险' : ''"
                @click="editable(m) && openEdit(m, s.id)"
              >{{ s.name }}</button>
              <span v-if="subRiskNote(m, s.id)" class="sub-note">{{ subRiskNote(m, s.id) }}</span>
            </div>
          </div>

          <footer class="card-foot">
            <span class="updated">{{ statusOf(m)?.updated_at ? '更新于 ' + statusOf(m).updated_at.slice(5, 16).replace('T', ' ') : '未更新' }}</span>
            <button
              v-if="editable(m)"
              class="edit-btn"
              v-tooltip="'编辑该模块状态、KPI 与风险'"
              @click="openEdit(m)"
            >编辑</button>
          </footer>
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
.empty {
  padding: 60px 24px;
  text-align: center;
  color: var(--status-green);
  background: var(--status-green-bg);
  border-radius: 6px;
  font-size: 18px;
  font-weight: 600;
}
.empty .emoji { font-size: 36px; display: block; margin-bottom: 6px; }
.empty .sub-msg { font-size: 13px; font-weight: 400; color: var(--text-muted); margin-top: 4px; }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 16px;
}
.column { display: flex; flex-direction: column; gap: 12px; }
.col-head {
  font-size: 13px; font-weight: 700; color: var(--text); letter-spacing: 0.4px;
  padding: 6px 4px; border-bottom: 2px solid var(--accent-soft);
}
.col-empty { font-size: 12px; color: var(--text-muted); padding: 4px 6px; }

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 16px;
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
.card.tone-red::before { background: var(--status-red); }
.card.tone-yellow::before { background: var(--status-yellow); }
.card.tone-green::before { background: var(--status-green); }

.card-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; gap: 8px; }
.m-name { font-weight: 700; font-size: 16px; }
.m-owner { font-size: 11px; color: var(--text-muted); }

.m-risks { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.risk-note {
  font-size: 13px;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 6px;
  line-height: 1.55;
  display: flex;
  gap: 6px;
  align-items: flex-start;
}
.risk-note.sev-red { background: var(--status-red-bg); color: var(--status-red); border: 1px solid rgba(220,38,38,0.20); }
.risk-note.sev-yellow { background: var(--status-yellow-bg); color: var(--status-yellow); border: 1px solid rgba(217,119,6,0.20); }
.risk-icon { font-size: 13px; flex-shrink: 0; }

.sub-risks { display: flex; flex-direction: column; gap: 6px; }
.sub-risk { display: flex; gap: 8px; align-items: flex-start; }
.sub-chip {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  padding: 4px 10px;
  border-radius: 6px;
  border: none;
  background: var(--status-gray);
  flex-shrink: 0;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
.sub-chip.tone-red { background: var(--status-red); }
.sub-chip.tone-yellow { background: var(--status-yellow); }
.sub-chip.tone-green { background: var(--status-green); }
.sub-chip:disabled { cursor: default; }
.sub-note { font-size: 12.5px; color: var(--text); line-height: 1.5; flex: 1; padding-top: 2px; }

.card-foot {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
}
.edit-btn { font-size: 12px; padding: 3px 12px; }
.updated { font-variant-numeric: tabular-nums; }
</style>
