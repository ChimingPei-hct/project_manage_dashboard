<script setup>
/**
 * 创建 LTC 表单:ID + 名称 +「从模板复制」勾选项。
 * - 仅 super / pdt admin 可触发(按钮入口在 LtcTree)
 * - 提交流程:POST /api/ltcs → 若勾选,再 POST /api/ltc/{id}/init-from-template
 * - 模板拷贝失败不回滚 LTC,通过 emit 把 templateErr 报到上层
 */
import { ref } from 'vue'
import Modal from '../harness/Modal.vue'
import { adminApi } from '../../composables/useAdminApi.js'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'created'])

const ID_RE = /^[a-z][a-z0-9-]{1,31}$/

const draft = ref({ id: '', name: '', copyTemplate: true })
const errorMsg = ref('')
const submitting = ref(false)

function reset() {
  draft.value = { id: '', name: '', copyTemplate: true }
  errorMsg.value = ''
}

function onClose() {
  if (submitting.value) return
  reset()
  emit('close')
}

async function submit() {
  errorMsg.value = ''
  const id = draft.value.id.trim()
  const name = draft.value.name.trim()
  if (!ID_RE.test(id)) {
    errorMsg.value = 'ID 格式非法:小写字母开头,允许小写字母 / 数字 / 短横线,长度 2–32'
    return
  }
  if (!name || name.length > 80) {
    errorMsg.value = 'LTC 名称必填,长度 1–80 字'
    return
  }
  submitting.value = true
  try {
    await adminApi.createLtc({ id, name })
  } catch (e) {
    errorMsg.value = e.payload?.detail || e.message || '创建失败'
    submitting.value = false
    return
  }
  let templateErr = ''
  if (draft.value.copyTemplate) {
    try {
      await adminApi.initLtcFromTemplate(id)
    } catch (e) {
      templateErr = e.payload?.detail || e.message || '模板拷贝失败'
    }
  }
  submitting.value = false
  emit('created', { id, templateCopied: draft.value.copyTemplate && !templateErr, templateErr })
  reset()
}
</script>

<template>
  <Modal :open="open" title="新建 LTC" width="480px" @close="onClose">
    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>
    <label class="fld">
      <span>LTC ID *</span>
      <input
        v-model="draft.id"
        placeholder="如:mainline-id5"
        maxlength="32"
        :disabled="submitting"
        v-tooltip="'创建后不可改;小写字母 / 数字 / 短横线,2–32 字'"
      />
    </label>
    <label class="fld">
      <span>LTC 名称 *</span>
      <input
        v-model="draft.name"
        placeholder="如:主线 ID5"
        maxlength="80"
        :disabled="submitting"
      />
    </label>
    <label class="check">
      <input
        type="checkbox"
        v-model="draft.copyTemplate"
        :disabled="submitting"
      />
      <span v-tooltip="'勾选:创建后立即从模板池拷贝 6 大类 + 18 示例模块,可随后自由删改'">
        从模板复制大类与示例模块(推荐)
      </span>
    </label>
    <footer class="acts">
      <button :disabled="submitting" v-tooltip="'放弃创建'" @click="onClose">取消</button>
      <button class="primary" :disabled="submitting" v-tooltip="'创建 LTC,并按勾选拷贝模板'" @click="submit">
        {{ submitting ? '创建中…' : '创建' }}
      </button>
    </footer>
  </Modal>
</template>

<style scoped>
.fld { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.fld > span { font-size: 11.5px; color: var(--text-muted); }
.fld input {
  font-size: 13px; padding: 6px 10px;
  border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--panel);
}
.fld input:disabled { background: var(--panel-soft); cursor: not-allowed; }
.check {
  display: flex; align-items: center; gap: 6px;
  margin: 4px 0 16px; font-size: 12.5px; cursor: pointer; user-select: none;
}
.check input { cursor: pointer; }
.acts {
  display: flex; justify-content: flex-end; gap: 8px;
  padding-top: 12px; border-top: 1px solid var(--border-subtle);
}
.acts button {
  font-size: 12px; padding: 6px 14px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--panel); cursor: pointer;
}
.acts button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.acts button.primary:hover:not(:disabled) { opacity: 0.92; }
.acts button:disabled { opacity: 0.5; cursor: not-allowed; }
.err {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0 0 12px;
}
</style>
