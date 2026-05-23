<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboard } from '../composables/useDashboard.js'
import { useEditableModules } from '../composables/useEditableModules.js'
import { useContactCache, displayName } from '../composables/useContactCache.js'
import { kpiItemsOf, risksOf, currentWeekRange } from '../composables/useStatusHelpers.js'
import TimelineBar from './TimelineBar.vue'
import StatusLegend from './StatusLegend.vue'
import ModuleStatusDots from './ModuleStatusDots.vue'
import StatusEditDialog from './StatusEditDialog.vue'
import OwnerChip from './OwnerChip.vue'

const { pdt, status, modulesByScope } = useDashboard()
const { canEdit } = useEditableModules()
const { ensureContacts } = useContactCache()
onMounted(() => { ensureContacts() })

/* 优先用配置的 overview_cards;无则回退到 modulesByScope.pdt(老 schema 自动适配) */
const cards = computed(() => {
  const oc = pdt.value?.overview_cards
  if (Array.isArray(oc) && oc.length) {
    /* overview_cards 关联到 modules.json 中 scope=pdt 的模块,通过 module_id 引用 */
    return oc.map(c => {
      const mod = modulesByScope.value.pdt.find(m => m.id === c.module_id)
      return {
        id: c.id,
        name: c.name || mod?.name || '未命名',
        owner_open_id: c.owner_open_id || mod?.owner_open_id,
        module: mod, // 真正的 module 对象(用于状态/编辑权限)
        kpi_fields: mod?.kpi_fields || c.kpi_fields || [],
        show_risk: c.show_risk !== false,
        order: c.order ?? 0,
      }
    }).filter(c => c.module).sort((a, b) => a.order - b.order)
  }
  return modulesByScope.value.pdt.map((m, i) => ({
    id: m.id,
    name: m.name,
    owner_open_id: m.owner_open_id,
    module: m,
    kpi_fields: m.kpi_fields || [],
    show_risk: true,
    order: m.order ?? i,
  })).sort((a, b) => a.order - b.order)
})

function statusOf(card) { return status.value?.[card.module.id] || null }
function colorOf(card) { return statusOf(card)?.module_color || 'gray' }
function kpisOf(card) { return kpiItemsOf(statusOf(card), card.kpi_fields) }
function risksFor(card) { return card.show_risk ? risksOf(statusOf(card)) : [] }

const editing = ref(null)
function openEdit(card) {
  if (canEdit(card.module.id)) editing.value = card.module
}
function closeEdit() { editing.value = null }

const dateRange = computed(() => currentWeekRange())
</script>

<template>
  <div class="pdt-overview">
    <div class="head">
      <div class="title-block">
        <h1>{{ pdt?.name || '— 未配置 PDT —' }}</h1>
        <span class="date-range">{{ dateRange }}</span>
      </div>
      <StatusLegend />
    </div>

    <TimelineBar :milestones="pdt?.milestones || []" />

    <div v-if="!cards.length" class="empty">
      暂无 PDT 级总览卡片,请管理员前往
      <a href="?view=admin">管理后台</a> 配置总览卡片或添加 scope=pdt 的模块。
    </div>

    <div v-else class="cards-grid">
      <article
        v-for="card in cards"
        :key="card.id"
        class="card"
        :class="`tone-${colorOf(card)}`"
      >
        <header class="card-head">
          <span class="card-name">{{ card.name }}</span>
          <ModuleStatusDots
            :color="colorOf(card)"
            :editable="canEdit(card.module.id)"
            :note="(risksFor(card)[0] || {}).text"
            @edit="openEdit(card)"
          />
        </header>

        <ul v-if="kpisOf(card).length" class="kpis">
          <li v-for="(kpi, i) in kpisOf(card)" :key="i">
            <span class="dot-bullet"></span>
            <span class="k">{{ kpi.label }}</span>
            <span class="sep">:</span>
            <span class="v">{{ kpi.value || '—' }}</span>
            <span v-if="kpi.target" class="target">/ {{ kpi.target }}</span>
          </li>
        </ul>
        <div v-else class="kpis-empty">暂无 KPI</div>

        <div v-if="risksFor(card).length" class="risks">
          <div class="risks-title">重点问题</div>
          <div
            v-for="(r, i) in risksFor(card)"
            :key="i"
            class="risk-line"
            :class="`sev-${r.severity}`"
          >
            <span class="risk-icon">⚠</span>
            <span class="risk-text">{{ r.text }}</span>
          </div>
        </div>

        <footer class="card-foot">
          <OwnerChip :open-id="card.owner_open_id" prefix="Owner: " fallback="未指派" />
          <button
            v-if="canEdit(card.module.id)"
            class="edit-btn"
            v-tooltip="'编辑该卡片对应模块的状态、KPI 与风险'"
            @click="openEdit(card)"
          >编辑</button>
        </footer>
      </article>
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
.pdt-overview { padding: 18px 0 32px; }
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0 24px 14px;
  gap: 16px;
  flex-wrap: wrap;
}
.title-block { display: flex; align-items: baseline; gap: 12px; }
h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #1a1f36 30%, var(--accent) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.date-range {
  font-size: 14px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  background: var(--panel-soft);
  padding: 3px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--border-subtle);
}

.empty { text-align: center; padding: 64px 24px; color: var(--text-muted); }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
  padding: 0 24px;
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 14px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
  position: relative;
  overflow: hidden;
}
.card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--status-gray);
  border-radius: var(--radius) 0 0 var(--radius);
}
.card.tone-green::before { background: var(--status-green); }
.card.tone-yellow::before { background: var(--status-yellow); }
.card.tone-red::before { background: var(--status-red); }
.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: var(--accent-soft);
}

.card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.card-name { font-weight: 700; font-size: 15px; color: var(--text); }

.kpis {
  list-style: none;
  margin: 0;
  padding: 8px 0;
  font-size: 12.5px;
  border-top: 1px dashed var(--border-subtle);
  border-bottom: 1px dashed var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.kpis li { display: flex; align-items: baseline; gap: 4px; line-height: 1.5; }
.dot-bullet {
  width: 4px; height: 4px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  display: inline-block;
  flex-shrink: 0;
  margin-right: 4px;
  margin-top: 7px;
  align-self: flex-start;
}
.k { color: var(--text-muted); flex-shrink: 0; }
.sep { color: var(--text-dim); margin: 0 2px; }
.v { color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
.target { color: var(--text-dim); font-size: 11px; margin-left: 4px; font-variant-numeric: tabular-nums; }
.kpis-empty { font-size: 12px; color: var(--text-dim); padding: 6px 0; border-top: 1px dashed var(--border-subtle); border-bottom: 1px dashed var(--border-subtle); text-align: center; }

.risks { display: flex; flex-direction: column; gap: 4px; }
.risks-title { font-size: 11px; color: var(--text-dim); font-weight: 600; letter-spacing: 0.4px; }
.risk-line {
  display: flex;
  gap: 6px;
  align-items: flex-start;
  font-size: 12px;
  padding: 6px 8px;
  border-radius: var(--radius);
  line-height: 1.5;
}
.risk-line.sev-red { background: var(--status-red-bg); color: var(--status-red); }
.risk-line.sev-yellow { background: var(--status-yellow-bg); color: var(--status-yellow); }
.risk-icon { flex-shrink: 0; font-size: 12px; }
.risk-text { flex: 1; }

.card-foot {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
}
.owner {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: var(--radius);
  font-weight: 500;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.edit-btn { font-size: 11px; padding: 2px 10px; }
</style>
