<script setup>
import { computed } from 'vue'
const props = defineProps({ milestones: { type: Array, default: () => [] } })
const sorted = computed(() => [...props.milestones].sort((a, b) => (a.date || '').localeCompare(b.date || '')))
</script>

<template>
  <div class="timeline">
    <div v-if="!sorted.length" class="empty">暂无里程碑</div>
    <div v-else class="bar">
      <div v-for="m in sorted" :key="m.name + m.date" class="m" v-tooltip="`${m.name} · ${m.date}${m.note ? ' · ' + m.note : ''}`">
        <div class="dot" :class="`type-${m.type || 'other'}`"></div>
        <div class="meta">
          <div class="name">{{ m.name }}</div>
          <div class="date">{{ m.date }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline { padding: 12px 24px; background: var(--panel); border-bottom: 1px solid var(--border); }
.empty { color: var(--text-muted); font-size: 13px; }
.bar { display: flex; gap: 24px; overflow-x: auto; }
.m { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.dot { width: 10px; height: 10px; border-radius: 2px; background: var(--accent); }
.dot.type-SOP { background: var(--status-red); }
.dot.type-TR { background: var(--accent); }
.dot.type-review { background: var(--status-yellow); }
.meta { font-size: 12px; line-height: 1.2; }
.name { font-weight: 500; }
.date { color: var(--text-muted); }
</style>
