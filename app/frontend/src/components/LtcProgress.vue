<script setup>
import { computed, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { risksOf, subRiskOf, currentWeekRange } from '../composables/useStatusHelpers.js'
import StatusLegend from './StatusLegend.vue'
import ModuleStatusDots from './ModuleStatusDots.vue'
import StatusEditDialog from './StatusEditDialog.vue'

const { pdt, ltcs, status, modulesByScope } = useDashboard()
const { current, pushView } = useView()
const { canEdit } = useEditableModules()

const currentLtcId = computed(() => current.value.id || ltcs.value[0]?.id || '')
const currentLtc = computed(() => ltcs.value.find(l => l.id === currentLtcId.value))

const ltcModules = computed(() =>
  (modulesByScope.value.ltc[currentLtcId.value] || [])
    .slice()
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
)

const groups = computed(() => {
  const g = {}
  for (const m of ltcModules.value) {
    const key = m.group || '其他'
    if (!g[key]) g[key] = []
    g[key].push(m)
  }
  return g
})

function colorOf(m) { return status.value?.[m.id]?.module_color || 'gray' }
function subColor(m, sid) { return status.value?.[m.id]?.sub_items_color?.[sid] || 'gray' }
function hasMismatch(m) {
  if (colorOf(m) !== 'green') return false
  const subs = status.value?.[m.id]?.sub_items_color || {}
  return Object.values(subs).some(c => c && c !== 'green')
}
function firstRiskText(m) {
  return (risksOf(status.value?.[m.id])[0] || {}).text || ''
}
function subTooltip(m, s) {
  const note = subRiskOf(status.value?.[m.id], s.id) || s.risk_note || ''
  const lbl = { red: 'Delay/Block', yellow: '预警', green: '正常', gray: '未填报' }[subColor(m, s.id)]
  return `${s.name} · ${lbl}${note ? '\n' + note : ''}`
}

function changeLtc(e) { pushView({ view: 'ltc', id: e.target.value }) }
function goRisks() { pushView({ view: 'risks', id: currentLtcId.value }) }

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
  <div class="ltc-progress">
    <div class="head">
      <div class="title-block">
        <h1>
          <span class="pdt-prefix" v-if="pdt?.name">{{ pdt.name }} ·</span>
          {{ currentLtc?.name || '—' }} 研发进展看板
        </h1>
        <span class="date-range">{{ dateRange }}</span>
      </div>
      <div class="head-right">
        <select
          :value="currentLtcId"
          @change="changeLtc"
          class="ltc-switcher"
          v-tooltip="'切换查看的 LTC 子项目'"
        >
          <option v-for="l in ltcs" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
        <button v-tooltip="'仅展示黄/红子项及风险说明'" @click="goRisks">风险详情 →</button>
        <StatusLegend />
      </div>
    </div>

    <div v-if="!ltcModules.length" class="empty">该 LTC 下暂无模块</div>

    <div v-else class="columns">
      <section v-for="(items, group) in groups" :key="group" class="column">
        <header class="col-head">
          <span class="col-title">{{ group }}</span>
          <span v-if="items[0]?.owner_open_id" class="col-owner">Owner: {{ items[0].owner_open_id }}</span>
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
              <span
                v-if="hasMismatch(m)"
                class="warn"
                v-tooltip="'模块绿但子项非绿,请核对一致性'"
              >⚠</span>
            </span>
            <ModuleStatusDots
              :color="colorOf(m)"
              :editable="canEdit(m.id)"
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
              :class="[`tone-${subColor(m, s.id)}`, { editable: canEdit(m.id) }]"
              :disabled="!canEdit(m.id)"
              v-tooltip="subTooltip(m, s)"
              @click="canEdit(m.id) && openEdit(m, s.id)"
            >{{ s.name }}</button>
          </div>
          <div v-else-if="m.owner_open_id" class="owner-line">Owner: {{ m.owner_open_id }}</div>
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
.ltc-progress { padding: 18px 24px 28px; }
.head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 18px; flex-wrap: wrap; }
.title-block { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.2px;
}
.pdt-prefix { color: var(--text-muted); font-weight: 500; }
.date-range {
  font-size: 13px;
  color: var(--text-muted);
  background: var(--panel-soft);
  padding: 2px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--border-subtle);
  font-variant-numeric: tabular-nums;
}
.head-right { display: flex; align-items: center; gap: 12px; }
.ltc-switcher { min-width: 160px; }

.empty { color: var(--text-muted); padding: 48px; text-align: center; }

.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.column {
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.col-head { display: flex; justify-content: space-between; align-items: baseline; padding: 0 2px 4px; border-bottom: 2px solid var(--accent-soft); }
.col-title { font-size: 13px; font-weight: 700; color: var(--text); letter-spacing: 0.3px; }
.col-owner { font-size: 11px; color: var(--text-muted); }

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 12px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition);
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
.card:hover { box-shadow: var(--shadow-md); }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px; }
.name { font-weight: 600; font-size: 13px; display: inline-flex; align-items: center; gap: 4px; }
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
  border-radius: var(--radius);
  background: var(--status-gray);
  min-height: 28px;
  line-height: 1.25;
  letter-spacing: 0.2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
  transition: transform 120ms, box-shadow 120ms;
}
.sub-cell.tone-green { background: var(--status-green); }
.sub-cell.tone-yellow { background: var(--status-yellow); color: #fff; }
.sub-cell.tone-red { background: var(--status-red); }
.sub-cell.tone-gray { background: var(--status-gray); color: var(--text-muted); }
.sub-cell.editable { cursor: pointer; }
.sub-cell.editable:hover { transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,0.12); }
.sub-cell:disabled:hover { transform: none; box-shadow: none; }
.owner-line { font-size: 11px; color: var(--text-muted); }
</style>
