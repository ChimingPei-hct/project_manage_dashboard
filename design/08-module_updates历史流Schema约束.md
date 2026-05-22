# module_updates 历史流 Schema 约束

## 1. 模块目标

定义 `module_updates.jsonl`(历史层)的字段、不可篡改性、与当前态的强一致关系。这是状态变更的"细粒度时间线"。

## 2. 边界

### 管什么

- `module_updates.jsonl` 每行的字段定义
- append-only 不可改写规则
- 与 `module_status.json` 的双写一致性

### 不管什么

- 当前态 → `07`
- 周快照 → `09`
- 配置变更历史(本约束只跟踪状态变更,不跟踪配置变更;后者由 `metadata` 与 git 历史承担)

## 3. 文件格式

- 路径:`DATA_DIR/module_updates.jsonl`
- 类型:**JSONL**,每行一个 JSON 对象,UTF-8 无 BOM,行尾 `\n`
- main 分支模板:空文件
- **append-only**

## 4. 完整字段定义

```jsonc
{
  "id": "upd-01HZX...",                 // 必填,ULID 或 UUIDv7,后端生成
  "ts": "2026-05-22T15:30:00+08:00",    // 必填,后端写入
  "module_id": "ltc-as33-mcu-bsw",      // 必填
  "kind": "status_update",              // 必填,枚举
  "before": { ... },                    // 旧 entry(完整 module_status entry),首次填报为 null
  "after": { ... },                     // 新 entry(完整 module_status entry),"deleted" 时为 null
  "updated_by": "ou_xxxxxx",            // 必填
  "client": "web",                      // 可空,来源标识
  "metadata": {}
}
```

## 5. `kind` 枚举

| 值 | 触发 | before / after |
|----|------|---------------|
| `status_update` | Owner 填报模块状态 | before=旧 entry(或 null), after=新 entry |
| `module_deleted` | 模块被删除 | before=旧 entry, after=null |
| `bulk_import` | 管理员批量导入(预留) | before=null, after=新 entry |
| `migration` | 后端迁移脚本自动产生(预留) | 视情况 |

v1 强制支持 `status_update` 与 `module_deleted`。

## 6. 字段规则

### 6.1 `id`

- 必填,ULID(优先)或 UUIDv7,后端生成
- 全局唯一
- 用于幂等校验与定位

### 6.2 `ts`

- 必填,ISO 8601 with timezone
- 后端写入,忽略客户端值

### 6.3 `module_id`

- 必填;允许指向已删除的模块(历史不可消失)

### 6.4 `before` / `after`

- 类型与 `module_status` 单 entry 一致(见 `07` 第 4 节)
- 至少其中一个非 `null`
- 首次填报:`before=null, after=新`
- 删除模块:`before=旧, after=null`

### 6.5 `updated_by`

- 必填,open_id

### 6.6 `client`

- 可空,字符串:`"web"` / `"cli"` / `"migration"` / `"api"`

### 6.7 `metadata`

- 自由 JSON 对象

## 7. 一致性不变量

- `module_status.json` 中任一 entry 的"最后一次状态" = `module_updates.jsonl` 中匹配 `module_id` 的最近一行(按 `ts`)的 `after`
- 同 `module_id` 的相邻两行,前一行的 `after` 应等于后一行的 `before`(允许 `bulk_import` 例外)
- 任意行的 `module_id` 必须有对应历史(不存在则可能是配置层先删除,此时下一条记录的 `kind=module_deleted` 且 `after=null`)

## 8. 执行约束

### 8.1 写历史流

- 必须在 `module_status.json` 覆写**之前或之后**的同事务内追加(不可独立)
- 失败时整体回滚:不能写了历史但 status 未更新,反之亦然
- 文件锁:`fcntl.flock` 串行化追加

### 8.2 读历史流

- 按 `ts` 升序读;前端"模块详情"页倒序展示
- 提供 `GET /api/status/history?module_id=...&limit=...&before_ts=...` 分页接口

### 8.3 校验

- `validate_data_files.py` 校验:每行合法 JSON、必填字段齐全、`ts` 单调不减(允许同时刻并列)、与 `module_status.json` 一致性

## 9. 禁止项

- **禁止 in-place 修改任意已写行**(包括"修正错别字"也不行;如要纠错,追加一行 `kind=migration` 说明)
- **禁止删除任意已写行**(包括"清理历史";如需归档,见扩展方式)
- **禁止跳过历史写当前态**(双写不可分割)
- **禁止把当前态 entry 整段塞进 metadata**(`before`/`after` 已是完整 entry)

## 10. 扩展方式

- 历史归档:文件超大时按月切分到 `module_updates/2026-05.jsonl`,主文件保留近 N 月;读 API 透明合并
- 评论与讨论:不进本流;另起 `module_comments.jsonl`
- 字段级 diff:在 `metadata` 里存 `changed_fields: [...]`,前端可高亮变化字段

## 11. 关联文档

- 当前态:`07-module_status当前态Schema约束.md`
- 周快照:`09-周快照Schema与冻结规则.md`
- 后端事务:`11-后端API约束.md`
- 校验:`design/validate_data_files.py`
