<script setup>
import { computed, ref, toRef, watch } from 'vue'
import { api } from '../api/client.js'
import { useDashboard } from '../composables/useDashboard.js'
import { kpiItemsOf, risksOf, subRiskOf } from '../composables/useStatusHelpers.js'
import { adminApi, newId } from '../composables/useAdminApi.js'
import { useContactCache, displayName } from '../composables/useContactCache.js'
import { useEscClose } from '../composables/useEscClose.js'
import UserSearchInput from './UserSearchInput.vue'
import ConfirmDialog from './harness/ConfirmDialog.vue'

/**
 * 模块编辑弹窗 —— 三块布局:基本信息 / KPI / 风险。
 * 约束:design/07 §风险说明必填、design/13 §3.3。
 * 端点:状态走 PUT /api/status/{id};结构走 PUT/POST/DELETE /api/modules/{id}。
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  module: { type: Object, default: null },
  current: { type: Object, default: () => ({}) },
  focusSubId: { type: String, default: '' },
  statusKey: { type: String, default: '' },
  ltcId: { type: String, default: '' },
  mode: { type: String, default: 'edit' }, // 'edit' | 'create'
  canEditStructure: { type: Boolean, default: false },
  createDefaults: { type: Object, default: () => ({ scope: 'pdt', ltc_id: null, group: '总览' }) },
})
const emit = defineEmits(['close', 'saved', 'created', 'deleted', 'updated'])

useEscClose(toRef(props, 'open'), () => emit('close'))

const COLORS = ['green', 'yellow', 'red']
const COLOR_LABEL = { green: '绿/正常', yellow: '黄/预警', red: '红/Block', gray: '灰/未报' }

const { refresh, modules } = useDashboard()
const { contacts, ensureContacts } = useContactCache()

/* === 状态 draft === */
const moduleColor = ref('gray')
const subColors = ref({})
const subRisks = ref({})
const kpiItems = ref([])
const risks = ref([])
const saving = ref(false)
const errorMsg = ref('')
const toast = ref('')

/* === 结构 draft === */
const sName = ref('')
const sGroup = ref('')
const sOwnerOpenId = ref(null)
const sOwnerName = ref('')
const confirmDeleteOpen = ref(false)

function ownerNameOf(openId) {
  if (!openId) return ''
  const u = (contacts.value || []).find(x => x.open_id === openId)
  return u?.name || displayName(openId) || openId
}

function resetStatus() {
  const c = props.current || {}
  moduleColor.value = c.module_color || 'gray'
  subColors.value = { ...(c.sub_items_color || {}) }
  subRisks.value = { ...(c.sub_items_risk || {}) }
  kpiItems.value = kpiItemsOf(c, props.module?.kpi_fields || [])
  risks.value = risksOf(c)
  errorMsg.value = ''
  toast.value = ''
  for (const s of props.module?.sub_items || []) {
    if (!subColors.value[s.id]) subColors.value[s.id] = 'gray'
    if (subRisks.value[s.id] === undefined) subRisks.value[s.id] = ''
  }
}

function resetStructure() {
  const m = props.module
  if (props.mode === 'create' || !m) {
    sName.value = ''
    sGroup.value = props.createDefaults?.group || '总览'
    sOwnerOpenId.value = null
    sOwnerName.value = ''
  } else {
    sName.value = m.name || ''
    sGroup.value = m.group || ''
    sOwnerOpenId.value = m.owner_open_id || null
    sOwnerName.value = ownerNameOf(m.owner_open_id)
  }
}

watch(() => [props.open, props.module?.id, props.mode], () => {
  if (props.open) {
    resetStatus()
    resetStructure()
    ensureContacts()
  }
}, { immediate: true })

/* === 派生校验 === */
const anyNonGreen = computed(() => {
  if (moduleColor.value !== 'green') return true
  return Object.values(subColors.value).some(v => v && v !== 'green')
})
const hasRiskText = computed(() => risks.value.some(r => (r.text || '').trim()))
const riskMissing = computed(() => false)

/* === 编辑操作 === */
function pickModuleColor(c) { moduleColor.value = c }
function pickSubColor(sid, c) { subColors.value = { ...subColors.value, [sid]: c } }
function addKpi() { kpiItems.value.push({ goal: '', actual: '', color: '' }) }
function removeKpi(i) { kpiItems.value.splice(i, 1) }
function addRisk() { risks.value.push({ severity: 'red', text: '' }) }
function removeRisk(i) { risks.value.splice(i, 1) }

function pickOwner(u) {
  sOwnerOpenId.value = u?.open_id || null
  sOwnerName.value = u?.name || ''
}
function clearOwner() {
  sOwnerOpenId.value = null
  sOwnerName.value = ''
}

const structureDirty = computed(() => {
  if (props.mode === 'create') return true
  const m = props.module || {}
  if (sName.value !== (m.name || '')) return true
  if (sGroup.value !== (m.group || '')) return true
  if ((sOwnerOpenId.value || null) !== (m.owner_open_id || null)) return true
  return false
})

function buildStructureBody() {
  return {
    name: sName.value.trim(),
    group: sGroup.value.trim() || '总览',
    owner_open_id: sOwnerOpenId.value || null,
  }
}

/* === 保存(edit) === */
async function save() {
  errorMsg.value = ''
  if (riskMissing.value) {
    errorMsg.value = '存在非绿项时必须至少填写一条风险'
    addRisk()
    return
  }
  saving.value = true
  try {
    /* 1) status */
    const cleanKpi = kpiItems.value
      .map(k => ({
        goal: (k.goal || '').trim(),
        actual: (k.actual || '').trim(),
        color: COLORS.includes(k.color) && k.color !== 'gray' ? k.color : '',
      }))
      .filter(k => k.goal || k.actual)
    const cleanRisks = risks.value
      .map(r => ({ severity: r.severity || 'red', text: (r.text || '').trim() }))
      .filter(r => r.text)
    const cleanSubRisks = {}
    for (const [k, v] of Object.entries(subRisks.value)) {
      const t = (v || '').trim()
      if (t) cleanSubRisks[k] = t
    }
    const key = props.statusKey || props.module.id
    await api.put(`/api/status/${encodeURIComponent(key)}`, {
      module_color: moduleColor.value,
      sub_items_color: subColors.value,
      sub_items_risk: cleanSubRisks,
      kpi_items: cleanKpi,
      risks: cleanRisks,
      risk_note: cleanRisks[0]?.text || '',
    })

    /* 2) structure(仅 PDT Admin 改过才发) */
    if (props.canEditStructure && structureDirty.value) {
      const body = buildStructureBody()
      if (!body.name) { errorMsg.value = '卡名不能为空'; saving.value = false; return }
      const updated = await adminApi.updateModule(props.module.id, body)
      const arr = modules.value || []
      const idx = arr.findIndex(m => m.id === props.module.id)
      if (idx >= 0) modules.value = [...arr.slice(0, idx), { ...arr[idx], ...updated }, ...arr.slice(idx + 1)]
      emit('updated', { id: props.module.id, patch: updated })
    } else {
      await refresh()
    }

    emit('saved')
    emit('close')
  } catch (e) {
    if (e.status === 422) errorMsg.value = typeof e.payload?.detail === 'string' ? e.payload.detail : '校验失败'
    else if (e.status === 403) { toast.value = '无权编辑此模块'; setTimeout(() => { toast.value = '' }, 3000) }
    else errorMsg.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

/* === 创建(create) === */
async function createCard() {
  errorMsg.value = ''
  const body = buildStructureBody()
  if (!body.name) { errorMsg.value = '卡名不能为空'; return }
  saving.value = true
  try {
    const id = newId()
    const scope = props.createDefaults?.scope || 'pdt'
    const ltc_id = props.createDefaults?.ltc_id || props.ltcId || null
    const full = {
      id,
      scope,
      ltc_id: scope === 'ltc' ? ltc_id : null,
      sub_items: [],
      kpi_fields: [],
      order: (modules.value || []).filter(m => m.scope === scope).length + 1,
      ...body,
    }
    const created = await adminApi.createModule(full)
    modules.value = [...(modules.value || []), created]

    /* 若用户在新增弹框里也填了 KPI / 风险 / 整体色,串联写入 status */
    const cleanKpi = kpiItems.value
      .map(k => ({
        goal: (k.goal || '').trim(),
        actual: (k.actual || '').trim(),
        color: COLORS.includes(k.color) && k.color !== 'gray' ? k.color : '',
      }))
      .filter(k => k.goal || k.actual)
    const cleanRisks = risks.value
      .map(r => ({ severity: r.severity || 'red', text: (r.text || '').trim() }))
      .filter(r => r.text)
    const hasStatus =
      cleanKpi.length || cleanRisks.length ||
      (moduleColor.value && moduleColor.value !== 'gray')
    if (hasStatus) {
      try {
        await api.put(`/api/status/${encodeURIComponent(created.id || id)}`, {
          module_color: moduleColor.value || 'gray',
          sub_items_color: {},
          sub_items_risk: {},
          kpi_items: cleanKpi,
          risks: cleanRisks,
          risk_note: cleanRisks[0]?.text || '',
        })
      } catch (e) {
        toast.value = '卡片已创建,状态未保存,请打开编辑补填'
        await refresh()
        emit('created', created)
        setTimeout(() => { toast.value = ''; emit('close') }, 2500)
        return
      }
    }
    await refresh()
    emit('created', created)
    emit('close')
  } catch (e) {
    errorMsg.value = e.payload?.detail || e.message || '创建失败'
  } finally {
    saving.value = false
  }
}

async function doDelete() {
  confirmDeleteOpen.value = false
  try {
    await adminApi.deleteModule(props.module.id)
    modules.value = (modules.value || []).filter(m => m.id !== props.module.id)
    emit('deleted', props.module.id)
    emit('close')
  } catch (e) {
    errorMsg.value = e.payload?.detail || e.message || '删除失败'
  }
}

function onBackdrop(e) { if (e.target === e.currentTarget) emit('close') }

const SCOPE_LABEL = { pdt: 'PDT 总览', ltc: '本 LTC 私有卡', ltc_template: '基础卡(所有 LTC 共享)' }
const headerTitle = computed(() => {
  if (props.mode === 'create') {
    const sc = props.createDefaults?.scope || 'pdt'
    if (sc === 'ltc') return '新建 LTC 私有卡'
    if (sc === 'ltc_template') return '新建基础卡'
    return '新建 PDT 卡片'
  }
  return props.module?.name || '模块编辑'
})
const headerSub = computed(() => {
  if (props.mode === 'create') {
    const sc = props.createDefaults?.scope || 'pdt'
    return `${SCOPE_LABEL[sc] || sc} · 可一次填齐基本信息 / 目标 / 风险 / 状态色`
  }
  return `${props.module?.group || ''} · ${SCOPE_LABEL[props.module?.scope] || props.module?.scope || ''}`
})

const isTemplateCard = computed(() => props.module?.scope === 'ltc_template')
const deleteBody = computed(() => {
  if (isTemplateCard.value) {
    return `确认删除基础卡「${props.module?.name || ''}」?\n注意:基础卡删除会影响所有 LTC,所有 LTC 上的该卡及状态都会同步消失,历史流保留。`
  }
  return `确认删除卡片「${props.module?.name || ''}」?\n本卡状态会被清除,历史流保留。`
})
</script>

<template>
  <div v-if="open" class="edit-mask" @click="onBackdrop">
    <div class="edit-box" role="dialog" :aria-label="`编辑 ${module?.name || ''}`">
      <header class="dlg-head">
        <div>
          <h3>{{ headerTitle }}</h3>
          <p class="sub">{{ headerSub }}</p>
        </div>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗,放弃未保存修改'">×</button>
      </header>

      <!-- Block 1:基本信息 -->
      <section class="block block-basic">
        <div class="block-title">基本信息</div>
        <div class="basic-grid">
          <label class="field">
            <span class="lbl">卡名</span>
            <input v-model="sName" :readonly="!canEditStructure" placeholder="如:性能专项" />
          </label>
          <div class="field field-owner">
            <span class="lbl">Owner</span>
            <UserSearchInput
              v-if="canEditStructure"
              :modelValue="sOwnerName"
              @update:modelValue="v => sOwnerName = v"
              @select="pickOwner"
              placeholder="搜索人员姓名…"
            />
            <input v-else :value="sOwnerName || '未指派'" readonly class="readonly" />
            <button
              v-if="canEditStructure && sOwnerOpenId"
              class="mini-del owner-clear"
              v-tooltip="'清除 Owner 绑定'"
              @click="clearOwner"
            >×</button>
          </div>
        </div>

        <div class="basic-row light-row">
          <span class="lbl">整体状态灯</span>
          <div class="color-row">
            <button
              v-for="c in COLORS"
              :key="c"
              type="button"
              class="swatch"
              :class="{ active: moduleColor === c }"
              :style="{ background: `var(--status-${c})` }"
              v-tooltip="`将整体状态置为 ${COLOR_LABEL[c]}`"
              @click="pickModuleColor(c)"
            >{{ c === moduleColor ? '✓' : '' }}</button>
          </div>
        </div>

        <div v-if="canEditStructure && mode === 'edit'" class="basic-foot">
          <button
            class="danger"
            v-tooltip="'从总览删除此卡(状态同步清除,历史保留)'"
            @click="confirmDeleteOpen = true"
          >🗑 删除该卡</button>
        </div>
      </section>

      <!-- Block 2:关键目标 -->
      <section class="block">
        <div class="block-title">
          <span>关键目标</span>
          <button
            v-if="canEditStructure"
            class="mini-add"
            v-tooltip="'新增一组指标(目标 / 现状 / 灯)'"
            @click="addKpi"
          >+ 加目标</button>
        </div>
        <div v-if="!kpiItems.length" class="hint">暂无指标</div>
        <div v-else class="kpi-table">
          <div class="kpi-row head">
            <span>目标</span><span>现状</span><span>灯</span><span></span>
          </div>
          <div v-for="(k, i) in kpiItems" :key="i" class="kpi-row">
            <textarea v-model="k.goal" rows="2" placeholder="如:CPU 占用率 ≤70%" v-tooltip="'本组指标的目标(应该是什么)'"></textarea>
            <textarea v-model="k.actual" rows="2" placeholder="如:78%" v-tooltip="'本组指标的现状(实际是什么)'"></textarea>
            <select v-model="k.color" v-tooltip="'本组指标的当前红绿灯'">
              <option value="">—</option>
              <option value="green">🟢 绿/达成</option>
              <option value="yellow">🟡 黄/略差</option>
              <option value="red">🔴 红/未达</option>
            </select>
            <button
              v-if="canEditStructure"
              class="mini-del"
              v-tooltip="'删除该组指标'"
              @click="removeKpi(i)"
            >✕</button>
            <span v-else></span>
          </div>
        </div>
      </section>

      <!-- Block 3:风险 -->
      <section class="block">
        <div class="block-title">
          <span>风险 / 重点问题</span>
          <button class="mini-add" v-tooltip="'新增一条风险'" @click="addRisk">+ 风险</button>
        </div>
        <div v-if="!risks.length" class="hint">暂无风险,点击「+ 风险」添加</div>
        <div v-else class="risk-list">
          <div v-for="(r, i) in risks" :key="i" class="risk-row">
            <textarea
              v-model="r.text"
              rows="2"
              placeholder="描述当前阻塞 / 风险 / 待跟进事项"
              v-tooltip="'风险文本,会显示在卡片底部的「重点问题」区'"
            />
            <button class="mini-del" v-tooltip="'删除该条风险'" @click="removeRisk(i)">✕</button>
          </div>
        </div>
      </section>

      <p v-if="errorMsg" class="err-banner">{{ errorMsg }}</p>

      <footer class="dlg-foot">
        <button @click="emit('close')" v-tooltip="'放弃未保存的修改'">取消</button>
        <button
          v-if="mode === 'create'"
          class="primary"
          :disabled="saving || !sName.trim()"
          v-tooltip="'创建卡片(含已填写的目标 / 风险 / 状态色)'"
          @click="createCard"
        >{{ saving ? '创建中…' : '创建' }}</button>
        <button
          v-else
          class="primary"
          :disabled="saving || riskMissing"
          v-tooltip="riskMissing ? '风险说明不能为空' : '一键保存状态与结构改动'"
          @click="save"
        >{{ saving ? '保存中…' : '保存' }}</button>
      </footer>

      <div v-if="toast" class="toast">{{ toast }}</div>

      <ConfirmDialog
        :open="confirmDeleteOpen"
        :title="isTemplateCard ? '删除基础卡' : '删除卡片'"
        :body="deleteBody"
        confirm-text="删除"
        @confirm="doDelete"
        @cancel="confirmDeleteOpen = false"
      />
    </div>
  </div>
</template>

<style scoped>
.edit-mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000; backdrop-filter: blur(2px);
}
.edit-box {
  background: var(--panel); border-radius: var(--radius);
  padding: 18px 22px; min-width: 540px; max-width: 680px; width: 92vw;
  max-height: 88vh; overflow-y: auto;
  box-shadow: var(--shadow-lg);
  position: relative;
}
.dlg-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
h3 { margin: 0; font-size: 16px; font-weight: 700; }
.sub { margin: 2px 0 0; font-size: 12px; color: var(--text-muted); }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; }
.close:hover { color: var(--accent); background: transparent; }

.block { margin-bottom: 14px; }
.block-title {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; color: var(--text); font-weight: 700;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-subtle);
}
.req { color: var(--status-red); margin-left: 6px; font-size: 11px; font-weight: 500; }

.block-basic {
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 12px 14px;
}
.block-basic .block-title { border-bottom: 1px solid var(--border); }
.basic-grid { display: grid; grid-template-columns: 1.2fr 1fr 1.4fr; gap: 8px; }
.field { display: flex; flex-direction: column; gap: 3px; position: relative; }
.field .lbl { font-size: 11px; color: var(--text-muted); }
.field input { width: 100%; font-size: 13px; padding: 5px 8px; }
.field input.readonly { background: var(--panel); color: var(--text-muted); }
.field-owner { position: relative; }
.owner-clear { position: absolute; right: 4px; top: 22px; font-size: 11px; padding: 1px 5px; }

.basic-row.light-row {
  display: flex; align-items: center; gap: 12px;
  margin-top: 10px;
}
.basic-row .lbl { font-size: 11px; color: var(--text-muted); }
.basic-foot { display: flex; justify-content: flex-end; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border-subtle); }

.color-row { display: flex; gap: 4px; }
.swatch {
  width: 34px; height: 26px; border-radius: var(--radius);
  border: 1px solid var(--border); color: #fff; font-size: 13px;
  padding: 0; cursor: pointer;
}
.swatch.sm { width: 22px; height: 20px; font-size: 10px; }
.swatch.active { outline: 2px solid var(--accent); outline-offset: 1px; }

.sub-list { display: flex; flex-direction: column; gap: 6px; }
.sub-row { padding: 6px 8px; border-radius: var(--radius); background: var(--panel-soft); border: 1px solid var(--border-subtle); }
.sub-row.focus { background: var(--accent-soft); border-color: var(--accent); }
.sub-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.sub-name { font-size: 13px; font-weight: 500; }
.sub-note-input { width: 100%; margin-top: 6px; font-size: 12px; }

.mini-add, .mini-del {
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--panel); cursor: pointer;
}
.mini-add { color: var(--accent); border-color: var(--accent); }
.mini-del { color: var(--text-muted); }
.mini-del:hover { color: var(--status-red); border-color: var(--status-red); }

.kpi-table { display: flex; flex-direction: column; gap: 4px; }
.kpi-row { display: grid; grid-template-columns: 1.4fr 1fr 110px 28px; gap: 6px; align-items: stretch; }
.kpi-row.head { font-size: 11px; color: var(--text-dim); padding: 0 4px; align-items: center; }
.kpi-row input, .kpi-row select { font-size: 12.5px; padding: 4px 8px; }
.kpi-row textarea { font-size: 12.5px; padding: 6px 8px; resize: vertical; min-height: 40px; font-family: inherit; }
.kpi-row select { align-self: start; }
.kpi-row .mini-del { align-self: start; }

.risk-list { display: flex; flex-direction: column; gap: 6px; }
.risk-row { display: grid; grid-template-columns: 1fr 28px; gap: 6px; align-items: stretch; padding: 6px; border-radius: var(--radius); background: var(--status-red-bg); }
.risk-row textarea { font-size: 12.5px; padding: 6px 8px; resize: vertical; min-height: 36px; }

.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.hint.err { color: var(--status-red); }

.err-banner {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0 0 10px;
}

.dlg-foot { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; padding-top: 12px; border-top: 1px solid var(--border-subtle); }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.danger:hover { opacity: 0.9; }
.toast {
  position: absolute; left: 50%; bottom: 16px; transform: translateX(-50%);
  background: rgba(15,23,42,0.95); color: #fff;
  padding: 6px 14px; border-radius: var(--radius); font-size: 12px;
}
</style>
