<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api/client.js'
import { useView } from '../composables/useView.js'
import { sseBus } from '../composables/sseBus.js'

const snapshots = ref([])
const { current, pushView } = useView()

async function loadList() {
  try {
    snapshots.value = await api.get('/api/snapshots') || []
  } catch (_) { /* ignore */ }
}

function onChange(e) {
  const w = e.target.value || ''
  // 单一事实来源 = URL;App.vue 的 watcher 会同步到 useDashboard
  pushView({ view: current.value.view, id: current.value.id, week: w })
}

let off = null
onMounted(() => {
  loadList()
  // 新快照创建时(手动冻结 / 周五定时)自动刷新下拉
  off = sseBus.on('snapshot:created', loadList)
})
onBeforeUnmount(() => { off && off() })
</script>

<template>
  <select
    class="week-switcher"
    :value="current.week || ''"
    v-tooltip="'切换查看周次,历史周为只读快照'"
    @change="onChange"
  >
    <option value="">当前(实时)</option>
    <option v-for="s in snapshots" :key="s.week" :value="s.week">{{ s.week }}</option>
  </select>
</template>

<style scoped>
.week-switcher { min-width: 140px; }
</style>
