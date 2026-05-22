/**
 * 单例 SSE 总线 + 指数退避重连。
 * 参考:oversea_projects/app/frontend/src/composables/sseBus.js
 */

const subscribers = new Map() // event → Set<callback>
let es = null
let backoff = 1000
let stableSince = 0
let timer = null

function dispatch(event, data) {
  const set = subscribers.get(event)
  if (!set) return
  for (const cb of set) {
    try { cb(data) } catch (e) { console.error('[sse handler]', e) }
  }
}

function connect() {
  if (es) return
  try {
    es = new EventSource('/api/events', { withCredentials: true })
  } catch (e) {
    scheduleReconnect()
    return
  }
  es.addEventListener('open', () => {
    stableSince = Date.now()
  })
  // 后端用 named events;监听通用消息
  ;['hello', 'status:reload', 'config:reload', 'snapshot:created'].forEach((name) => {
    es.addEventListener(name, (ev) => {
      let data = {}
      try { data = JSON.parse(ev.data || '{}') } catch (_) {}
      dispatch(name, data)
    })
  })
  es.addEventListener('error', () => {
    if (es) {
      try { es.close() } catch (_) {}
      es = null
    }
    if (Date.now() - stableSince > 10000) backoff = 1000
    scheduleReconnect()
  })
}

function scheduleReconnect() {
  if (timer) return
  timer = setTimeout(() => {
    timer = null
    backoff = Math.min(backoff * 2, 60000)
    connect()
  }, backoff)
}

export const sseBus = {
  start() { connect() },
  on(event, cb) {
    if (!subscribers.has(event)) subscribers.set(event, new Set())
    subscribers.get(event).add(cb)
    return () => subscribers.get(event)?.delete(cb)
  },
}
