<script setup>
import { ref, watch } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi } from '../../composables/useAdminApi.js'
import { TYPE_OPTIONS, styleOf } from '../../constants/milestoneTypes.js'

const { pdt, refresh } = useDashboard()
const draft = ref([])
const dirty = ref(false)
const saving = ref(false)
const errMsg = ref('')

watch(pdt, (v) => {
  draft.value = (v?.milestones || []).map(m => ({
    label: m.label || m.name || '',
    date: m.date || '',
    type: m.type || 'TR',
    note: m.note || '',
  }))
  dirty.value = false
}, { immediate: true })

function add() {
  draft.value.push({ label: '新节点', date: new Date().toISOString().slice(0, 10), type: 'TR', note: '' })
  dirty.value = true
}
function remove(i) { draft.value.splice(i, 1); dirty.value = true }
function move(i, dir) {
  const j = i + dir
  if (j < 0 || j >= draft.value.length) return
  ;[draft.value[i], draft.value[j]] = [draft.value[j], draft.value[i]]
  dirty.value = true
}

async function save() {
  saving.value = true
  errMsg.value = ''
  try {
    const body = { ...(pdt.value || {}), milestones: draft.value.map(m => ({
      label: m.label, date: m.date, type: m.type, note: m.note,
    })) }
    delete body.updated_at
    await adminApi.updatePdt(body)
    await refresh()
    dirty.value = false
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '保存失败' }
  finally { saving.value = false }
}
</script>

<template>
  <div class="milestone-editor">
    <div class="ops">
      <button v-tooltip="'添加一个时间线节点'" @click="add">+ 新增</button>
      <button class="primary" :disabled="!dirty || saving" v-tooltip="dirty ? '保存修改' : '无变更'" @click="save">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <div v-if="!draft.length" class="hint">还没有时间线节点 · 点上方「+ 新增」开始</div>
      <div v-else class="ms-table">
        <div class="ms-row head">
          <span>名称</span><span>日期</span><span>类型</span><span>备注</span><span>操作</span>
        </div>
        <div v-for="(m, i) in draft" :key="i" class="ms-row">
          <input v-model="m.label" @input="dirty = true" placeholder="如:TR4-2" />
          <input type="date" v-model="m.date" @input="dirty = true" />
          <div class="type-cell">
            <select v-model="m.type" @change="dirty = true" v-tooltip="'时间线节点类型,决定时间线上的形状与颜色'">
              <option v-for="opt in TYPE_OPTIONS" :key="opt.key" :value="opt.key">
                {{ opt.shape }} {{ opt.key }} · {{ opt.label }}
              </option>
            </select>
            <span class="type-glyph" :style="{ color: styleOf(m.type).color }" v-tooltip="styleOf(m.type).label">
              {{ styleOf(m.type).shape }}
            </span>
          </div>
          <input v-model="m.note" @input="dirty = true" placeholder="备注(可选)" />
          <div class="row-ops">
            <button v-tooltip="'上移'" :disabled="i === 0" @click="move(i, -1)">↑</button>
            <button v-tooltip="'下移'" :disabled="i === draft.length - 1" @click="move(i, 1)">↓</button>
            <button class="danger" v-tooltip="'删除'" @click="remove(i)">×</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.milestone-editor { display: flex; flex-direction: column; gap: 12px; }
.ops { display: flex; gap: 8px; justify-content: flex-end; }
.block h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; }

.ms-table { display: flex; flex-direction: column; gap: 4px; }
.ms-row { display: grid; grid-template-columns: 1.4fr 130px 1.4fr 1.4fr 110px; gap: 6px; align-items: center; }
.ms-row.head { font-size: 11px; color: var(--text-dim); padding: 0 4px; }
.ms-row input, .ms-row select { font-size: 12.5px; }
.type-cell { display: flex; align-items: center; gap: 6px; }
.type-cell select { flex: 1; min-width: 0; }
.type-glyph { font-size: 15px; line-height: 1; width: 18px; text-align: center; flex-shrink: 0; }
.row-ops { display: flex; gap: 2px; justify-content: flex-end; }
.row-ops button { font-size: 11px; padding: 2px 6px; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>
