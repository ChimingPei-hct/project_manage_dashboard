# PMD — 产品线项目看板系统

> Project Manage Dashboard,服务于单个 PDT(产品线)的项目交付看板系统。

一个部署实例只服务一个 PDT(Product Development Team),覆盖该产品线下多个 LTC(Lead To Cash)子项目的模块状态、周报、风险与里程碑展示。

---

## 核心概念

| 术语 | 含义 |
|------|------|
| **PDT** | 产品线(如 Multicam Pilot 3.0)。一个部署实例只服务一个 PDT |
| **LTC** | Lead To Cash 子项目,PDT 下面的独立交付项目(如上汽 AS33) |
| **Module** | 模块,看板基本单元。`scope=pdt` 为总览卡片,`scope=ltc` 为子模块 |
| **Sub-item** | LTC 模块下的子项色块(如 MCU 底软下的 Autosar BSW、RTE) |
| **Owner** | 模块负责人,只能填报自己模块的状态 |

权限角色:Super / PDT 管理员 / LTC 管理员 / Owner / 访客(详见 `design/10`)。

---

## 技术栈

- **后端**:FastAPI 单文件 `app/backend/main.py` + JSON 文件存储(文件锁原子写)+ SSE 推送
- **前端**:Vue 3 + Vite,自研 UI(无组件库),6px 统一圆角
- **认证**:飞书 OAuth(复用 lark-cli app),JWT cookie
- **数据**:`design/*.json`(空模板,main 分支)+ data 分支 worktree 承载实例数据

---

## 目录结构

```
project_manage_dashboard/
├── design/        # harness 约束文档(01–14)+ 空模板数据 + 校验脚本
├── app/
│   ├── backend/   # FastAPI 单文件 main.py + pytest
│   └── frontend/  # Vue 3 + Vite + vitest + Playwright
├── 系统/          # 全局进展、更新日志、环境问题、灵光捕手
├── datas/         # 原始参考资料(PPT 截图等),不入产品
├── icons/
├── start.sh
└── CLAUDE.md      # harness 工作流与上下文路由
```

---

## 快速开始

```bash
# 启动(前后端并行,dev 后门已开)
cd app && ./start.sh
# 后端 http://localhost:18080
# 前端 http://localhost:15173

# 关闭 dev 后门,走真实飞书登录
DEV_LOGIN=0 ./app/start.sh
```

需要先在飞书开放平台为 app `cli_a943bae284f89cd1` 添加重定向 URL `http://localhost:15173/feishu/callback`,并配置必要的 scope(详见 `系统/飞书app申请清单.md`)。

---

## 开发命令

```bash
# 后端测试
cd app/backend && source .venv/bin/activate && pytest -v

# 前端测试
cd app/frontend && npm run test

# 角色回归测试(后端权限矩阵 + 前端组件)
bash scripts/role-test.sh

# 数据校验
python3 design/validate_data_files.py
```

---

## 核心工作流(harness engineering)

本项目采用 **设计与约束先行** 方法论,`design/` 下的约束文档是代码的上位规则。

**任何代码修改前必须**:

1. **查约束** — 通过 `CLAUDE.md` 上下文路由表找到相关 `design/` 文档,完整阅读
2. **对齐检查** — 约束缺失或模糊时,先补充约束文档,再写代码
3. **安全评估** — 评估破坏哪些已有契约、影响哪些上下游
4. **最小实现** — 在约束框架内用最简方式实现
5. **回写设计** — 结构性变更必须同步更新约束文档

完整规则与红线见根目录 `CLAUDE.md`。

---

## 约束文档索引(design/)

| 编号 | 文件 | 职责 |
|------|------|------|
| 01 | 设计文档编写约束 | 文档编写元规则、harness 模板 |
| 02 | 项目看板系统全局设计大纲 | 系统全局架构、推进顺序、v1 完成标准 |
| 03 | 代码与数据分离约束 | main/data 分支拆分、worktree、空模板规则 |
| 04 | PDT 与 LTC 管理规范 | 命名、生命周期、动态配置原则 |
| 05 | 模块与状态模型基础规则 | module 统一模型、状态/历史/快照三层分离 |
| 06–09 | 数据 Schema 约束 | modules / module_status / module_updates / weekly_snapshots |
| 10 | 权限与角色约束 | 五角色权限矩阵 |
| 11 | 后端 API 约束 | FastAPI endpoint 规范、SSE、Cookie |
| 12 | 前端实现约束 | Vue 3 组件、6px 圆角、tooltip、composables |
| 13 | 页面编辑与展示约束 | 四类页面编辑入口与展示主信息 |
| 14 | AI 边界与系统演进约束 | AI 操作边界、数据迁移、未来扩展 |

---

## 红线约束(摘要)

- **禁止跳过约束直接写代码** — 不查 `design/` 就动手 = 盲改
- **禁止 main 分支写入实例数据** — `design/*.json` 在 main 上必须保持空模板,实例数据走 data 分支 worktree
- **禁止新增写端点不补角色矩阵测试** — 写操作 / 权限改动必须在 `app/backend/tests/test_role_matrix.py` 补端点 × 角色用例
- **看板卡片解耦** — PDT 卡片(`ModuleCardGrid`)与 LTC 卡片(`LtcCategoryGrid` 三级结构)互不 import,严禁跨用
- **统一弧边矩形**(`border-radius: 6px`)— 严禁胶囊形(50% / 9999px / 与高度同量级的大圆角)
- **状态色固定** — 绿 `#52c41a` / 黄 `#faad14` / 红 `#f5222d`,严禁用其他色替代状态语义
- **截图与临时产物落 `.cache/`** — 严禁在仓库根写 `*.png` / `*.log` 等散落产物

---

## 当前进度

单一事实来源:`系统/全局进展.md`。

截至 2026-05-25,Phase 0–13 全部完成(文档体系、骨架、管理后台 CRUD、飞书 OAuth、状态填报编辑、视觉打磨、周快照前端联动、定时快照、视觉验收 + 部署、数据模型升级、管理后台树+抽屉重构、前台视觉对齐、StatusEditDialog 新结构化弹窗、Playwright 截图回归)。

后端 75 测试 + 前端 11 测试全绿。

下一步:Phase 14 — 真实 Luna 6 实例数据落地(阻塞于用户完成飞书 app 重定向 URL + scope 核对)。

---

## 进一步阅读

- 根目录 `CLAUDE.md` — harness 工作流与上下文路由
- `design/CLAUDE.md` — 约束文档编写规则
- `app/CLAUDE.md` / `app/backend/CLAUDE.md` / `app/frontend/CLAUDE.md` — 代码↔文档对齐路由
- `系统/全局进展.md` — 当前阶段与下一步
- `系统/环境问题.md` — 踩坑记录
- `系统/灵光捕手.md` — 工作中的 insight 与灵感
