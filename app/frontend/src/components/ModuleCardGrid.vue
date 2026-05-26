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
  hideAddButton: { type: Boolean, default: false },
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

const showAdd = computed(() => props.canEnterAdmin && !isReadonly.value && !props.hideAddButton)
defineExpose({ openCreate })
const hasEmpty = computed(() => !props.cards.length && !(props.canEnterAdmin && !isReadonly.value))
const addTip = computed(() => props.createDefaults.scope === 'ltc'
  ? '新建一张本 LTC 私有卡(scope=ltc)'
  : '新建一张 PDT 级总览卡片(scope=pdt)')
</script>

<template>
  <div v-if="showAdd" class="cards-toolbar">
    <button
      type="button"
      class="add-btn"
      v-tooltip="addTip"
      @click="openCreate"
    ><span class="add-btn-plus">+</span>新增卡片</button>
  </div>

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
        <div class="card-head-top">
          <span class="card-name">{{ card.name }}</span>
          <div class="card-head-right">
            <OwnerChip
              class="card-owner"
              :open-id="card.owner_open_id"
              fallback="未指派"
              v-tooltip="'Owner:负责该卡片的填报与跟进'"
            />
            <ModuleStatusDots
              :color="colorOf(card)"
              :editable="canEdit(card.module.id, ltcId)"
              :note="(risksFor(card)[0] || {}).text"
              @edit="openEdit(card)"
            />
          </div>
        </div>
      </header>

      <div class="kpis-block">
        <div class="section-label">
          <span class="sl-cn">关键目标</span>
        </div>
        <div v-if="kpisOf(card).length" class="kpi-groups">
          <div v-for="(kpi, i) in kpisOf(card)" :key="i" class="kpi-group">
            <div class="kpi-row goal">
              <span class="kr-label">目标</span>
              <span class="kr-text">{{ kpi.goal || '—' }}</span>
              <span class="kpi-dot" :class="`tone-${kpi.color || 'gray'}`" :title="kpi.color || '未填'"></span>
            </div>
            <div class="kpi-row actual">
              <span class="kr-label">现状</span>
              <span class="kr-text">{{ kpi.actual || '—' }}</span>
            </div>
          </div>
        </div>
        <div v-else class="section-empty">— 暂无 —</div>
      </div>

      <div class="risks-block">
        <div class="section-label">
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
        <button
          v-if="canEdit(card.module.id, ltcId)"
          class="edit-btn"
          v-tooltip="'编辑该卡片对应模块的状态、KPI 与风险'"
          @click="openEdit(card)"
        >编辑</button>
      </footer>
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
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  padding: 0 24px;
}

/* ── 卡片:顶部 4px 状态色条 + 状态色微 tint 背景 + 强化 elevation ── */
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  padding: 22px 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition:
    box-shadow var(--transition),
    transform var(--transition),
    border-color var(--transition),
    background var(--transition);
  position: relative;
  overflow: hidden;
  font-feature-settings: 'tnum' on;
}
/* 顶部状态色横条 —— 最显眼的状态指示 */
.card::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 4px;
  background: var(--status-gray);
}
.card.tone-green  { background: linear-gradient(180deg, var(--status-green-bg) 0%, var(--panel) 96px); }
.card.tone-yellow { background: linear-gradient(180deg, var(--status-yellow-bg) 0%, var(--panel) 96px); }
.card.tone-red    { background: linear-gradient(180deg, var(--status-red-bg) 0%, var(--panel) 96px); }
.card.tone-green::before  { background: var(--status-green); }
.card.tone-yellow::before { background: var(--status-yellow); }
.card.tone-red::before    { background: var(--status-red); }
.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-3px);
  border-color: var(--border-strong);
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
  flex-direction: column;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
}
.card-head-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.card-head-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.card-owner {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-name {
  font-family: 'Source Han Serif SC', 'Songti SC', 'STSong', 'Noto Serif CJK SC', serif;
  font-weight: 600;
  font-size: 19px;
  letter-spacing: 1.5px;
  color: var(--text-strong);
  line-height: 1.3;
}

.kpis-block, .risks-block { display: flex; flex-direction: column; gap: 6px; }

.section-label {
  display: flex; align-items: baseline; justify-content: space-between;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 2px;
}
.sl-cn {
  font-family: 'Source Han Serif SC', 'Songti SC', 'STSong', 'Noto Serif CJK SC', serif;
  letter-spacing: 4px; font-size: 12px; color: var(--text-muted);
}

.section-empty {
  font-size: 12px; color: var(--text-dim);
  font-style: italic; padding: 2px 0;
}

.kpi-groups { display: flex; flex-direction: column; }
.kpi-group {
  padding: 6px 0;
  border-bottom: 1px dashed var(--border-subtle);
}
.kpi-group:last-child { border-bottom: 0; }
.kpi-row {
  display: flex; align-items: baseline; gap: 8px;
  font-size: 13px; line-height: 1.55;
}
.kpi-row .kr-label {
  flex: 0 0 28px;
  font-size: 11px; letter-spacing: 2px;
  color: var(--text-dim);
}
.kpi-row .kr-text {
  flex: 1 1 auto;
  white-space: pre-wrap; word-break: break-word;
  font-variant-numeric: tabular-nums;
}
.kpi-row.goal .kr-text {
  color: var(--text-muted);
}
.kpi-row.actual .kr-text {
  color: var(--text); font-weight: 600;
}
.kpi-row.goal .kpi-dot { margin-left: auto; flex: 0 0 auto; }
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
  justify-content: flex-end;
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

.cards-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 0 24px 10px;
}
.add-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  letter-spacing: 2px;
  padding: 5px 14px;
  border: 1px dashed var(--border);
  background: var(--panel-soft);
  color: var(--text-muted);
  border-radius: var(--radius);
  cursor: pointer;
  transition: color 120ms, border-color 120ms, background 120ms;
}
.add-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--panel);
}
.add-btn-plus {
  font-size: 16px;
  font-weight: 400;
  line-height: 1;
}
</style>
