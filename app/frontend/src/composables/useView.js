import { ref } from 'vue'

const WEEK_RE = /^\d{4}-W\d{2}$/
const VIEW_ALIAS = { risk: 'risks' }

function parseView() {
  const sp = new URLSearchParams(window.location.search)
  const wk = sp.get('week') || ''
  const rawView = sp.get('view') || 'pdt'
  return {
    view: VIEW_ALIAS[rawView] || rawView,
    id: sp.get('id') || sp.get('ltc') || '',
    week: WEEK_RE.test(wk) ? wk : '',
  }
}

const current = ref(parseView())

function pushView(next) {
  const sp = new URLSearchParams()
  if (next.view) sp.set('view', next.view)
  if (next.id) sp.set('id', next.id)
  if (next.week && WEEK_RE.test(next.week)) sp.set('week', next.week)
  const url = `${window.location.pathname}?${sp.toString()}`
  window.history.pushState({}, '', url)
  current.value = parseView()
}

window.addEventListener('popstate', () => {
  current.value = parseView()
})

export function useView() {
  return { current, pushView }
}
