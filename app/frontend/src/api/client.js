/**
 * 统一 API 客户端。
 * 约束:design/12 §8。
 */

const DEFAULT_TIMEOUT = 10000

async function request(method, url, { body, signal, timeout = DEFAULT_TIMEOUT } = {}) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeout)
  const init = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    signal: signal || ctrl.signal,
  }
  if (body !== undefined) init.body = JSON.stringify(body)
  try {
    const res = await fetch(url, init)
    let payload = null
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      payload = await res.json().catch(() => null)
    }
    if (!res.ok) {
      const detail = payload?.detail || `${res.status} ${res.statusText}`
      const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      err.status = res.status
      err.payload = payload
      throw err
    }
    return payload
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  get: (url, opts) => request('GET', url, opts),
  post: (url, body, opts) => request('POST', url, { ...(opts || {}), body }),
  put: (url, body, opts) => request('PUT', url, { ...(opts || {}), body }),
  del: (url, opts) => request('DELETE', url, opts),
}
