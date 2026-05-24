<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useAuth } from '../composables/useAuth.js'
import { useAdmins } from '../composables/useAdmins.js'
import { useContactCache } from '../composables/useContactCache.js'
import { aggregateStatusTone, currentWeekRange } from '../composables/useStatusHelpers.js'
import LtcTree from './LtcTree.vue'
import TimelineBar from './TimelineBar.vue'
import ModuleCardGrid from './ModuleCardGrid.vue'
import ModuleRiskList from './ModuleRiskList.vue'
import Modal from './harness/Modal.vue'
import LtcDrawer from './admin/LtcDrawer.vue'
import AdminUsers from './admin/AdminUsers.vue'
import SnapshotPanel from './admin/SnapshotPanel.vue'

const { ltcs, status, ltcVisibleModules, statusKeyOf, isReadonly } = useDashboard()
const { current, pushView } = useView()
const { me } = useAuth()
const { admins, reload: reloadAdmins } = useAdmins()
const { ensureContacts } = useContactCache()
onMounted(() => { ensureContacts(); reloadAdmins() })

const currentLtcId = computed(() => current.value.id || ltcs.value[0]?.id || '')
const currentLtc = computed(() => ltcs.value.find(l => l.id === currentLtcId.value))
const modules = computed(() => ltcVisibleModules(currentLtcId.value))
const milestones = computed(() => currentLtc.value?.milestones || [])
const dateRange = computed(() => currentWeekRange())

const canEnterLtcAdmin = computed(() => {
  const u = me.value
  if (!u?.open_id) return false
  if (u.is_super || u.is_pdt_admin) return true
  const ltcMap = admins.value?.ltc || {}
  return (ltcMap[currentLtcId.value] || []).includes(u.open_id)
})

const cards = computed(() => modules.value.map((m, i) => ({
  id: m.scope === 'ltc_template' ? `${currentLtcId.value}::${m.id}` : m.id,
  name: m.name,
  owner_open_id: m.owner_open_id,
  module: m,
  kpi_fields: m.kpi_fields || [],
  show_risk: true,
  order: m.order ?? i,
})))

function ltcStatusKey(m) { return statusKeyOf(m, currentLtcId.value) }

const summary = computed(() => {
  const total = { red: 0, yellow: 0, green: 0, gray: 0 }
  for (const m of modules.value) {
    const k = ltcStatusKey(m)
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

const showAdminTool = ref('') // '' | 'ltc-base' | 'people' | 'snapshots'
function openAdminTool(name) { showAdminTool.value = name }
function closeAdminTool() { showAdminTool.value = '' }
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
          <div v-if="canEnterLtcAdmin && !isReadonly" class="admin-tools">
            <button
              class="tool-btn"
              v-tooltip="'编辑本 LTC 基础信息与里程碑'"
              @click="openAdminTool('ltc-base')"
            >⚙ LTC 基础</button>
            <button
              class="tool-btn"
              v-tooltip="'管理人员与角色绑定(全局)'"
              @click="openAdminTool('people')"
            >👥 人员</button>
            <button
              class="tool-btn"
              v-tooltip="'查看历史周快照与定时冻结'"
              @click="openAdminTool('snapshots')"
            >📸 快照</button>
          </div>
        </div>
      </header>

      <section v-if="milestones.length" class="timeline-section">
        <div class="section-title">里程碑 · 本 LTC 自有</div>
        <TimelineBar :milestones="milestones" />
      </section>

      <section id="board-section" class="board-section">
        <div class="section-title">看板 · {{ currentLtc?.name || '' }}</div>
        <ModuleCardGrid
          v-if="currentLtcId"
          :cards="cards"
          :ltc-id="currentLtcId"
          :can-enter-admin="canEnterLtcAdmin"
          :create-defaults="{ scope: 'ltc', ltc_id: currentLtcId, group: currentLtc?.name || '' }"
          :template-badge="true"
          :status-key-of="ltcStatusKey"
          empty-hint="该 LTC 暂无卡片,可在 PDT 总览全局看板新增基础卡,或点本页「+ 新增卡片」加私有卡。"
        />
      </section>

      <section id="risk-section" class="risk-section">
        <div class="section-title">风险详情 · {{ currentLtc?.name || '' }}</div>
        <ModuleRiskList :modules="modules" :ltc-id="currentLtcId" />
      </section>
    </div>

    <Modal :open="showAdminTool === 'ltc-base'" :title="`LTC 基础 · ${currentLtc?.name || ''}`" width="720px" @close="closeAdminTool">
      <LtcDrawer v-if="currentLtcId" :ltc-id="currentLtcId" @deleted="closeAdminTool" />
    </Modal>
    <Modal :open="showAdminTool === 'people'" title="人员与角色" width="880px" @close="closeAdminTool">
      <AdminUsers />
    </Modal>
    <Modal :open="showAdminTool === 'snapshots'" title="周快照" width="880px" @close="closeAdminTool">
      <SnapshotPanel />
    </Modal>
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
  padding: 18px 0 32px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  scroll-behavior: smooth;
}
.hdr {
  display: flex; justify-content: space-between; align-items: flex-end;
  gap: 16px; flex-wrap: wrap;
  padding: 0 24px;
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
.hdr-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
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
.chip .dot { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.chip.red .dot { background: var(--status-red); }
.chip.yellow .dot { background: var(--status-yellow); }
.chip.green .dot { background: var(--status-green); }

.admin-tools { display: flex; gap: 6px; }
.admin-tools .tool-btn {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--panel-soft);
  color: var(--text-muted);
  cursor: pointer;
  transition: color 120ms, background 120ms, border-color 120ms;
}
.admin-tools .tool-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--panel);
}

.timeline-section, .board-section, .risk-section { padding: 0 24px; }
.section-title {
  font-size: 14px; font-weight: 700;
  margin-bottom: 8px; color: var(--text);
  padding-bottom: 4px; border-bottom: 1px solid var(--border-subtle);
}
/* 让 ModuleCardGrid 自带的 24px padding 不与本页冲突 — 由于 board-section 已有 padding,清掉网格本身的 padding */
.board-section :deep(.cards-grid) { padding: 0; }
.board-section :deep(.empty) { padding: 36px 0; }
</style>
