<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { adminApi } from '../../composables/useAdminApi.js'
import { useAuth } from '../../composables/useAuth.js'
import { useView } from '../../composables/useView.js'
import { sseBus } from '../../composables/sseBus.js'
import ConfirmDialog from '../harness/ConfirmDialog.vue'

const { me } = useAuth()
const { current, pushView } = useView()
const list = ref([])
const loading = ref(false)
const freezing = ref(false)
const msg = ref('')

const autoCfg = ref({ enabled: false, weekday: 4, hour: 18, minute: 0, next_run_at: null })
const autoSaving = ref(false)
const autoErr = ref('')

const WEEKDAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

async function refresh() {
  loading.value = true
  try { list.value = await adminApi.listSnapshots() }
  finally { loading.value = false }
}

async function refreshAutoCfg() {
  try { autoCfg.value = await adminApi.getAutoFreeze() } catch (_) { /* ignore */ }
}

async function saveAuto(partial) {
  if (!me.value?.is_super) return
  autoSaving.value = true
  autoErr.value = ''
  try {
    autoCfg.value = await adminApi.updateAutoFreeze({ ...autoCfg.value, ...partial })
  } catch (e) {
    autoErr.value = e.message || '保存失败'
  } finally { autoSaving.value = false }
}

function fmtNextRun(iso) {
  if (!iso) return '—'
  return iso.replace('T', ' ').slice(0, 16)
}

let off = null
let offCfg = null
onMounted(() => {
  refresh()
  refreshAutoCfg()
  off = sseBus.on('snapshot:created', refresh)
  offCfg = sseBus.on('config:reload', (data) => {
    if (!data || data.kind === 'auto_freeze') refreshAutoCfg()
  })
})
onBeforeUnmount(() => {
  off && off()
  offCfg && offCfg()
})

const forceState = ref({ open: false })

async function freezeNow(force = false) {
  freezing.value = true
  msg.value = ''
  try {
    const r = await adminApi.freezeSnapshot(null, force)
    msg.value = `已冻结快照 ${r.week}`
    await refresh()
  } catch (e) {
    if (e.status === 409) {
      forceState.value.open = true
      msg.value = '本周快照已存在'
    } else {
      msg.value = `失败:${e.message}`
    }
  } finally { freezing.value = false }
}

async function doForce() {
  forceState.value.open = false
  await freezeNow(true)
}

const viewingWeek = computed(() => current.value.week || '')

function goWeek(w) {
  pushView({ view: 'pdt', week: w })
}
function goCurrent() {
  pushView({ view: 'pdt' })
}
</script>

<template>
  <div class="snapshot-panel">
    <div class="head">
      <h3>周快照</h3>
      <div class="head-actions">
        <button
          v-if="viewingWeek"
          v-tooltip="'切回当前实时数据视图'"
          @click="goCurrent"
        >返回当前周</button>
        <button class="primary" :disabled="freezing" @click="freezeNow(false)"
                v-tooltip="'冻结当前 ISO 周的看板状态;已存在则提示是否覆盖(仅 Super 可强制覆盖)'">
          {{ freezing ? '冻结中…' : '冻结本周' }}
        </button>
      </div>
    </div>
    <p v-if="msg" class="msg" :class="{ ok: msg.startsWith('已冻结') }">{{ msg }}</p>

    <section class="auto-block">
      <header class="auto-head">
        <div>
          <h4>自动冻结</h4>
          <p class="hint">
            到指定时刻后,后端 60s 内自动冻结当周快照(trigger=auto)。
            <template v-if="autoCfg.enabled">
              下次执行:<strong>{{ fmtNextRun(autoCfg.next_run_at) }}</strong>
            </template>
            <template v-else>当前未启用。</template>
          </p>
        </div>
        <label class="switch" v-tooltip="me?.is_super ? '开启 / 关闭自动冻结调度' : '仅 Super Admin 可改'">
          <input
            type="checkbox"
            :checked="autoCfg.enabled"
            :disabled="!me?.is_super || autoSaving"
            @change="e => saveAuto({ enabled: e.target.checked })"
          />
          <span>{{ autoCfg.enabled ? '已启用' : '未启用' }}</span>
        </label>
      </header>
      <div class="auto-fields" v-if="autoCfg.enabled || me?.is_super">
        <label>
          <span>星期</span>
          <select
            :value="autoCfg.weekday"
            :disabled="!me?.is_super || autoSaving"
            v-tooltip="'每周哪一天执行自动冻结'"
            @change="e => saveAuto({ weekday: Number(e.target.value) })"
          >
            <option v-for="(w, i) in WEEKDAY_LABELS" :key="i" :value="i">{{ w }}</option>
          </select>
        </label>
        <label>
          <span>小时</span>
          <input
            type="number"
            min="0"
            max="23"
            :value="autoCfg.hour"
            :disabled="!me?.is_super || autoSaving"
            v-tooltip="'24 小时制,0–23'"
            @change="e => saveAuto({ hour: Number(e.target.value) })"
          />
        </label>
        <label>
          <span>分钟</span>
          <input
            type="number"
            min="0"
            max="59"
            :value="autoCfg.minute"
            :disabled="!me?.is_super || autoSaving"
            v-tooltip="'0–59'"
            @change="e => saveAuto({ minute: Number(e.target.value) })"
          />
        </label>
      </div>
      <p v-if="autoErr" class="msg err">{{ autoErr }}</p>
    </section>

    <div v-if="!list.length" class="empty">尚无快照。冻结本周以归档当前状态供历史回看。</div>
    <table v-else class="snap-table">
      <thead>
        <tr><th>周次</th><th>冻结时间</th><th>触发</th><th>操作者</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="s in list" :key="s.week" :class="{ active: viewingWeek === s.week }">
          <td>
            <a
              :href="`?view=pdt&week=${s.week}`"
              @click.prevent="goWeek(s.week)"
              v-tooltip="'切换到该周快照查看(只读)'"
            >{{ s.week }}</a>
            <span v-if="viewingWeek === s.week" class="badge">正在查看</span>
          </td>
          <td>{{ s.frozen_at }}</td>
          <td>{{ s.trigger }}</td>
          <td>{{ s.frozen_by }}</td>
          <td class="row-actions">
            <button
              v-if="viewingWeek !== s.week"
              v-tooltip="'切换到该周快照查看'"
              @click="goWeek(s.week)"
            >查看</button>
          </td>
        </tr>
      </tbody>
    </table>

    <ConfirmDialog
      :open="forceState.open"
      title="本周快照已存在"
      :body="me?.is_super ? '是否强制覆盖现有快照?\n这会丢失现有快照内容。' : '只有 Super Admin 可强制覆盖,请联系超管。'"
      :confirm-text="me?.is_super ? '强制覆盖' : '我知道了'"
      :danger="me?.is_super"
      @confirm="me?.is_super ? doForce() : forceState.open = false"
      @cancel="forceState.open = false"
    />
  </div>
</template>

<style scoped>
.snapshot-panel { max-width: 920px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.head h3 { margin: 0; font-size: 14px; }
.head-actions { display: flex; gap: 8px; }
.msg { color: var(--text-muted); font-size: 13px; margin: 0 0 12px; }
.msg.ok { color: var(--status-green); }
.empty { color: var(--text-muted); padding: 24px; background: var(--panel); border: 1px dashed var(--border); border-radius: var(--radius); text-align: center; }
.snap-table { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm); }
.snap-table th, .snap-table td { padding: 9px 12px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border-subtle); }
.snap-table tr:last-child td { border-bottom: none; }
.snap-table th { background: var(--panel-soft); color: var(--text-muted); font-weight: 600; font-size: 12px; letter-spacing: 0.3px; text-transform: uppercase; }
.snap-table tr.active { background: var(--accent-soft); }
.snap-table tr.active td { color: var(--text); }
.badge {
  display: inline-block;
  margin-left: 8px;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: var(--radius);
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}
.row-actions { text-align: right; }
.row-actions button { font-size: 12px; padding: 2px 10px; }

/* 自动冻结配置块 */
.auto-block {
  border: 1px solid var(--border-subtle);
  background: var(--panel-soft);
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-bottom: 16px;
}
.auto-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.auto-head h4 { margin: 0 0 4px; font-size: 13px; font-weight: 600; }
.auto-head .hint { margin: 0; font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.auto-head .hint strong { color: var(--text); font-variant-numeric: tabular-nums; }
.switch { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
.switch input { accent-color: var(--accent); }
.auto-fields { display: flex; gap: 12px; align-items: center; margin-top: 12px; flex-wrap: wrap; }
.auto-fields label { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-muted); }
.auto-fields input, .auto-fields select { width: 80px; }
.msg.err { color: var(--status-red); }
</style>
