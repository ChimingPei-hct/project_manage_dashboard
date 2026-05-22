import { ref } from 'vue'
import { api } from '../api/client.js'

const me = ref(null)
const loading = ref(false)
const error = ref(null)

async function refresh() {
  loading.value = true
  error.value = null
  try {
    me.value = await api.get('/api/auth/me')
  } catch (e) {
    error.value = e
    me.value = null
  } finally {
    loading.value = false
  }
}

export function useAuth() {
  return { me, loading, error, refresh }
}
