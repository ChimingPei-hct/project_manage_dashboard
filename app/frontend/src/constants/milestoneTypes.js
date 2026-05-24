/* 时间线节点类型样式单一来源
 * 红线:TimelineBar / MilestoneEditor 必须从本文件 import,禁止在组件内拷贝
 */

export const TYPE_STYLE = {
  TR:     { shape: '△', color: 'var(--accent)',        label: 'TR',     order: 1 },
  SOP:    { shape: '◇', color: 'var(--status-red)',    label: 'SOP',    order: 2 },
  OTA:    { shape: '△', color: '#7c3aed',              label: 'OTA',    order: 3 },
  review: { shape: '☆', color: '#0891b2',              label: '评审',   order: 4 },
  goal:   { shape: '★', color: '#d97706',              label: '目标',   order: 5 },
  Block:  { shape: '■', color: 'var(--status-yellow)', label: 'Block',  order: 6 },
  other:  { shape: '●', color: 'var(--text-muted)',    label: '其他',   order: 9 },
}

export const FALLBACK_STYLE = { shape: '●', color: 'var(--text-muted)', label: '其他', order: 8 }

export function styleOf(type) {
  return TYPE_STYLE[type] || { ...FALLBACK_STYLE, label: type || '其他' }
}

/* 下拉选项,按 order 排序;不含 Custom(legacy 兼容由 styleOf 兜底) */
export const TYPE_OPTIONS = Object.entries(TYPE_STYLE)
  .map(([key, v]) => ({ key, ...v }))
  .sort((a, b) => a.order - b.order)
