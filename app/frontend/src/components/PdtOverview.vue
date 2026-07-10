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
import MilestoneEditor from './admin/MilestoneEditor.vue'

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

const showAdminTool = ref('') // '' | 'perms' | 'snapshots' | 'milestones'
function openAdminTool(name) { showAdminTool.value = name }
function closeAdminTool() { showAdminTool.value = '' }

const { current, pushView } = useView()
const sub = computed(() => current.value.sub || 'timeline')
function switchSub(s) { pushView({ ...current.value, sub: s }) }
function onTabKeydown(e) {
  const tabs = ['timeline', 'kanban']
  const i = tabs.indexOf(sub.value)
  if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
    e.preventDefault()
    const next = e.key === 'ArrowRight' ? (i + 1) % tabs.length : (i - 1 + tabs.length) % tabs.length
    switchSub(tabs[next])
  }
}

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
          v-tooltip="'查看 PDT 时间线 · 全局里程碑视图'"
          @click="switchSub('timeline')"
          @keydown="onTabKeydown"
        ><span class="tab-icon" aria-hidden="true">🗓</span>时间线</button>
        <button
          role="tab"
          :aria-selected="sub === 'kanban'"
          :class="['seg-tab', { active: sub === 'kanban' }]"
          v-tooltip="'查看 PDT 模块卡片看板'"
          @click="switchSub('kanban')"
          @keydown="onTabKeydown"
        ><span class="tab-icon" aria-hidden="true">📊</span>全局看板</button>
      </nav>
      <div class="page-actions">
        <template v-if="canEnterPdtAdmin && !isReadonly">
          <template v-if="sub === 'timeline'">
            <button
              class="tool-btn"
              v-tooltip="'编辑时间线节点(打开弹窗)'"
              @click="openAdminTool('milestones')"
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
    <Modal :open="showAdminTool === 'milestones'" title="时间线管理" width="1080px" @close="closeAdminTool">
      <MilestoneEditor />
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

/* ── Segmented tabs:更大字号 + icon + active 加 tint 背景 + 3px 粗下划线 ── */
.seg-tabs {
  display: flex;
  gap: 2px;
  align-items: stretch;
}
.seg-tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 10px 18px 12px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  border-radius: var(--radius) var(--radius) 0 0;
  cursor: pointer;
  transition: color var(--transition), background var(--transition);
}
.seg-tab .tab-icon {
  font-size: 15px;
  line-height: 1;
  opacity: 0.7;
  transition: opacity var(--transition), transform var(--transition);
}
.seg-tab::after {
  content: '';
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: -1px;
  height: 3px;
  background: transparent;
  border-radius: 2px 2px 0 0;
  transition: background var(--transition), left var(--transition), right var(--transition);
}
.seg-tab:hover {
  color: var(--text-strong);
  background: var(--panel-soft);
}
.seg-tab:hover .tab-icon { opacity: 1; transform: scale(1.1); }
.seg-tab.active {
  color: var(--accent);
  background: var(--accent-soft);
}
.seg-tab.active .tab-icon { opacity: 1; }
.seg-tab.active::after {
  background: var(--gradient-brand);
  left: 6px;
  right: 6px;
}
.seg-tab:focus-visible { outline: 2px solid var(--accent-ring); outline-offset: 2px; }
.seg-tab:focus-visible .tab-icon { opacity: 1; }

/* ── 右侧 actions 区:工具按钮放大 + 加边框 + hover 出 accent ── */
.page-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 8px;
}
.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-sans);
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.03em;
  padding: 7px 14px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text);
  border-radius: var(--radius);
  cursor: pointer;
  transition:
    color var(--transition),
    background var(--transition),
    border-color var(--transition),
    transform 140ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow var(--transition);
}
.tool-btn:hover {
  color: var(--accent);
  background: var(--accent-soft);
  border-color: var(--accent);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.tool-btn:active { transform: translateY(0); }
.tool-icon {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1;
  transition: color var(--transition), transform var(--transition);
}
.tool-btn:hover .tool-icon { color: var(--accent); transform: scale(1.1); }

.action-divider {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 8px;
}

.add-card-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.03em;
  padding: 7px 16px;
  border-radius: var(--radius);
  box-shadow: 0 1px 2px var(--accent-glow);
}
.add-card-plus {
  font-size: 16px;
  font-weight: 400;
  line-height: 1;
  margin-right: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .seg-tab:hover .tab-icon { transform: none; }
  .tool-btn:hover { transform: none; }
  .tool-btn:hover .tool-icon { transform: none; }
}
</style>
