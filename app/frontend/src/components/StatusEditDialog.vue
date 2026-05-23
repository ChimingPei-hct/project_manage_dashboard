<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api/client.js'
import { useDashboard } from '../composables/useDashboard.js'
import { kpiItemsOf, risksOf, subRiskOf } from '../composables/useStatusHelpers.js'

/**
 * 模块状态编辑弹窗(新结构化 schema)。
 * 约束:design/07 §风险说明必填、design/13 §3.3/§4.3/§5.3。
 * 单一入口:PUT /api/status/{module_id}。
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  module: { type: Object, default: null },
  current: { type: Object, default: () => ({}) },
  focusSubId: { type: String, default: '' },
  // 复合键 <ltc_id>::<module_id> 用于 ltc_template 模块;留空则用 module.id 兜底
  statusKey: { type: String, default: '' },
})
const emit = defineEmits(['close', 'saved'])

const COLORS = ['green', 'yellow', 'red', 'gray']
const COLOR_LABEL = { green: '绿/正常', yellow: '黄/预警', red: '红/Block', gray: '灰/未报' }

const moduleColor = ref('gray')
const subColors = ref({})
const subRisks = ref({}) // {sub_id: text}
const kpiItems = ref([]) // [{label, value, target}]
const risks = ref([]) // [{severity, text}]
const saving = ref(false)
const errorMsg = ref('')
const toast = ref('')

const { refresh } = useDashboard()

function reset() {
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

watch(() => [props.open, props.module?.id], () => {
  if (props.open) reset()
}, { immediate: true })

const anyNonGreen = computed(() => {
  if (moduleColor.value !== 'green') return true
  return Object.values(subColors.value).some(v => v && v !== 'green')
})
const hasRiskText = computed(() => risks.value.some(r => (r.text || '').trim()))
const riskMissing = computed(() => anyNonGreen.value && !hasRiskText.value)

function pickModuleColor(c) { moduleColor.value = c }
function pickSubColor(sid, c) { subColors.value = { ...subColors.value, [sid]: c } }

function addKpi() { kpiItems.value.push({ label: '', value: '', target: '' }) }
function removeKpi(i) { kpiItems.value.splice(i, 1) }
function addRisk(sev = 'red') { risks.value.push({ severity: sev, text: '' }) }
function removeRisk(i) { risks.value.splice(i, 1) }

function onBackdrop(e) { if (e.target === e.currentTarget) emit('close') }

async function save() {
  errorMsg.value = ''
  if (riskMissing.value) {
    errorMsg.value = '存在非绿项时必须至少填写一条风险'
    addRisk('red')
    return
  }
  saving.value = true
  try {
    const cleanKpi = kpiItems.value
      .map(k => ({ label: (k.label || '').trim(), value: (k.value || '').trim(), target: (k.target || '').trim() }))
      .filter(k => k.label)
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
    await refresh()
    emit('saved')
    emit('close')
  } catch (e) {
    if (e.status === 422) {
      errorMsg.value = typeof e.payload?.detail === 'string' ? e.payload.detail : '校验失败'
    } else if (e.status === 403) {
      toast.value = '无权编辑此模块'
      setTimeout(() => { toast.value = '' }, 3000)
    } else {
      errorMsg.value = e.message || '保存失败'
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="open" class="edit-mask" @click="onBackdrop">
    <div class="edit-box" role="dialog" :aria-label="`编辑 ${module?.name || ''} 状态`">
      <header class="dlg-head">
        <div>
          <h3>{{ module?.name || '模块状态' }}</h3>
          <p class="sub">{{ module?.group || '' }} · {{ module?.scope === 'pdt' ? 'PDT 级' : 'LTC 级' }}</p>
        </div>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗,放弃未保存修改'">×</button>
      </header>

      <section class="block">
        <div class="label">整体灯</div>
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
      </section>

      <section v-if="module?.sub_items?.length" class="block">
        <div class="label">子项状态 + 风险说明</div>
        <div class="sub-list">
          <div
            v-for="s in module.sub_items"
            :key="s.id"
            class="sub-row"
            :class="{ focus: focusSubId === s.id }"
          >
            <div class="sub-head">
              <span class="sub-name">{{ s.name }}</span>
              <div class="color-row">
                <button
                  v-for="c in COLORS"
                  :key="c"
                  type="button"
                  class="swatch sm"
                  :class="{ active: subColors[s.id] === c }"
                  :style="{ background: `var(--status-${c})` }"
                  v-tooltip="`置为 ${COLOR_LABEL[c]}`"
                  @click="pickSubColor(s.id, c)"
                >{{ subColors[s.id] === c ? '✓' : '' }}</button>
              </div>
            </div>
            <input
              v-if="subColors[s.id] === 'red' || subColors[s.id] === 'yellow'"
              v-model="subRisks[s.id]"
              class="sub-note-input"
              placeholder="该子项的风险/阻塞说明(用于风险详情页)"
              v-tooltip="'子项级风险说明,会在风险详情页显示在色块右侧'"
            />
          </div>
        </div>
      </section>

      <section class="block">
        <div class="label">
          <span>KPI</span>
          <button class="mini-add" @click="addKpi" v-tooltip="'新增一行 KPI'">+ 添加</button>
        </div>
        <div v-if="!kpiItems.length" class="hint">暂无 KPI,点击「+ 添加」开始填写</div>
        <div v-else class="kpi-table">
          <div class="kpi-row head">
            <span>指标</span><span>当前值</span><span>目标(可选)</span><span></span>
          </div>
          <div v-for="(k, i) in kpiItems" :key="i" class="kpi-row">
            <input v-model="k.label" placeholder="如 Bug 闭环率" v-tooltip="'KPI 名称'" />
            <input v-model="k.value" placeholder="如 91%" v-tooltip="'KPI 当前值'" />
            <input v-model="k.target" placeholder="如 95%" v-tooltip="'KPI 目标值(可选)'" />
            <button class="mini-del" v-tooltip="'删除该 KPI'" @click="removeKpi(i)">✕</button>
          </div>
        </div>
      </section>

      <section class="block">
        <div class="label">
          <span>风险 / 重点问题<span v-if="anyNonGreen" class="req">(非绿必填至少一条)</span></span>
          <span class="risk-add-group">
            <button class="mini-add sev-red" @click="addRisk('red')" v-tooltip="'新增红色风险(Delay/Block)'">+ 红</button>
            <button class="mini-add sev-yellow" @click="addRisk('yellow')" v-tooltip="'新增黄色风险(预警)'">+ 黄</button>
          </span>
        </div>
        <div v-if="!risks.length" class="hint" :class="{ err: riskMissing }">
          {{ riskMissing ? '风险说明不能为空(非绿项必填至少一条)' : '暂无风险,点击「+ 红/+ 黄」添加' }}
        </div>
        <div v-else class="risk-list">
          <div v-for="(r, i) in risks" :key="i" class="risk-row" :class="`sev-${r.severity}`">
            <select v-model="r.severity" v-tooltip="'风险级别'">
              <option value="red">红 · Delay/Block</option>
              <option value="yellow">黄 · 预警</option>
            </select>
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
          class="primary"
          :disabled="saving || riskMissing"
          v-tooltip="riskMissing ? '风险说明不能为空' : '提交并刷新看板'"
          @click="save"
        >{{ saving ? '保存中…' : '保存' }}</button>
      </footer>

      <div v-if="toast" class="toast">{{ toast }}</div>
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
  padding: 18px 22px; min-width: 520px; max-width: 640px; width: 90vw;
  max-height: 88vh; overflow-y: auto;
  box-shadow: var(--shadow-lg);
  position: relative;
}
.dlg-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
h3 { margin: 0; font-size: 16px; font-weight: 700; }
.sub { margin: 2px 0 0; font-size: 12px; color: var(--text-muted); }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; }
.close:hover { color: var(--accent); background: transparent; }

.block { margin-bottom: 16px; }
.label {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; color: var(--text-muted); margin-bottom: 6px; font-weight: 600;
}
.req { color: var(--status-red); margin-left: 6px; font-weight: 500; }

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
.mini-add.sev-red { color: var(--status-red); border-color: var(--status-red); }
.mini-add.sev-yellow { color: var(--status-yellow); border-color: var(--status-yellow); }
.risk-add-group { display: inline-flex; gap: 4px; }
.mini-del { color: var(--text-muted); }
.mini-del:hover { color: var(--status-red); border-color: var(--status-red); }

.kpi-table { display: flex; flex-direction: column; gap: 4px; }
.kpi-row { display: grid; grid-template-columns: 1.4fr 1fr 1fr 28px; gap: 6px; align-items: center; }
.kpi-row.head { font-size: 11px; color: var(--text-dim); padding: 0 4px; }
.kpi-row input { font-size: 12.5px; padding: 4px 8px; }

.risk-list { display: flex; flex-direction: column; gap: 6px; }
.risk-row { display: grid; grid-template-columns: 130px 1fr 28px; gap: 6px; align-items: stretch; padding: 6px; border-radius: var(--radius); }
.risk-row.sev-red { background: var(--status-red-bg); }
.risk-row.sev-yellow { background: var(--status-yellow-bg); }
.risk-row select { font-size: 12px; }
.risk-row textarea { font-size: 12.5px; padding: 6px 8px; resize: vertical; min-height: 36px; }

.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.hint.err { color: var(--status-red); }

.err-banner {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0 0 10px;
}

.dlg-foot { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; padding-top: 12px; border-top: 1px solid var(--border-subtle); }
.toast {
  position: absolute; left: 50%; bottom: 16px; transform: translateX(-50%);
  background: rgba(15,23,42,0.95); color: #fff;
  padding: 6px 14px; border-radius: var(--radius); font-size: 12px;
}
</style>
