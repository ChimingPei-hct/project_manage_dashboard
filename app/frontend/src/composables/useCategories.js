import { ref } from 'vue'
import { api } from '../api/client.js'
import { sseBus } from './sseBus.js'

const categories = ref([])
const loading = ref(false)

async function reload() {
  loading.value = true
  try {
    categories.value = (await api.get('/api/categories')) || []
  } finally {
    loading.value = false
  }
}

let sseHooked = false
function ensureSSE() {
  if (sseHooked) return
  sseHooked = true
  sseBus.on('config:reload', (payload) => {
    if (!payload || payload.kind === 'categories') reload()
  })
}

/** 给 LTC 主页准备分组数据:返回 [{ category, modules }] 顺序按 category.order。
 *  - category=null 表示"未分类"虚拟组,容纳所有 category_id 为空的模块
 *  - 只取 scope=ltc & ltc_id 匹配的大类;模板池(scope=ltc_template)不直接展示,
 *    需通过「从模板初始化本 LTC」拷贝为副本后才进入 LTC 视图(详见 design/04 §5.5) */
function groupedForLtc(ltcId, modules) {
  const cats = (categories.value || []).filter(c => {
    if (c.scope === 'ltc' && c.ltc_id === ltcId) return true
    return false
  }).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0))

  const byCat = new Map()
  for (const c of cats) byCat.set(c.id, [])
  const orphan = []
  for (const m of modules) {
    const cid = m.category_id || null
    if (cid && byCat.has(cid)) byCat.get(cid).push(m)
    else orphan.push(m)
  }
  const out = cats.map(c => ({
    category: c,
    modules: byCat.get(c.id).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
  }))
  if (orphan.length) {
    out.push({
      category: null,
      modules: orphan.slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    })
  }
  return out
}

export function useCategories() {
  ensureSSE()
  return { categories, loading, reload, groupedForLtc }
}
