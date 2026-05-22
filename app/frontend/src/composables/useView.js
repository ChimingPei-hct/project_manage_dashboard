import { ref, onMounted, onBeforeUnmount } from 'vue'

function parseView() {
  const sp = new URLSearchParams(window.location.search)
  return {
    view: sp.get('view') || 'pdt',
    id: sp.get('id') || '',
    ltc: sp.get('ltc') || '',
  }
}

const current = ref(parseView())

function pushView(next) {
  const sp = new URLSearchParams()
  if (next.view) sp.set('view', next.view)
  if (next.id) sp.set('id', next.id)
  if (next.ltc) sp.set('ltc', next.ltc)
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
