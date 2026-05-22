/* 状态数据归一化辅助:兼容新旧 schema。
   - 新:status.kpi_items[] / status.risks[] / status.sub_items_risk{}
   - 旧:status.kpi_values{} / status.risk_note (string)
*/

export function kpiItemsOf(statusEntry, kpiFields) {
  if (!statusEntry) return []
  if (Array.isArray(statusEntry.kpi_items) && statusEntry.kpi_items.length) {
    return statusEntry.kpi_items.map(k => ({
      label: k.label || '',
      value: k.value || '',
      target: k.target || '',
    }))
  }
  const vals = statusEntry.kpi_values || {}
  if (!kpiFields?.length) {
    return Object.entries(vals).map(([k, v]) => ({ label: k, value: String(v ?? ''), target: '' }))
  }
  return kpiFields.map(f => ({
    label: f.label || f.key,
    value: String(vals[f.key] ?? ''),
    target: f.target || '',
  })).filter(k => k.value || k.target)
}

export function risksOf(statusEntry) {
  if (!statusEntry) return []
  if (Array.isArray(statusEntry.risks) && statusEntry.risks.length) {
    return statusEntry.risks.map(r => ({
      severity: r.severity === 'yellow' ? 'yellow' : 'red',
      text: r.text || '',
    })).filter(r => r.text.trim())
  }
  const note = (statusEntry.risk_note || '').trim()
  if (!note) return []
  return [{ severity: 'red', text: note }]
}

export function subRiskOf(statusEntry, subId) {
  if (!statusEntry || !subId) return ''
  return (statusEntry.sub_items_risk?.[subId] || '').trim()
}

export function aggregateStatusTone(statusEntry) {
  /* 返回 { red, yellow, green, gray } 计数,用于 summary chip 和卡片三圆点 */
  const out = { red: 0, yellow: 0, green: 0, gray: 0 }
  if (!statusEntry) { out.gray = 1; return out }
  const mc = statusEntry.module_color || 'gray'
  if (out[mc] !== undefined) out[mc] += 1
  const subs = statusEntry.sub_items_color || {}
  for (const c of Object.values(subs)) {
    if (out[c] !== undefined) out[c] += 1
  }
  return out
}

export function formatDateCN(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getMonth() + 1}.${String(d.getDate()).padStart(2, '0')}`
}

export function currentWeekRange(date = new Date()) {
  /* 返回 ISO 周一 ~ 周日的 M.DD ~ M.DD 字符串 */
  const d = new Date(date)
  const day = d.getDay() || 7  // 周日=0 → 7
  const mon = new Date(d); mon.setDate(d.getDate() - (day - 1))
  const sun = new Date(mon); sun.setDate(mon.getDate() + 6)
  return `${mon.getMonth() + 1}.${String(mon.getDate()).padStart(2, '0')}~${sun.getMonth() + 1}.${String(sun.getDate()).padStart(2, '0')}`
}
