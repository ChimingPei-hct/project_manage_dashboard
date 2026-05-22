<script setup>
import { ref, watch, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi } from '../../composables/useAdminApi.js'
import TimelineBar from '../TimelineBar.vue'

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
  draft.value.push({ label: '新里程碑', date: new Date().toISOString().slice(0, 10), type: 'TR', note: '' })
  dirty.value = true
}
function remove(i) { draft.value.splice(i, 1); dirty.value = true }
function move(i, dir) {
  const j = i + dir
  if (j < 0 || j >= draft.value.length) return
  ;[draft.value[i], draft.value[j]] = [draft.value[j], draft.value[i]]
  dirty.value = true
}

const previewMilestones = computed(() => draft.value.filter(m => m.date))

async function save() {
  saving.value = true
  errMsg.value = ''
  try {
    /* 保留 PDT 其他字段,只覆盖 milestones */
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
  <div class="milestones-drawer">
    <header class="dh">
      <div>
        <div class="crumb">PDT 配置 / 里程碑</div>
        <h2>时间轴里程碑</h2>
      </div>
      <div class="ops">
        <button v-tooltip="'添加一个里程碑'" @click="add">+ 新增</button>
        <button class="primary" :disabled="!dirty || saving" v-tooltip="dirty ? '保存修改' : '无变更'" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </div>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>预览</h3>
      <TimelineBar :milestones="previewMilestones" />
    </section>

    <section class="block">
      <h3>里程碑列表</h3>
      <div v-if="!draft.length" class="hint">还没有里程碑 · 点上方「+ 新增」开始</div>
      <div v-else class="ms-table">
        <div class="ms-row head">
          <span>名称</span><span>日期</span><span>类型</span><span>备注</span><span>操作</span>
        </div>
        <div v-for="(m, i) in draft" :key="i" class="ms-row">
          <input v-model="m.label" @input="dirty = true" placeholder="如:TR4-2" />
          <input type="date" v-model="m.date" @input="dirty = true" />
          <select v-model="m.type" @change="dirty = true" v-tooltip="'里程碑类型,决定时间轴上的色块'">
            <option value="TR">TR · 技术评审</option>
            <option value="SOP">SOP · 量产</option>
            <option value="Block">Block · 阻塞</option>
            <option value="Custom">Custom · 其他</option>
          </select>
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
.milestones-drawer { display: flex; flex-direction: column; gap: 16px; }
.dh { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
.ops { display: flex; gap: 8px; }
.block h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; }

.ms-table { display: flex; flex-direction: column; gap: 4px; }
.ms-row { display: grid; grid-template-columns: 1.4fr 130px 1fr 1.4fr 110px; gap: 6px; align-items: center; }
.ms-row.head { font-size: 11px; color: var(--text-dim); padding: 0 4px; }
.ms-row input, .ms-row select { font-size: 12.5px; }
.row-ops { display: flex; gap: 2px; justify-content: flex-end; }
.row-ops button { font-size: 11px; padding: 2px 6px; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }
.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>
