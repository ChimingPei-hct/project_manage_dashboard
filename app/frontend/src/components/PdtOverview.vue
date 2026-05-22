<script setup>
import { computed } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import TimelineBar from './TimelineBar.vue'
import StatusCell from './StatusCell.vue'

const { pdt, status, modulesByScope } = useDashboard()

const grouped = computed(() => {
  const groups = {}
  for (const m of modulesByScope.value.pdt) {
    const g = m.group || '其他'
    if (!groups[g]) groups[g] = []
    groups[g].push(m)
  }
  return groups
})

function colorOf(m) {
  return status.value?.[m.id]?.module_color || 'gray'
}
function noteOf(m) {
  return status.value?.[m.id]?.risk_note || ''
}
</script>

<template>
  <div class="pdt-overview">
    <div class="head">
      <h1>{{ pdt?.name || '— 未配置 —' }}</h1>
      <p v-if="pdt?.description" class="desc">{{ pdt.description }}</p>
    </div>
    <TimelineBar :milestones="pdt?.milestones || []" />
    <div class="grid">
      <div v-if="!modulesByScope.pdt.length" class="empty">
        暂无 PDT 级模块,请管理员前往 <a href="?view=admin">管理后台</a> 添加。
      </div>
      <section v-for="(items, group) in grouped" :key="group" class="group">
        <h2>{{ group }}</h2>
        <div class="cards">
          <article v-for="m in items" :key="m.id" class="card">
            <header>
              <span class="name">{{ m.name }}</span>
              <StatusCell :color="colorOf(m)" size="sm" :note="noteOf(m)" />
            </header>
            <ul class="kpis" v-if="m.kpi_fields?.length">
              <li v-for="kpi in m.kpi_fields" :key="kpi.key">
                <span class="k">{{ kpi.label }}:</span>
                <span class="v">{{ status?.[m.id]?.kpi_values?.[kpi.key] || '—' }}</span>
              </li>
            </ul>
            <p v-if="noteOf(m)" class="risk">{{ noteOf(m) }}</p>
            <footer>Owner: {{ m.owner_open_id || '未指派' }}</footer>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.pdt-overview { padding-bottom: 24px; }
.head { padding: 16px 24px 0; }
h1 { margin: 0; font-size: 20px; }
.desc { color: var(--text-muted); margin: 4px 0 0; }
.grid { padding: 8px 24px 24px; }
.empty { color: var(--text-muted); padding: 32px 0; text-align: center; }
.group h2 { font-size: 14px; color: var(--text-muted); margin: 16px 0 8px; font-weight: 500; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; }
.card header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.name { font-weight: 500; }
.kpis { list-style: none; margin: 0; padding: 0; font-size: 13px; }
.kpis li { display: flex; justify-content: space-between; padding: 2px 0; }
.k { color: var(--text-muted); }
.risk { font-size: 12px; color: var(--status-red); margin: 6px 0 0; line-height: 1.4; }
footer { margin-top: 8px; font-size: 12px; color: var(--text-muted); }
</style>
