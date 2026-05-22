<script setup>
import { computed, onMounted } from 'vue'
import { useAuth } from './composables/useAuth.js'
import { useDashboard } from './composables/useDashboard.js'
import { useView } from './composables/useView.js'
import PdtOverview from './components/PdtOverview.vue'
import LtcProgress from './components/LtcProgress.vue'
import RiskDetail from './components/RiskDetail.vue'
import AdminPanel from './components/AdminPanel.vue'
import WeekSwitcher from './components/WeekSwitcher.vue'

const { me, refresh: refreshAuth } = useAuth()
const { pdt, isReadonly, refresh, startSSE } = useDashboard()
const { current, pushView } = useView()

const viewComp = computed(() => {
  switch (current.value.view) {
    case 'ltc': return LtcProgress
    case 'risks': return RiskDetail
    case 'admin': return AdminPanel
    case 'pdt':
    default: return PdtOverview
  }
})

const navItems = [
  { view: 'pdt', label: 'PDT 总览', tip: '切换到产品线总览页' },
  { view: 'ltc', label: 'LTC 进展', tip: '查看子项目研发进展矩阵' },
  { view: 'risks', label: '风险详情', tip: '只看本周非绿项与风险说明' },
  { view: 'admin', label: '管理', tip: '管理 PDT / LTC / 模块 / 人员' },
]

function nav(view) { pushView({ view }) }

onMounted(async () => {
  await refreshAuth()
  await refresh()
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
