<script setup>
/* PDT 总览卡片管理:scope=pdt 的 modules 一一对应一个卡片 */
import { ref, computed } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'

const emit = defineEmits(['pick-module'])

const { modules, refresh } = useDashboard()
const cards = computed(() =>
  (modules.value || [])
    .filter(m => m.scope === 'pdt')
    .slice()
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
)

const newDraft = ref({ group: '', name: '' })
const adding = ref(false)
const errMsg = ref('')

async function add() {
  if (!newDraft.value.name.trim() || !newDraft.value.group.trim()) return
  adding.value = true
  errMsg.value = ''
  try {
    const created = await adminApi.createModule({
      id: newId(),
      scope: 'pdt',
      ltc_id: null,
      group: newDraft.value.group.trim(),
      name: newDraft.value.name.trim(),
      kpi_fields: [],
      sub_items: [],
    })
    newDraft.value = { group: '', name: '' }
    await refresh()
    emit('pick-module', created.id)
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '创建失败' }
  finally { adding.value = false }
}

async function move(card, dir) {
  const idx = cards.value.findIndex(x => x.id === card.id)
  const j = idx + dir
  if (j < 0 || j >= cards.value.length) return
  const a = cards.value[idx], b = cards.value[j]
  await Promise.all([
    adminApi.updateModule(a.id, { order: b.order ?? j + 1 }),
    adminApi.updateModule(b.id, { order: a.order ?? idx + 1 }),
  ])
  await refresh()
}

const PRESET_GROUPS = ['项目', '市场/产品', '质量', '产品指标', '研发-感知包', '研发-全栈', '测试', '服务(关键战役交付)']
</script>

<template>
  <div class="oc-drawer">
    <header class="dh">
      <div>
        <div class="crumb">PDT 配置 / 总览卡片</div>
        <h2>PDT 总览卡片</h2>
        <p class="sub">每张卡对应一个 scope=pdt 的模块,在「PDT 总览」视图中以网格展示</p>
      </div>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>新增卡片</h3>
      <div class="add-row">
        <select v-model="newDraft.group" v-tooltip="'选择预置分组或自定义'">
          <option value="">— 选择分组 —</option>
          <option v-for="g in PRESET_GROUPS" :key="g" :value="g">{{ g }}</option>
        </select>
        <input v-model="newDraft.group" placeholder="或自定义分组(如:项目)" />
        <input v-model="newDraft.name" placeholder="卡片名称(如:质量总览)" @keyup.enter="add" />
        <button
          class="primary"
          :disabled="adding || !newDraft.name.trim() || !newDraft.group.trim()"
          v-tooltip="'创建一张总览卡片,创建后自动进入模块详情设置 KPI'"
          @click="add"
        >+ 新增卡片</button>
      </div>
    </section>

    <section class="block">
      <h3>现有卡片({{ cards.length }})</h3>
      <div v-if="!cards.length" class="hint">还没有总览卡片 · 上方新增</div>
      <div v-else class="cards">
        <div
          v-for="(c, i) in cards"
          :key="c.id"
          class="card-item"
        >
          <button class="row-main" v-tooltip="'编辑该卡对应模块(KPI、Owner、子项)'" @click="emit('pick-module', c.id)">
            <span class="grp-pill">{{ c.group }}</span>
            <span class="nm">{{ c.name }}</span>
            <span class="metrics">
              <span class="metric">{{ (c.kpi_fields || []).length }} KPI</span>
              <span class="metric">{{ c.owner_open_id || '未指派 Owner' }}</span>
            </span>
          </button>
          <div class="ops">
            <button v-tooltip="'上移'" :disabled="i === 0" @click="move(c, -1)">↑</button>
            <button v-tooltip="'下移'" :disabled="i === cards.length - 1" @click="move(c, 1)">↓</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.oc-drawer { display: flex; flex-direction: column; gap: 16px; }
.dh { padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
.sub { margin: 4px 0 0; font-size: 12px; color: var(--text-muted); }
.block h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; }
.add-row { display: grid; grid-template-columns: 160px 1fr 1.4fr 130px; gap: 8px; }
.cards { display: flex; flex-direction: column; gap: 6px; }
.card-item { display: grid; grid-template-columns: 1fr 80px; gap: 8px; align-items: center; }
.row-main {
  display: grid;
  grid-template-columns: 130px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  cursor: pointer;
  text-align: left;
}
.row-main:hover { border-color: var(--accent); background: var(--accent-soft); }
.grp-pill { background: var(--accent-soft); color: var(--accent); font-size: 11px; padding: 2px 8px; border-radius: var(--radius); text-align: center; font-weight: 600; }
.nm { font-weight: 600; }
.metrics { display: flex; gap: 8px; font-size: 11px; color: var(--text-muted); }
.metric { background: var(--panel); padding: 1px 6px; border-radius: var(--radius); }
.ops { display: flex; gap: 2px; justify-content: flex-end; }
.ops button { font-size: 11px; padding: 2px 6px; }
.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>
