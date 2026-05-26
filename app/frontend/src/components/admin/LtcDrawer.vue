<script setup>
/* 单个 LTC 详细抽屉:基础信息 + 该 LTC 下模块树形管理。
 * 模块清单按 大类(category) → 模块(module) → 子项(sub_item) 三级树渲染。
 * 详见 design/13 §LTC 配置抽屉。 */
import { computed, onMounted, ref, watch } from 'vue'
import { useDashboard } from '../../composables/useDashboard.js'
import { useCategories } from '../../composables/useCategories.js'
import { adminApi, newId } from '../../composables/useAdminApi.js'
import { useContactCache, displayName } from '../../composables/useContactCache.js'
import ConfirmDialog from '../harness/ConfirmDialog.vue'
import OwnerChip from '../OwnerChip.vue'

const props = defineProps({ ltcId: { type: String, required: true } })
const emit = defineEmits(['pick-module', 'deleted'])

const { ltcs, modules, refresh } = useDashboard()
const { groupedForLtc, reload: reloadCats } = useCategories()
const { ensureContacts } = useContactCache()
onMounted(() => { ensureContacts(); reloadCats() })
const ltc = computed(() => (ltcs.value || []).find(l => l.id === props.ltcId))
const mods = computed(() =>
  (modules.value || [])
    .filter(m => m.scope === 'ltc' && m.ltc_id === props.ltcId)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
)
const grouped = computed(() => groupedForLtc(props.ltcId, mods.value))

// 折叠状态:Map<key, collapsed?> — 大类 key = "cat:<id>",模块 key = "mod:<id>";默认大类展开、模块折叠
const collapsed = ref({})
function catKey(c) { return c ? `cat:${c.id}` : 'cat:_orphan_' }
function modKey(m) { return `mod:${m.id}` }
function isCollapsed(key, defaultCollapsed = false) {
  return key in collapsed.value ? collapsed.value[key] : defaultCollapsed
}
function toggle(key, defaultCollapsed = false) {
  collapsed.value = { ...collapsed.value, [key]: !isCollapsed(key, defaultCollapsed) }
}

const draft = ref({ name: '' })
const dirty = ref(false)
watch(ltc, (v) => {
  if (!v) return
  draft.value = { name: v.name }
  dirty.value = false
}, { immediate: true })

const newMod = ref({ group: '', name: '' })
const adding = ref(false)
const saving = ref(false)
const errMsg = ref('')

async function save() {
  saving.value = true
  errMsg.value = ''
  try {
    await adminApi.updateLtc(props.ltcId, { name: draft.value.name })
    await refresh()
    dirty.value = false
  } catch (e) { errMsg.value = e.message } finally { saving.value = false }
}

async function addModule() {
  if (!newMod.value.name.trim() || !newMod.value.group.trim()) return
  adding.value = true
  try {
    const body = {
      id: newId(),
      scope: 'ltc',
      ltc_id: props.ltcId,
      group: newMod.value.group.trim(),
      name: newMod.value.name.trim(),
      kpi_fields: [],
      sub_items: [],
    }
    const created = await adminApi.createModule(body)
    newMod.value = { group: '', name: '' }
    await refresh()
    emit('pick-module', created.id)
  } catch (e) {
    errMsg.value = e.payload?.detail || e.message || '创建失败'
  } finally { adding.value = false }
}

const confirmDel = ref(false)
async function doDelete() {
  confirmDel.value = false
  try {
    await adminApi.deleteLtc(props.ltcId)
    await refresh()
    emit('deleted')
  } catch (e) { errMsg.value = e.payload?.detail || e.message || '删除失败' }
}

async function toggleArchive() {
  await adminApi.updateLtc(props.ltcId, { archived: !ltc.value.archived })
  await refresh()
}
</script>

<template>
  <div v-if="ltc" class="ltc-drawer">
    <header class="dh">
      <div>
        <div class="crumb">LTC 子项目</div>
        <h2>{{ ltc.name }}</h2>
      </div>
      <div class="ops">
        <button class="primary" :disabled="!dirty || saving" v-tooltip="'保存 LTC 基础信息'" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
        <button v-tooltip="ltc.archived ? '取消归档' : '归档此 LTC(不删除)'" @click="toggleArchive">
          {{ ltc.archived ? '取消归档' : '归档' }}
        </button>
        <button class="danger" v-tooltip="'仅当该 LTC 下无模块时可删除'" @click="confirmDel = true">删除</button>
      </div>
    </header>

    <p v-if="errMsg" class="err-banner">{{ errMsg }}</p>

    <section class="block">
      <h3>基础信息</h3>
      <label class="line">
        <span>名称</span>
        <input v-model="draft.name" @input="dirty = true" />
      </label>
      <div class="meta-line">
        <span>状态:{{ ltc.archived ? '已归档' : '活跃' }}</span>
        <span>order: {{ ltc.order }}</span>
        <span>id: <code>{{ ltc.id }}</code></span>
      </div>
    </section>

    <section class="block">
      <header class="sec-head">
        <h3>模块清单({{ mods.length }})</h3>
      </header>
      <div class="add-mod">
        <input v-model="newMod.group" placeholder="分组(如:硬件和底软)" />
        <input v-model="newMod.name" placeholder="模块名(如:MCU 底软)" @keyup.enter="addModule" />
        <button
          class="primary"
          :disabled="adding || !newMod.name.trim() || !newMod.group.trim()"
          v-tooltip="'在此 LTC 下创建模块,创建后自动进入模块详情'"
          @click="addModule"
        >+ 添加模块</button>
      </div>
      <div v-if="!mods.length" class="hint">该 LTC 下还没有模块</div>
      <div v-else class="tree">
        <div v-for="g in grouped" :key="catKey(g.category)" class="tree-cat">
          <button
            type="button"
            class="row cat-row"
            v-tooltip="'折叠/展开本大类'"
            @click="toggle(catKey(g.category), false)"
          >
            <span class="caret">{{ isCollapsed(catKey(g.category), false) ? '▶' : '▼' }}</span>
            <span class="cat-name">{{ g.category?.name || '未分类' }}</span>
            <span class="badge">{{ g.modules.length }} 模块</span>
          </button>
          <div v-show="!isCollapsed(catKey(g.category), false)" class="cat-body">
            <div v-if="!g.modules.length" class="empty-cat">本大类下暂无模块</div>
            <template v-else>
              <div v-for="m in g.modules" :key="m.id" class="tree-mod">
                <div class="row mod-row">
                  <button
                    type="button"
                    class="caret-btn"
                    v-tooltip="(m.sub_items || []).length ? '展开/折叠子项' : '此模块暂无子项'"
                    :disabled="!(m.sub_items || []).length"
                    @click.stop="toggle(modKey(m), true)"
                  >
                    {{ (m.sub_items || []).length
                      ? (isCollapsed(modKey(m), true) ? '▶' : '▼')
                      : '·' }}
                  </button>
                  <button
                    type="button"
                    class="mod-link"
                    v-tooltip="'点击进入该模块的详细编辑'"
                    @click="emit('pick-module', m.id)"
                  >
                    <span class="mod-name">{{ m.name }}</span>
                    <span class="mod-meta">{{ (m.sub_items || []).length }} 子项 · {{ (m.kpi_fields || []).length }} KPI</span>
                  </button>
                  <OwnerChip :open-id="m.owner_open_id" fallback="未指派" />
                </div>
                <div
                  v-if="(m.sub_items || []).length && !isCollapsed(modKey(m), true)"
                  class="sub-list"
                >
                  <span
                    v-for="s in m.sub_items"
                    :key="s.id"
                    class="sub-chip"
                    v-tooltip="s.risk_note || s.name"
                  >{{ s.name }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </section>

    <ConfirmDialog
      :open="confirmDel"
      title="删除 LTC"
      :body="`确认删除 LTC「${ltc.name}」?\n仅在该 LTC 下无模块时可删除。`"
      confirm-text="删除"
      @confirm="doDelete"
      @cancel="confirmDel = false"
    />
  </div>
</template>

<style scoped>
.ltc-drawer { display: flex; flex-direction: column; gap: 16px; }
.dh { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
.ops { display: flex; gap: 8px; }
.danger { background: var(--status-red); color: #fff; border-color: var(--status-red); }

.block h3 { font-size: 13px; margin: 0 0 8px; font-weight: 700; }
.sec-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.line { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--text-muted); }
.line span { width: 50px; flex-shrink: 0; }
.line input { flex: 1; }
.meta-line { font-size: 11px; color: var(--text-dim); display: flex; gap: 16px; margin-top: 8px; }
.meta-line code { font-family: ui-monospace, monospace; background: var(--panel-soft); padding: 1px 5px; border-radius: var(--radius); }

.add-mod { display: grid; grid-template-columns: 1fr 1fr 130px; gap: 6px; margin-bottom: 10px; }

/* ---- 树形结构 ---- */
.tree { display: flex; flex-direction: column; gap: 4px; }
.tree-cat { display: flex; flex-direction: column; }
.row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  text-align: left;
  font-size: 12.5px;
  width: 100%;
  transition: background var(--transition), border-color var(--transition);
}
.cat-row {
  background: var(--panel-soft);
  border-color: var(--border-subtle);
  font-weight: 600;
  color: var(--text);
}
.cat-row:hover { border-color: var(--accent); }
.caret {
  display: inline-block;
  width: 14px;
  text-align: center;
  color: var(--text-muted);
  font-size: 11px;
}
.cat-name { flex: 1; }
.badge {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--panel);
  padding: 1px 8px;
  border-radius: var(--radius);
  border: 1px solid var(--border-subtle);
}

.cat-body { display: flex; flex-direction: column; gap: 3px; padding: 4px 0 4px 18px; }
.empty-cat { padding: 6px 10px; font-size: 11px; color: var(--text-dim); }

.tree-mod { display: flex; flex-direction: column; }
.mod-row {
  padding: 6px 10px 6px 4px;
  background: var(--panel-soft);
  border-color: var(--border-subtle);
}
.mod-row:hover { background: var(--accent-soft); border-color: var(--accent); }
.caret-btn {
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  width: 18px;
  height: 18px;
  padding: 0;
  cursor: pointer;
  border-radius: var(--radius);
}
.caret-btn:hover:not(:disabled) { color: var(--accent); background: var(--panel); }
.caret-btn:disabled { cursor: default; opacity: 0.5; }
.mod-link {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--text);
}
.mod-name { font-weight: 600; }
.mod-meta { font-size: 11px; color: var(--text-dim); }

.sub-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 10px 6px 30px;
}
.sub-chip {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--panel);
  border: 1px solid var(--border-subtle);
  padding: 1px 8px;
  border-radius: var(--radius);
}

.hint { font-size: 12px; color: var(--text-dim); padding: 6px 0; }
.err-banner { background: var(--status-red-bg); border: 1px solid rgba(220,38,38,0.30); color: var(--status-red); padding: 6px 10px; border-radius: var(--radius); font-size: 12px; margin: 0; }
</style>
