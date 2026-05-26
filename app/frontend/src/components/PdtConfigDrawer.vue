<script setup>
/**
 * PDT 级配置抽屉(顶栏齿轮入口)。
 * Tab 1 "PDT 信息":名称 + 图标编辑(原 PdtNameDialog 能力,内容原样搬过来)
 * Tab 2 "LTC 模板":单一模板池的 category/module CRUD
 */
import { ref, toRef, watch, computed } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { adminApi } from '../composables/useAdminApi.js'
import { useEscClose } from '../composables/useEscClose.js'
import { iconUrlOf } from '../utils/favicon.js'
import LtcTemplateEditor from './admin/LtcTemplateEditor.vue'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

useEscClose(toRef(props, 'open'), () => emit('close'))

const { pdt, refresh } = useDashboard()
const tab = ref('pdt')

const MIN_W = 360
const MAX_W = 1200
const WIDTH_KEY = 'pdt-config-drawer-width'
const drawerWidth = ref(Math.max(MIN_W, Math.min(MAX_W, Number(localStorage.getItem(WIDTH_KEY)) || 640)))
const dragging = ref(false)

function onDragStart(ev) {
  ev.preventDefault()
  dragging.value = true
  const startX = ev.clientX
  const startW = drawerWidth.value
  function onMove(e) {
    const next = startW + (startX - e.clientX)
    drawerWidth.value = Math.max(MIN_W, Math.min(MAX_W, next))
  }
  function onUp() {
    dragging.value = false
    localStorage.setItem(WIDTH_KEY, String(drawerWidth.value))
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

const name = ref('')
const saving = ref(false)
const errMsg = ref('')
const iconUploading = ref(false)
const fileInput = ref(null)

const NAME_RE = /^[A-Za-z0-9_\-一-龥]+$/
const ICON_MAX = 256 * 1024
const ICON_MIMES = ['image/svg+xml', 'image/png']

const iconUrl = computed(() => iconUrlOf(pdt.value))

watch(() => props.open, (open) => {
  if (open) {
    name.value = pdt.value?.name || pdt.value?.code || ''
    errMsg.value = ''
    tab.value = 'pdt'
  }
}, { immediate: true })

watch(pdt, (p) => {
  if (props.open && p) name.value = p.name || p.code || ''
})

async function pickIcon() { fileInput.value?.click() }

async function onIconFile(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file) return
  errMsg.value = ''
  if (!ICON_MIMES.includes(file.type)) { errMsg.value = '仅支持 .svg / .png'; return }
  if (file.size > ICON_MAX) { errMsg.value = `图片过大(>${Math.round(ICON_MAX / 1024)}KB)`; return }
  iconUploading.value = true
  try {
    await adminApi.uploadPdtIcon(file)
    await refresh()
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '上传失败' }
  finally { iconUploading.value = false }
}

async function clearIcon() {
  if (!pdt.value?.icon) return
  iconUploading.value = true
  errMsg.value = ''
  try {
    await adminApi.deletePdtIcon()
    await refresh()
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '清除失败' }
  finally { iconUploading.value = false }
}

const invalid = computed(() => name.value.length > 0 && !NAME_RE.test(name.value))
const dirty = computed(() => name.value !== (pdt.value?.name || pdt.value?.code || ''))
const canSave = computed(() => dirty.value && !saving.value && name.value.length > 0 && !invalid.value)

async function saveName() {
  if (!canSave.value) return
  saving.value = true
  errMsg.value = ''
  try {
    await adminApi.updatePdt({ name: name.value, code: name.value })
    await refresh()
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '保存失败' }
  finally { saving.value = false }
}
</script>

<template>
  <!-- 抽屉里是编辑表单,点遮罩不应该误关丢失修改:仅 × / Esc 关闭(详见 design/12 §7.6) -->
  <div v-if="open" class="drawer-mask">
    <aside class="drawer" role="dialog" :style="{ width: drawerWidth + 'px' }" :class="{ dragging }">
      <div
        class="resize-handle"
        v-tooltip="'拖动调整抽屉宽度'"
        @mousedown="onDragStart"
      ></div>
      <header class="d-head">
        <h3>PDT 配置</h3>
        <button class="close" v-tooltip="'关闭'" @click="emit('close')">×</button>
      </header>
      <div class="d-tabs">
        <button
          :class="{ active: tab === 'pdt' }"
          v-tooltip="'编辑 PDT 名称与图标(顶栏品牌区与浏览器标签)'"
          @click="tab = 'pdt'"
        >PDT 信息</button>
        <button
          :class="{ active: tab === 'template' }"
          v-tooltip="'管理新建 LTC 时使用的模板池(大类与模块骨架)'"
          @click="tab = 'template'"
        >LTC 模板</button>
      </div>
      <div class="d-body">
        <section v-show="tab === 'pdt'" class="pane">
          <p class="hint">名称与图标会显示在左上角品牌区与浏览器标签。图标随实例数据存储,不与代码耦合。</p>
          <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>
          <label class="field">
            <span>PDT 名称</span>
            <input
              v-model="name"
              placeholder="如:Luna6"
              :class="{ invalid }"
              @keyup.enter="saveName"
            />
            <em v-if="invalid" class="hint-err">仅允许字母 / 数字 / 中文 / 下划线 / 连字符</em>
          </label>
          <div class="field">
            <span>PDT 图标</span>
            <div class="icon-row">
              <div class="icon-preview" :class="{ empty: !iconUrl }">
                <img v-if="iconUrl" :src="iconUrl" alt="" />
                <span v-else>无</span>
              </div>
              <div class="icon-actions">
                <button
                  type="button"
                  v-tooltip="'上传 .svg 或 .png,≤256KB,作为顶栏与浏览器标签图标'"
                  :disabled="iconUploading"
                  @click="pickIcon"
                >{{ iconUploading ? '上传中…' : (iconUrl ? '更换' : '上传') }}</button>
                <button
                  type="button"
                  v-tooltip="'清除图标,回退到默认 📊'"
                  :disabled="iconUploading || !iconUrl"
                  @click="clearIcon"
                >清除</button>
                <input ref="fileInput" type="file" accept=".svg,.png,image/svg+xml,image/png" hidden @change="onIconFile" />
              </div>
            </div>
          </div>
          <div class="save-row">
            <button
              class="primary"
              :disabled="!canSave"
              v-tooltip="dirty ? (invalid ? '名称格式不合法' : '保存修改,顶栏品牌名立即更新') : '无变更'"
              @click="saveName"
            >{{ saving ? '保存中…' : '保存名称' }}</button>
          </div>
        </section>
        <section v-show="tab === 'template'" class="pane">
          <LtcTemplateEditor />
        </section>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.drawer-mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; justify-content: flex-end;
  z-index: 9000; backdrop-filter: blur(2px);
}
.drawer {
  background: var(--panel);
  max-width: 100vw; height: 100vh;
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column;
  animation: slideIn 180ms ease-out;
  position: relative;
}
.drawer.dragging { user-select: none; }
.resize-handle {
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 6px; cursor: col-resize;
  background: transparent;
  z-index: 10;
  transition: background 120ms;
}
.resize-handle:hover, .drawer.dragging .resize-handle {
  background: color-mix(in srgb, var(--accent) 40%, transparent);
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

.d-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px; border-bottom: 1px solid var(--border);
}
.d-head h3 { margin: 0; font-size: 15px; font-weight: 700; }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; color: var(--text-muted); }
.close:hover { color: var(--accent); }

.d-tabs { display: flex; gap: 4px; padding: 6px 16px 0; border-bottom: 1px solid var(--border); }
.d-tabs button {
  font-size: 12.5px; padding: 8px 14px;
  background: transparent; border: 1px solid transparent;
  border-bottom: 2px solid transparent;
  color: var(--text-muted); cursor: pointer;
  border-radius: 6px 6px 0 0;
}
.d-tabs button:hover { color: var(--text); }
.d-tabs button.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: var(--panel-soft);
}

.d-body { flex: 1; overflow: auto; padding: 16px 20px; }
.pane { display: flex; flex-direction: column; gap: 12px; }
.hint { font-size: 12px; color: var(--text-muted); margin: 0; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--text-muted); }
.field input { font-size: 13px; padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border); }
.field input.invalid { border-color: var(--status-red); }
.hint-err { color: var(--status-red); font-size: 11px; font-style: normal; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: 6px; font-size: 12px; margin: 0; }

.icon-row { display: flex; align-items: center; gap: 12px; }
.icon-preview {
  width: 48px; height: 48px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--panel-soft);
  display: inline-flex; align-items: center; justify-content: center;
  overflow: hidden; flex-shrink: 0;
}
.icon-preview.empty { color: var(--text-muted); font-size: 11px; }
.icon-preview img { width: 100%; height: 100%; object-fit: contain; padding: 4px; box-sizing: border-box; }
.icon-actions { display: flex; gap: 6px; }
.icon-actions button { font-size: 12px; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); background: var(--panel); cursor: pointer; }

.save-row { display: flex; justify-content: flex-end; padding-top: 8px; border-top: 1px solid var(--border-subtle); }
.primary {
  background: var(--accent); color: #fff; border-color: var(--accent);
  font-size: 12px; padding: 6px 14px; border-radius: 6px; cursor: pointer; border: 1px solid var(--accent);
}
.primary:disabled { opacity: 0.5; cursor: not-allowed; }
.primary:hover:not(:disabled) { opacity: 0.92; }
</style>
