<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client.js'
import { useDashboard } from '../composables/useDashboard.js'

const snapshots = ref([])
const { week, setWeek } = useDashboard()

async function loadList() {
  try {
    snapshots.value = await api.get('/api/snapshots') || []
  } catch (e) { /* ignore */ }
}
onMounted(loadList)
</script>

<template>
  <select
    class="week-switcher"
    :value="week || ''"
    v-tooltip="'切换查看周次,历史周为只读快照'"
    @change="e => setWeek(e.target.value || null)"
  >
    <option value="">当前(实时)</option>
    <option v-for="s in snapshots" :key="s.week" :value="s.week">{{ s.week }}</option>
  </select>
</template>

<style scoped>
.week-switcher { min-width: 140px; }
</style>
