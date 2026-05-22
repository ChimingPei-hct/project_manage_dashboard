# design/ — 约束文档目录

## 进入前必读

`01-设计文档编写约束.md` — 所有文档的上位规则,定义文档编写方式和结构要求。**修改任何 module 文档前必须先读此文件。**

## 文档层次

| 编号 | 文件 | 职责 |
|------|------|------|
| 01 | 设计文档编写约束 | 文档编写元规则,harness 模板 |
| 02 | 项目看板系统全局设计大纲 | 系统全局架构、PDT/LTC 概念、推进顺序、v1 完成标准 |
| 03 | 代码与数据分离约束 | main/数据分支拆分、worktree、DATA_DIR、空模板规则 |
| 04 | PDT 与 LTC 管理规范 | 命名、生命周期、动态配置原则、单 PDT 多 LTC 模型 |
| 05 | 模块与状态模型基础规则 | module 统一模型、状态/历史/快照三层分离、颜色语义 |
| 06 | modules 配置 Schema 约束 | `modules.json` 字段定义 |
| 07 | module_status 当前态 Schema 约束 | `module_status.json` 字段定义 |
| 08 | module_updates 历史流 Schema 约束 | `module_updates.jsonl` 字段定义 |
| 09 | 周快照 Schema 与冻结规则 | `weekly_snapshots/` 命名、冻结时机、只读语义 |
| 10 | 权限与角色约束 | Super/PDT/LTC/Owner/访客 五角色、权限矩阵 |
| 11 | 后端 API 约束 | FastAPI endpoint 命名、错误返回、SSE、Cookie |
| 12 | 前端实现约束 | Vue 3 自研 UI、6px 圆角、tooltip、composables |
| 13 | 页面编辑与展示约束 | 四类页面编辑入口与展示主信息 |
| 14 | AI 边界与系统演进约束 | AI 修改边界、数据迁移、未来扩展 |

## 写入规则

- 修改任何 module 文档前,先读 `01` 确认编写约束
- 修改系统边界相关内容,同步更新 `02`
- 讨论未收敛的内容不得写入正式区域,用 `TBD` 标记
- 新增 module 文档必须遵守 `01` 的统一模板,并在本表登记

## 活数据文件(main 分支保持空模板,实例数据走 data 分支)

| 文件 | main 模板 | 用途 |
|------|----------|------|
| `pdt.json` | `{}` | PDT 当前信息(单对象) |
| `ltcs.json` | `[]` | LTC 列表 |
| `modules.json` | `[]` | 模块定义(配置) |
| `module_status.json` | `{}` | 模块状态当前态 |
| `module_updates.jsonl` | 空 | 模块状态历史流(append-only) |
| `weekly_snapshots/` | 空目录 | 周快照存档 |
| `super_admins.json` | `[]` | 超级管理员 |
| `pdt_admins.json` | `[]` | PDT 管理员 open_id 列表 |
| `ltc_admins.json` | `{}` | `{ltc_id: [open_id, ...]}` |
| `user_registry.json` | `[]` | 用户注册表 |
| `config.json` | 见 `03` | 部署配置(port、PDT 默认名等) |
| `contact_cache.json` | 共享 | 公司通讯录,各实例共享 |

完整规则见 `03-代码与数据分离约束.md`。

## 校验

- `validate_data_files.py` — 校验 JSON/JSONL 字段、格式与跨文件一致性

> 修改活数据时必须通过校验:`python3 design/validate_data_files.py`
