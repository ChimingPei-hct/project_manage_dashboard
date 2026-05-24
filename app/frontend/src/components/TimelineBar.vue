<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { Timeline, DataSet } from 'vis-timeline/standalone'
import 'vis-timeline/styles/vis-timeline-graph2d.min.css'
import moment from 'moment/min/moment-with-locales'
moment.locale('zh-cn')
import { TYPE_STYLE, styleOf } from '../constants/milestoneTypes.js'

const props = defineProps({
  milestones: { type: Array, default: () => [] },
})

const container = ref(null)
let timeline = null
let items = null
let groups = null

const sorted = computed(() =>
  [...props.milestones]
    .filter(m => m.date)
    .sort((a, b) => (a.date || '').localeCompare(b.date || ''))
)

function buildItems() {
  return sorted.value.map((m, i) => {
    const type = m.type || 'other'
    const label = m.label || m.name || ''
    const date = m.date
    const safeType = String(type).replace(/[^a-zA-Z0-9_-]/g, '_')
    return {
      id: (m.id != null ? m.id : `${label}-${date}-${i}`),
      group: type,
      start: date,
      type: 'box',
      className: `ms-item ms-${safeType}`,
      title: `${label} · ${date}${m.note ? ' · ' + m.note : ''}`,
      _meta: { type, label, date, note: m.note || '' },
    }
  })
}

/* 返回 DOM 元素绕过 vis-timeline 的 XSS 字符串过滤 */
function itemTemplate(item) {
  const meta = item._meta
  if (!meta) return ''
  const st = styleOf(meta.type)
  const wrap = document.createElement('div')
  wrap.className = 'ms-content'
  const shape = document.createElement('div')
  shape.className = 'ms-shape'
  shape.textContent = st.shape
  shape.style.color = st.color
  const label = document.createElement('div')
  label.className = 'ms-label'
  label.textContent = meta.label
  label.style.color = st.color
  const date = document.createElement('div')
  date.className = 'ms-date'
  date.textContent = meta.date.slice(5)
  wrap.append(shape, label, date)
  return wrap
}

/* 默认窗口:覆盖所有里程碑 + 跨度 ~8% 的左右留白,左侧留白稍大以容纳贴边 item 的居中文字 */
function defaultWindow() {
  const today = new Date()
  let earliest = today, latest = today
  for (const m of sorted.value) {
    const d = new Date(m.date)
    if (d < earliest) earliest = d
    if (d > latest) latest = d
  }
  const span = Math.max(1000 * 60 * 60 * 24 * 90, latest - earliest)
  const padL = Math.max(span * 0.08, 1000 * 60 * 60 * 24 * 30)
  const padR = Math.max(span * 0.05, 1000 * 60 * 60 * 24 * 20)
  return { start: new Date(+earliest - padL), end: new Date(+latest + padR) }
}

/* 仅显示数据中出现的类型,顺序按 TYPE_STYLE.order */
function activeGroups() {
  const used = [...new Set(sorted.value.map(m => m.type || 'other'))]
  return used
    .map(t => ({ id: t, content: styleOf(t).label, _order: styleOf(t).order }))
    .sort((a, b) => a._order - b._order)
}

function render() {
  if (!container.value) return
  if (!sorted.value.length) {
    if (timeline) { timeline.destroy(); timeline = null }
    return
  }
  const { start, end } = defaultWindow()
  const itemList = buildItems()
  const groupList = activeGroups()

  if (!timeline) {
    items = new DataSet(itemList)
    groups = new DataSet(groupList)
    timeline = new Timeline(container.value, items, groups, {
      stack: true,
      orientation: { axis: 'top', item: 'top' },
      showCurrentTime: true,
      showMajorLabels: true,
      showMinorLabels: true,
      zoomMin: 1000 * 60 * 60 * 24 * 14,
      zoomMax: 1000 * 60 * 60 * 24 * 365 * 6,
      start, end,
      margin: { item: { vertical: 8, horizontal: 12 }, axis: 14 },
      moveable: true,
      selectable: false,
      template: itemTemplate,
      locale: 'zh-cn',
      locales: {
        'zh-cn': { current: '当前', time: '', deleteSelected: '删除' },
      },
      moment: (date) => moment(date),
      format: {
        minorLabels: {
          millisecond: 'SSS', second: 's', minute: 'HH:mm', hour: 'HH:mm',
          weekday: 'ddd D', day: 'D', week: '[W]w', month: 'M月', year: 'YYYY',
        },
        majorLabels: {
          millisecond: 'HH:mm:ss', second: 'D MMMM HH:mm', minute: 'ddd D MMMM',
          hour: 'ddd D MMMM', weekday: 'MMMM YYYY', day: 'YYYY年M月',
          week: 'YYYY年M月', month: 'YYYY 年', year: '',
        },
      },
    })
  } else {
    items.clear(); items.add(itemList)
    groups.clear(); groups.add(groupList)
    timeline.setWindow(start, end, { animation: false })
  }
}

onMounted(render)
onBeforeUnmount(() => { if (timeline) { timeline.destroy(); timeline = null } })
watch(() => props.milestones, render, { deep: true })
</script>

<template>
  <div class="timeline-wrap">
    <div v-if="!sorted.length" class="empty">暂无时间线节点 · 可在管理后台添加</div>
    <div v-show="sorted.length" ref="container" class="vis-host"></div>
  </div>
</template>

<style scoped>
.timeline-wrap {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 12px 12px;
  margin: 0 24px 16px;
}
.empty { color: var(--text-muted); font-size: 13px; padding: 12px 0; text-align: center; }
.vis-host { width: 100%; min-height: 160px; }
</style>

<style>
/* vis-timeline 全局样式覆写(scoped 选择不到 vis 注入的 DOM) */
.vis-timeline {
  border: none !important;
  font-family: inherit !important;
}
.vis-panel.vis-center,
.vis-panel.vis-left,
.vis-panel.vis-right,
.vis-panel.vis-top,
.vis-panel.vis-bottom {
  border-color: var(--border-subtle) !important;
}
.vis-time-axis .vis-grid.vis-minor { border-color: var(--border-subtle) !important; }
.vis-time-axis .vis-grid.vis-major { border-color: var(--border) !important; }
.vis-time-axis .vis-text {
  color: var(--text-dim) !important;
  font-variant-numeric: tabular-nums;
}
.vis-time-axis .vis-text.vis-major {
  font-weight: 700;
  color: var(--text) !important;
}

/* 左侧 group 标签栏 */
.vis-labelset .vis-label {
  color: var(--text-dim);
  font-size: 12px;
  font-weight: 600;
  border-color: var(--border-subtle) !important;
}

/* 里程碑 item:取消默认背景框,用形状 + 文字呈现 */
.vis-item.ms-item {
  background: transparent !important;
  border: none !important;
  color: var(--text);
}
.vis-item.ms-item .vis-item-content {
  padding: 0;
  text-align: center;
  line-height: 1.2;
}
.vis-item.ms-item .ms-shape {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 2px;
}
.vis-item.ms-item .ms-label {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vis-item.ms-item .ms-date {
  font-size: 10px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  margin-top: 1px;
}
/* 形状颜色按类型 */
.vis-item.ms-TR .ms-shape { color: var(--accent); }
.vis-item.ms-TR .ms-label { color: var(--accent); }
.vis-item.ms-SOP .ms-shape { color: var(--status-red); }
.vis-item.ms-SOP .ms-label { color: var(--status-red); }
.vis-item.ms-Block .ms-shape { color: var(--status-yellow); }
.vis-item.ms-Block .ms-label { color: var(--status-yellow); }
.vis-item.ms-Custom .ms-shape { color: var(--text-muted); }

/* 今天竖线 */
.vis-current-time {
  background-color: var(--accent) !important;
  width: 2px !important;
}
</style>
