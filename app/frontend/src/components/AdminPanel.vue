<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth.js'
import PdtForm from './admin/PdtForm.vue'
import LtcList from './admin/LtcList.vue'
import ModuleEditor from './admin/ModuleEditor.vue'
import AdminUsers from './admin/AdminUsers.vue'
import SnapshotPanel from './admin/SnapshotPanel.vue'

const { me } = useAuth()

const TABS = [
  { key: 'pdt', label: 'PDT 信息', comp: PdtForm, needs: 'pdt_admin' },
  { key: 'ltcs', label: 'LTC 列表', comp: LtcList, needs: 'pdt_admin' },
  { key: 'modules', label: '模块管理', comp: ModuleEditor, needs: 'ltc_or_above' },
  { key: 'admins', label: '人员管理', comp: AdminUsers, needs: 'pdt_admin' },
  { key: 'snapshots', label: '快照管理', comp: SnapshotPanel, needs: 'pdt_admin' },
]

const tabKey = ref(new URLSearchParams(window.location.search).get('tab') || 'pdt')
const currentTab = computed(() => TABS.find(t => t.key === tabKey.value) || TABS[0])
const currentComp = computed(() => currentTab.value.comp)

function setTab(key) {
  tabKey.value = key
  const url = new URL(window.location)
  url.searchParams.set('tab', key)
  url.searchParams.set('view', 'admin')
  window.history.replaceState({}, '', url)
}

function canSee(needs) {
  if (!me.value) return false
  if (me.value.is_super || me.value.is_pdt_admin) return true
  if (needs === 'ltc_or_above') {
    // LTC Admin 也能进模块管理 tab(但只能改自己 LTC)
    return true
  }
  return false
}
</script>

<template>
  <div class="admin">
    <h1>管理后台</h1>
    <div class="tabs">
      <button
        v-for="t in TABS"
        :key="t.key"
        :class="{ primary: tabKey === t.key }"
        :disabled="!canSee(t.needs)"
        v-tooltip="canSee(t.needs) ? `切换到「${t.label}」` : '当前角色无权访问此 tab'"
        @click="canSee(t.needs) && setTab(t.key)"
      >{{ t.label }}</button>
    </div>
    <div class="panel">
      <component :is="currentComp" />
    </div>
  </div>
</template>

<style scoped>
.admin { padding: 16px 24px; }
h1 { margin: 0 0 12px; font-size: 20px; }
.tabs { display: flex; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; min-height: 320px; }
</style>
