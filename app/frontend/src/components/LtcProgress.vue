<script setup>
import { computed } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useView } from '../composables/useView.js'
import StatusCell from './StatusCell.vue'

const { ltcs, status, modulesByScope } = useDashboard()
const { current, pushView } = useView()

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

function changeLtc(e) { pushView({ view: 'ltc', id: e.target.value }) }
function goRisks() { pushView({ view: 'risks', ltc: currentLtcId.value }) }
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
            <span class="name">{{ m.name }}</span>
            <StatusCell :color="colorOf(m)" size="sm" :note="noteOf(m)" />
          </header>
          <div v-if="m.sub_items?.length" class="subs">
            <StatusCell
              v-for="s in m.sub_items"
              :key="s.id"
              :color="subColor(m, s.id)"
              :label="s.name"
              size="sm"
            />
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<style scoped>
.ltc-progress { padding: 16px 24px 24px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h1 { margin: 0; font-size: 20px; }
.actions { display: flex; gap: 8px; }
.empty { color: var(--text-muted); padding: 32px; text-align: center; }
.columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
.column h2 { font-size: 14px; color: var(--text-muted); margin: 0 0 8px; font-weight: 500; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px 12px; margin-bottom: 8px; }
.card header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.name { font-weight: 500; font-size: 13px; }
.subs { display: flex; flex-wrap: wrap; gap: 4px; }
</style>
