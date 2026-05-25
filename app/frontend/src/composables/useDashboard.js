import { ref, computed } from 'vue'
import { api } from '../api/client.js'
import { sseBus } from './sseBus.js'

const pdt = ref(null)
const ltcs = ref([])
const modules = ref([])
const status = ref({})
const week = ref(null) // null = 当前;'2026-W21' = 历史只读
const loading = ref(false)
const error = ref(null)

async function loadCurrent() {
  const [p, l, m, s] = await Promise.all([
    api.get('/api/pdt'),
    api.get('/api/ltcs'),
    api.get('/api/modules'),
    api.get('/api/status'),
  ])
  pdt.value = p
  ltcs.value = l || []
  modules.value = m || []
  status.value = s || {}
}

async function loadSnapshot(w) {
  const snap = await api.get(`/api/snapshots/${encodeURIComponent(w)}`)
  pdt.value = snap.pdt
  ltcs.value = snap.ltcs || []
  modules.value = snap.modules || []
  status.value = snap.module_status || {}
}

async function refresh() {
  loading.value = true
  error.value = null
  try {
    if (week.value) await loadSnapshot(week.value)
    else await loadCurrent()
  } catch (e) {
    error.value = e
  } finally {
    loading.value = false
  }
}

function setWeek(w) {
  week.value = w || null
  refresh()
}

const isReadonly = computed(() => !!week.value)

const modulesByScope = computed(() => {
  const groups = { pdt: [], ltc_template: [], ltc: {} }
  for (const m of modules.value) {
    if (m.scope === 'pdt') groups.pdt.push(m)
    else if (m.scope === 'ltc_template') groups.ltc_template.push(m)
    else if (m.scope === 'ltc') {
      if (!groups.ltc[m.ltc_id]) groups.ltc[m.ltc_id] = []
      groups.ltc[m.ltc_id].push(m)
    }
  }
  return groups
})

/** 给定 LTC 在主页面展示的模块:仅返回该 LTC 自有副本(scope=ltc & ltc_id=ltcId)。
 *  模板池(scope=ltc_template)不直接展示,需通过「新建 LTC → 从模板池初始化」
 *  深拷贝为本 LTC 副本(详见 design/04 §5.5)。历史 LTC 若未初始化,主页会空,
 *  需手动调 POST /api/ltc/{id}/init-from-template 补齐。 */
function ltcVisibleModules(ltcId) {
  if (!ltcId) return []
  const own = modulesByScope.value.ltc[ltcId] || []
  return own.slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
}

/** 给定模块在某 LTC 上下文中的 status key:模板模块需复合键,其他用 module.id。 */
function statusKeyOf(module, ltcId) {
  if (!module) return ''
  if (module.scope === 'ltc_template') {
    return ltcId ? `${ltcId}::${module.id}` : module.id
  }
  return module.id
}

let sseStarted = false
function startSSE() {
  if (sseStarted) return
  sseStarted = true
  sseBus.start()
  sseBus.on('status:reload', () => { if (!week.value) refresh() })
  sseBus.on('config:reload', () => { if (!week.value) refresh() })
}

export function useDashboard() {
  return {
    pdt, ltcs, modules, status, week, loading, error,
    isReadonly, modulesByScope,
    ltcVisibleModules, statusKeyOf,
    refresh, setWeek, startSSE,
  }
}
