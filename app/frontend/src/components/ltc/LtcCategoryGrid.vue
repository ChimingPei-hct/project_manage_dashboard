<script setup>
import { computed, onMounted, ref } from 'vue'
import { useCategories } from '../../composables/useCategories.js'
import { useContactCache, displayName } from '../../composables/useContactCache.js'
import { useDashboard } from '../../composables/useDashboard.js'
import LtcModuleCard from './LtcModuleCard.vue'
import LtcRiskCard from './LtcRiskCard.vue'
import SubItemEditDialog from './SubItemEditDialog.vue'

/**
 * LTC 三级看板:Category(列) → Module(模块卡) → Sub-item(色块)。
 * 支持 mode='board' / 'risk' / 'both' 三种渲染:
 *   - board: 全部模块,所有子项色块
 *   - risk:  仅非绿态的模块/子项,带风险文字
 *   - both:  两段并排显示
 * 子项点击触发内嵌 SubItemEditDialog(全量 PUT,设计 07 §8)。
 */
const props = defineProps({
  ltcId: { type: String, required: true },
  modules: { type: Array, default: () => [] },
  mode: { type: String, default: 'both' }, // 'board' | 'risk' | 'both'
  canEditModuleStatus: { type: Function, default: () => false },
  statusKeyOf: { type: Function, required: true },
})

const { categories, reload: reloadCategories, groupedForLtc } = useCategories()
const { status } = useDashboard()
const { contacts, ensureContacts } = useContactCache()

onMounted(() => { reloadCategories(); ensureContacts() })

const grouped = computed(() => groupedForLtc(props.ltcId, props.modules))

function ownerLabel(openId) {
  if (!openId) return '未指派'
  const u = (contacts.value || []).find(x => x.open_id === openId)
  return u?.name || displayName(openId) || openId
}

function entryOf(module) {
  return status.value?.[props.statusKeyOf(module)] || {}
}

function hasRisk(module) {
  const e = entryOf(module)
  const mc = e?.module_color
  if (mc === 'red' || mc === 'yellow') return true
  for (const v of Object.values(e?.sub_items_color || {})) {
    if (v === 'red' || v === 'yellow') return true
  }
  return false
}

const riskModulesByGroup = computed(() => grouped.value.map(g => ({
  category: g.category,
  modules: g.modules.filter(hasRisk),
})))

const editingSub = ref(null) // { module, sub }
function openSub(module, sub) {
  editingSub.value = { module, sub }
}
function closeSub() { editingSub.value = null }

const editingStatusKey = computed(() => editingSub.value ? props.statusKeyOf(editingSub.value.module) : '')
const editingCanEdit = computed(() => {
  if (!editingSub.value) return false
  return props.canEditModuleStatus(editingStatusKey.value)
})

const showBoard = computed(() => props.mode === 'board' || props.mode === 'both')
const showRisk = computed(() => props.mode === 'risk' || props.mode === 'both')
const totalCats = computed(() => grouped.value.length)
</script>

<template>
  <div class="ltc-cat-wrap">
    <div v-if="!totalCats" class="empty-hint">
      该 LTC 暂未配置大类(Category)。请在「LTC 配置 → 大类」中先建大类,并把模块关联到大类。
    </div>

    <!-- 看板段 -->
    <section v-if="showBoard && totalCats" class="grid-section">
      <div class="grid">
        <div v-for="g in grouped" :key="`b-${g.category?.id || '__uncat'}`" class="col">
          <header class="col-head">
            <span class="cat-name">{{ g.category?.name || '未分类' }}</span>
            <span v-if="g.category" class="cat-owner">Owner · {{ ownerLabel(g.category.owner_open_id) }}</span>
          </header>
          <div v-if="!g.modules.length" class="col-empty">该大类暂无模块</div>
          <LtcModuleCard
            v-for="m in g.modules"
            :key="`b-mod-${m.id}`"
            :module="m"
            :entry="entryOf(m)"
            :can-edit="canEditModuleStatus(statusKeyOf(m))"
            @edit-sub="(s) => openSub(m, s)"
          />
        </div>
      </div>
    </section>

    <!-- 风险段 -->
    <section v-if="showRisk && totalCats" class="grid-section">
      <div class="risk-banner">
        风险详情 · 仅显示状态非绿的模块和子项
      </div>
      <div class="grid">
        <div v-for="g in riskModulesByGroup" :key="`r-${g.category?.id || '__uncat'}`" class="col">
          <header class="col-head">
            <span class="cat-name">{{ g.category?.name || '未分类' }}</span>
            <span v-if="g.category" class="cat-owner">Owner · {{ ownerLabel(g.category.owner_open_id) }}</span>
          </header>
          <div v-if="!g.modules.length" class="col-empty all-green">本大类全绿</div>
          <LtcRiskCard
            v-for="m in g.modules"
            :key="`r-mod-${m.id}`"
            :module="m"
            :entry="entryOf(m)"
            :can-edit="canEditModuleStatus(statusKeyOf(m))"
            @edit-sub="(s) => openSub(m, s)"
          />
        </div>
      </div>
    </section>

    <SubItemEditDialog
      :open="!!editingSub"
      :module="editingSub?.module"
      :sub-item="editingSub?.sub"
      :status-key="editingStatusKey"
      :can-edit="editingCanEdit"
      @close="closeSub"
    />
  </div>
</template>

<style scoped>
.ltc-cat-wrap { display: flex; flex-direction: column; gap: 18px; }
.empty-hint {
  padding: 24px; background: var(--panel-soft);
  border: 1px dashed var(--border); border-radius: var(--radius);
  font-size: 13px; color: var(--text-muted); text-align: center;
}

.grid-section { display: flex; flex-direction: column; gap: 8px; }
.risk-banner {
  font-size: 12px; color: var(--text-muted);
  padding: 4px 8px;
  background: var(--status-yellow-bg);
  border-radius: var(--radius);
  width: fit-content;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  align-items: start;
}
.col {
  display: flex; flex-direction: column; gap: 6px;
  background: var(--panel-soft);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 8px 8px 10px;
}
.col-head {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 8px; padding: 2px 4px 6px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 4px;
}
.cat-name { font-size: 13px; font-weight: 700; color: var(--text); }
.cat-owner { font-size: 11px; color: var(--text-muted); }
.col-empty {
  font-size: 11.5px; color: var(--text-dim);
  padding: 6px 4px;
  font-style: italic;
}
.col-empty.all-green { color: var(--status-green); font-style: normal; }
</style>
