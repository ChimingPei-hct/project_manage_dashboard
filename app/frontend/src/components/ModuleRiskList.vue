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
  padding: 64px 24px;
  text-align: center;
  color: var(--status-green-text-strong);
  background: linear-gradient(180deg, var(--status-green-bg) 0%, var(--panel) 100%);
  border: 1px solid var(--status-green-border);
  border-radius: var(--radius-lg);
  font-size: var(--fs-lg);
  font-weight: 600;
  box-shadow: var(--shadow-md);
}
.empty .emoji { font-size: 40px; display: block; margin-bottom: 12px; }
.empty .sub-msg { font-size: var(--fs-sm); font-weight: 400; color: var(--text-muted); margin-top: 8px; }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 20px;
}
.column { display: flex; flex-direction: column; gap: 14px; }
.col-head {
  font-size: var(--fs-xs); font-weight: 600; color: var(--text-muted); letter-spacing: 0.06em;
  padding: 8px 4px; border-bottom: 2px solid var(--accent);
  text-transform: uppercase;
}
.col-empty { font-size: var(--fs-sm); color: var(--text-dim); padding: 8px 6px; font-style: italic; }

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-md);
  position: relative;
  transition: all var(--transition);
}
.card::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 3px;
  background: var(--status-gray);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
.card.tone-green::before  { background: var(--status-green); }
.card.tone-yellow::before { background: var(--status-yellow); }
.card.tone-red::before    { background: var(--status-red); }
.card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
  border-color: var(--border-strong);
}

.card-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid var(--border-subtle); }
.m-name { font-weight: 600; font-size: var(--fs-lg); color: var(--text-strong); letter-spacing: -0.01em; font-family: var(--font-serif); }
.m-owner { font-size: var(--fs-xs); color: var(--text-muted); }

.m-risks { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.risk-note {
  font-size: var(--fs-sm);
  font-weight: 500;
  padding: 10px 12px;
  border-radius: var(--radius);
  line-height: 1.6;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  border-left: 3px solid transparent;
  transition: all var(--transition);
}
.risk-note.sev-red {
  background: var(--status-red-bg);
  color: var(--status-red-text-strong);
  border: 1px solid var(--status-red-border);
  border-left: 3px solid var(--status-red);
}
.risk-note.sev-yellow {
  background: var(--status-yellow-bg);
  color: var(--status-yellow-text-strong);
  border: 1px solid var(--status-yellow-border);
  border-left: 3px solid var(--status-yellow);
}
.risk-icon { font-size: var(--fs-sm); flex-shrink: 0; margin-top: 1px; }

.sub-risks { display: flex; flex-direction: column; gap: 8px; }
.sub-risk { display: flex; gap: 10px; align-items: flex-start; padding: 6px 0; }
.sub-chip {
  font-size: var(--fs-xs);
  font-weight: 600;
  color: #fff;
  padding: 5px 10px;
  border-radius: var(--radius);
  border: none;
  background: var(--status-gray);
  flex-shrink: 0;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  letter-spacing: 0.02em;
}
.sub-chip.tone-red { background: var(--status-red); box-shadow: 0 2px 4px rgba(220,38,38,0.25); }
.sub-chip.tone-yellow { background: var(--status-yellow); box-shadow: 0 2px 4px rgba(217,119,6,0.25); }
.sub-chip.tone-green { background: var(--status-green); box-shadow: 0 2px 4px rgba(22,163,74,0.25); }
.sub-chip:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent-ring);
}
.sub-chip:disabled { cursor: default; opacity: 0.6; }
.sub-note { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; flex: 1; padding-top: 4px; }

.card-foot {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}
.edit-btn {
  font-size: var(--fs-xs);
  padding: 6px 14px;
  letter-spacing: 0.04em;
  font-weight: 600;
  text-transform: uppercase;
}
.edit-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent-ring);
  border-color: var(--accent);
}
.updated { font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
@media (prefers-reduced-motion: reduce) {
  .card:hover { transform: none; }
  .risk-note { transition: none; }
  .sub-chip { transition: none; }
}
</style>
