<script setup>
import { ref, watch, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi } from '../../composables/useAdminApi.js'

const { pdt, refresh } = useDashboard()
const draft = ref({ name: '', description: '' })
const dirty = ref(false)
const saving = ref(false)
const errMsg = ref('')

const NAME_RE = /^[A-Za-z0-9_\-一-龥]+$/

watch(pdt, (v) => {
  if (!v) return
  draft.value = { name: v.name || v.code || '', description: v.description || '' }
  dirty.value = false
}, { immediate: true })

const nameInvalid = computed(() => draft.value.name.length > 0 && !NAME_RE.test(draft.value.name))
const canSave = computed(() => dirty.value && !saving.value && draft.value.name.length > 0 && !nameInvalid.value)

async function save() {
  if (!canSave.value) return
  saving.value = true
  errMsg.value = ''
  try {
    const name = draft.value.name
    await adminApi.updatePdt({ name, code: name, description: draft.value.description })
    await refresh()
    dirty.value = false
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '保存失败' }
  finally { saving.value = false }
}
</script>

<template>
  <div class="pdt-base">
    <header class="dh">
      <div>
        <div class="crumb">PDT 配置</div>
        <h2>{{ draft.name || '产品线基础信息' }}</h2>
      </div>
      <button class="primary" :disabled="!canSave" v-tooltip="dirty ? (nameInvalid ? '名称不允许空格或特殊字符' : '保存修改') : '无变更'" @click="save">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>基础信息</h3>
      <label class="field">
        <span>PDT 名称(用作显示名与路径标识,不含空格/特殊字符)</span>
        <input v-model="draft.name" @input="dirty = true" placeholder="如:Luna6" :class="{ invalid: nameInvalid }" />
        <em v-if="nameInvalid" class="hint-err">仅允许字母/数字/中文/下划线/连字符,不允许空格</em>
      </label>
      <label class="field">
        <span>描述(可选)</span>
        <textarea v-model="draft.description" @input="dirty = true" rows="3" placeholder="本产品线的简短说明"></textarea>
      </label>
    </section>
  </div>
</template>

<style scoped>
.pdt-base { display: flex; flex-direction: column; gap: 16px; }
.dh { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
.block h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--text-muted); margin-bottom: 10px; }
.field input, .field textarea { font-size: 13px; }
.field input.invalid { border-color: var(--status-red); }
.hint-err { color: var(--status-red); font-size: 11px; font-style: normal; margin-top: 2px; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>
