<script setup>
import { computed } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import StatusCell from './StatusCell.vue'

const { ltcs, status, modulesByScope } = useDashboard()
const { current, pushView } = useView()

const ltcId = computed(() => current.value.ltc || ltcs.value[0]?.id || '')
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
            <StatusCell :color="colorOf(m)" size="sm" />
          </header>
          <div v-if="noteOf(m)" class="note">{{ noteOf(m) }}</div>
          <div v-if="m.sub_items?.length" class="subs">
            <div
              v-for="s in m.sub_items.filter(x => (status?.[m.id]?.sub_items_color?.[x.id] || 'green') !== 'green')"
              :key="s.id"
              class="sub-block"
            >
              <StatusCell :color="subColor(m, s.id)" :label="s.name" size="sm" />
            </div>
          </div>
          <footer>Owner: {{ m.owner_open_id || '—' }} · 更新于 {{ status?.[m.id]?.updated_at || '—' }}</footer>
        </article>
      </section>
    </div>
  </div>
</template>

<style scoped>
.risk-detail { padding: 16px 24px 24px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h1 { margin: 0; font-size: 20px; }
.empty { padding: 48px; text-align: center; color: var(--text-muted); font-size: 16px; }
.columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
.column h2 { font-size: 14px; color: var(--text-muted); margin: 0 0 8px; font-weight: 500; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; margin-bottom: 10px; }
.card header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.name { font-weight: 500; }
.note { background: #fff7e6; border: 1px solid #ffd591; color: #ad6800; padding: 8px 10px; border-radius: var(--radius); font-size: 13px; line-height: 1.5; white-space: pre-wrap; }
.subs { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
footer { margin-top: 8px; font-size: 12px; color: var(--text-muted); }
</style>
