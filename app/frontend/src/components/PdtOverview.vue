<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useAuth } from '../composables/useAuth.js'
import { useContactCache } from '../composables/useContactCache.js'
import TimelineBar from './TimelineBar.vue'
import ModuleCardGrid from './ModuleCardGrid.vue'
import Modal from './harness/Modal.vue'
import MilestonesDrawer from './admin/MilestonesDrawer.vue'
import OverviewCardsDrawer from './admin/OverviewCardsDrawer.vue'
import ModuleDrawer from './admin/ModuleDrawer.vue'
import AdminUsers from './admin/AdminUsers.vue'
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

const showAdminTool = ref('') // '' | 'milestones' | 'overview' | 'people' | 'snapshots'
function openAdminTool(name) { showAdminTool.value = name }
function closeAdminTool() { showAdminTool.value = '' }

const editingModuleId = ref('')
function pickModule(id) { editingModuleId.value = id }
function closeModuleDrawer() { editingModuleId.value = '' }

const { current, pushView } = useView()
const sub = computed(() => current.value.sub || 'timeline')
function switchSub(s) { pushView({ ...current.value, sub: s }) }
</script>

<template>
  <div class="pdt-overview">
    <nav class="sub-tabs">
      <button
        :class="{ primary: sub === 'timeline' }"
        v-tooltip="'查看里程碑甘特图'"
        @click="switchSub('timeline')"
      >甘特图</button>
      <button
        :class="{ primary: sub === 'kanban' }"
        v-tooltip="'查看 PDT 模块卡片看板'"
        @click="switchSub('kanban')"
      >全局看板</button>
      <div v-if="canEnterPdtAdmin && !isReadonly" class="admin-tools">
        <button
          class="tool-btn"
          v-tooltip="'编辑里程碑(甘特图数据源)'"
          @click="openAdminTool('milestones')"
        >🗓 里程碑</button>
        <button
          class="tool-btn"
          v-tooltip="'管理 PDT 总览卡片(新增 / 排序 / 进入模块详情)'"
          @click="openAdminTool('overview')"
        >🧩 总览卡片</button>
        <button
          class="tool-btn"
          v-tooltip="'管理 PDT/LTC Admin 与 Owner 绑定'"
          @click="openAdminTool('people')"
        >👥 人员</button>
        <button
          class="tool-btn"
          v-tooltip="'查看历史周快照与定时冻结'"
          @click="openAdminTool('snapshots')"
        >📸 快照</button>
      </div>
    </nav>

    <TimelineBar v-if="sub === 'timeline'" :milestones="pdt?.milestones || []" />

    <ModuleCardGrid
      v-if="sub === 'kanban'"
      :cards="cards"
      :can-enter-admin="canEnterPdtAdmin"
      :create-defaults="{ scope: 'pdt', group: '总览' }"
      empty-hint="暂无 PDT 级总览卡片,请管理员添加。"
    />

    <Modal :open="showAdminTool === 'milestones'" title="里程碑编辑" width="960px" @close="closeAdminTool">
      <MilestonesDrawer />
    </Modal>
    <Modal :open="showAdminTool === 'overview'" title="PDT 总览卡片" width="880px" @close="closeAdminTool">
      <OverviewCardsDrawer @pick-module="pickModule" />
    </Modal>
    <Modal :open="showAdminTool === 'people'" title="人员与角色" width="880px" @close="closeAdminTool">
      <AdminUsers />
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
.pdt-overview { padding: 18px 0 32px; }
.admin-tools { display: flex; gap: 6px; margin-left: auto; }
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
.sub-tabs {
  display: flex;
  gap: 8px;
  padding: 0 24px 12px;
  align-items: center;
}
.sub-tabs button {
  font-size: 13px;
  padding: 6px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text);
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition), color var(--transition);
}
.sub-tabs button:hover { border-color: var(--accent-soft); }
.sub-tabs button.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

</style>
