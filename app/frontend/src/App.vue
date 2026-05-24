<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuth } from './composables/useAuth.js'
import { useDashboard } from './composables/useDashboard.js'
import { useView } from './composables/useView.js'
import { useAdmins } from './composables/useAdmins.js'
import { handleCallbackIfPresent, startLogin } from './composables/useFeishuLogin.js'
import PdtOverview from './components/PdtOverview.vue'
import LtcMain from './components/LtcMain.vue'
import PdtConfigDrawer from './components/PdtConfigDrawer.vue'
import MilestonesDrawer from './components/admin/MilestonesDrawer.vue'
import { setFavicon, iconUrlOf } from './utils/favicon.js'

const { me, refresh: refreshAuth } = useAuth()
const { pdt, week, isReadonly, refresh, setWeek, startSSE } = useDashboard()
const { current, pushView } = useView()

// URL ?week=YYYY-Www ↔ useDashboard.week 双向同步:URL 是单一事实来源
watch(() => current.value.week, (w) => {
  const cur = week.value || ''
  if (w !== cur) setWeek(w || null)
}, { immediate: false })

const { admins: adminsMap, reload: reloadAdmins } = useAdmins()

const isAdminish = computed(() => {
  if (!me.value) return false
  if (me.value.is_super || me.value.is_pdt_admin) return true
  // LTC Admin
  const myOid = me.value.open_id
  return Object.values(adminsMap.value.ltc || {}).some(arr => arr.includes(myOid))
})

const viewComp = computed(() => {
  switch (current.value.view) {
    case 'ltc': return LtcMain
    case 'risks': return LtcMain  // 同一组件,内部按 current.view 决定是否滚到风险锚点
    case 'milestones': return MilestonesDrawer
    case 'pdt':
    default: return PdtOverview
  }
})

const pdtConfigOpen = ref(false)

const pdtIconUrl = computed(() => iconUrlOf(pdt.value))

watch([pdtIconUrl, () => pdt.value?.name], ([url, name]) => {
  setFavicon(url)
  document.title = name ? `${name} · PMD 项目看板` : 'PMD · 产品线项目看板'
}, { immediate: true })

const navItems = computed(() => [
  { view: 'pdt', label: 'PDT 总览', tip: '切换到产品线总览页' },
  { view: 'ltc', label: 'LTC 进展', tip: '查看子项目研发进展矩阵' },
])

function nav(view) { pushView({ view, week: current.value.week }) }

const loginError = ref('')
const loginPending = ref(false)

const needLogin = computed(() => {
  // 已加载 me 且没有 open_id,后端有飞书凭证 → 显示登录页
  if (!me.value) return false
  if (me.value.open_id) return false
  return !!me.value.feishu_configured
})

async function clickLogin() {
  loginPending.value = true
  loginError.value = ''
  try { await startLogin() } catch (e) {
    loginError.value = e.message || '飞书登录跳转失败'
    loginPending.value = false
  }
}

onMounted(async () => {
  // 先处理 /feishu/callback?code=... 回调(若不在此路径则 no-op)
  try { await handleCallbackIfPresent() } catch (e) { loginError.value = e.message || '登录失败' }
  await refreshAuth()
  if (me.value?.open_id) {
    // 若 URL 已带 ?week=,先同步到 useDashboard 再触发首次加载,避免拉两次
    if (current.value.week && !week.value) {
      setWeek(current.value.week)
    } else {
      await refresh()
    }
    await reloadAdmins()
    startSSE()
  }
})
</script>

<template>
  <div v-if="needLogin" class="login-screen">
    <div class="login-card">
      <h1>📊 PMD 项目看板</h1>
      <p class="muted">使用飞书账号登录</p>
      <button class="primary" :disabled="loginPending" v-tooltip="'跳转到飞书授权页'" @click="clickLogin">
        {{ loginPending ? '跳转中…' : '飞书登录' }}
      </button>
      <p v-if="loginError" class="err">{{ loginError }}</p>
    </div>
  </div>
  <div v-else class="layout">
    <header class="topbar">
      <div class="brand" v-tooltip="(pdt?.name ? pdt.name + ' · ' : '') + '产品线项目看板'">
        <img v-if="pdtIconUrl" :src="pdtIconUrl" class="brand-logo" alt="" />
        <span v-else class="brand-emoji">📊</span>
        <span class="brand-text">{{ pdt?.name || 'PMD' }}</span>
      </div>
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
        <span class="user" v-tooltip="me?.dev_login ? 'Dev 后门身份(本地调试)' : '当前登录用户'">
          {{ me?.name || me?.open_id || '未登录' }}
          <em v-if="me?.is_super">·super</em>
          <em v-else-if="me?.is_pdt_admin">·pdt-admin</em>
        </span>
        <button
          v-if="isAdminish"
          class="icon-btn"
          :class="{ active: pdtConfigOpen }"
          v-tooltip="'PDT 配置:名称/图标 + LTC 模板池'"
          @click="pdtConfigOpen = true"
          aria-label="PDT 配置"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </button>
      </div>
    </header>
    <div v-if="isReadonly" class="banner-readonly">
      历史周(只读)· 所有编辑入口已禁用
    </div>
    <main>
      <component :is="viewComp" />
    </main>
    <PdtConfigDrawer :open="pdtConfigOpen" @close="pdtConfigOpen = false" />
  </div>
</template>

<style scoped>
.layout { min-height: 100vh; display: flex; flex-direction: column; }
.topbar {
  display: flex; align-items: center; gap: 18px;
  padding: 10px 24px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(8px);
}
.brand { display: inline-flex; align-items: center; gap: 8px; font-weight: 700; font-size: 16px; letter-spacing: -0.2px; }
.brand-emoji { font-size: 16px; }
.brand-logo { width: 24px; height: 24px; border-radius: 6px; display: block; object-fit: contain; }
.brand-text {
  background: linear-gradient(135deg, var(--accent), #0ea5e9);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
nav { display: flex; gap: 4px; flex: 1; }
nav button { font-weight: 500; }
.right { display: flex; gap: 12px; align-items: center; }
.user {
  font-size: 13px;
  color: var(--text-muted);
  padding: 4px 10px;
  border-radius: var(--radius);
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
}
.user em { font-style: normal; color: var(--accent); margin-left: 4px; font-weight: 600; }
.icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  padding: 0;
  border-radius: 6px;
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  cursor: pointer;
  transition: color 120ms, background 120ms, border-color 120ms;
}
.icon-btn:hover { color: var(--text); background: var(--panel); }
.icon-btn.active {
  color: var(--accent);
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 8%, var(--panel));
}
.icon-btn svg { display: block; }
main { flex: 1; }

.login-screen {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg, #f5f7fa);
}
.login-card {
  background: var(--panel, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 6px;
  padding: 36px 40px;
  width: 320px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.login-card h1 { font-size: 20px; margin: 0 0 8px; }
.login-card .muted { color: var(--text-muted, #6b7280); font-size: 13px; margin: 0 0 20px; }
.login-card button { width: 100%; padding: 10px; border-radius: 6px; }
.login-card .err { color: var(--status-red, #f5222d); font-size: 12px; margin-top: 12px; }
</style>
