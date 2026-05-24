<script setup>
import MilestoneEditor from './MilestoneEditor.vue'
</script>

<template>
  <div class="milestones-drawer">
    <header class="dh">
      <div>
        <div class="crumb">PDT 配置 / 时间线</div>
        <h2>时间线管理</h2>
      </div>
    </header>
    <MilestoneEditor />
  </div>
</template>

<style scoped>
.milestones-drawer { display: flex; flex-direction: column; gap: 16px; padding: 18px 24px 32px; }
.dh { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.crumb { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
h2 { margin: 0; font-size: 18px; font-weight: 700; }
</style>
