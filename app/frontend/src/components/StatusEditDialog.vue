<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api/client.js'
import { useDashboard } from '../composables/useDashboard.js'

/**
 * 模块状态编辑弹窗。
 * 约束:design/07 §风险说明必填、design/13 §3.3/§4.3/§5.3。
 * 单一入口:`PUT /api/status/{module_id}`,422 inline 提示、403 toast。
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  module: { type: Object, default: null }, // 必传:被编辑的 module 配置
  current: { type: Object, default: () => ({}) }, // status[module_id] 当前态
  focusSubId: { type: String, default: '' }, // 点击子项进入时,聚焦提示
})
const emit = defineEmits(['close', 'saved'])

const COLORS = ['green', 'yellow', 'red', 'gray']

const moduleColor = ref('gray')
const subColors = ref({})
const kpiValues = ref({})
const riskNote = ref('')
const saving = ref(false)
const errorMsg = ref('')
const toast = ref('')

const { refresh } = useDashboard()

function reset() {
  const c = props.current || {}
  moduleColor.value = c.module_color || 'gray'
  subColors.value = { ...(c.sub_items_color || {}) }
  kpiValues.value = { ...(c.kpi_values || {}) }
  riskNote.value = c.risk_note || ''
  errorMsg.value = ''
  toast.value = ''
  // 确保所有 sub_items / kpi 都有 key,缺省 gray / ''
  for (const s of props.module?.sub_items || []) {
    if (!subColors.value[s.id]) subColors.value[s.id] = 'gray'
  }
  for (const k of props.module?.kpi_fields || []) {
    if (kpiValues.value[k.key] === undefined) kpiValues.value[k.key] = ''
  }
}

watch(() => [props.open, props.module?.id], () => {
  if (props.open) reset()
}, { immediate: true })

const anyNonGreen = computed(() => {
  if (moduleColor.value !== 'green') return true
  return Object.values(subColors.value).some(v => v && v !== 'green')
})
const noteRequired = computed(() => anyNonGreen.value)
const noteMissing = computed(() => noteRequired.value && !riskNote.value.trim())

function pickModuleColor(c) { moduleColor.value = c }
function pickSubColor(sid, c) { subColors.value = { ...subColors.value, [sid]: c } }

function onBackdrop(e) {
  if (e.target === e.currentTarget) emit('close')
}

async function save() {
  errorMsg.value = ''
  if (noteMissing.value) {
    errorMsg.value = '存在非绿项时必须填写风险说明'
    return
  }
  saving.value = true
  try {
    await api.put(`/api/status/${props.module.id}`, {
      module_color: moduleColor.value,
      sub_items_color: subColors.value,
      kpi_values: kpiValues.value,
      risk_note: riskNote.value.trim(),
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
      <header>
        <h3>{{ module?.name || '模块状态' }}</h3>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗,放弃未保存的修改'">×</button>
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
            v-tooltip="`将整体状态置为 ${c}`"
            @click="pickModuleColor(c)"
          >{{ c === moduleColor ? '✓' : '' }}</button>
        </div>
      </section>

      <section v-if="module?.sub_items?.length" class="block">
        <div class="label">子项状态</div>
        <div class="sub-list">
          <div
            v-for="s in module.sub_items"
            :key="s.id"
            class="sub-row"
            :class="{ focus: focusSubId === s.id }"
          >
            <span class="sub-name">{{ s.name }}</span>
            <div class="color-row">
              <button
                v-for="c in COLORS"
                :key="c"
                type="button"
                class="swatch sm"
                :class="{ active: subColors[s.id] === c }"
                :style="{ background: `var(--status-${c})` }"
                v-tooltip="`将子项 ${s.name} 状态置为 ${c}`"
                @click="pickSubColor(s.id, c)"
              >{{ subColors[s.id] === c ? '✓' : '' }}</button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="module?.kpi_fields?.length" class="block">
        <div class="label">KPI 值(可选)</div>
        <div class="kpi-list">
          <label v-for="k in module.kpi_fields" :key="k.key" class="kpi-row">
            <span class="kpi-label">{{ k.label }}</span>
            <input
              v-model="kpiValues[k.key]"
              :placeholder="k.hint || ''"
              v-tooltip="`填写 ${k.label}`"
            />
          </label>
        </div>
      </section>

      <section class="block">
        <div class="label">
          风险说明
          <span v-if="noteRequired" class="req">(非绿项必填)</span>
        </div>
        <textarea
          v-model="riskNote"
          rows="3"
          :placeholder="noteRequired ? '存在非绿项,必填' : '可选'"
          v-tooltip="'描述当前阻塞 / 风险 / 待跟进事项'"
        />
        <div v-if="noteMissing" class="inline-err">风险说明不能为空</div>
      </section>

      <p v-if="errorMsg" class="err">{{ errorMsg }}</p>

      <footer>
        <button @click="emit('close')" v-tooltip="'放弃未保存的修改'">取消</button>
        <button
          class="primary"
          :disabled="saving || noteMissing"
          v-tooltip="'提交并刷新看板'"
          @click="save"
        >{{ saving ? '保存中…' : '保存' }}</button>
      </footer>

      <div v-if="toast" class="toast">{{ toast }}</div>
    </div>
  </div>
</template>

<style scoped>
.edit-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.36);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000;
}
.edit-box {
  background: var(--panel); border-radius: var(--radius);
  padding: 18px 22px; min-width: 420px; max-width: 560px;
  max-height: 86vh; overflow-y: auto;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  position: relative;
}
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h3 { margin: 0; font-size: 16px; }
.close { border: none; background: transparent; font-size: 20px; line-height: 1; padding: 0 6px; }
.block { margin-bottom: 14px; }
.label { font-size: 13px; color: var(--text-muted); margin-bottom: 6px; }
.req { color: var(--status-red); margin-left: 4px; }
.color-row { display: flex; gap: 6px; }
.swatch {
  width: 32px; height: 28px; border-radius: var(--radius);
  border: 1px solid var(--border); color: #fff; font-size: 13px;
  padding: 0; cursor: pointer;
}
.swatch.sm { width: 24px; height: 22px; font-size: 11px; }
.swatch.active { outline: 2px solid var(--accent); outline-offset: 1px; }
.sub-list { display: flex; flex-direction: column; gap: 6px; }
.sub-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 6px; border-radius: var(--radius);
}
.sub-row.focus { background: #eef4ff; }
.sub-name { font-size: 13px; }
.kpi-list { display: flex; flex-direction: column; gap: 6px; }
.kpi-row { display: flex; align-items: center; gap: 8px; }
.kpi-label { width: 100px; color: var(--text-muted); font-size: 13px; }
.kpi-row input { flex: 1; }
textarea {
  width: 100%; border-radius: var(--radius); border: 1px solid var(--border);
  padding: 8px 10px; font: inherit; resize: vertical;
}
textarea:focus { border-color: var(--accent); outline: none; }
.inline-err { color: var(--status-red); font-size: 12px; margin-top: 4px; }
.err {
  background: #fff1f0; border: 1px solid #ffa39e; color: var(--status-red);
  padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0 0 10px;
}
footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.toast {
  position: absolute; left: 50%; bottom: 16px; transform: translateX(-50%);
  background: rgba(31, 41, 55, 0.95); color: #fff;
  padding: 6px 14px; border-radius: var(--radius); font-size: 12px;
}
</style>
