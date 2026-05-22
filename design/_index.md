# design

> 产品线项目看板系统(PMD)相关设计文档集中目录。

## 文件清单

| 文件 | 用途 |
|------|------|
| `01-设计文档编写约束.md` | `design/` 目录的统一编写规则与 harness 文档模板 |
| `02-项目看板系统全局设计大纲.md` | 全局任务列表、模块映射、v1 完成标准 |
| `03-代码与数据分离约束.md` | main/数据分支拆分、git worktree、空模板规则 |
| `04-PDT与LTC管理规范.md` | PDT/LTC 命名、生命周期、动态配置 |
| `05-模块与状态模型基础规则.md` | module 统一模型、状态/历史/快照三层分离、颜色语义 |
| `06-modules配置Schema约束.md` | `modules.json` 字段定义 |
| `07-module_status当前态Schema约束.md` | `module_status.json` 字段定义 |
| `08-module_updates历史流Schema约束.md` | `module_updates.jsonl` 字段定义 |
| `09-周快照Schema与冻结规则.md` | `weekly_snapshots/` 命名、冻结时机、只读语义 |
| `10-权限与角色约束.md` | Super/PDT/LTC/Owner/访客 五角色权限矩阵 |
| `11-后端API约束.md` | FastAPI endpoint 规范 |
| `12-前端实现约束.md` | Vue 3 组件与状态管理规范 |
| `13-页面编辑与展示约束.md` | 四类页面编辑入口与展示主信息 |
| `14-AI边界与系统演进约束.md` | AI 操作边界、数据迁移、未来扩展 |
| `pdt.json` 等 | 空模板数据文件(main 分支保持空,实例数据走 data 分支) |
| `validate_data_files.py` | 数据校验脚本(CLI 可调) |

## 使用建议

- 先看 `01-设计文档编写约束.md`,理解 `design/` 文档应该怎么写
- 再看 `02-项目看板系统全局设计大纲.md`,理解全局模块划分与当前推进状态
- 再看 `03-代码与数据分离约束.md`,理解部署模型与 main/data 分支的边界
- 再看 `04` 和 `05`,理解 PDT/LTC/模块/状态的概念与基础规则
- 最后按需进入各 module 正式约束文档:
  - 关注数据 Schema → `06` / `07` / `08` / `09`
  - 关注权限与 API → `10` / `11`
  - 关注页面与组件 → `12` / `13`
  - 关注 AI 与演进 → `14`
