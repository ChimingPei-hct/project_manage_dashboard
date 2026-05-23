<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { aggregateStatusTone, currentWeekRange } from '../composables/useStatusHelpers.js'
import LtcTree from './LtcTree.vue'
import TimelineBar from './TimelineBar.vue'
import ModuleBoardGrid from './ModuleBoardGrid.vue'
import ModuleRiskList from './ModuleRiskList.vue'
import StatusLegend from './StatusLegend.vue'

const { ltcs, status, ltcVisibleModules, statusKeyOf } = useDashboard()
const { current, pushView } = useView()

const currentLtcId = computed(() => current.value.id || ltcs.value[0]?.id || '')
const currentLtc = computed(() => ltcs.value.find(l => l.id === currentLtcId.value))
const modules = computed(() => ltcVisibleModules(currentLtcId.value))
const milestones = computed(() => currentLtc.value?.milestones || [])
const dateRange = computed(() => currentWeekRange())

const summary = computed(() => {
  const total = { red: 0, yellow: 0, green: 0, gray: 0 }
  for (const m of modules.value) {
    const k = statusKeyOf(m, currentLtcId.value)
    const t = aggregateStatusTone(status.value?.[k])
    for (const c of Object.keys(total)) total[c] += t[c] || 0
  }
  return total
})

function selectPdt() { pushView({ view: 'pdt', week: current.value.week }) }
function selectLtc(id) { pushView({ view: 'ltc', id, week: current.value.week }) }

const scrollRef = ref(null)
async function maybeScrollToRisk() {
  if (current.value.view !== 'risks') return
  await nextTick()
  const el = scrollRef.value?.querySelector('#risk-section')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
watch(() => [current.value.view, currentLtcId.value], () => { maybeScrollToRisk() }, { immediate: true, flush: 'post' })
</script>

<template>
  <div class="ltc-main">
    <LtcTree
      :current-ltc-id="currentLtcId"
      @select-pdt="selectPdt"
      @select-ltc="selectLtc"
    />
    <div ref="scrollRef" class="scroll-col">
      <header class="hdr">
        <h1>
          {{ currentLtc?.name || '请选择 LTC' }}
          <span class="date-range">{{ dateRange }}</span>
        </h1>
        <div class="hdr-right">
          <span class="tone-summary">
            <span class="chip red" v-tooltip="'Delay/Block 项总数'"><i class="dot"></i>{{ summary.red }}</span>
            <span class="chip yellow" v-tooltip="'预警项总数'"><i class="dot"></i>{{ summary.yellow }}</span>
            <span class="chip green" v-tooltip="'正常项总数'"><i class="dot"></i>{{ summary.green }}</span>
          </span>
          <StatusLegend />
        </div>
      </header>

      <section class="timeline-section">
        <div class="section-title">里程碑(本 LTC 自有)</div>
        <TimelineBar v-if="milestones.length" :milestones="milestones" />
        <div v-else class="placeholder">该 LTC 暂未配置里程碑,可在管理后台「LTC 列表 → 里程碑」补充。</div>
      </section>

      <section id="board-section" class="board-section">
        <div class="section-title">看板 · {{ currentLtc?.name || '' }}</div>
        <ModuleBoardGrid :modules="modules" :ltc-id="currentLtcId" />
      </section>

      <section id="risk-section" class="risk-section">
        <div class="section-title">风险详情 · {{ currentLtc?.name || '' }}</div>
        <ModuleRiskList :modules="modules" :ltc-id="currentLtcId" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.ltc-main {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: calc(100vh - 52px);
  min-height: 0;
}
.scroll-col {
  overflow-y: auto;
  padding: 18px 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  scroll-behavior: smooth;
}
.hdr {
  display: flex; justify-content: space-between; align-items: flex-end;
  gap: 16px; flex-wrap: wrap;
}
h1 {
  margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.2px;
  display: inline-flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
}
.date-range {
  font-size: 13px; color: var(--text-muted);
  background: var(--panel-soft); padding: 2px 10px;
  border-radius: 6px; border: 1px solid var(--border-subtle);
  font-variant-numeric: tabular-nums; font-weight: 500;
}
.hdr-right { display: flex; align-items: center; gap: 12px; }
.tone-summary { display: inline-flex; gap: 4px; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600;
  padding: 3px 9px; border-radius: 6px;
  font-variant-numeric: tabular-nums;
}
.chip.red { background: var(--status-red-bg); color: var(--status-red); }
.chip.yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.chip.green { background: var(--status-green-bg); color: var(--status-green); }
.chip .dot { width: 8px; height: 8px; border-radius: 6px; display: inline-block; }
.chip.red .dot { background: var(--status-red); }
.chip.yellow .dot { background: var(--status-yellow); }
.chip.green .dot { background: var(--status-green); }

.section-title {
  font-size: 14px; font-weight: 700;
  margin-bottom: 8px; color: var(--text);
  padding-bottom: 4px; border-bottom: 1px solid var(--border-subtle);
}
.placeholder {
  font-size: 12px; color: var(--text-muted);
  padding: 18px; text-align: center;
  background: var(--panel-soft); border-radius: 6px;
  border: 1px dashed var(--border-subtle);
}
</style>
