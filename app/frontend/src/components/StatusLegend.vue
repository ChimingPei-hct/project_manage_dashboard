<script setup>
/* 右上角图例:●进展正常 / ●进展预警 / ●Delay/Block */
</script>

<template>
  <div class="legend">
    <span class="item"><i class="dot green"></i>进展正常</span>
    <span class="item"><i class="dot yellow"></i>进展预警</span>
    <span class="item"><i class="dot red"></i>Delay/Block</span>
  </div>
</template>

<style scoped>
.legend {
  display: inline-flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  align-items: center;
}
.item { display: inline-flex; align-items: center; gap: 5px; }
.dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-sm);
  display: inline-block;
}
.dot.green { background: var(--status-green); }
.dot.yellow { background: var(--status-yellow); }
.dot.red { background: var(--status-red); }
</style>
