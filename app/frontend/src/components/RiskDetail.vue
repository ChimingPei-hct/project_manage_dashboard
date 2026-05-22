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

const ltcId = computed(() => current.value.id || ltcs.value[0]?.id || '')
const ltc = computed(() => ltcs.value.find(l => l.id === ltcId.value))

function colorOf(m) { return status.value?.[m.id]?.module_color || 'gray' }
function subColor(m, sid) { return status.value?.[m.id]?.sub_items_color?.[sid] || 'gray' }
function noteOf(m) { return status.value?.[m.id]?.risk_note || '' }

const riskyModules = computed(() => {
  const all = modulesByScope.value.ltc[ltcId.value] || []
  return all.filter(m => {
    if (colorOf(m) !== 'green' && colorOf(m) !== 'gray') return true
    const subs = status.value?.[m.id]?.sub_items_color || {}
    return Object.values(subs).some(c => c !== 'green')
  })
})

const groups = computed(() => {
  const g = {}
  for (const m of riskyModules.value) {
    const key = m.group || '其他'
    if (!g[key]) g[key] = []
    g[key].push(m)
  }
  return g
})

function back() { pushView({ view: 'ltc', id: ltcId.value }) }

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
  <div class="risk-detail">
    <div class="head">
      <h1>{{ ltc?.name }} · 风险详情</h1>
      <button @click="back" v-tooltip="'返回 LTC 研发进展页'">返回 LTC 进展</button>
    </div>
    <div v-if="!riskyModules.length" class="empty">本周无风险项 🎉</div>
    <div v-else class="columns">
      <section v-for="(items, group) in groups" :key="group" class="column">
        <h2>{{ group }}</h2>
        <article v-for="m in items" :key="m.id" class="card">
          <header>
            <span class="name">{{ m.name }}</span>
            <StatusCell
              :color="colorOf(m)"
              size="sm"
              :editable="canEdit(m.id)"
              @edit="openEdit(m)"
            />
          </header>
          <div v-if="noteOf(m)" class="note">{{ noteOf(m) }}</div>
          <div v-if="m.sub_items?.length" class="subs">
            <div
              v-for="s in m.sub_items.filter(x => (status?.[m.id]?.sub_items_color?.[x.id] || 'green') !== 'green')"
              :key="s.id"
              class="sub-block"
            >
              <StatusCell
                :color="subColor(m, s.id)"
                :label="s.name"
                size="sm"
                :editable="canEdit(m.id)"
                @edit="openEdit(m, s.id)"
              />
            </div>
          </div>
          <footer>
            <span>Owner: {{ m.owner_open_id || '—' }} · 更新于 {{ status?.[m.id]?.updated_at || '—' }}</span>
            <button
              v-if="canEdit(m.id)"
              class="edit-btn"
              v-tooltip="'编辑状态与风险说明,可在此直接修复'"
              @click="openEdit(m)"
            >编辑</button>
          </footer>
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
/* 风险详情页用于评审会议大屏:字号、行距、对比度均放大 */
.risk-detail { padding: 20px 28px 28px; font-size: 15px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.3px; }
.empty {
  padding: 80px 24px;
  text-align: center;
  color: var(--status-green);
  background: var(--status-green-bg);
  border-radius: var(--radius);
  font-size: 22px;
  font-weight: 600;
}
.columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; }
.column h2 {
  font-size: 13px;
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
  padding: 16px 18px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-sm);
}
.card header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.name { font-weight: 700; font-size: 17px; }
.note {
  background: var(--status-yellow-bg);
  border: 1px solid rgba(217,119,6,0.30);
  color: var(--status-yellow);
  padding: 12px 14px;
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 500;
  line-height: 1.6;
  white-space: pre-wrap;
}
.subs { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
footer {
  margin-top: 14px;
  padding-top: 10px;
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-subtle);
}
.edit-btn { font-size: 13px; padding: 4px 12px; }
</style>
