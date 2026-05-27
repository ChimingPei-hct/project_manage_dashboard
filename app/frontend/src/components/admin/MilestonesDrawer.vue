<script setup>
import MilestoneEditor from './MilestoneEditor.vue'
</script>

<template>
  <div class="milestones-drawer">
    <header class="dh">
      <div>
        <div class="crumb">PDT 配置 <span class="sep">/</span> 时间线</div>
        <h2>时间线管理</h2>
        <p class="sub">编辑 PDT 全局时间线节点 · 拖拽/上下移调整顺序 · 类型决定时间轴上的形状与颜色</p>
      </div>
    </header>
    <MilestoneEditor />
  </div>
</template>

<style scoped>
.milestones-drawer {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px 40px;
  max-width: 1600px;
  margin: 0 auto;
}
.dh {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}
.crumb {
  font-size: 12.5px;
  color: var(--text-muted);
  margin-bottom: 6px;
  font-weight: 500;
  letter-spacing: 0.2px;
}
.crumb .sep { color: var(--text-dim); margin: 0 6px; }
h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: var(--text-strong);
}
.sub {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
