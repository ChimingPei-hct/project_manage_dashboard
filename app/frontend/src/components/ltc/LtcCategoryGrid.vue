<script setup>
import { computed, onMounted, ref } from 'vue'
import { useCategories } from '../../composables/useCategories.js'
import { useContactCache, displayName } from '../../composables/useContactCache.js'
import { useDashboard } from '../../composables/useDashboard.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'
import { useEscClose } from '../../composables/useEscClose.js'
import LtcModuleCard from './LtcModuleCard.vue'
import SubItemEditDialog from './SubItemEditDialog.vue'
import ModuleStatusDialog from './ModuleStatusDialog.vue'
import UserSearchInput from '../UserSearchInput.vue'

/**
 * LTC 三级看板:Category(列) → Module(模块卡) → Sub-item(色块)。
 * 三类编辑入口:
 *   - 点 sub chip:SubItemEditDialog(编辑 / 删除)
 *   - 点「+ 子项」tile:SubItemEditDialog(创建态)
 *   - 点模块头:ModuleStatusDialog(改模块色 + risk_note)
 *   - 点模块头「⚙」:emit pick-module → LtcMain 打开 ModuleDrawer(改结构:名/Owner/sub_items/KPI)
 *   - 点列尾「+ 新模块」tile:本 LTC 本地新建模块
 * 全部走全量 PUT,设计 07 §8。
 */
const props = defineProps({
  ltcId: { type: String, required: true },
  modules: { type: Array, default: () => [] },
  mode: { type: String, default: 'both' }, // 'board' | 'risk' | 'both'
  canEditModuleStatus: { type: Function, default: () => false },
  statusKeyOf: { type: Function, required: true },
  canEnterAdmin: { type: Boolean, default: false },
  editMode: { type: Boolean, default: false },
})
const emit = defineEmits(['pick-module'])

const { categories, reload: reloadCategories, groupedForLtc } = useCategories()
const { status, refresh } = useDashboard()
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

// ---- sub-item dialog (edit/create/delete) ----
const editingSub = ref(null) // { module, sub | null }
function openSubEdit(module, sub) { editingSub.value = { module, sub } }
function openSubCreate(module)   { editingSub.value = { module, sub: null } }
function closeSub() { editingSub.value = null }
const editingSubKey  = computed(() => editingSub.value ? props.statusKeyOf(editingSub.value.module) : '')
const editingSubCan  = computed(() => editingSub.value ? props.canEditModuleStatus(editingSubKey.value) : false)

// ---- module-level status dialog (module_color + risk_note) ----
const editingMod = ref(null)
function openModStatus(module) { editingMod.value = module }
function closeModStatus() { editingMod.value = null }
const editingModKey = computed(() => editingMod.value ? props.statusKeyOf(editingMod.value) : '')
const editingModCan = computed(() => editingMod.value ? props.canEditModuleStatus(editingModKey.value) : false)

// ---- new module create (inline) ----
const newMod = ref(null) // { categoryId, categoryName, name, saving, err }
const newModOpen = computed(() => newMod.value !== null)
useEscClose(newModOpen, () => { newMod.value = null })

// ---- 大类 Owner 指派 (仅在 editMode + canEnterAdmin 时显示按钮) ----
const ownerPicker = ref(null) // { catId, busy, err } | null
const ownerPickerOpen = computed(() => ownerPicker.value !== null)
useEscClose(ownerPickerOpen, () => { ownerPicker.value = null })
function openOwnerPicker(catId) { ownerPicker.value = { catId, busy: false, err: '' } }
function closeOwnerPicker() { ownerPicker.value = null }
async function assignCatOwner(openId) {
  if (!ownerPicker.value) return
  ownerPicker.value.busy = true
  ownerPicker.value.err = ''
  try {
    await adminApi.updateCategory(ownerPicker.value.catId, { owner_open_id: openId || null })
    await reloadCategories()
    ownerPicker.value = null
  } catch (e) {
    ownerPicker.value.err = e.payload?.detail || e.message || '保存失败'
    ownerPicker.value.busy = false
  }
}
function openNewMod(cat) {
  newMod.value = { categoryId: cat?.id || null, categoryName: cat?.name || '未分类', name: '', saving: false, err: '' }
}
function closeNewMod() { newMod.value = null }
async function submitNewMod() {
  if (!newMod.value) return
  const n = newMod.value.name.trim()
  if (!n) { newMod.value.err = '请输入模块名'; return }
  newMod.value.saving = true; newMod.value.err = ''
  try {
    await adminApi.createModule({
      id: `ltc-${props.ltcId}-${newId().slice(0, 10)}`,
      scope: 'ltc',
      ltc_id: props.ltcId,
      category_id: newMod.value.categoryId,
      name: n,
      group: newMod.value.categoryName || '未分类',
      owner_open_id: null,
      kpi_fields: [],
      sub_items: [],
      order: (grouped.value.find(g => (g.category?.id || null) === newMod.value.categoryId)?.modules?.length || 0) + 1,
    })
    await refresh()
    closeNewMod()
  } catch (e) {
    newMod.value.err = e.payload?.detail || e.message || '创建失败'
  } finally {
    if (newMod.value) newMod.value.saving = false
  }
}

const showBoard = computed(() => props.mode === 'board' || props.mode === 'both')
const showRisk = computed(() => props.mode === 'risk' || props.mode === 'both')
const totalCats = computed(() => grouped.value.length)

const gridStyle = computed(() => {
  const n = Math.min(Math.max(totalCats.value, 1), 3)
  return { gridTemplateColumns: `repeat(${n}, 1fr)` }
})
</script>

<template>
  <div class="ltc-cat-wrap">
    <div v-if="!totalCats" class="empty-hint">
      该 LTC 暂未配置大类(Category)。请按「设计 04 §5.5」从模板池初始化本 LTC。
    </div>

    <!-- 看板/风险同卡:两段由 showBoard/showRisk 在卡内显隐 -->
    <section v-if="totalCats" class="grid-section">
      <div class="grid" :style="gridStyle">
        <div v-for="g in grouped" :key="`b-${g.category?.id || '__uncat'}`" class="col">
          <header class="col-head">
            <span class="cat-name">{{ g.category?.name || '未分类' }}</span>
            <span v-if="g.category" class="cat-owner">Owner · {{ ownerLabel(g.category.owner_open_id) }}</span>
            <button
              v-if="g.category && canEnterAdmin && editMode"
              type="button"
              class="cat-owner-edit"
              v-tooltip="g.category.owner_open_id ? '更换大类 Owner' : '指派大类 Owner'"
              @click="openOwnerPicker(g.category.id)"
            >{{ g.category.owner_open_id ? '换' : '+ 指派' }}</button>
          </header>
          <div v-if="!g.modules.length && !canEnterAdmin" class="col-empty">该大类暂无模块</div>
          <LtcModuleCard
            v-for="m in g.modules"
            :key="`b-mod-${m.id}`"
            :module="m"
            :entry="entryOf(m)"
            :can-edit="canEditModuleStatus(statusKeyOf(m))"
            :show-board="showBoard"
            :show-risk="showRisk"
            @edit-sub="(s) => openSubEdit(m, s)"
            @add-sub="openSubCreate(m)"
            @edit-module-status="openModStatus(m)"
            @edit-module-structure="emit('pick-module', m.id)"
          />
          <button
            v-if="canEnterAdmin"
            type="button"
            class="add-mod-tile"
            v-tooltip="`在大类「${g.category?.name || '未分类'}」中新建一个本 LTC 模块`"
            @click="openNewMod(g.category)"
          >+ 新模块</button>
        </div>
      </div>
    </section>

    <SubItemEditDialog
      :open="!!editingSub"
      :module="editingSub?.module"
      :sub-item="editingSub?.sub"
      :status-key="editingSubKey"
      :can-edit="editingSubCan"
      @close="closeSub"
    />
    <ModuleStatusDialog
      :open="!!editingMod"
      :module="editingMod"
      :status-key="editingModKey"
      :can-edit="editingModCan"
      @close="closeModStatus"
    />

    <!-- inline 新建模块对话 -->
    <div v-if="newMod" class="mask" @click.self="closeNewMod">
      <div class="box" role="dialog">
        <header class="head">
          <div>
            <h3>新建本 LTC 模块</h3>
            <p class="sub">大类:{{ newMod.categoryName }}</p>
          </div>
          <button class="close" @click="closeNewMod" v-tooltip="'关闭'">×</button>
        </header>
        <section class="block">
          <div class="block-title">模块名</div>
          <input
            v-model="newMod.name"
            placeholder="如:智驾 OTA、网关、ZP22 专属诊断"
            maxlength="60"
            @keydown.enter="submitNewMod"
            v-tooltip="'新模块的显示名(本 LTC 私有)'"
          />
          <p class="hint">创建后可点模块头 ⚙ 进一步加 Owner / sub_items / KPI。</p>
        </section>
        <p v-if="newMod.err" class="err-banner">{{ newMod.err }}</p>
        <footer class="foot">
          <button @click="closeNewMod">取消</button>
          <button
            class="primary"
            :disabled="!newMod.name.trim() || newMod.saving"
            v-tooltip="'创建模块(默认无子项、无 KPI、无 Owner,后续可改)'"
            @click="submitNewMod"
          >{{ newMod.saving ? '创建中…' : '创建' }}</button>
        </footer>
      </div>
    </div>

    <!-- 大类 Owner 指派弹窗(仅 editMode + canEnterAdmin 才能触发) -->
    <div v-if="ownerPicker" class="mask">
      <div class="box">
        <header class="mh">
          <h3>指派大类 Owner</h3>
          <button class="close" v-tooltip="'关闭'" @click="closeOwnerPicker">×</button>
        </header>
        <p v-if="ownerPicker.err" class="err">{{ ownerPicker.err }}</p>
        <p class="hint">搜索通讯录人员并指派为本大类负责人。指派后该大类标题旁会显示 Owner 姓名。</p>
        <UserSearchInput
          :modelValue="null"
          placeholder="搜姓名/邮箱/手机号"
          @select="u => assignCatOwner(u.open_id)"
        />
        <footer class="mf">
          <button :disabled="ownerPicker.busy" v-tooltip="'清除当前 Owner(置为未指派)'" @click="assignCatOwner(null)">清除 Owner</button>
          <button :disabled="ownerPicker.busy" v-tooltip="'放弃'" @click="closeOwnerPicker">取消</button>
        </footer>
      </div>
    </div>
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

.grid {
  display: grid;
  gap: 12px;
  align-items: start;
}
.col {
  display: flex; flex-direction: column; gap: 8px;
  background: var(--panel-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 10px 12px;
  min-width: 0;
}
.col-head {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 8px; padding: 2px 4px 8px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 2px;
}
.cat-name { font-size: 14px; font-weight: 700; color: var(--text); }
.cat-owner { font-size: 11px; color: var(--text-muted); }
.col-empty {
  font-size: 11.5px; color: var(--text-dim);
  padding: 6px 4px;
  font-style: italic;
}

.add-mod-tile {
  margin-top: 4px;
  border: 1px dashed var(--border);
  background: transparent; color: var(--text-muted);
  padding: 6px 10px; font-size: 12px;
  border-radius: var(--radius); cursor: pointer;
  font-weight: 500;
}
.add-mod-tile:hover { color: var(--accent); border-color: var(--accent); background: var(--panel); }

.mask {
  position: fixed; inset: 0; background: rgba(15,23,42,0.42);
  display: flex; align-items: center; justify-content: center;
  z-index: 9100; backdrop-filter: blur(2px);
}
.box {
  background: var(--panel); border-radius: var(--radius);
  padding: 18px 22px; min-width: 380px; max-width: 480px; width: 92vw;
  box-shadow: var(--shadow-lg);
}
.head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
h3 { margin: 0; font-size: 15px; font-weight: 700; }
.sub { margin: 2px 0 0; font-size: 12px; color: var(--text-muted); }
.close { border: none; background: transparent; font-size: 22px; line-height: 1; padding: 0 6px; cursor: pointer; color: var(--text-muted); }
.block { margin-bottom: 14px; }
.block-title { font-size: 12px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
input {
  width: 100%; font-size: 13px; padding: 6px 10px;
  border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--panel); font-family: inherit;
}
.hint { font-size: 11px; padding: 6px 0 0; margin: 0; color: var(--text-muted); }
.err-banner {
  background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30);
  color: var(--status-red); padding: 6px 10px; border-radius: var(--radius);
  font-size: 12px; margin: 0 0 10px;
}
.foot { display: flex; justify-content: flex-end; gap: 8px; padding-top: 10px; border-top: 1px solid var(--border-subtle); }
.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.primary:disabled { opacity: 0.55; cursor: not-allowed; }

/* 大类 Owner 指派按钮 + 弹窗 */
.cat-owner-edit {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius);
  border: 1px dashed var(--accent);
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  margin-left: 6px;
}
.cat-owner-edit:hover { background: var(--accent-soft); }
.mh { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.mh h3 { margin: 0; font-size: 15px; font-weight: 700; }
.mf { display: flex; justify-content: flex-end; gap: 8px; padding-top: 12px; margin-top: 12px; border-top: 1px solid var(--border-subtle); }
.mf button {
  font-size: 12px; padding: 5px 12px; border: 1px solid var(--border);
  background: var(--panel); border-radius: var(--radius); cursor: pointer;
}
.err { background: var(--status-red-bg); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0 0 8px; }
</style>
