<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '../../composables/useAdminApi.js'
import { useAuth } from '../../composables/useAuth.js'
import ConfirmDialog from '../harness/ConfirmDialog.vue'

const { me } = useAuth()
const list = ref([])
const loading = ref(false)
const freezing = ref(false)
const msg = ref('')

async function refresh() {
  loading.value = true
  try { list.value = await adminApi.listSnapshots() }
  finally { loading.value = false }
}
onMounted(refresh)

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
</script>

<template>
  <div class="snapshot-panel">
    <div class="head">
      <h3>周快照</h3>
      <button class="primary" :disabled="freezing" @click="freezeNow(false)"
              v-tooltip="'冻结当前 ISO 周的看板状态;已存在则提示是否覆盖(仅 Super 可强制覆盖)'">
        {{ freezing ? '冻结中…' : '冻结本周' }}
      </button>
    </div>
    <p v-if="msg" class="msg">{{ msg }}</p>

    <div v-if="!list.length" class="empty">尚无快照。</div>
    <table v-else class="snap-table">
      <thead>
        <tr><th>周次</th><th>冻结时间</th><th>触发</th><th>操作者</th></tr>
      </thead>
      <tbody>
        <tr v-for="s in list" :key="s.week">
          <td><a :href="`?view=pdt&week=${s.week}`" v-tooltip="'切换到该周快照查看(只读)'">{{ s.week }}</a></td>
          <td>{{ s.frozen_at }}</td>
          <td>{{ s.trigger }}</td>
          <td>{{ s.frozen_by }}</td>
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
.msg { color: var(--text-muted); font-size: 13px; margin: 0 0 12px; }
.empty { color: var(--text-muted); padding: 16px; background: var(--panel); border: 1px dashed var(--border); border-radius: var(--radius); }
.snap-table { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.snap-table th, .snap-table td { padding: 8px 12px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border); }
.snap-table th { background: #fafafa; color: var(--text-muted); font-weight: 500; }
</style>
