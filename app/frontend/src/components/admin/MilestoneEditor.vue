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
    <div class="ops-bar">
      <div class="counts">
        <span class="count-chip">共 <strong>{{ draft.length }}</strong> 个节点</span>
        <span v-if="dirty" class="dirty-chip" v-tooltip="'有未保存修改'">● 未保存</span>
      </div>
      <div class="ops">
        <button class="ghost" v-tooltip="'添加一个时间线节点'" @click="add">
          <span class="plus">+</span>新增节点
        </button>
        <button class="primary" :disabled="!dirty || saving" v-tooltip="dirty ? '保存所有修改到 PDT' : '无变更可保存'" @click="save">
          {{ saving ? '保存中…' : (dirty ? '保存修改' : '已保存') }}
        </button>
      </div>
    </div>

    <p v-if="errMsg" class="err-banner">⚠ {{ errMsg }}</p>

    <section class="block">
      <div v-if="!draft.length" class="empty-state">
        <div class="empty-icon">🗓</div>
        <div class="empty-title">还没有时间线节点</div>
        <div class="empty-hint">点上方「+ 新增节点」开始,或先在 PDT 总览里看时间轴形态</div>
      </div>
      <div v-else class="ms-list">
        <div class="ms-head">
          <span class="h-name">名称</span>
          <span class="h-date">日期</span>
          <span class="h-type">类型</span>
          <span class="h-note">备注</span>
          <span class="h-ops">操作</span>
        </div>
        <div
          v-for="(m, i) in draft"
          :key="i"
          class="ms-card"
          :class="`type-${m.type}`"
          :style="{ '--type-color': styleOf(m.type).color }"
        >
          <div class="type-shape" v-tooltip="styleOf(m.type).label">{{ styleOf(m.type).shape }}</div>
          <input class="f-name" v-model="m.label" @input="dirty = true" placeholder="如:TR4-2" />
          <input class="f-date" type="date" v-model="m.date" @input="dirty = true" />
          <select
            class="f-type"
            v-model="m.type"
            :style="{ color: styleOf(m.type).color, fontWeight: 600 }"
            @change="dirty = true"
            v-tooltip="'时间线节点类型,决定时间轴上的形状与颜色'"
          >
            <option v-for="opt in TYPE_OPTIONS" :key="opt.key" :value="opt.key">
              {{ opt.shape }} {{ opt.key }} · {{ opt.label }}
            </option>
          </select>
          <input class="f-note" v-model="m.note" @input="dirty = true" placeholder="备注(可选)" />
          <div class="row-ops">
            <button class="ops-icon" v-tooltip="'上移'" :disabled="i === 0" @click="move(i, -1)">↑</button>
            <button class="ops-icon" v-tooltip="'下移'" :disabled="i === draft.length - 1" @click="move(i, 1)">↓</button>
            <button class="ops-icon danger" v-tooltip="'删除节点'" @click="remove(i)">×</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.milestone-editor { display: flex; flex-direction: column; gap: 16px; }

/* ── 操作栏:左侧计数,右侧主操作 ── */
.ops-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}
.counts { display: flex; gap: 10px; align-items: center; }
.count-chip {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}
.count-chip strong { color: var(--text-strong); font-weight: 700; font-variant-numeric: tabular-nums; }
.dirty-chip {
  font-size: 12px;
  color: var(--status-yellow);
  font-weight: 600;
  background: var(--status-yellow-bg-strong);
  border: 1px solid var(--status-yellow-border);
  padding: 3px 9px;
  border-radius: var(--radius);
  letter-spacing: 0.3px;
}
.ops { display: flex; gap: 8px; }
.ops button {
  font-size: 13px;
  font-weight: 600;
  padding: 7px 14px;
  border-radius: var(--radius);
  transition: all var(--transition);
}
.ops button.ghost {
  background: transparent;
  border-color: var(--border);
  color: var(--text-strong);
}
.ops button.ghost:hover {
  background: var(--panel-soft);
  border-color: var(--accent);
  color: var(--accent);
}
.ops .plus { font-size: 15px; margin-right: 3px; font-weight: 400; }

/* ── 表头 + 行卡片 ── */
.ms-list { display: flex; flex-direction: column; gap: 6px; }
.ms-head {
  display: grid;
  grid-template-columns: 28px 1.6fr 140px 1.6fr 1.8fr 110px;
  gap: 10px;
  padding: 0 14px 4px 14px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.ms-head > span:nth-child(1) { grid-column: 2; }
.ms-head > span:nth-child(2) { grid-column: 3; }
.ms-head > span:nth-child(3) { grid-column: 4; }
.ms-head > span:nth-child(4) { grid-column: 5; }
.ms-head > span:nth-child(5) { grid-column: 6; text-align: right; }

.ms-card {
  display: grid;
  grid-template-columns: 28px 1.6fr 140px 1.6fr 1.8fr 110px;
  gap: 10px;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 4px solid var(--type-color, var(--text-dim));
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 10px 14px 10px 12px;
  transition:
    box-shadow var(--transition),
    transform var(--transition),
    border-color var(--transition);
}
.ms-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateX(2px);
  border-color: var(--border-strong);
  border-left-color: var(--type-color);
}
.type-shape {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  color: var(--type-color);
  flex-shrink: 0;
}
.ms-card input,
.ms-card select {
  font-size: 13.5px;
  padding: 7px 11px;
  min-width: 0;
  width: 100%;
  background: var(--panel-soft);
  border-color: var(--border-subtle);
}
.ms-card input:hover,
.ms-card select:hover { background: var(--panel); border-color: var(--border); }
.ms-card input:focus,
.ms-card select:focus { background: var(--panel); }
.f-date { font-family: var(--font-mono); font-variant-numeric: tabular-nums; letter-spacing: 0.2px; }

.row-ops {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}
.ops-icon {
  font-size: 13px;
  font-weight: 600;
  padding: 5px 9px;
  min-width: 30px;
  border-radius: var(--radius);
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition);
}
.ops-icon:hover:not(:disabled) {
  background: var(--panel-soft);
  border-color: var(--border);
  color: var(--text-strong);
}
.ops-icon:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.ops-icon.danger:hover {
  background: var(--status-red-bg-strong);
  border-color: var(--status-red-border-strong);
  color: var(--status-red);
}

/* ── 空状态 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  background: var(--panel-soft);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  gap: 8px;
}
.empty-icon { font-size: 40px; opacity: 0.5; line-height: 1; }
.empty-title { font-size: 15px; font-weight: 600; color: var(--text-strong); }
.empty-hint { font-size: 13px; color: var(--text-muted); }

.err-banner {
  background: var(--status-red-bg-strong);
  border: 1px solid var(--status-red-border-strong);
  color: var(--text-strong);
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  margin: 0;
}
</style>
