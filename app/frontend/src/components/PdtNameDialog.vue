<script setup>
import { ref, watch, computed } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { adminApi } from '../composables/useAdminApi.js'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const { pdt, refresh } = useDashboard()
const name = ref('')
const saving = ref(false)
const errMsg = ref('')

const NAME_RE = /^[A-Za-z0-9_\-一-龥]+$/

watch(() => [props.open, pdt.value], () => {
  if (props.open) {
    name.value = pdt.value?.name || pdt.value?.code || ''
    errMsg.value = ''
  }
}, { immediate: true })

const invalid = computed(() => name.value.length > 0 && !NAME_RE.test(name.value))
const dirty = computed(() => name.value !== (pdt.value?.name || pdt.value?.code || ''))
const canSave = computed(() => dirty.value && !saving.value && name.value.length > 0 && !invalid.value)

async function save() {
  if (!canSave.value) return
  saving.value = true
  errMsg.value = ''
  try {
    await adminApi.updatePdt({ name: name.value, code: name.value })
    await refresh()
    emit('close')
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '保存失败' }
  finally { saving.value = false }
}
</script>

<template>
  <div v-if="open" class="modal-mask" @click.self="emit('close')">
    <div class="modal-box" role="dialog">
      <header class="modal-head">
        <h3>编辑 PDT 名称</h3>
        <button class="close" v-tooltip="'关闭弹窗'" @click="emit('close')">×</button>
      </header>
      <div class="modal-body">
        <p class="hint">该名称会显示在左上角品牌区,用作产品线标识(不允许空格或特殊字符)。</p>
        <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>
        <label class="field">
          <span>PDT 名称</span>
          <input
            v-model="name"
            placeholder="如:Luna6"
            :class="{ invalid }"
            @keyup.enter="save"
          />
          <em v-if="invalid" class="hint-err">仅允许字母 / 数字 / 中文 / 下划线 / 连字符</em>
        </label>
      </div>
      <footer class="modal-foot">
        <button v-tooltip="'放弃修改并关闭'" @click="emit('close')">取消</button>
        <button
          class="primary"
          :disabled="!canSave"
          v-tooltip="dirty ? (invalid ? '名称格式不合法' : '保存修改,顶栏品牌名立即更新') : '无变更'"
          @click="save"
        >{{ saving ? '保存中…' : '保存' }}</button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: flex-start; justify-content: center;
  z-index: 9000; backdrop-filter: blur(2px);
  padding: 80px 16px 24px;
}
.modal-box {
  background: var(--panel); border-radius: var(--radius);
  width: 100%; max-width: 420px;
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column;
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
}
.modal-head h3 { margin: 0; font-size: 15px; font-weight: 700; }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; color: var(--text-muted); }
.close:hover { color: var(--accent); }
.modal-body { padding: 16px 20px; }
.modal-foot {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}
.hint { font-size: 12px; color: var(--text-muted); margin: 0 0 12px; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--text-muted); }
.field input { font-size: 13px; padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border); }
.field input.invalid { border-color: var(--status-red); }
.hint-err { color: var(--status-red); font-size: 11px; font-style: normal; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0 0 12px; }
</style>
