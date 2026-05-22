import { ref } from 'vue'
import { api } from '../api/client.js'

const admins = ref({ super: [], pdt: [], ltc: {} })

async function reload() {
  try { admins.value = await api.get('/api/admins') } catch (_) {}
}

export function useAdmins() {
  return { admins, reload }
}
