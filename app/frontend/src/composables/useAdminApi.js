/**
 * 管理后台的 API 调用封装。集中处理错误 toast 与 SSE-triggered 自动刷新。
 */
import { api } from '../api/client.js'

export const adminApi = {
  // PDT
  updatePdt: (body) => api.put('/api/pdt', body),
  uploadPdtIcon: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.postForm('/api/pdt/icon', fd)
  },
  deletePdtIcon: () => api.del('/api/pdt/icon'),

  // LTCs
  createLtc: (body) => api.post('/api/ltcs', body),
  updateLtc: (id, body) => api.put(`/api/ltcs/${id}`, body),
  deleteLtc: (id) => api.del(`/api/ltcs/${id}`),

  // Modules
  listModules: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.scope) qs.set('scope', params.scope)
    if (params.ltc_id) qs.set('ltc_id', params.ltc_id)
    const q = qs.toString()
    return api.get(`/api/modules${q ? `?${q}` : ''}`)
  },
  createModule: (body) => api.post('/api/modules', body),
  updateModule: (id, body) => api.put(`/api/modules/${id}`, body),
  deleteModule: (id) => api.del(`/api/modules/${id}`),

  // Categories
  listCategories: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.scope) qs.set('scope', params.scope)
    if (params.ltc_id) qs.set('ltc_id', params.ltc_id)
    const q = qs.toString()
    return api.get(`/api/categories${q ? `?${q}` : ''}`)
  },
  createCategory: (body) => api.post('/api/categories', body),
  updateCategory: (id, body) => api.put(`/api/categories/${id}`, body),
  deleteCategory: (id) => api.del(`/api/categories/${id}`),
  initLtcFromTemplate: (ltcId) => api.post(`/api/ltc/${ltcId}/init-from-template`),

  // Admins
  getAdmins: () => api.get('/api/admins'),
  updateAdmins: (role, body) => api.put(`/api/admins/${role}`, body),

  // Snapshots
  listSnapshots: () => api.get('/api/snapshots'),
  freezeSnapshot: (week, force = false) => {
    const qs = new URLSearchParams()
    if (week) qs.set('week', week)
    if (force) qs.set('force', 'true')
    return api.post(`/api/snapshots/freeze?${qs.toString()}`)
  },

  // Auto-freeze config
  getAutoFreeze: () => api.get('/api/config/auto_freeze'),
  updateAutoFreeze: (body) => api.put('/api/config/auto_freeze', body),
}

export function newId() {
  return crypto?.randomUUID ? crypto.randomUUID().replace(/-/g, '') : Math.random().toString(36).slice(2)
}
