# PMD — 产品线项目看板系统(Project Manage Dashboard)

## 核心理念:设计与约束先行

本项目采用 **harness engineering** 方法论:`design/` 目录下的约束文档是代码的上位规则,代码实现必须与文档对齐。

### 强制工作流(任何代码修改前必须执行)

1. **查约束** — 确定本次修改涉及哪些模块,通过下方上下文路由表找到对应的 CLAUDE.md 和 `design/` 下的约束文档,完整阅读
2. **对齐检查** — 判断当前修改是否在已有约束的覆盖范围内。如果是,严格按约束实现;如果约束缺失或模糊,**先补充/澄清约束文档,再写代码**
3. **安全评估** — 基于约束文档思考:这个修改会破坏哪些已有契约?影响哪些上下游?有没有约束文档中明确禁止的做法?
4. **最小实现** — 在约束框架内用最简方式实现,不超出约束定义的边界
5. **回写设计** — 实现完成后,如果产生了新的设计决策、接口变更或行为约定,**立即更新对应的约束文档**,保持代码与文档双向同步

### 违规红线

- **禁止跳过第 1 步直接写代码** — 不查约束就动手 = 盲改
- **禁止代码与约束文档不一致** — 实现偏离约束必须先更新约束文档并说明原因,再改代码
- **禁止只改代码不更新设计** — 结构性变更(新增接口、修改数据模型、改变组件职责)必须同步更新约束文档
- **禁止在 main 分支写入实例数据** — `design/*.json` 在 main 上必须保持空模板;实例数据走 data 分支 worktree(详见 `design/03-代码与数据分离约束.md`)
- **禁止新增写端点不补角色矩阵测试** — 写操作端点 / 权限改动必须在 `app/backend/tests/test_role_matrix.py` 补"端点 × 角色"用例,跑 `role-test.sh` 全绿

## 工作纪律

### 踩坑驱动规则

犯过的错不能犯第二次。踩坑经验记录在 `系统/环境问题.md`。**衰减机制**:超过 3 个月未触发的规则可清理,保持文档精简。

### 批判性思维

- 对任何方案保持怀疑,先问"这能失败在哪里"
- 不盲从文档 — 文档本身有矛盾时,指出来
- 用事实和代码验证,不靠假设推进

### 信息输入三通道

所有信息输入(用户指令、外部数据、讨论结论)都必须同时评估三个落点:

1. **文档更新** — 是否需要更新 `design/` 或 `系统/` 下的 md 文档
2. **任务更新** — 是否需要更新现有任务的状态、优先级、备注
3. **任务新增** — 是否需要创建新任务

不允许只处理其中一个通道而遗漏其他。处理完后明确说明每个通道的处置结果(已更新 / 不涉及)。

### 灵光捕手

工作中发现的 insight、直觉、灵感立即记录到 `系统/灵光捕手.md`,不要求完整,重在不遗忘。

## 回复风格

- 精简直接,不废话
- 客观陈述,不用"我觉得"/"可能"等模糊表达
- 迭代意识:说清楚当前做了什么、下一步是什么
- 风险意识:涉及破坏性操作主动提醒

## 上下文路由

进入子目录前必读对应 CLAUDE.md:

| 目录 | CLAUDE.md | 核心约束 |
|------|-----------|----------|
| `design/` | `design/CLAUDE.md` | 文档编写与维护规则 |
| `app/` | `app/CLAUDE.md` | 代码↔文档对齐路由 |
| `app/backend/` | `app/backend/CLAUDE.md` | 后端技术栈与 API 约束 |
| `app/frontend/` | `app/frontend/CLAUDE.md` | 前端技术栈与组件约束 |

## 项目术语(全文统一)

| 术语 | 含义 |
|------|------|
| **PDT** | Product Development Team,**产品线**(如 Multicam Pilot 3.0)。一个部署实例只服务一个 PDT |
| **LTC** | Lead To Cash 子项目,PDT 下面的独立交付项目(如上汽 AS33) |
| **Module** | 模块,看板的基本组成单元。`scope=pdt` 表示 PDT 级总览卡片,`scope=ltc` 表示某 LTC 下的子模块 |
| **Sub-item** | LTC 模块下的子项色块(如"MCU 底软"模块下的 Autosar BSW、RTE 等) |
| **Owner** | 模块负责人,只能填报自己模块的状态 |

## 项目结构

```
project_manage_dashboard/
├── design/          # harness 约束文档 + 空模板数据(main 分支)
├── app/
│   ├── backend/     # FastAPI 单文件 main.py
│   └── frontend/    # Vue 3 + Vite
├── datas/           # 原始参考资料(PPT 截图等),不入产品
├── 系统/            # 全局进展、更新日志、环境问题、灵光捕手
└── start.sh
```

**当前进度的单一事实来源:`系统/全局进展.md`**。开始任何新阶段前必读;完成阶段后必须先更新它再 commit。

## 代码与数据分离

main 分支只存代码和**空模板数据**,不存任何实例真实数据。实例数据放在独立 data 分支,通过 git worktree 挂载。完整规则见 `design/03-代码与数据分离约束.md`。

## 开发命令

```bash
# 启动(前后端一起,dev 后门已启)
cd app && ./start.sh

# 后端测试
cd app/backend && source .venv/bin/activate && pytest -v

# 前端测试
cd app/frontend && npm run test

# 角色回归测试(后端权限矩阵 + 前端组件)
bash scripts/role-test.sh

# 数据校验
python3 design/validate_data_files.py
```

## 看板卡片解耦约束(harness 红线)

PDT 总览与 LTC 看板形态不同,**互相解耦**,各自一套实现:

- **PDT 卡片(scope=pdt 模块的看板/风险展示)**
  - 唯一实现:`app/frontend/src/components/ModuleCardGrid.vue`(卡片网格) + `ModuleRiskList.vue`(风险列表)
  - 仅在 `PdtOverview.vue` 中 import;PDT 总览页内卡片与风险共用同一组件
- **LTC 卡片(三级结构 Category → Module → Sub-item)**
  - 唯一实现:`app/frontend/src/components/ltc/LtcCategoryGrid.vue` + `LtcModuleCard.vue` + `SubItemEditDialog.vue` + `ModuleStatusDialog.vue`
  - 仅在 `LtcMain.vue` 中 import;LTC 内"看板"与"风险"**同卡两段**,由 `LtcModuleCard` 的 `showBoard`/`showRisk` props 按 `mode='board'|'risk'|'both'` 切换显隐(无独立风险卡)
- **严禁跨用**:LTC 页不得 import `ModuleCardGrid.vue`,PDT 页不得 import `LtcCategoryGrid.vue` 或 `LtcModuleCard.vue`
- 同一面板内(PDT 自身或 LTC 自身)看板与风险仍**共享单一组件**,差异通过 props/mode 表达;**不允许在外层页面内嵌写卡片 HTML/CSS**
- 新增看板类型(如未来 PMO 总览)必须明确选择复用现有组件或新建独立组件;**不允许新增第三套与 PDT/LTC 重复的实现**
- 违反 → PR 拒收

## UI 规范要点(详见 `design/12-前端实现约束.md`)

- **统一弧边矩形**(`border-radius: 6px`):按钮、状态色块、chip、徽章等一律 6px。**严禁**胶囊形(50% / 9999px / 与高度同量级的大圆角)
- **引导气泡**:新增有交互行为的 UI 元素必须同步加 hover 引导气泡(`v-tooltip="文案"`),文案动词开头说明"会发生什么"
- **状态色**:绿 `#52c41a` / 黄 `#faad14` / 红 `#f5222d`,严禁用其他色替代状态语义

## 本地测试 / 截图输出

- 所有 Playwright 截图、调试图片、临时 dump 一律落 `.cache/screenshots/`(已 gitignore)
- **严禁**在仓库根写 `*.png` / `*.log` / `screenshot-*` 等散落产物
- 临时脚本输出落 `.cache/`(根级,不分子目录)
- 主目录只保留入仓资产,杜绝"用完不清"的产物堆积

## 搜索排除

搜索代码时排除:`node_modules/`、`dist/`、`.venv/`、`__pycache__/`、`datas/`、`doc/`、`.cache/`
