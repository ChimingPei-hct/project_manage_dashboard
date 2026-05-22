<script setup>
import { computed, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import TimelineBar from './TimelineBar.vue'
import StatusCell from './StatusCell.vue'
import StatusEditDialog from './StatusEditDialog.vue'

const { pdt, status, modulesByScope } = useDashboard()
const { canEdit } = useEditableModules()

const grouped = computed(() => {
  const groups = {}
  for (const m of modulesByScope.value.pdt) {
    const g = m.group || '其他'
    if (!groups[g]) groups[g] = []
    groups[g].push(m)
  }
  return groups
})

function colorOf(m) { return status.value?.[m.id]?.module_color || 'gray' }
function noteOf(m) { return status.value?.[m.id]?.risk_note || '' }

const editing = ref(null) // module
function openEdit(m) { if (canEdit(m.id)) editing.value = m }
function closeEdit() { editing.value = null }
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
              <StatusCell
                :color="colorOf(m)"
                size="sm"
                :note="noteOf(m)"
                :editable="canEdit(m.id)"
                @edit="openEdit(m)"
              />
            </header>
            <ul class="kpis" v-if="m.kpi_fields?.length">
              <li v-for="kpi in m.kpi_fields" :key="kpi.key">
                <span class="k">{{ kpi.label }}</span>
                <span
                  class="v"
                  :class="{ 'empty-v': !status?.[m.id]?.kpi_values?.[kpi.key] }"
                >{{ status?.[m.id]?.kpi_values?.[kpi.key] || '— —' }}</span>
              </li>
            </ul>
            <p v-if="noteOf(m)" class="risk">{{ noteOf(m) }}</p>
            <footer>
              <span>Owner: {{ m.owner_open_id || '未指派' }}</span>
              <button
                v-if="canEdit(m.id)"
                class="edit-btn"
                v-tooltip="'编辑本模块的状态、风险说明与 KPI'"
                @click="openEdit(m)"
              >编辑</button>
            </footer>
          </article>
        </div>
      </section>
    </div>
    <StatusEditDialog
      :open="!!editing"
      :module="editing"
      :current="editing ? status?.[editing.id] : {}"
      @close="closeEdit"
    />
  </div>
</template>

<style scoped>
.pdt-overview { padding-bottom: 24px; }
.head { padding: 20px 24px 4px; }
h1 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: -0.2px; }
.desc { color: var(--text-muted); margin: 6px 0 0; font-size: 13px; }
.grid { padding: 4px 24px 24px; }
.empty { color: var(--text-muted); padding: 48px 0; text-align: center; }
.group { margin-top: 18px; }
.group h2 {
  font-size: 12px;
  color: var(--text-dim);
  margin: 0 0 10px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition), border-color var(--transition);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.card:hover { box-shadow: var(--shadow-md); border-color: var(--border); }
.card header { display: flex; justify-content: space-between; align-items: center; }
.name { font-weight: 600; font-size: 14px; }
.kpis { list-style: none; margin: 0; padding: 6px 0 0; font-size: 13px; border-top: 1px dashed var(--border-subtle); }
.kpis li { display: flex; justify-content: space-between; padding: 4px 0; }
.k { color: var(--text-muted); }
.v { font-variant-numeric: tabular-nums; font-weight: 500; color: var(--text); }
.v.empty-v { color: var(--text-dim); font-weight: 400; }
.risk {
  font-size: 12px;
  color: var(--status-red);
  background: var(--status-red-bg);
  border-radius: var(--radius);
  padding: 6px 10px;
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
footer {
  margin-top: auto;
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-subtle);
  padding-top: 8px;
}
.edit-btn { font-size: 12px; padding: 2px 10px; }
</style>
