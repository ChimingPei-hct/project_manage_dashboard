<script setup>
import { computed } from 'vue'
const props = defineProps({ milestones: { type: Array, default: () => [] } })
const sorted = computed(() => [...props.milestones].sort((a, b) => (a.date || '').localeCompare(b.date || '')))

const today = new Date().toISOString().slice(0, 10)
function isPast(d) { return (d || '') < today }
function isUpcoming(d) {
  if (!d || d < today) return false
  const diff = (new Date(d) - new Date(today)) / 86400000
  return diff <= 30
}
function typeLabel(t) {
  return { SOP: 'SOP', TR: 'TR', review: '评审' }[t] || (t || '里程碑')
}
</script>

<template>
  <div class="timeline">
    <div v-if="!sorted.length" class="empty">暂无里程碑</div>
    <div v-else class="track">
      <div class="line"></div>
      <div class="markers">
        <div
          v-for="m in sorted"
          :key="m.name + m.date"
          class="marker"
          :class="{ past: isPast(m.date), upcoming: isUpcoming(m.date) }"
          v-tooltip="`${m.name} · ${m.date}${m.note ? ' · ' + m.note : ''}`"
        >
          <span class="badge" :class="`type-${m.type || 'other'}`">{{ typeLabel(m.type) }}</span>
          <div class="dot" :class="`type-${m.type || 'other'}`"></div>
          <div class="meta">
            <div class="name">{{ m.name }}</div>
            <div class="date">{{ m.date }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  padding: 14px 24px 16px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}
.empty { color: var(--text-muted); font-size: 13px; }
.track { position: relative; padding: 6px 0 0; }
.line {
  position: absolute;
  top: 22px;
  left: 6px;
  right: 6px;
  height: 2px;
  background: linear-gradient(to right, var(--border-subtle), var(--border), var(--border-subtle));
  border-radius: var(--radius);
}
.markers { display: flex; justify-content: flex-start; gap: 36px; overflow-x: auto; position: relative; padding-bottom: 2px; }
.marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  min-width: 72px;
  position: relative;
  z-index: 1;
}
.badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: var(--radius);
  color: #fff;
  background: var(--text-muted);
  margin-bottom: 6px;
  letter-spacing: 0.4px;
  font-weight: 600;
}
.badge.type-SOP { background: var(--status-red); }
.badge.type-TR { background: var(--accent); }
.badge.type-review { background: var(--status-yellow); }
.dot {
  width: 12px; height: 12px;
  border-radius: var(--radius);
  background: var(--accent);
  border: 2px solid var(--panel);
  box-shadow: 0 0 0 2px var(--border);
  margin-bottom: 6px;
}
.marker.past .dot { background: var(--text-dim); box-shadow: 0 0 0 2px var(--border-subtle); }
.marker.upcoming .dot { box-shadow: 0 0 0 3px var(--accent-glow); }
.dot.type-SOP { background: var(--status-red); }
.dot.type-TR { background: var(--accent); }
.dot.type-review { background: var(--status-yellow); }
.meta { font-size: 12px; line-height: 1.3; text-align: center; }
.name { font-weight: 600; color: var(--text); }
.date { color: var(--text-muted); margin-top: 2px; font-variant-numeric: tabular-nums; }
.marker.past .name, .marker.past .date { color: var(--text-dim); }
</style>
