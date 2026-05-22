<script setup>
import { computed, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { risksOf, subRiskOf, aggregateStatusTone, currentWeekRange } from '../composables/useStatusHelpers.js'
import StatusLegend from './StatusLegend.vue'
import StatusEditDialog from './StatusEditDialog.vue'

const { pdt, ltcs, status, modulesByScope } = useDashboard()
const { current, pushView } = useView()
const { canEdit } = useEditableModules()

const ltcId = computed(() => current.value.id || ltcs.value[0]?.id || '')
const ltc = computed(() => ltcs.value.find(l => l.id === ltcId.value))

const allModules = computed(() => modulesByScope.value.ltc[ltcId.value] || [])

function colorOf(m) { return status.value?.[m.id]?.module_color || 'gray' }
function subColor(m, sid) { return status.value?.[m.id]?.sub_items_color?.[sid] || 'gray' }

const summary = computed(() => {
  const total = { red: 0, yellow: 0, green: 0, gray: 0 }
  for (const m of allModules.value) {
    const t = aggregateStatusTone(status.value?.[m.id])
    for (const k of Object.keys(total)) total[k] += t[k] || 0
  }
  return total
})

const riskyModules = computed(() => allModules.value.filter(m => {
  if (colorOf(m) === 'red' || colorOf(m) === 'yellow') return true
  const subs = status.value?.[m.id]?.sub_items_color || {}
  return Object.values(subs).some(c => c === 'red' || c === 'yellow')
}))

const groups = computed(() => {
  const g = {}
  for (const m of riskyModules.value) {
    const key = m.group || '其他'
    if (!g[key]) g[key] = []
    g[key].push(m)
  }
  return g
})

function riskySubs(m) {
  return (m.sub_items || []).filter(s => {
    const c = subColor(m, s.id)
    return c === 'red' || c === 'yellow'
  })
}
function moduleRisks(m) { return risksOf(status.value?.[m.id]) }
function subRiskNote(m, sid) {
  return subRiskOf(status.value?.[m.id], sid) || (m.sub_items.find(x => x.id === sid)?.risk_note || '')
}

function back() { pushView({ view: 'ltc', id: ltcId.value }) }

const editing = ref(null)
const focusSubId = ref('')
function openEdit(m, subId = '') {
  if (!canEdit(m.id)) return
  focusSubId.value = subId
  editing.value = m
}
function closeEdit() { editing.value = null; focusSubId.value = '' }

const dateRange = computed(() => currentWeekRange())
</script>

<template>
  <div class="risk-detail">
    <div class="head">
      <div class="title-block">
        <h1>
          <span class="pdt-prefix" v-if="pdt?.name">{{ pdt.name }} ·</span>
          {{ ltc?.name || '—' }} 风险详情
        </h1>
        <span class="date-range">{{ dateRange }}</span>
      </div>
      <div class="head-right">
        <span class="tone-summary">
          <span class="chip red" v-tooltip="'Delay/Block 项总数'"><i class="dot"></i>{{ summary.red }}</span>
          <span class="chip yellow" v-tooltip="'预警项总数'"><i class="dot"></i>{{ summary.yellow }}</span>
          <span class="chip green" v-tooltip="'正常项总数'"><i class="dot"></i>{{ summary.green }}</span>
        </span>
        <button @click="back" v-tooltip="'返回 LTC 研发进展'">← 返回</button>
        <StatusLegend />
      </div>
    </div>

    <div v-if="!riskyModules.length" class="empty">
      <span class="emoji">🎉</span>
      <div>本周无风险项</div>
      <div class="sub-msg">所有模块与子项均为绿灯</div>
    </div>

    <div v-else class="columns">
      <section v-for="(items, group) in groups" :key="group" class="column">
        <header class="col-head"><span>{{ group }}</span></header>
        <article
          v-for="m in items"
          :key="m.id"
          class="card"
          :class="`tone-${colorOf(m)}`"
        >
          <header class="card-head">
            <span class="m-name">{{ m.name }}</span>
            <span class="m-owner" v-if="m.owner_open_id">Owner: {{ m.owner_open_id }}</span>
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
                :disabled="!canEdit(m.id)"
                v-tooltip="canEdit(m.id) ? '编辑该子项状态与风险' : ''"
                @click="canEdit(m.id) && openEdit(m, s.id)"
              >{{ s.name }}</button>
              <span v-if="subRiskNote(m, s.id)" class="sub-note">{{ subRiskNote(m, s.id) }}</span>
            </div>
          </div>

          <footer class="card-foot">
            <span class="updated">{{ status?.[m.id]?.updated_at ? '更新于 ' + status[m.id].updated_at.slice(5, 16).replace('T', ' ') : '未更新' }}</span>
            <button
              v-if="canEdit(m.id)"
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
      :current="editing ? status?.[editing.id] : {}"
      :focus-sub-id="focusSubId"
      @close="closeEdit"
    />
  </div>
</template>

<style scoped>
.risk-detail { padding: 20px 28px 32px; font-size: 14.5px; }
.head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.title-block { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.3px; }
.pdt-prefix { color: var(--text-muted); font-weight: 500; font-size: 18px; }
.date-range {
  font-size: 14px; color: var(--text-muted); padding: 3px 10px;
  background: var(--panel-soft); border: 1px solid var(--border-subtle); border-radius: var(--radius);
  font-variant-numeric: tabular-nums;
}
.head-right { display: flex; align-items: center; gap: 12px; }
.tone-summary { display: inline-flex; gap: 4px; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600;
  padding: 3px 9px; border-radius: var(--radius);
  font-variant-numeric: tabular-nums;
}
.chip.red { background: var(--status-red-bg); color: var(--status-red); }
.chip.yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.chip.green { background: var(--status-green-bg); color: var(--status-green); }
.chip .dot { width: 8px; height: 8px; border-radius: var(--radius-sm); display: inline-block; }
.chip.red .dot { background: var(--status-red); }
.chip.yellow .dot { background: var(--status-yellow); }
.chip.green .dot { background: var(--status-green); }

.empty {
  padding: 80px 24px;
  text-align: center;
  color: var(--status-green);
  background: var(--status-green-bg);
  border-radius: var(--radius);
  font-size: 20px;
  font-weight: 600;
}
.empty .emoji { font-size: 40px; display: block; margin-bottom: 6px; }
.empty .sub-msg { font-size: 14px; font-weight: 400; color: var(--text-muted); margin-top: 4px; }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 16px;
}
.column { display: flex; flex-direction: column; gap: 12px; }
.col-head {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.4px;
  padding: 6px 4px;
  border-bottom: 2px solid var(--accent-soft);
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
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
  border-radius: var(--radius);
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
  border-radius: var(--radius);
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
.sub-chip:hover:not(:disabled) { box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
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
