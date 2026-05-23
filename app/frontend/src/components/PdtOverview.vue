<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useAuth } from '../composables/useAuth.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { useContactCache, displayName } from '../composables/useContactCache.js'
import { kpiItemsOf, risksOf } from '../composables/useStatusHelpers.js'
import TimelineBar from './TimelineBar.vue'
import MilestoneEditor from './admin/MilestoneEditor.vue'
import StatusLegend from './StatusLegend.vue'
import ModuleStatusDots from './ModuleStatusDots.vue'
import StatusEditDialog from './StatusEditDialog.vue'
import OwnerChip from './OwnerChip.vue'
import Modal from './harness/Modal.vue'
import PdtBaseDrawer from './admin/PdtBaseDrawer.vue'
import AdminUsers from './admin/AdminUsers.vue'
import SnapshotPanel from './admin/SnapshotPanel.vue'

const { pdt, status, modulesByScope, isReadonly } = useDashboard()
const { me } = useAuth()
const { canEdit } = useEditableModules()

const canEnterPdtAdmin = computed(() => !!(me.value && (me.value.is_super || me.value.is_pdt_admin)))
const { ensureContacts } = useContactCache()
onMounted(() => { ensureContacts() })

/* 优先用配置的 overview_cards;无则回退到 modulesByScope.pdt(老 schema 自动适配) */
const cards = computed(() => {
  const oc = pdt.value?.overview_cards
  if (Array.isArray(oc) && oc.length) {
    /* overview_cards 关联到 modules.json 中 scope=pdt 的模块,通过 module_id 引用 */
    return oc.map(c => {
      const mod = modulesByScope.value.pdt.find(m => m.id === c.module_id)
      return {
        id: c.id,
        name: c.name || mod?.name || '未命名',
        owner_open_id: c.owner_open_id || mod?.owner_open_id,
        module: mod, // 真正的 module 对象(用于状态/编辑权限)
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

function statusOf(card) { return status.value?.[card.module.id] || null }
function colorOf(card) { return statusOf(card)?.module_color || 'gray' }
function kpisOf(card) { return kpiItemsOf(statusOf(card), card.kpi_fields) }
function risksFor(card) { return card.show_risk ? risksOf(statusOf(card)) : [] }

const editing = ref(null)
const dialogMode = ref('edit')
function openEdit(card) {
  if (canEdit(card.module.id)) {
    dialogMode.value = 'edit'
    editing.value = card.module
  }
}
function openCreate() {
  dialogMode.value = 'create'
  editing.value = { id: '__new__', name: '', group: '总览', scope: 'pdt', kpi_fields: [], sub_items: [] }
}
function closeEdit() { editing.value = null; dialogMode.value = 'edit' }

const showAdminTool = ref('') // '' | 'pdt-base' | 'people' | 'snapshots'
function openAdminTool(name) { showAdminTool.value = name }
function closeAdminTool() { showAdminTool.value = '' }

const { current, pushView } = useView()
const sub = computed(() => current.value.sub || 'timeline')
function switchSub(s) {
  pushView({ ...current.value, sub: s })
}
</script>

<template>
  <div class="pdt-overview">
    <div class="head">
      <StatusLegend />
      <div v-if="canEnterPdtAdmin && !isReadonly" class="admin-tools">
        <button
          class="tool-btn"
          v-tooltip="'编辑 PDT 名称、SOP 等基础信息'"
          @click="openAdminTool('pdt-base')"
        >⚙ PDT 基础</button>
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
    </div>

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
    </nav>

    <template v-if="sub === 'timeline'">
      <TimelineBar :milestones="pdt?.milestones || []" />
      <section v-if="canEnterPdtAdmin && !isReadonly" class="milestone-inline">
        <header class="mi-head">
          <h3>编辑里程碑</h3>
          <span class="mi-hint">所见即所得 · 改动保存后甘特图即时刷新</span>
        </header>
        <MilestoneEditor :show-preview="false" />
      </section>
    </template>

    <div v-if="sub === 'kanban' && !cards.length && !(canEnterPdtAdmin && !isReadonly)" class="empty">
      暂无 PDT 级总览卡片,请管理员添加。
    </div>

    <div v-else-if="sub === 'kanban'" class="cards-grid">
      <article
        v-for="card in cards"
        :key="card.id"
        class="card"
        :class="`tone-${colorOf(card)}`"
      >
        <header class="card-head">
          <span class="card-name">{{ card.name }}</span>
          <ModuleStatusDots
            :color="colorOf(card)"
            :editable="canEdit(card.module.id)"
            :note="(risksFor(card)[0] || {}).text"
            @edit="openEdit(card)"
          />
        </header>

        <div class="kpis-block">
          <div class="section-label">
            <span class="sl-en">KPI</span>
            <span class="sl-cn">关键指标</span>
          </div>
          <table v-if="kpisOf(card).length" class="kpis">
            <tbody>
              <tr v-for="(kpi, i) in kpisOf(card)" :key="i">
                <td class="k-name">{{ kpi.label }}</td>
                <td class="k-value">{{ kpi.value || '—' }}</td>
                <td class="k-target">{{ kpi.target || '' }}</td>
                <td class="k-light">
                  <span v-if="kpi.color" class="kpi-dot" :class="`tone-${kpi.color}`" :title="kpi.color"></span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="section-empty">— 暂无 —</div>
        </div>

        <div class="risks-block">
          <div class="section-label">
            <span class="sl-en">ISSUES · {{ risksFor(card).length }}</span>
            <span class="sl-cn">重点问题</span>
          </div>
          <ul v-if="risksFor(card).length" class="risks">
            <li
              v-for="(r, i) in risksFor(card)"
              :key="i"
              class="risk-line"
              :class="`sev-${r.severity}`"
            >{{ r.text }}</li>
          </ul>
          <div v-else class="section-empty">— 暂无 —</div>
        </div>

        <footer class="card-foot">
          <OwnerChip :open-id="card.owner_open_id" prefix="Owner: " fallback="未指派" />
          <button
            v-if="canEdit(card.module.id)"
            class="edit-btn"
            v-tooltip="'编辑该卡片对应模块的状态、KPI 与风险'"
            @click="openEdit(card)"
          >编辑</button>
        </footer>
      </article>

      <article
        v-if="canEnterPdtAdmin && !isReadonly"
        class="card add-card"
        v-tooltip="'新建一张 PDT 级总览卡片(scope=pdt)'"
        @click="openCreate"
      >
        <span class="plus">+</span>
        <span class="add-lbl">新增卡片</span>
      </article>
    </div>

    <StatusEditDialog
      :open="!!editing"
      :module="editing"
      :current="editing && dialogMode === 'edit' ? status?.[editing.id] : {}"
      :mode="dialogMode"
      :can-edit-structure="canEnterPdtAdmin && !isReadonly"
      @close="closeEdit"
    />

    <Modal :open="showAdminTool === 'pdt-base'" title="PDT 基础信息" width="640px" @close="closeAdminTool">
      <PdtBaseDrawer />
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
.pdt-overview { padding: 18px 0 32px; }
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0 24px 14px;
  gap: 16px;
  flex-wrap: wrap;
}
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

.empty { text-align: center; padding: 64px 24px; color: var(--text-muted); }

.milestone-inline {
  margin: 8px 24px 24px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--shadow-sm);
}
.milestone-inline .mi-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-subtle);
}
.milestone-inline .mi-head h3 { margin: 0; font-size: 14px; font-weight: 700; }
.milestone-inline .mi-hint { font-size: 11px; color: var(--text-dim); }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
  padding: 0 24px;
}

/* ===== 样板 B · Report 体 ===== */
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 16px 18px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
  position: relative;
  overflow: hidden;
  font-feature-settings: 'tnum' on;
}
.card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--status-gray);
  border-radius: var(--radius) 0 0 var(--radius);
}
.card.tone-green::before  { background: var(--status-green); }
.card.tone-yellow::before { background: var(--status-yellow); }
.card.tone-red::before    { background: var(--status-red); }
.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: var(--accent-soft);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--text);
}
.card-name {
  font-family: 'Source Han Serif SC', 'Songti SC', 'STSong', 'Noto Serif CJK SC', serif;
  font-weight: 600;
  font-size: 17px;
  letter-spacing: 1px;
  color: var(--text);
}

.kpis-block, .risks-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 2px;
}
.sl-en {
  font-size: 10px;
  letter-spacing: 3px;
  color: var(--text-dim);
  font-weight: 600;
  text-transform: uppercase;
}
.sl-cn {
  font-family: 'Source Han Serif SC', 'Songti SC', 'STSong', 'Noto Serif CJK SC', serif;
  letter-spacing: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.section-empty {
  font-size: 12px;
  color: var(--text-dim);
  font-style: italic;
  padding: 2px 0;
}

.kpis {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.kpis td {
  padding: 6px 0;
  border-bottom: 1px dotted var(--border-subtle);
  vertical-align: baseline;
}
.kpis tr:last-child td { border-bottom: 0; }
.k-name  { color: var(--text-muted); }
.k-value {
  text-align: right;
  font-weight: 600;
  font-size: 16px;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  width: 72px;
}
.k-target {
  text-align: right;
  font-size: 11px;
  color: var(--text-dim);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  width: 56px;
}
.k-light { width: 14px; text-align: right; padding-left: 6px; }
.kpi-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 2px;
  background: var(--status-gray);
  vertical-align: middle;
}
.kpi-dot.tone-green  { background: var(--status-green); }
.kpi-dot.tone-yellow { background: var(--status-yellow); }
.kpi-dot.tone-red    { background: var(--status-red); }

.risks {
  list-style: none;
  margin: 0;
  padding: 0;
}
.risk-line {
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--text);
  padding: 5px 0 5px 16px;
  border-bottom: 1px dotted var(--border-subtle);
  position: relative;
}
.risks li:last-child { border-bottom: 0; }
.risk-line::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 13px;
  width: 5px;
  height: 5px;
  background: var(--text-muted);
  border-radius: 50%;
}
.risk-line.sev-yellow::before { background: var(--status-yellow); }
.risk-line.sev-red::before    { background: var(--status-red); }

.card-foot {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-muted);
  padding-top: 10px;
  border-top: 1px solid var(--text);
}
.owner {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: var(--radius);
  font-weight: 500;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.edit-btn {
  font-size: 12px;
  padding: 4px 12px;
  letter-spacing: 2px;
  border-radius: var(--radius);
}

.add-card {
  border: 1px dashed var(--border);
  background: var(--panel-soft);
  box-shadow: none;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  cursor: pointer;
  color: var(--text-muted);
  transition: color 120ms, border-color 120ms, background 120ms;
}
.add-card::before { display: none; }
.add-card:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--panel);
  transform: none;
}
.add-card .plus {
  font-size: 36px;
  line-height: 1;
  font-weight: 300;
}
.add-card .add-lbl {
  font-size: 13px;
  letter-spacing: 4px;
}
</style>
