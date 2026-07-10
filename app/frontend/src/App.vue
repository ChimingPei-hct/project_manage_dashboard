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
  { view: 'pdt', label: 'PDT 总览', icon: '📊', tip: '切换到产品线总览页' },
  { view: 'ltc', label: 'LTC 进展', icon: '🚀', tip: '查看子项目研发进展矩阵' },
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
      <p v-if="loginError" class="err" role="alert">{{ loginError }}</p>
    </div>
  </div>
  <div v-else class="layout">
    <h1 class="sr-only">{{ pdt?.name || 'PMD' }} · 项目看板</h1>
    <a href="#main-content" class="skip-link">跳到主内容</a>
    <header class="topbar">
      <button
        type="button"
        class="brand"
        v-tooltip="(pdt?.name ? pdt.name + ' · ' : '') + '返回 PDT 总览'"
        @click="nav('pdt')"
      >
        <img v-if="pdtIconUrl" :src="pdtIconUrl" class="brand-logo" alt="" />
        <span v-else class="brand-emoji" aria-hidden="true">📊</span>
        <span class="brand-text">{{ pdt?.name || 'PMD' }}</span>
      </button>
      <nav>
        <button
          v-for="n in navItems"
          :key="n.view"
          :class="['nav-btn', { active: current.view === n.view }]"
          v-tooltip="n.tip"
          @click="nav(n.view)"
        ><span class="nav-icon" aria-hidden="true">{{ n.icon }}</span>{{ n.label }}</button>
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
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </button>
      </div>
    </header>
    <div v-if="isReadonly" class="banner-readonly" role="alert">
      历史周(只读)· 所有编辑入口已禁用
    </div>
    <main id="main-content">
      <component :is="viewComp" />
    </main>
    <PdtConfigDrawer :open="pdtConfigOpen" @close="pdtConfigOpen = false" />
  </div>
</template>

<style scoped>
.layout { min-height: 100vh; display: flex; flex-direction: column; }

/* ═══ Deep indigo header ═══ */
.topbar {
  display: flex; align-items: center; gap: 24px;
  padding: 0 28px;
  height: 56px;
  background: var(--gradient-header);
  box-shadow: var(--shadow-topbar);
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar::after { display: none; }

/* Brand */
.brand {
  display: inline-flex; align-items: center; gap: 10px;
  font-weight: 700; font-size: 16px; letter-spacing: 0.02em;
  background: transparent; border: none; padding: 6px 12px;
  border-radius: var(--radius); cursor: pointer;
  font-family: var(--font-serif); color: var(--header-text);
  transition: background var(--transition);
  flex-shrink: 0;
}
.brand:hover { background: var(--header-hover); }
.brand-emoji { font-size: 20px; filter: brightness(1.2); }
.brand-logo { width: 28px; height: 28px; border-radius: 6px; display: block; object-fit: contain; }
.brand-text {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe, #a5b4fc);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}
.brand:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--header-bg), 0 0 0 4px rgba(165, 180, 252, 0.5);
}

/* Nav */
nav { display: flex; gap: 4px; flex: 1; margin-left: 4px; }
.nav-btn {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--font-sans);
  font-size: 13.5px; font-weight: 500;
  letter-spacing: 0.02em;
  padding: 8px 16px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--header-text-muted);
  border-radius: var(--radius);
  cursor: pointer;
  transition:
    color var(--transition),
    background var(--transition),
    border-color var(--transition);
}
.nav-btn .nav-icon {
  font-size: 15px; line-height: 1; opacity: 0.7;
  transition: opacity var(--transition), transform var(--transition);
}
.nav-btn:hover {
  color: var(--header-text);
  background: var(--header-hover);
}
.nav-btn:hover .nav-icon { opacity: 1; transform: scale(1.05); }
.nav-btn.active {
  color: #fff;
  background: var(--header-active);
  border-color: var(--header-border);
  font-weight: 600;
}
.nav-btn.active .nav-icon { opacity: 1; }
.nav-btn:focus-visible { outline: none; box-shadow: 0 0 0 2px rgba(165, 180, 252, 0.5); }

/* Right section */
.right { display: flex; gap: 10px; align-items: center; flex-shrink: 0; }
.user {
  font-family: var(--font-sans);
  font-size: 12.5px;
  font-weight: 500;
  color: var(--header-text);
  padding: 5px 12px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--header-border);
  letter-spacing: 0.02em;
  transition: background var(--transition), border-color var(--transition);
}
.user:hover { background: var(--header-hover); border-color: rgba(255,255,255,0.12); }
.user em {
  font-style: normal;
  color: #a5b4fc;
  margin-left: 6px;
  font-weight: 700;
  font-size: 10.5px;
  letter-spacing: 0.06em;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: rgba(165, 180, 252, 0.15);
}
.icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px;
  padding: 0;
  border-radius: var(--radius);
  background: transparent;
  border: 1px solid var(--header-border);
  color: var(--header-text-muted);
  cursor: pointer;
  transition:
    color var(--transition),
    background var(--transition),
    border-color var(--transition),
    transform 100ms ease,
    box-shadow var(--transition);
}
.icon-btn:hover {
  color: var(--header-text);
  background: var(--header-hover);
  border-color: rgba(255,255,255,0.14);
  transform: translateY(-1px);
}
.icon-btn.active {
  color: #c7d2fe;
  border-color: rgba(199, 210, 254, 0.3);
  background: rgba(199, 210, 254, 0.12);
}
.icon-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(165, 180, 252, 0.5);
  border-color: rgba(165, 180, 252, 0.5);
}
.icon-btn svg { display: block; width: 17px; height: 17px; }

main { flex: 1; background: var(--bg); }

/* Login screen */
.login-screen {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg);
}
.login-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px 44px;
  width: 340px;
  text-align: center;
  box-shadow: var(--shadow-lg);
}
.login-card h1 { font-size: 22px; margin: 0 0 8px; font-family: var(--font-serif); }
.login-card .muted { color: var(--text-muted); font-size: 13px; margin: 0 0 24px; }
.login-card button { width: 100%; padding: 11px; border-radius: var(--radius); font-size: 14px; }
.login-card .err { color: var(--status-red); font-size: 12px; margin-top: 12px; }

@media (prefers-reduced-motion: reduce) {
  .icon-btn:hover { transform: none; }
  .nav-btn:hover .nav-icon { transform: none; }
  .nav-btn.active .nav-icon { transform: none; }
}
</style>
