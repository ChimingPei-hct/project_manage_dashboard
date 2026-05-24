<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../../api/client.js'
import { useDashboard } from '../../composables/useDashboard.js'

/**
 * 子项色块编辑弹窗。
 * 仅允许编辑单个 sub_item 的 color + risk_text;读取当前 entry 后做全量 PUT(design/07 §8 禁止 PATCH 单字段)。
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  module: { type: Object, default: null },
  subItem: { type: Object, default: null },
  statusKey: { type: String, default: '' },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'saved'])

const { status, refresh } = useDashboard()
const color = ref('green')
const riskText = ref('')
const saving = ref(false)
const errorMsg = ref('')

const COLORS = [
  { value: 'green', label: '绿/正常' },
  { value: 'yellow', label: '黄/预警' },
  { value: 'red', label: '红/Block' },
]

function reset() {
  const entry = status.value?.[props.statusKey] || {}
  const sid = props.subItem?.id
  color.value = entry.sub_items_color?.[sid] || 'green'
  riskText.value = entry.sub_items_risk?.[sid] || ''
  errorMsg.value = ''
}

watch(() => [props.open, props.statusKey, props.subItem?.id], () => {
  if (props.open) reset()
}, { immediate: true })

const requireRisk = computed(() => color.value !== 'green')
const canSave = computed(() => {
  if (!props.canEdit || saving.value) return false
  if (requireRisk.value && !riskText.value.trim()) return false
  return true
})

async function save() {
  errorMsg.value = ''
  if (!props.canEdit) return
  saving.value = true
  try {
    const entry = status.value?.[props.statusKey] || {}
    const sid = props.subItem.id
    const sub_items_color = { ...(entry.sub_items_color || {}), [sid]: color.value }
    const sub_items_risk = { ...(entry.sub_items_risk || {}) }
    const t = riskText.value.trim()
    if (t) sub_items_risk[sid] = t
    else delete sub_items_risk[sid]
    await api.put(`/api/status/${encodeURIComponent(props.statusKey)}`, {
      module_color: entry.module_color || 'green',
      sub_items_color,
      sub_items_risk,
      kpi_items: entry.kpi_items || [],
      risks: entry.risks || [],
      risk_note: entry.risk_note || '',
    })
    await refresh()
    emit('saved')
    emit('close')
  } catch (e) {
    if (e.status === 403) errorMsg.value = '无权编辑该子项'
    else errorMsg.value = e.payload?.detail || e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

function onBackdrop(e) { if (e.target === e.currentTarget) emit('close') }
</script>

<template>
  <div v-if="open" class="mask" @click="onBackdrop">
    <div class="box" role="dialog">
      <header class="head">
        <div>
          <h3>{{ subItem?.name || '子项' }}</h3>
          <p class="sub">{{ module?.name || '' }}</p>
        </div>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗,放弃修改'">×</button>
      </header>

      <section class="block">
        <div class="block-title">状态灯</div>
        <div class="color-row">
          <button
            v-for="c in COLORS"
            :key="c.value"
            type="button"
            class="swatch"
            :class="{ active: color === c.value }"
            :style="{ background: `var(--status-${c.value})` }"
            :disabled="!canEdit"
            v-tooltip="`将本子项标记为 ${c.label}`"
            @click="color = c.value"
          >{{ color === c.value ? '✓' : '' }}</button>
        </div>
      </section>

      <section class="block">
        <div class="block-title">
          <span>风险说明</span>
          <span v-if="requireRisk" class="req">* 非绿态必填</span>
        </div>
        <textarea
          v-model="riskText"
          :readonly="!canEdit"
          rows="4"
          :placeholder="requireRisk ? '描述当前阻塞 / 风险(必填)' : '可选,绿色态可不填'"
          v-tooltip="'写明本子项当前的阻塞、风险或重点事项'"
        />
        <p v-if="requireRisk && !riskText.trim()" class="hint err">非绿态必须填写风险说明</p>
      </section>

      <p v-if="errorMsg" class="err-banner">{{ errorMsg }}</p>

      <footer class="foot">
        <button @click="emit('close')" v-tooltip="'放弃修改'">取消</button>
        <button
          class="primary"
          :disabled="!canSave"
          v-tooltip="canEdit ? '保存子项状态与风险说明' : '当前账号无编辑权限'"
          @click="save"
        >{{ saving ? '保存中…' : '保存' }}</button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: center; justify-content: center;
  z-index: 9100; backdrop-filter: blur(2px);
}
.box {
  background: var(--panel); border-radius: var(--radius);
  padding: 18px 22px; min-width: 420px; max-width: 540px; width: 92vw;
  box-shadow: var(--shadow-lg);
}
.head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
h3 { margin: 0; font-size: 15px; font-weight: 700; }
.sub { margin: 2px 0 0; font-size: 12px; color: var(--text-muted); }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; color: var(--text-muted); }
.close:hover { color: var(--accent); }

.block { margin-bottom: 14px; }
.block-title {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12px; font-weight: 700; color: var(--text); letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.req { font-size: 11px; color: var(--status-red); font-weight: 500; }

.color-row { display: flex; gap: 6px; }
.swatch {
  width: 40px; height: 28px; border-radius: var(--radius);
  border: 1px solid var(--border); color: #fff; font-size: 13px;
  padding: 0; cursor: pointer;
}
.swatch.active { outline: 2px solid var(--accent); outline-offset: 1px; }
.swatch:disabled { cursor: not-allowed; opacity: 0.6; }

textarea {
  width: 100%; font-size: 13px; padding: 8px 10px;
  border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--panel); resize: vertical; min-height: 64px;
  font-family: inherit;
}
.hint { font-size: 11px; padding: 4px 0 0; margin: 0; }
.hint.err { color: var(--status-red); }
.err-banner {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0 0 10px;
}
.foot { display: flex; justify-content: flex-end; gap: 8px; padding-top: 10px; border-top: 1px solid var(--border-subtle); }
.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.primary:disabled { opacity: 0.55; cursor: not-allowed; }
</style>
