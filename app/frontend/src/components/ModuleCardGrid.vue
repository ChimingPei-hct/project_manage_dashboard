<script setup>
/**
 * ModuleCardGrid — PDT 总览看板 / LTC 看板共享的卡片网格(harness 红线:不允许在外层页面内嵌写卡片)。
 *
 * Props:
 * - cards: Array<{id, name, owner_open_id, module, kpi_fields, show_risk, order}>
 *     每个 card 必须带 module(真正用于状态/编辑权限的 module 对象)
 * - ltcId?: String  LTC 上下文(传给 StatusEditDialog 路由 status key)
 * - canEnterAdmin: Boolean  控制「+ 新增卡片」和编辑结构入口可见性
 * - createDefaults: Object  新建卡片时的预设(scope/ltc_id 等)
 * - templateBadge: Boolean  是否对 scope='ltc_template' 的卡渲染「基础」徽标(LTC 视图传 true)
 * - statusKeyOf: Function  (module) => String  外部注入的 status key 计算(默认 module.id)
 * - emptyHint?: String  无卡时的占位文案
 */
import { computed, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { kpiItemsOf, risksOf } from '../composables/useStatusHelpers.js'
import ModuleStatusDots from './ModuleStatusDots.vue'
import StatusEditDialog from './StatusEditDialog.vue'
import OwnerChip from './OwnerChip.vue'

const props = defineProps({
  cards: { type: Array, required: true },
  ltcId: { type: String, default: '' },
  canEnterAdmin: { type: Boolean, default: false },
  createDefaults: { type: Object, default: () => ({ scope: 'pdt' }) },
  templateBadge: { type: Boolean, default: false },
  statusKeyOf: { type: Function, default: null },
  emptyHint: { type: String, default: '暂无卡片,请管理员添加。' },
})

const { status, isReadonly } = useDashboard()
const { canEdit } = useEditableModules()

function keyOf(mod) {
  if (typeof props.statusKeyOf === 'function') return props.statusKeyOf(mod)
  return mod?.id || ''
}

function statusOf(card) { return status.value?.[keyOf(card.module)] || null }
function colorOf(card) { return statusOf(card)?.module_color || 'gray' }
function kpisOf(card) { return kpiItemsOf(statusOf(card), card.kpi_fields) }
function risksFor(card) { return card.show_risk ? risksOf(statusOf(card)) : [] }

const editing = ref(null)
const dialogMode = ref('edit')

function openEdit(card) {
  if (!canEdit(card.module.id, props.ltcId)) return
  dialogMode.value = 'edit'
  editing.value = card.module
}
function openCreate() {
  dialogMode.value = 'create'
  editing.value = {
    id: '__new__',
    name: '',
    group: props.createDefaults.group || '',
    scope: props.createDefaults.scope || 'pdt',
    ltc_id: props.createDefaults.ltc_id || props.ltcId || '',
    kpi_fields: [],
    sub_items: [],
  }
}
function closeEdit() { editing.value = null; dialogMode.value = 'edit' }

const dialogStatusKey = computed(() => editing.value ? keyOf(editing.value) : '')

const showAddTile = computed(() => props.canEnterAdmin && !isReadonly.value)
const hasEmpty = computed(() => !props.cards.length && !showAddTile.value)
</script>

<template>
  <div v-if="hasEmpty" class="empty">{{ emptyHint }}</div>
  <div v-else class="cards-grid">
    <article
      v-for="card in cards"
      :key="card.id"
      class="card"
      :class="`tone-${colorOf(card)}`"
    >
      <span
        v-if="templateBadge && card.module.scope === 'ltc_template'"
        class="card-badge"
        v-tooltip="'基础卡:由 PDT Admin 维护,所有 LTC 共享结构'"
      >基础</span>

      <header class="card-head">
        <span class="card-name">{{ card.name }}</span>
        <ModuleStatusDots
          :color="colorOf(card)"
          :editable="canEdit(card.module.id, ltcId)"
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
          v-if="canEdit(card.module.id, ltcId)"
          class="edit-btn"
          v-tooltip="'编辑该卡片对应模块的状态、KPI 与风险'"
          @click="openEdit(card)"
        >编辑</button>
      </footer>
    </article>

    <article
      v-if="showAddTile"
      class="card add-card"
      v-tooltip="createDefaults.scope === 'ltc' ? '新建一张本 LTC 私有卡(scope=ltc)' : '新建一张 PDT 级总览卡片(scope=pdt)'"
      @click="openCreate"
    >
      <span class="plus">+</span>
      <span class="add-lbl">新增卡片</span>
    </article>
  </div>

  <StatusEditDialog
    :open="!!editing"
    :module="editing"
    :status-key="dialogStatusKey"
    :ltc-id="ltcId"
    :current="editing && dialogMode === 'edit' ? status?.[dialogStatusKey] : {}"
    :mode="dialogMode"
    :can-edit-structure="canEnterAdmin && !isReadonly"
    @close="closeEdit"
  />
</template>

<style scoped>
.empty { text-align: center; padding: 64px 24px; color: var(--text-muted); }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
  padding: 0 24px;
}

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

.card-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: var(--radius);
  background: var(--panel-soft);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
  letter-spacing: 1px;
  z-index: 1;
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

.kpis-block, .risks-block { display: flex; flex-direction: column; gap: 6px; }

.section-label {
  display: flex; align-items: baseline; justify-content: space-between;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 2px;
}
.sl-en {
  font-size: 10px; letter-spacing: 3px;
  color: var(--text-dim); font-weight: 600;
  text-transform: uppercase;
}
.sl-cn {
  font-family: 'Source Han Serif SC', 'Songti SC', 'STSong', 'Noto Serif CJK SC', serif;
  letter-spacing: 4px; font-size: 12px; color: var(--text-muted);
}

.section-empty {
  font-size: 12px; color: var(--text-dim);
  font-style: italic; padding: 2px 0;
}

.kpis { width: 100%; border-collapse: collapse; font-size: 13px; }
.kpis td {
  padding: 6px 0;
  border-bottom: 1px dotted var(--border-subtle);
  vertical-align: baseline;
}
.kpis tr:last-child td { border-bottom: 0; }
.k-name  { color: var(--text-muted); }
.k-value {
  text-align: right; font-weight: 600; font-size: 16px;
  color: var(--text); font-variant-numeric: tabular-nums;
  white-space: nowrap; width: 72px;
}
.k-target {
  text-align: right; font-size: 11px; color: var(--text-dim);
  font-variant-numeric: tabular-nums; white-space: nowrap; width: 56px;
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

.risks { list-style: none; margin: 0; padding: 0; }
.risk-line {
  font-size: 12.5px; line-height: 1.65;
  color: var(--text);
  padding: 5px 0 5px 16px;
  border-bottom: 1px dotted var(--border-subtle);
  position: relative;
}
.risks li:last-child { border-bottom: 0; }
.risk-line::before {
  content: '';
  position: absolute;
  left: 4px; top: 13px;
  width: 5px; height: 5px;
  background: var(--text-muted);
  border-radius: 6px;
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
.add-card .plus { font-size: 36px; line-height: 1; font-weight: 300; }
.add-card .add-lbl { font-size: 13px; letter-spacing: 4px; }
</style>
