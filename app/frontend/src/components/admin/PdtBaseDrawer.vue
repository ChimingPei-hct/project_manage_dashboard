<script setup>
import { ref, watch, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi } from '../../composables/useAdminApi.js'

const { pdt, refresh } = useDashboard()
const draft = ref({ name: '', code: '', description: '' })
const dirty = ref(false)
const saving = ref(false)
const errMsg = ref('')

watch(pdt, (v) => {
  if (!v) return
  draft.value = { name: v.name || '', code: v.code || '', description: v.description || '' }
  dirty.value = false
}, { immediate: true })

async function save() {
  saving.value = true
  errMsg.value = ''
  try {
    await adminApi.updatePdt({ name: draft.value.name, code: draft.value.code, description: draft.value.description })
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
      <button class="primary" :disabled="!dirty || saving" v-tooltip="dirty ? '保存修改' : '无变更'" @click="save">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>基础信息</h3>
      <label class="field">
        <span>PDT 代号(短码,用于路径)</span>
        <input v-model="draft.code" @input="dirty = true" placeholder="如:luna6" />
      </label>
      <label class="field">
        <span>PDT 名称</span>
        <input v-model="draft.name" @input="dirty = true" placeholder="如:Multicam Pilot 3.0" />
      </label>
      <label class="field">
        <span>描述(可选)</span>
        <textarea v-model="draft.description" @input="dirty = true" rows="3" placeholder="本产品线的简短说明"></textarea>
      </label>
    </section>

    <section class="block hint-block">
      <h3>下一步</h3>
      <ul>
        <li>左侧「里程碑」配置时间轴节点(TR/SOP/Block)</li>
        <li>左侧「总览卡片」配置 PDT 总览展示哪些模块卡</li>
        <li>左侧「LTC 子项目」管理交付子项目,每个 LTC 下可加模块和子项</li>
      </ul>
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
.hint-block ul { padding-left: 20px; font-size: 12.5px; color: var(--text-muted); line-height: 1.7; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>
