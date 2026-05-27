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
import OwnerChip from '../OwnerChip.vue'

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
  /* 状态色显隐:{ green, yellow, red } 三色独立 toggle,gray 跟随 green */
  visibleTones: { type: Object, default: () => ({ green: true, yellow: true, red: true }) },
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

// ---- 新建大类(本 LTC 内,scope=ltc) ----
// 仅在 editMode + canEnterAdmin 时显示按钮;手动建的 LTC 没大类导致单列,
// 此入口让用户能后补大类把布局拉回三级结构(详见 design/04 §5.5)
const newCat = ref(null) // { name, saving, err } | null
const newCatOpen = computed(() => newCat.value !== null)
useEscClose(newCatOpen, () => { newCat.value = null })
function openNewCat() { newCat.value = { name: '', saving: false, err: '' } }
function closeNewCat() { newCat.value = null }
function genCatId(name) {
  const sani = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  const ltcSlug = sani(props.ltcId) || 'ltc'
  const slug = sani(name) || 'new'
  return `cat-${ltcSlug}-${slug}-${Math.random().toString(36).slice(2, 6)}`
}
async function submitNewCat() {
  if (!newCat.value) return
  const n = newCat.value.name.trim()
  if (!n) { newCat.value.err = '请输入大类名'; return }
  newCat.value.saving = true; newCat.value.err = ''
  try {
    // 取本 LTC 已有大类的最大 order + 1
    const existing = (categories.value || []).filter(c => c.scope === 'ltc' && c.ltc_id === props.ltcId)
    const nextOrder = existing.length
      ? Math.max(...existing.map(c => c.order ?? 0)) + 1
      : 1
    await adminApi.createCategory({
      id: genCatId(n),
      scope: 'ltc',
      ltc_id: props.ltcId,
      name: n,
      order: nextOrder,
    })
    await reloadCategories()
    closeNewCat()
  } catch (e) {
    newCat.value.err = e.payload?.detail || e.message || '创建失败'
  } finally {
    if (newCat.value) newCat.value.saving = false
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

const totalCats = computed(() => grouped.value.length)

const gridStyle = computed(() => {
  const n = Math.min(Math.max(totalCats.value, 1), 3)
  return { gridTemplateColumns: `repeat(${n}, 1fr)` }
})
</script>

<template>
  <div class="ltc-cat-wrap">
    <div v-if="!totalCats" class="empty-hint">
      <p>该 LTC 暂未配置大类(Category)。两种补救方式:</p>
      <p>① 从模板池初始化(详见 design/04 §5.5)</p>
      <p>② 手动新建大类(下方按钮,需先进入编辑模式)</p>
      <button
        v-if="canEnterAdmin && editMode"
        type="button"
        class="new-cat-btn"
        v-tooltip="'在本 LTC 内新建第一个大类'"
        @click="openNewCat"
      >+ 新建大类</button>
    </div>

    <!-- 三级看板:每个 LtcModuleCard 内同时展示 chips + 风险行,按 visibleTones 过滤 -->
    <section v-if="totalCats" class="grid-section">
      <div v-if="canEnterAdmin && editMode" class="new-cat-bar">
        <button
          type="button"
          class="new-cat-btn"
          v-tooltip="'在本 LTC 内新建大类(可放置自己的模块,把单列布局拉回多列三级结构)'"
          @click="openNewCat"
        >+ 新建大类</button>
      </div>
      <div class="grid" :style="gridStyle">
        <div v-for="g in grouped" :key="`b-${g.category?.id || '__uncat'}`" class="col">
          <header class="col-head">
            <span class="cat-name">{{ g.category?.name || '未分类' }}</span>
            <OwnerChip
              v-if="g.category && g.category.owner_open_id"
              class="cat-owner"
              :open-id="g.category.owner_open_id"
              :size="22"
              v-tooltip="'大类负责人'"
            />
            <span v-else-if="g.category" class="cat-owner cat-owner-unassigned">未指派</span>
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
            :visible-tones="visibleTones"
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

    <!-- 新建大类弹窗(本 LTC 内,scope=ltc) -->
    <div v-if="newCat" class="mask">
      <div class="box">
        <header class="mh">
          <h3>新建大类</h3>
          <button class="close" v-tooltip="'关闭'" @click="closeNewCat">×</button>
        </header>
        <p v-if="newCat.err" class="err">{{ newCat.err }}</p>
        <p class="hint">新建本 LTC 私有大类(不影响模板池与其他 LTC)。创建后即可在该大类下添加模块。</p>
        <label class="block">
          <span class="block-title">大类名称 *</span>
          <input
            v-model="newCat.name"
            placeholder="如:感知 / 规控 / 工具与交付"
            maxlength="32"
            autofocus
            @keyup.enter="submitNewCat"
          />
        </label>
        <footer class="mf">
          <button :disabled="newCat.saving" v-tooltip="'放弃'" @click="closeNewCat">取消</button>
          <button
            class="primary"
            :disabled="!newCat.name.trim() || newCat.saving"
            v-tooltip="'创建大类'"
            @click="submitNewCat"
          >{{ newCat.saving ? '创建中…' : '创建' }}</button>
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
  gap: 16px;
  align-items: start;
}
/* ── Category 列升级为 surface 卡片 ── */
.col {
  display: flex; flex-direction: column; gap: 10px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  padding: 16px 14px 14px;
  min-width: 0;
  transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
}
.col:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
  border-color: var(--border-strong);
}
.col-head {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 8px; padding: 0 2px 10px;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 2px;
}
.cat-name {
  font-family: var(--font-serif);
  font-size: 19px; font-weight: 600;
  color: var(--text-strong);
  letter-spacing: 0.04em;
  line-height: 1.3;
}
.cat-owner { font-size: 12.5px; color: var(--text); font-weight: 500; }
.cat-owner.cat-owner-unassigned {
  font-family: var(--font-sans);
  color: var(--text-muted);
  font-style: italic;
  letter-spacing: 0.04em;
}
.cat-owner :deep(.name) { color: var(--text-strong); font-weight: 600; letter-spacing: 0.03em; }
.col-empty {
  font-size: 12.5px; color: var(--text-muted);
  padding: 8px 4px;
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
.mf .primary,
.foot .primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.mf .primary:disabled,
.foot .primary:disabled { opacity: 0.55; cursor: not-allowed; }

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

/* 新建大类按钮 — 顶部条 + 空态 共用 */
.new-cat-bar { display: flex; justify-content: flex-end; margin-bottom: 8px; }
.new-cat-btn {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: var(--radius);
  border: 1px dashed var(--accent);
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  font-weight: 500;
}
.new-cat-btn:hover { background: var(--accent-soft); }
.empty-hint .new-cat-btn { margin-top: 12px; }
.mh { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.mh h3 { margin: 0; font-size: 15px; font-weight: 700; }
.mf { display: flex; justify-content: flex-end; gap: 8px; padding-top: 12px; margin-top: 12px; border-top: 1px solid var(--border-subtle); }
.mf button {
  font-size: 12px; padding: 5px 12px; border: 1px solid var(--border);
  background: var(--panel); border-radius: var(--radius); cursor: pointer;
}
.err { background: var(--status-red-bg); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0 0 8px; }
</style>
