<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useAuth } from '../composables/useAuth.js'
import { useAdmins } from '../composables/useAdmins.js'
import { useContactCache } from '../composables/useContactCache.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { aggregateStatusTone, currentWeekRange } from '../composables/useStatusHelpers.js'
import LtcTree from './LtcTree.vue'
import TimelineBar from './TimelineBar.vue'
import LtcCategoryGrid from './ltc/LtcCategoryGrid.vue'
import Modal from './harness/Modal.vue'
import LtcDrawer from './admin/LtcDrawer.vue'
import ModuleDrawer from './admin/ModuleDrawer.vue'
import SnapshotPanel from './admin/SnapshotPanel.vue'

const { ltcs, status, ltcVisibleModules, statusKeyOf, isReadonly } = useDashboard()
const { current, pushView } = useView()
const { me } = useAuth()
const { admins, reload: reloadAdmins } = useAdmins()
const { ensureContacts } = useContactCache()
const { canEdit } = useEditableModules()
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

/* 编辑模式:默认关闭(纯查看)。开启后才暴露所有就地编辑入口
   (sub chip 可点、模块头可点、⚙、+ 子项、+ 新模块)。切换 LTC 自动退出编辑。 */
const editMode = ref(false)
watch(currentLtcId, () => { editMode.value = false })
const canManageStructure = computed(() => canEnterLtcAdmin.value && !isReadonly.value && editMode.value)

function ltcStatusKey(m) { return statusKeyOf(m, currentLtcId.value) }
function canEditStatusKey(key) {
  if (!editMode.value) return false
  if (!key) return false
  const sep = '::'
  let ltcId = ''
  let modId = key
  if (key.includes(sep)) {
    const i = key.indexOf(sep)
    ltcId = key.slice(0, i)
    modId = key.slice(i + sep.length)
  }
  return canEdit(modId, ltcId)
}

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

/* 状态色 chip 三合一:click 切换该色显隐(至少保留一个) */
const visibleTones = ref({ green: true, yellow: true, red: true })
function toggleTone(key) {
  const cur = visibleTones.value
  if (cur[key]) {
    const onCount = Object.values(cur).filter(Boolean).length
    if (onCount <= 1) return // 至少保留一个
  }
  visibleTones.value = { ...cur, [key]: !cur[key] }
}

const showAdminTool = ref('') // '' | 'ltc-base' | 'snapshots'
function openAdminTool(name) { showAdminTool.value = name }
function closeAdminTool() { showAdminTool.value = '' }

const editingModuleId = ref('')
function pickModule(id) { editingModuleId.value = id }
function closeModuleDrawer() { editingModuleId.value = '' }
</script>

<template>
  <div class="ltc-main">
    <LtcTree
      :current-ltc-id="currentLtcId"
      @select-pdt="selectPdt"
      @select-ltc="selectLtc"
    />
    <div class="scroll-col">
      <header class="hdr">
        <h1>
          {{ currentLtc?.name || '请选择 LTC' }}
          <span class="date-range">{{ dateRange }}</span>
        </h1>
        <div class="hdr-right">
          <span class="tone-summary" role="group" aria-label="正常/预警/阻塞 显隐切换">
            <button
              class="chip green"
              :class="{ off: !visibleTones.green }"
              v-tooltip="visibleTones.green ? '隐藏正常项(至少保留一个色)' : '显示正常项(绿色+灰色)'"
              @click="toggleTone('green')"
            ><i class="dot"></i>正常 {{ summary.green }}</button>
            <button
              class="chip yellow"
              :class="{ off: !visibleTones.yellow }"
              v-tooltip="visibleTones.yellow ? '隐藏预警项(至少保留一个色)' : '显示预警项(黄色)'"
              @click="toggleTone('yellow')"
            ><i class="dot"></i>预警 {{ summary.yellow }}</button>
            <button
              class="chip red"
              :class="{ off: !visibleTones.red }"
              v-tooltip="visibleTones.red ? '隐藏阻塞项(至少保留一个色)' : '显示阻塞项(红色)'"
              @click="toggleTone('red')"
            ><i class="dot"></i>阻塞 {{ summary.red }}</button>
          </span>
          <div v-if="canEnterLtcAdmin && !isReadonly" class="admin-tools">
            <button
              class="tool-btn"
              :class="{ 'edit-on': editMode }"
              v-tooltip="editMode ? '退出编辑模式(隐藏增删入口)' : '进入编辑模式(显示子项/模块增删入口)'"
              @click="editMode = !editMode"
            >{{ editMode ? '✓ 完成编辑' : '✏️ 编辑' }}</button>
            <button
              class="tool-btn"
              v-tooltip="'编辑本 LTC 基础信息、时间线与模块清单'"
              @click="openAdminTool('ltc-base')"
            >⚙ LTC 配置</button>
            <button
              class="tool-btn"
              v-tooltip="'查看历史周快照与定时冻结'"
              @click="openAdminTool('snapshots')"
            >📸 快照</button>
          </div>
        </div>
      </header>

      <section v-if="milestones.length" class="timeline-section">
        <div class="section-title">时间线 · 本 LTC 自有</div>
        <TimelineBar :milestones="milestones" />
      </section>

      <section class="grid-wrap">
        <LtcCategoryGrid
          v-if="currentLtcId"
          :ltc-id="currentLtcId"
          :modules="modules"
          :visible-tones="visibleTones"
          :status-key-of="ltcStatusKey"
          :can-edit-module-status="canEditStatusKey"
          :can-enter-admin="canManageStructure"
          :edit-mode="editMode"
          @pick-module="pickModule"
        />
      </section>
    </div>

    <Modal :open="showAdminTool === 'ltc-base'" :title="`LTC 配置 · ${currentLtc?.name || ''}`" width="720px" @close="closeAdminTool">
      <LtcDrawer
        v-if="currentLtcId"
        :ltc-id="currentLtcId"
        @pick-module="pickModule"
        @deleted="closeAdminTool"
      />
    </Modal>
    <Modal :open="showAdminTool === 'snapshots'" title="周快照" width="880px" @close="closeAdminTool">
      <SnapshotPanel />
    </Modal>
    <Modal :open="!!editingModuleId" title="模块详情" width="880px" @close="closeModuleDrawer">
      <ModuleDrawer v-if="editingModuleId" :key="editingModuleId" :module-id="editingModuleId" @deleted="closeModuleDrawer" />
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
  border: 1px solid transparent;
  cursor: pointer;
  transition: opacity 120ms, filter 120ms;
}
.chip.red { background: var(--status-red-bg); color: var(--status-red); }
.chip.yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.chip.green { background: var(--status-green-bg); color: var(--status-green); }
.chip .dot { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.chip.red .dot { background: var(--status-red); }
.chip.yellow .dot { background: var(--status-yellow); }
.chip.green .dot { background: var(--status-green); }
.chip:hover { filter: brightness(0.95); }
.chip.off {
  background: var(--panel-soft);
  color: var(--text-dim, var(--text-muted));
  border-color: var(--border);
  opacity: 0.55;
}
.chip.off .dot { background: var(--text-dim, var(--text-muted)); opacity: 0.6; }

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
.admin-tools .tool-btn.edit-on {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-soft, var(--panel));
  font-weight: 600;
}

.timeline-section, .grid-wrap { padding: 0 24px; }
.section-title {
  font-size: 14px; font-weight: 700;
  margin-bottom: 8px; color: var(--text);
  padding-bottom: 4px; border-bottom: 1px solid var(--border-subtle);
}
</style>
