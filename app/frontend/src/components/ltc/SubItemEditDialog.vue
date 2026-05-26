<script setup>
import { computed, ref, toRef, watch } from 'vue'
import { api } from '../../api/client.js'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'
import { useEscClose } from '../../composables/useEscClose.js'

/**
 * 子项色块 编辑/新建/删除 弹窗。
 * - 编辑态(subItem != null):改 color + risk_text,全量 PUT status
 * - 新建态(subItem == null):输入名称 → PUT module 追加 sub_items → 同时 PUT status 上色
 * - 删除态(编辑态点「删除」):PUT module 移除该 sub + PUT status 清理对应 color/risk
 * 全部走 design/07 §8 的全量 PUT(禁 PATCH 单字段)。
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  module: { type: Object, default: null },
  subItem: { type: Object, default: null }, // null = 新建态
  statusKey: { type: String, default: '' },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'saved'])

useEscClose(toRef(props, 'open'), () => emit('close'))

const { status, refresh } = useDashboard()
const isCreate = computed(() => !props.subItem)
const subName = ref('')
const color = ref('green')
const riskText = ref('')
const saving = ref(false)
const deleting = ref(false)
const confirmDel = ref(false)
const errorMsg = ref('')

const COLORS = [
  { value: 'green', label: '绿/正常' },
  { value: 'yellow', label: '黄/预警' },
  { value: 'red', label: '红/Block' },
]

function reset() {
  const entry = status.value?.[props.statusKey] || {}
  if (isCreate.value) {
    subName.value = ''
    color.value = 'green'
    riskText.value = ''
  } else {
    const sid = props.subItem.id
    subName.value = props.subItem.name || ''
    color.value = entry.sub_items_color?.[sid] || 'green'
    riskText.value = entry.sub_items_risk?.[sid] || ''
  }
  errorMsg.value = ''
  confirmDel.value = false
}

watch(() => [props.open, props.statusKey, props.subItem?.id], () => {
  if (props.open) reset()
}, { immediate: true })

const requireRisk = computed(() => color.value !== 'green')
const canSave = computed(() => {
  if (!props.canEdit || saving.value || deleting.value) return false
  if (isCreate.value && !subName.value.trim()) return false
  if (requireRisk.value && !riskText.value.trim()) return false
  return true
})

function moduleBody(overrideSubs) {
  const m = props.module
  return {
    name: m.name,
    group: m.group,
    category_id: m.category_id || null,
    owner_open_id: m.owner_open_id || null,
    kpi_fields: m.kpi_fields || [],
    sub_items: overrideSubs,
  }
}

async function putStatus(sub_items_color, sub_items_risk) {
  const entry = status.value?.[props.statusKey] || {}
  await api.put(`/api/status/${encodeURIComponent(props.statusKey)}`, {
    module_color: entry.module_color || 'green',
    sub_items_color,
    sub_items_risk,
    kpi_values: entry.kpi_values || {},
    risk_note: entry.risk_note || '',
  })
}

async function save() {
  errorMsg.value = ''
  if (!canSave.value) return
  saving.value = true
  try {
    const entry = status.value?.[props.statusKey] || {}
    let targetSid
    if (isCreate.value) {
      const newSub = {
        id: newId().slice(0, 12),
        name: subName.value.trim(),
        order: (props.module.sub_items || []).length + 1,
        owner_open_id: null,
        risk_note: '',
      }
      const subs = [...(props.module.sub_items || []), newSub]
      await adminApi.updateModule(props.module.id, moduleBody(subs))
      targetSid = newSub.id
    } else {
      targetSid = props.subItem.id
    }
    const sub_items_color = { ...(entry.sub_items_color || {}), [targetSid]: color.value }
    const sub_items_risk = { ...(entry.sub_items_risk || {}) }
    const t = riskText.value.trim()
    if (t) sub_items_risk[targetSid] = t
    else delete sub_items_risk[targetSid]
    await putStatus(sub_items_color, sub_items_risk)
    await refresh()
    emit('saved')
    emit('close')
  } catch (e) {
    if (e.status === 403) errorMsg.value = '无权操作该子项'
    else errorMsg.value = e.payload?.detail || e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function doDelete() {
  errorMsg.value = ''
  if (!props.canEdit || isCreate.value) return
  deleting.value = true
  try {
    const sid = props.subItem.id
    const subs = (props.module.sub_items || []).filter(s => s.id !== sid)
    await adminApi.updateModule(props.module.id, moduleBody(subs))
    const entry = status.value?.[props.statusKey] || {}
    const sub_items_color = { ...(entry.sub_items_color || {}) }
    const sub_items_risk = { ...(entry.sub_items_risk || {}) }
    delete sub_items_color[sid]
    delete sub_items_risk[sid]
    await putStatus(sub_items_color, sub_items_risk)
    await refresh()
    emit('saved')
    emit('close')
  } catch (e) {
    errorMsg.value = e.payload?.detail || e.message || '删除失败'
  } finally {
    deleting.value = false
    confirmDel.value = false
  }
}

function onBackdrop(e) { if (e.target === e.currentTarget) emit('close') }
</script>

<template>
  <div v-if="open" class="mask" @click="onBackdrop">
    <div class="box" role="dialog">
      <header class="head">
        <div>
          <h3>{{ isCreate ? '新增子项' : (subItem?.name || '子项') }}</h3>
          <p class="sub">{{ module?.name || '' }}</p>
        </div>
        <button class="close" @click="emit('close')" v-tooltip="'关闭弹窗,放弃修改'">×</button>
      </header>

      <section v-if="isCreate" class="block">
        <div class="block-title">子项名称</div>
        <input
          v-model="subName"
          maxlength="40"
          placeholder="如:RTE、AEB、定位融合"
          v-tooltip="'新子项的显示名(不超过 40 字)'"
        />
      </section>

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
        <button
          v-if="!isCreate && canEdit"
          class="danger"
          :disabled="deleting || saving"
          v-tooltip="'从本模块移除此子项(同时清掉它的颜色和风险记录)'"
          @click="confirmDel = true"
        >删除子项</button>
        <div class="foot-right">
          <button @click="emit('close')" v-tooltip="'放弃修改'">取消</button>
          <button
            class="primary"
            :disabled="!canSave"
            v-tooltip="canEdit ? (isCreate ? '创建子项并保存状态' : '保存子项状态与风险说明') : '当前账号无编辑权限'"
            @click="save"
          >{{ saving ? '保存中…' : (isCreate ? '创建' : '保存') }}</button>
        </div>
      </footer>

      <div v-if="confirmDel" class="confirm-mask" @click.self="confirmDel = false">
        <div class="confirm-box">
          <p>确认删除子项「{{ subItem?.name }}」?</p>
          <p class="hint">此操作会从模块的 sub_items 中移除,并清理其颜色/风险记录(历史快照不变)。</p>
          <div class="foot-right">
            <button @click="confirmDel = false">取消</button>
            <button class="danger" :disabled="deleting" @click="doDelete">{{ deleting ? '删除中…' : '确认删除' }}</button>
          </div>
        </div>
      </div>
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
  box-shadow: var(--shadow-lg); position: relative;
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

input {
  width: 100%; font-size: 13px; padding: 6px 10px;
  border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--panel); font-family: inherit;
}

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
.hint { font-size: 11px; padding: 4px 0 0; margin: 0; color: var(--text-muted); }
.hint.err { color: var(--status-red); }
.err-banner {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0 0 10px;
}
.foot {
  display: flex; justify-content: space-between; align-items: center; gap: 8px;
  padding-top: 10px; border-top: 1px solid var(--border-subtle);
}
.foot-right { display: flex; gap: 8px; }
.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.primary:disabled { opacity: 0.55; cursor: not-allowed; }
.danger {
  background: transparent; color: var(--status-red);
  border: 1px solid var(--status-red); border-radius: var(--radius);
  padding: 4px 12px; font-size: 12.5px; cursor: pointer;
}
.danger:disabled { opacity: 0.55; cursor: not-allowed; }
.danger:hover:not(:disabled) { background: var(--status-red-bg); }

.confirm-mask {
  position: absolute; inset: 0; background: rgba(15,23,42,0.55);
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius);
}
.confirm-box {
  background: var(--panel); border-radius: var(--radius);
  padding: 16px 18px; width: 88%; max-width: 380px;
  box-shadow: var(--shadow-lg);
}
.confirm-box p { margin: 0 0 8px; font-size: 13px; }
</style>
