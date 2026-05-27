<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useAuth } from '../composables/useAuth.js'
import { useContactCache } from '../composables/useContactCache.js'
import TimelineBar from './TimelineBar.vue'
import ModuleCardGrid from './ModuleCardGrid.vue'
import Modal from './harness/Modal.vue'
import AdminPerms from './admin/AdminPerms.vue'
import SnapshotPanel from './admin/SnapshotPanel.vue'

const { pdt, modulesByScope, isReadonly } = useDashboard()
const { me } = useAuth()

const canEnterPdtAdmin = computed(() => !!(me.value && (me.value.is_super || me.value.is_pdt_admin)))
const { ensureContacts } = useContactCache()
onMounted(() => { ensureContacts() })

/* 优先用配置的 overview_cards;无则回退到 modulesByScope.pdt(老 schema 自动适配) */
const cards = computed(() => {
  const oc = pdt.value?.overview_cards
  if (Array.isArray(oc) && oc.length) {
    return oc.map(c => {
      const mod = modulesByScope.value.pdt.find(m => m.id === c.module_id)
      return {
        id: c.id,
        name: c.name || mod?.name || '未命名',
        owner_open_id: c.owner_open_id || mod?.owner_open_id,
        module: mod,
        kpi_fields: mod?.kpi_fields || c.kpi_fields || [],
        show_risk: c.show_risk !== false,
        order: c.order ?? 0,
      }
    }).filter(c => c.module).sort((a, b) => a.order - b.order)
  }
  return modulesByScope.value.pdt.map((m, i) => ({
    id: m.id,
    name: m.name,
    owner_open_id: m.owner_open_id,
    module: m,
    kpi_fields: m.kpi_fields || [],
    show_risk: true,
    order: m.order ?? i,
  })).sort((a, b) => a.order - b.order)
})

const showAdminTool = ref('') // '' | 'perms' | 'snapshots'
function openAdminTool(name) { showAdminTool.value = name }
function closeAdminTool() { showAdminTool.value = '' }
function openMilestonesPage() {
  pushView({ view: 'milestones' })
}

const { current, pushView } = useView()
const sub = computed(() => current.value.sub || 'timeline')
function switchSub(s) { pushView({ ...current.value, sub: s }) }

const gridRef = ref(null)
const canAddCard = computed(() => sub.value === 'kanban' && canEnterPdtAdmin.value && !isReadonly.value)
function triggerCreate() { gridRef.value?.openCreate?.() }
</script>

<template>
  <div class="pdt-overview">
    <header class="page-header">
      <nav class="seg-tabs" role="tablist">
        <button
          role="tab"
          :aria-selected="sub === 'timeline'"
          :class="['seg-tab', { active: sub === 'timeline' }]"
          v-tooltip="'查看时间线'"
          @click="switchSub('timeline')"
        >时间线</button>
        <button
          role="tab"
          :aria-selected="sub === 'kanban'"
          :class="['seg-tab', { active: sub === 'kanban' }]"
          v-tooltip="'查看 PDT 模块卡片看板'"
          @click="switchSub('kanban')"
        >全局看板</button>
      </nav>
      <div class="page-actions">
        <template v-if="canEnterPdtAdmin && !isReadonly">
          <template v-if="sub === 'timeline'">
            <button
              class="tool-btn"
              v-tooltip="'在新标签页编辑时间线'"
              @click="openMilestonesPage"
            ><span class="tool-icon">🗓</span>时间线管理</button>
          </template>
          <template v-else>
            <button
              class="tool-btn"
              v-tooltip="'设置项目 Owner 与管理员名单'"
              @click="openAdminTool('perms')"
            ><span class="tool-icon">⚙</span>权限管理</button>
            <button
              class="tool-btn"
              v-tooltip="'查看历史周快照与定时冻结'"
              @click="openAdminTool('snapshots')"
            ><span class="tool-icon">📸</span>快照</button>
          </template>
        </template>
        <span v-if="canAddCard" class="action-divider" aria-hidden="true"></span>
        <button
          v-if="canAddCard"
          type="button"
          class="add-card-btn primary"
          v-tooltip="'新建一张 PDT 级总览卡片(scope=pdt)'"
          @click="triggerCreate"
        ><span class="add-card-plus">+</span>新增卡片</button>
      </div>
    </header>

    <TimelineBar v-if="sub === 'timeline'" :milestones="pdt?.milestones || []" />

    <ModuleCardGrid
      v-if="sub === 'kanban'"
      ref="gridRef"
      :cards="cards"
      :can-enter-admin="canEnterPdtAdmin"
      :create-defaults="{ scope: 'pdt', group: '总览' }"
      :hide-add-button="true"
      empty-hint="暂无 PDT 级总览卡片,请管理员添加。"
    />

    <Modal :open="showAdminTool === 'perms'" title="权限管理" width="640px" @close="closeAdminTool">
      <AdminPerms />
    </Modal>
    <Modal :open="showAdminTool === 'snapshots'" title="周快照" width="880px" @close="closeAdminTool">
      <SnapshotPanel />
    </Modal>
  </div>
</template>

<style scoped>
.pdt-overview { padding: 8px 0 32px; }

/* ── Page header:tabs 在左,actions 在右,底部一条 hairline 把 header 与内容区分开 ── */
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: 4px 24px 0;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--border-subtle);
}

/* ── Segmented tabs:无边框无背景,active 仅靠底部 2px 下划线 + 文字色 ── */
.seg-tabs {
  display: flex;
  gap: 4px;
  align-items: stretch;
}
.seg-tab {
  position: relative;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 14px 10px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  border-radius: 0;
  cursor: pointer;
  transition: color var(--transition);
}
.seg-tab::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: -1px;
  height: 2px;
  background: transparent;
  border-radius: var(--radius-sm);
  transition: background var(--transition);
}
.seg-tab:hover { color: var(--text); background: transparent; }
.seg-tab.active { color: var(--accent); }
.seg-tab.active::after { background: var(--accent); }
.seg-tab:focus-visible { outline: 2px solid var(--accent-soft); outline-offset: 2px; }

/* ── 右侧 actions 区:工具按钮 ghost 风,主按钮保留 primary 但更紧凑 ── */
.page-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-bottom: 6px;
}
.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  padding: 5px 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  border-radius: var(--radius);
  cursor: pointer;
  transition: color var(--transition), background var(--transition), border-color var(--transition);
}
.tool-btn:hover {
  color: var(--text);
  background: var(--panel-soft);
  border-color: var(--border-subtle);
}
.tool-icon {
  font-size: 11px;
  color: var(--text-dim);
  line-height: 1;
}
.tool-btn:hover .tool-icon { color: var(--text-muted); }

.action-divider {
  width: 1px;
  height: 16px;
  background: var(--border);
  margin: 0 6px;
}

.add-card-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12.5px;
  padding: 5px 12px;
  border-radius: var(--radius);
  box-shadow: 0 1px 1px var(--accent-glow);
}
.add-card-plus {
  font-size: 14px;
  font-weight: 400;
  line-height: 1;
  margin-right: 1px;
}
</style>
