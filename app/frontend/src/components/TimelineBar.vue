<script setup>
import { computed } from 'vue'

const props = defineProps({
  milestones: { type: Array, default: () => [] },
})

const sorted = computed(() =>
  [...props.milestones]
    .filter(m => m.date)
    .sort((a, b) => (a.date || '').localeCompare(b.date || ''))
)

/* 计算时间轴范围:从最早里程碑到最晚里程碑,跨度至少 4 个月,且包含今天 */
const range = computed(() => {
  const today = new Date()
  let earliest = today, latest = today
  for (const m of sorted.value) {
    const d = new Date(m.date)
    if (d < earliest) earliest = d
    if (d > latest) latest = d
  }
  // 兜底:前后各扩 15 天
  const start = new Date(earliest); start.setDate(start.getDate() - 15)
  const end = new Date(latest); end.setDate(end.getDate() + 15)
  return { start, end, today, span: Math.max(1, end - start) }
})

function pct(date) {
  const d = new Date(date)
  return Math.max(0, Math.min(100, ((d - range.value.start) / range.value.span) * 100))
}

/* 月份刻度 */
const monthTicks = computed(() => {
  const out = []
  const { start, end } = range.value
  const cur = new Date(start.getFullYear(), start.getMonth(), 1)
  while (cur <= end) {
    out.push({
      label: String(cur.getMonth() + 1).padStart(2, '0'),
      year: cur.getFullYear(),
      pct: pct(cur),
    })
    cur.setMonth(cur.getMonth() + 1)
  }
  return out
})

const todayPct = computed(() => pct(new Date()))

function typeLabel(t) {
  return { SOP: 'SOP', TR: 'TR', Block: 'Block', Custom: '' }[t] || (t || '')
}

function isPast(d) {
  return new Date(d) < new Date().setHours(0, 0, 0, 0)
}

/* 交错 4 行排列,缓解相邻里程碑标签重叠 */
const ROWS = ['r0', 'r1', 'r2', 'r3']
function rowOf(idx) { return ROWS[idx % ROWS.length] }
</script>

<template>
  <div class="timeline">
    <div v-if="!sorted.length" class="empty">暂无里程碑 · 可在管理后台添加</div>
    <div v-else class="track">
      <div class="months">
        <div
          v-for="t in monthTicks"
          :key="t.year + '-' + t.label"
          class="month-tick"
          :style="{ left: t.pct + '%' }"
        >
          <span class="m-label">{{ t.label }}</span>
        </div>
      </div>
      <div class="axis"></div>
      <div
        class="today-line"
        :style="{ left: todayPct + '%' }"
        v-tooltip="'今天'"
      >
        <span class="today-label">今天</span>
      </div>
      <div class="markers">
        <div
          v-for="(m, i) in sorted"
          :key="(m.name || m.label) + m.date"
          class="marker"
          :class="[rowOf(i), { past: isPast(m.date) }]"
          :style="{ left: pct(m.date) + '%' }"
          v-tooltip="`${m.label || m.name} · ${m.date}${m.note ? ' · ' + m.note : ''}`"
        >
          <span class="badge" :class="`type-${m.type || 'TR'}`">
            {{ typeLabel(m.type) }}
          </span>
          <span class="m-name">{{ m.label || m.name }}</span>
          <span class="m-date">{{ m.date.slice(5) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 24px 18px;
  margin: 0 24px 16px;
}
.empty { color: var(--text-muted); font-size: 13px; padding: 12px 0; text-align: center; }
.track {
  position: relative;
  height: 170px;
}
.months {
  position: absolute;
  inset: 0;
}
.month-tick {
  position: absolute;
  top: 80px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-dim);
}
.m-label {
  font-size: 11px;
  font-weight: 600;
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 1px 6px;
  font-variant-numeric: tabular-nums;
}
.axis {
  position: absolute;
  top: 84px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, var(--border), var(--accent-soft) 50%, var(--border));
  border-radius: var(--radius);
}
.today-line {
  position: absolute;
  top: 0;
  height: 100%;
  width: 1px;
  background: linear-gradient(to bottom, transparent, var(--accent) 30%, var(--accent) 70%, transparent);
  z-index: 1;
}
.today-line .today-label {
  position: absolute;
  top: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  background: var(--accent);
  color: #fff;
  padding: 1px 6px;
  border-radius: var(--radius);
  white-space: nowrap;
  font-weight: 600;
}
.markers { position: absolute; inset: 0; }
.marker {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateX(-50%);
  z-index: 2;
}
.marker.r0 { top: 2px; }
.marker.r1 { top: 38px; }
.marker.r2 { top: 96px; }
.marker.r3 { top: 132px; }
.marker.r0 .badge, .marker.r1 .badge { margin-bottom: 3px; }
.marker.r2 .badge, .marker.r3 .badge { order: 3; margin-top: 3px; }
.marker.r2 .m-name, .marker.r3 .m-name { order: 1; }
.marker.r2 .m-date, .marker.r3 .m-date { order: 2; }
/* 连接线:把上下排的 marker 用细线连到轴 */
.marker.r0::after, .marker.r1::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 100%;
  width: 1px;
  background: var(--border);
}
.marker.r0::after { height: 50px; }
.marker.r1::after { height: 14px; }
.marker.r2::after, .marker.r3::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 100%;
  width: 1px;
  background: var(--border);
}
.marker.r2::after { height: 14px; }
.marker.r3::after { height: 50px; }
.marker .badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius);
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.3px;
  min-width: 22px;
  text-align: center;
}
.marker .badge.type-TR { background: var(--accent); }
.marker .badge.type-SOP { background: var(--status-red); }
.marker .badge.type-Block { background: var(--status-yellow); }
.marker .badge.type-Custom { background: var(--text-muted); }
.m-name {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--text);
  background: var(--panel);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 1px 6px;
  white-space: nowrap;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.m-date {
  font-size: 10px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}
.marker.past { opacity: 0.55; }
.marker.past .badge { filter: grayscale(0.3); }
</style>
