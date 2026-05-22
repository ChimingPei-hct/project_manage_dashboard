<script setup>
import { computed, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import StatusCell from './StatusCell.vue'
import StatusEditDialog from './StatusEditDialog.vue'

const { ltcs, status, modulesByScope } = useDashboard()
const { current, pushView } = useView()
const { canEdit } = useEditableModules()

const currentLtcId = computed(() => current.value.id || ltcs.value[0]?.id || '')
const currentLtc = computed(() => ltcs.value.find(l => l.id === currentLtcId.value))

const ltcModules = computed(() => modulesByScope.value.ltc[currentLtcId.value] || [])
const groups = computed(() => {
  const g = {}
  for (const m of ltcModules.value) {
    const key = m.group || '其他'
    if (!g[key]) g[key] = []
    g[key].push(m)
  }
  return g
})

function colorOf(m) { return status.value?.[m.id]?.module_color || 'gray' }
function subColor(m, sid) { return status.value?.[m.id]?.sub_items_color?.[sid] || 'gray' }
function noteOf(m) { return status.value?.[m.id]?.risk_note || '' }
function hasMismatch(m) {
  if (colorOf(m) !== 'green') return false
  const subs = status.value?.[m.id]?.sub_items_color || {}
  return Object.values(subs).some(c => c && c !== 'green')
}

function changeLtc(e) { pushView({ view: 'ltc', id: e.target.value }) }
function goRisks() { pushView({ view: 'risks', id: currentLtcId.value }) }

const editing = ref(null)
const focusSubId = ref('')
function openEdit(m, subId = '') {
  if (!canEdit(m.id)) return
  focusSubId.value = subId
  editing.value = m
}
function closeEdit() { editing.value = null; focusSubId.value = '' }
</script>

<template>
  <div class="ltc-progress">
    <div class="head">
      <h1>{{ currentLtc?.name || '—' }}</h1>
      <div class="actions">
        <select :value="currentLtcId" @change="changeLtc" v-tooltip="'切换查看的 LTC 子项目'">
          <option v-for="l in ltcs" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
        <button v-tooltip="'仅展示黄/红项及风险说明'" @click="goRisks">风险详情</button>
      </div>
    </div>
    <div v-if="!ltcModules.length" class="empty">该 LTC 下暂无模块</div>
    <div v-else class="columns">
      <section v-for="(items, group) in groups" :key="group" class="column">
        <h2>{{ group }}</h2>
        <article v-for="m in items" :key="m.id" class="card">
          <header>
            <span class="name">
              {{ m.name }}
              <span
                v-if="hasMismatch(m)"
                class="warn"
                v-tooltip="'整体灯为绿,但有子项非绿,请核对一致性'"
              >⚠</span>
            </span>
            <StatusCell
              :color="colorOf(m)"
              size="sm"
              :note="noteOf(m)"
              :editable="canEdit(m.id)"
              @edit="openEdit(m)"
            />
          </header>
          <div v-if="m.sub_items?.length" class="subs">
            <StatusCell
              v-for="s in m.sub_items"
              :key="s.id"
              :color="subColor(m, s.id)"
              :label="s.name"
              size="sm"
              :editable="canEdit(m.id)"
              @edit="openEdit(m, s.id)"
            />
          </div>
        </article>
      </section>
    </div>
    <StatusEditDialog
      :open="!!editing"
      :module="editing"
      :current="editing ? status?.[editing.id] : {}"
      :focus-sub-id="focusSubId"
      @close="closeEdit"
    />
  </div>
</template>

<style scoped>
.ltc-progress { padding: 18px 24px 24px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
h1 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.2px; }
.actions { display: flex; gap: 8px; }
.empty { color: var(--text-muted); padding: 48px; text-align: center; }
.columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
.column {
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 12px;
}
.column h2 {
  font-size: 12px;
  color: var(--text-dim);
  margin: 0 0 10px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 12px;
  margin-bottom: 8px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition), border-color var(--transition);
}
.card:hover { box-shadow: var(--shadow-md); }
.card:last-child { margin-bottom: 0; }
.card header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px; }
.name { font-weight: 600; font-size: 13px; display: inline-flex; align-items: center; gap: 4px; }
.warn { color: var(--status-yellow); font-size: 14px; }
.subs { display: grid; grid-template-columns: repeat(auto-fill, minmax(82px, 1fr)); gap: 4px; }
</style>
