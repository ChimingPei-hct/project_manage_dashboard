# 周快照 Schema 与冻结规则

## 1. 模块目标

定义周快照(`weekly_snapshots/snapshot-YYYY-Www.json`)的文件格式、冻结时机、只读语义,使得"任意历史周的看板状态都可一键还原"。

## 2. 边界

### 管什么

- 快照文件命名与目录结构
- 周号口径(ISO week)
- 冻结时机与触发方式
- 只读语义与与历史流的差异

### 不管什么

- 当前态字段 → `07`
- 历史流字段 → `08`
- 前端如何切换周次 → `13`

## 3. 文件布局

```
DATA_DIR/weekly_snapshots/
├── snapshot-2026-W20.json
├── snapshot-2026-W21.json
└── ...
```

main 模板:`weekly_snapshots/` 空目录(可保留 `.gitkeep`)。

## 4. 周号口径

- 采用 **ISO 8601 周号**(`YYYY-Www`,周一开始)
- Python: `datetime.date.isocalendar()` → `(year, week, weekday)`
- 文件名格式:`snapshot-{ISO_year}-W{ISO_week:02d}.json`(如 `snapshot-2026-W21.json`)
- 跨年场景按 ISO 规则,可能 1 月初属于上一年的 W52/W53,12 月底属于下一年的 W01

## 5. 文件内容 Schema

```jsonc
{
  "week": "2026-W21",
  "frozen_at": "2026-05-22T18:00:00+08:00",
  "frozen_by": "ou_xxxxxx",     // 手动 freeze:操作者 open_id;自动 freeze:"system"
  "trigger": "manual",          // 枚举:"manual" | "auto"
  "pdt": { ... },               // 冻结时刻 pdt.json 完整快照
  "ltcs": [ ... ],              // 冻结时刻 ltcs.json 完整快照
  "modules": [ ... ],           // 冻结时刻 modules.json 完整快照
  "module_status": { ... },     // 冻结时刻 module_status.json 完整快照
  "metadata": {}
}
```

**为何同时冻结配置层与状态层**:历史周回看必须用"当时的模块结构"渲染,否则后续删/改模块会让历史回看错乱。

## 6. 冻结时机

### 6.1 自动冻结

- 默认时间:每周五 18:00(实例时区固定 Asia/Shanghai = `CN_TZ`,UTC+8)
- 由后端 FastAPI lifespan 启动的后台 `asyncio.Task` 每 60s 巡检触发,`frozen_by="system:auto"`,`trigger="auto"`
- 若该周已存在快照,**不覆盖**,跳过(避免重复)
- **可配置**:`DATA_DIR/config.json` 的 `auto_freeze` 子对象:
  ```jsonc
  {
    "auto_freeze": {
      "enabled": false,    // 默认关闭,需 Super 显式启用
      "weekday": 4,        // 0=周一 .. 6=周日(Python ISO);4=周五
      "hour": 18,          // 0..23,实例时区
      "minute": 0          // 0..59
    }
  }
  ```
- **运维开关**:环境变量 `PMD_DISABLE_SCHEDULER=1` 完全跳过启动调度器(供测试 / 维护用)
- **端点**:`GET /api/config/auto_freeze` 任意已登录角色可读,返回当前配置 + 计算出的 `next_run_at`;`PUT /api/config/auto_freeze` 仅 Super,支持部分字段更新,422 校验范围

### 6.2 手动冻结

- `POST /api/snapshots/freeze` 由 Super / PDT Admin 触发
- 若该周已存在快照:返 409;管理员可显式带 `?force=true` 覆盖(此操作记入审计日志)

### 6.3 冻结当周判定

- 自动 freeze 冻结"当前 ISO 周"
- 手动 freeze 默认冻结"当前 ISO 周";允许 `?week=2026-W20` 显式指定

## 7. 只读语义

- 冻结后的快照文件**只读**,不允许 in-place 修改
- "修正历史快照"= 删除该文件并重新 freeze(留下审计记录 `metadata.replaced_by` / `replaced_at`)
- 前端切换到历史周时:数据全部从快照拉取,Owner 的填报入口禁用,UI 显示"历史周(只读)"banner
- **前端 URL 协议**:`?week=YYYY-Www`(如 `?week=2026-W21`),格式校验在 `useView.parseView`;不合法的 week 参数会被忽略,等同于"当前周"
- 冻结成功后端发 SSE `snapshot:created`,`SnapshotPanel` 自动刷新表格,无需手动重载页面

## 8. 与历史流的关系

| 维度 | `module_updates.jsonl` | `weekly_snapshots/` |
|------|------------------------|---------------------|
| 粒度 | 单次填报事件 | 周粒度全量状态 |
| 修改性 | append-only | 冻结只读(可重 freeze) |
| 用途 | 模块详情时间线、审计 | 历史周回看、周对比 |
| 必需性 | 必需 | 必需 |

二者不可互相替代:历史流可重放出任意时刻状态,但代价高且没有"周对齐"语义;周快照不能给出周内细变化。

## 9. 执行约束

### 9.1 冻结流程

后端:

1. 取当前(或指定)ISO 周号 → 文件路径
2. 如已存在且非 force:409
3. 读 `pdt.json` / `ltcs.json` / `modules.json` / `module_status.json` 当前态
4. 组装快照对象,写 `weekly_snapshots/snapshot-YYYY-Www.json`(原子 rename)
5. 触发 SSE `snapshot:created` 让前端刷新可选周列表

### 9.2 读取

- `GET /api/snapshots` 返回快照元数据列表(week / frozen_at / frozen_by / trigger)
- `GET /api/snapshots/{week}` 返回完整快照
- 不提供 PUT/DELETE(管理员需删除时通过运维流程在 worktree 里手动 `rm` + commit;走审计)

### 9.3 校验

- `validate_data_files.py` 校验快照文件名与 `week` 字段一致、必填字段齐全、引用关系自洽

## 10. 禁止项

- **禁止 in-place 修改快照文件**
- **禁止用快照承担细粒度审计**(那是历史流的职责)
- **禁止前端在历史周下提交状态写**(后端也必须拦截:任何写端点在 `view=snapshot` 模式下返 403)
- **禁止跳过冻结直接 `cp module_status.json`**(必须经 API,保证 pdt/ltcs/modules 一同冻结)

## 11. 扩展方式

- 双周/月快照:新增 `monthly_snapshots/` + `biweekly_snapshots/`,与周快照并存
- 跨周对比:新增 `GET /api/snapshots/diff?from=2026-W20&to=2026-W21`,返回模块级 diff(后端计算,不入文件)
- 快照导出:新增 `GET /api/snapshots/{week}/export?format=pptx`(超出 v1)

## 12. 关联文档

- 当前态:`07`
- 历史流:`08`
- 后端 API:`11`
- 前端历史周切换:`13`
