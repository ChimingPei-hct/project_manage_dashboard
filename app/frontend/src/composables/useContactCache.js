/**
 * 通讯录缓存(改自 oversea_projects/app/frontend/src/composables/useContactCache.js)。
 * PMD 后端端点为 /api/users/search,数据源为 user_registry.json(v1)。
 * localStorage 24h 二级缓存,失效后台静默刷新。
 */
import { computed, ref } from 'vue'

const _contacts = ref([])
const _loaded = ref(false)
const _loading = ref(false)
const _lastFetchedAt = ref(0)
const TTL_MS = 24 * 60 * 60 * 1000
const LS_KEY = 'pmd_contact_cache_v2'  // v2: 含飞书头像 avatar_url

let _inflight = null

try {
  const raw = localStorage.getItem(LS_KEY)
  if (raw) {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed.users) && parsed.users.length && typeof parsed.time === 'number') {
      _contacts.value = parsed.users
      _loaded.value = true
      _lastFetchedAt.value = parsed.time
    }
  }
} catch {}

async function _fetch() {
  try {
    _loading.value = true
    const res = await fetch('/api/users/search?q=&limit=2000', { credentials: 'include' })
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data)) {
        _contacts.value = data
        _loaded.value = true
        _lastFetchedAt.value = Date.now()
        try {
          localStorage.setItem(LS_KEY, JSON.stringify({ users: data, time: _lastFetchedAt.value }))
        } catch {}
      }
    }
  } catch {
    // keep stale on failure
  } finally {
    _loading.value = false
    _inflight = null
  }
}

const _nameByOpenId = computed(() => {
  const map = {}
  for (const u of _contacts.value || []) {
    if (u?.open_id) map[u.open_id] = u.name || ''
  }
  return map
})

export function displayName(openId) {
  if (!openId) return ''
  return _nameByOpenId.value[openId] || openId
}

export function useContactCache() {
  function ensureContacts() {
    if (_loaded.value && Date.now() - _lastFetchedAt.value < TTL_MS) return Promise.resolve()
    if (_loaded.value && !_inflight) {
      _inflight = _fetch()
      return Promise.resolve()
    }
    if (_inflight) return _inflight
    _inflight = _fetch()
    return _inflight
  }
  function refreshContacts() {
    _inflight = _fetch()
    return _inflight
  }
  return { contacts: _contacts, loading: _loading, loaded: _loaded, ensureContacts, refreshContacts, displayName }
}
