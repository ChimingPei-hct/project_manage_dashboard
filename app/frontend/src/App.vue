<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuth } from './composables/useAuth.js'
import { useDashboard } from './composables/useDashboard.js'
import { useView } from './composables/useView.js'
import { adminApi } from './composables/useAdminApi.js'
import { api } from './api/client.js'
import PdtOverview from './components/PdtOverview.vue'
import LtcProgress from './components/LtcProgress.vue'
import RiskDetail from './components/RiskDetail.vue'
import AdminPanel from './components/AdminPanel.vue'
import WeekSwitcher from './components/WeekSwitcher.vue'

const { me, refresh: refreshAuth } = useAuth()
const { ltcs, modules, isReadonly, refresh, startSSE } = useDashboard()
const { current, pushView } = useView()

const adminsMap = ref({ super: [], pdt: [], ltc: {} })
async function reloadAdmins() {
  try { adminsMap.value = await api.get('/api/admins') } catch (_) {}
}

const isAdminish = computed(() => {
  if (!me.value) return false
  if (me.value.is_super || me.value.is_pdt_admin) return true
  // LTC Admin
  const myOid = me.value.open_id
  return Object.values(adminsMap.value.ltc || {}).some(arr => arr.includes(myOid))
})

const showSeedBtn = computed(() => {
  if (!me.value?.is_super) return false
  return (ltcs.value?.length || 0) === 0 && (modules.value?.length || 0) === 0
})

const seeding = ref(false)
async function seedDemo() {
  if (!confirm('将自动创建一份示例 PDT + LTC + 模块作为 onboarding 数据。仅空实例可用。继续?')) return
  seeding.value = true
  try {
    await adminApi.seedDemo()
    await refresh()
  } catch (e) {
    alert(`失败:${e.message}`)
  } finally { seeding.value = false }
}

const viewComp = computed(() => {
  switch (current.value.view) {
    case 'ltc': return LtcProgress
    case 'risks': return RiskDetail
    case 'admin': return AdminPanel
    case 'pdt':
    default: return PdtOverview
  }
})

const navItems = computed(() => {
  const base = [
    { view: 'pdt', label: 'PDT 总览', tip: '切换到产品线总览页' },
    { view: 'ltc', label: 'LTC 进展', tip: '查看子项目研发进展矩阵' },
    { view: 'risks', label: '风险详情', tip: '只看本周非绿项与风险说明' },
  ]
  if (isAdminish.value) base.push({ view: 'admin', label: '管理', tip: '管理 PDT / LTC / 模块 / 人员' })
  return base
})

function nav(view) { pushView({ view }) }

onMounted(async () => {
  await refreshAuth()
  await refresh()
  await reloadAdmins()
  startSSE()
})
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand" v-tooltip="'PMD · 产品线项目看板'">📊 PMD</div>
      <nav>
        <button
          v-for="n in navItems"
          :key="n.view"
          :class="{ primary: current.view === n.view }"
          v-tooltip="n.tip"
          @click="nav(n.view)"
        >{{ n.label }}</button>
      </nav>
      <div class="right">
        <button
          v-if="showSeedBtn"
          class="primary"
          :disabled="seeding"
          v-tooltip="'当前实例为空,一键填充一份示例 PDT/LTC/模块,便于演示与上手'"
          @click="seedDemo"
        >{{ seeding ? '创建中…' : '+ 示例数据' }}</button>
        <WeekSwitcher />
        <span class="user" v-tooltip="me?.dev_login ? 'Dev 后门身份(本地调试)' : '当前登录用户'">
          {{ me?.name || me?.open_id || '未登录' }}
          <em v-if="me?.is_super">·super</em>
          <em v-else-if="me?.is_pdt_admin">·pdt-admin</em>
        </span>
      </div>
    </header>
    <div v-if="isReadonly" class="banner-readonly">
      历史周(只读)· 所有编辑入口已禁用
    </div>
    <main>
      <component :is="viewComp" />
    </main>
  </div>
</template>

<style scoped>
.layout { min-height: 100vh; display: flex; flex-direction: column; }
.topbar {
  display: flex; align-items: center; gap: 16px;
  padding: 8px 24px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}
.brand { font-weight: 600; font-size: 16px; }
nav { display: flex; gap: 6px; flex: 1; }
.right { display: flex; gap: 12px; align-items: center; }
.user { font-size: 13px; color: var(--text-muted); }
.user em { font-style: normal; color: var(--accent); margin-left: 4px; }
main { flex: 1; }
</style>
