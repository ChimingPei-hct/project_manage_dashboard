# PDT 与 LTC 管理规范

## 1. 模块目标

定义 PDT、LTC 这两个核心业务对象的命名、生命周期、动态配置规则,确保:

- 同一实例下 PDT、LTC 的标识稳定可引用
- 增删 LTC、改名、归档不会破坏历史数据与已有引用
- 名称与显示文本可在线编辑,不写死在代码或前端

## 2. 边界与职责

### 管什么

- PDT 单对象的字段与生命周期
- LTC 列表的字段、命名、排序、归档
- 里程碑(milestones)的归属与字段
- 配置变更对下游(modules / status / snapshots)的影响

### 不管什么

- 模块定义本身(归 `05` / `06`)
- 模块状态(归 `07` / `08`)
- 权限(归 `10`)

## 3. 核心对象

### 3.1 PDT(`pdt.json`,单对象)

```jsonc
{
  "code": "Luna6",                 // 稳定标识,初始化后不变;UI 中不单独编辑
  "name": "Luna6",                 // 显示名;UI 唯一可编辑入口,保存时同步写入 code
  "description": "...",
  "icon": "assets/luna-6/icon.svg",// 可选;相对 DATA_DIR 的图标路径,前端走 /assets/<path> 静态服务取得
  "milestones": [
    { "name": "TR4-2", "date": "2026-05-12", "type": "TR", "note": "..." },
    { "name": "A 点 SOP", "date": "2026-07-15", "type": "SOP", "note": "" }
  ],
  "updated_at": "2026-05-22T10:00:00+08:00",
  "metadata": {}
}
```

### 3.2 LTC(`ltcs.json`,数组)

```jsonc
[
  {
    "id": "as33",                  // 稳定标识,初始化后不变
    "name": "上汽 AS33",            // 显示名,可改
    "order": 1,
    "archived": false,
    "milestones": [                // LTC 自有里程碑,与 pdt.milestones 完全解耦
      { "name": "AS33 PV 启动", "date": "2026-04-10", "type": "TR", "note": "" },
      { "name": "AS33 SOP", "date": "2026-09-01", "type": "SOP", "note": "" }
    ],
    "created_at": "2026-05-22T...",
    "updated_at": "2026-05-22T...",
    "metadata": {}
  }
]
```

## 4. 结构规则

### 4.1 标识(`code` / `id`)

- 一次创建终身不变,**严禁修改**
- 命名规则:小写字母 + 数字 + 短横线,长度 2–32(正则 `^[a-z][a-z0-9-]{1,31}$`)
- 不允许重复
- 所有下游引用(modules、status 等)用此标识,不用 name

### 4.1.x PDT 图标(`icon`)

- 单实例级元数据,**不与代码耦合**;每个 PDT 实例上传自己的图标,顶栏 brand / 浏览器 favicon / `document.title` 一并生效
- 存储:`design/assets/<pdt-code>/icon.svg`(或 `.png`),`pdt.json` 存相对路径 `"assets/<pdt-code>/icon.svg"`
- 文件类型白名单:`.svg` / `.png`(其余拒收);单文件 ≤ 256KB
- 编辑入口:顶栏齿轮 `PdtConfigDrawer` Tab「PDT 信息」(详见 `13 §6.0`);Super / PDT Admin / LTC Admin 可上传与清除
- 缺省(`icon` 字段空或文件不存在)时:顶栏回退 `📊` emoji、favicon 走浏览器默认、`document.title` 仍同步 `pdt.name`
- 前端不允许在代码中硬编码具体实例图标;新增 PDT 实例直接通过 UI 上传

### 4.2 显示名(`name`)

- LTC `name`:任意 Unicode 字符串,长度 1–80;允许在线编辑,变更不影响下游引用
- PDT `name`:UI 上是 PDT 配置抽屉唯一可编辑的标识字段,**与 `code` 同值**(保存时由前端同步写入),约束 `^[A-Za-z0-9_\-一-龥]+$`,不允许空格/特殊字符
  - 即:PDT 不再单独暴露 `code` 编辑入口;`code` 仍是底层稳定标识,初始化后不应再变(若必须改名仍走"删后重建"路径)

### 4.3 里程碑

- **归属规则**:`pdt.milestones` 与 `ltcs[*].milestones` **完全解耦**,各自独立维护
  - PDT 里程碑:产品线级关键节点(如 TR4-2、A 点 SOP),在 PDT 总览页时间轴展示
  - LTC 里程碑:子项目自有节点(如该 LTC 的 PV/SOP/OTA),仅在该 LTC 主页面时间轴展示
  - **不存在隐式继承或叠加显示**;若同一节点对两层都重要,需在两处分别录入
- 字段:`name`(必填,字符串)、`date`(必填,ISO 日期 `YYYY-MM-DD`)、`type`(自由字符串,推荐使用约定值)、`note`(可空)
- `type` 约定值(前端按此映射形状/颜色,未列值降级为灰色圆点):
  - `TR` 蓝色三角 △ · `SOP` 红色菱形 ◇ · `OTA` 紫色三角 △
  - `review` 青色五角星 ☆ · `goal` 橙色实心星 ★ · `Block` 黄色实心方块 ■
  - 新增类型时同步更新 `frontend/src/components/TimelineBar.vue::TYPE_STYLE` 与本表
- 按 `date` 升序展示
- 同一作用域(PDT 或某 LTC)下,(`name`+`date`)组合应唯一

### 4.4 归档(`archived`)

- `archived=true` 的 LTC:
  - 默认不在前端总览/进展页可见(管理员可切换显示)
  - 已有 module / status / snapshot 数据保留,不删除
  - 仍计入历史快照
- 不允许删除有数据关联的 LTC,只能归档

### 4.5 排序(`order`)

- 整数,前端按升序展示
- 管理员可拖拽改序

## 5. 执行约束

### 5.1 创建 LTC

- 必填:`id`、`name`
- 默认 `archived=false`、`order=max(existing.order)+1`
- 创建后自动写入 `created_at`、`updated_at`

### 5.2 修改 LTC

- 可改:`name`、`order`、`archived`、`milestones`、`metadata`
- 不可改:`id`、`created_at`
- 改任意字段都必须刷新 `updated_at`
- 增删/调整 `milestones` 视为 LTC 更新,刷新 `ltcs[i].updated_at`;不冻结快照

### 5.3 删除 LTC

- 仅允许删除"无任何关联 modules"的 LTC(校验 `modules.json` 中没有 `ltc_id == 该 id` 的记录)
- 有数据的 LTC 只能归档

### 5.4 修改里程碑

- 增删/调整里程碑视为 PDT 更新,刷新 `pdt.updated_at`
- 里程碑变更**不冻结**已有快照(快照只看状态,不看里程碑)

### 5.5 LTC 配置初始化(从模板拷贝)

- **模板池编辑入口**:顶栏齿轮 → `PdtConfigDrawer` → Tab「LTC 模板」(`LtcTemplateEditor`)。单一模板池(全 PDT 共享一套),字段仅 name / order / group;`sub_items` / `kpi_fields` / `owner_open_id` 不在模板里维护(详见 `13 §6.0`)
- LTC 创建后,可通过 `POST /api/ltc/{ltc_id}/init-from-template`(权限:Super / PDT Admin / 该 LTC Admin)将「模板池」(`categories.json` / `modules.json` 中 `scope=ltc_template` 的全量记录)**深拷贝**为本 LTC 的 `scope=ltc` 副本
- 拷贝语义:
  - **快照式**:模板与副本完全解耦,模板后续修改**不下推**已初始化的 LTC;副本删改也不影响模板
  - **不存反向指针**:副本不写 `template_id`,避免造成"应同步"的错觉
  - **新 ID**:`<原模板 id>--<ltc_id>`,所有 module 的 `category_id` 同步重写到新 category id
  - **重置元数据**:`created_at` / `updated_at` 取当前时间,`owner_open_id` 沿用模板(模板本身应不带 Owner)
- 前置检查:本 LTC 已存在任意 `scope=ltc` category 或 module → 409(不做合并/增量同步);如需重置,先手动清空再调用
- **LTC 主页前端只渲染 `scope=ltc & ltc_id=本LTC` 的副本**(`useDashboard.ltcVisibleModules`);**严禁**把 `scope=ltc_template` 的模板模块虚拟混入 LTC 视图,否则会出现"模板模块挂不上本 LTC 大类 → 全部塌到未分类"的视觉异常
- 历史(在本约束生效前手工建出的)LTC 若未初始化,主页将为空 → 必须手动调 `init-from-template` 补齐;裸建(无大类副本)的 LTC 视为数据异常
- 不在范围:模板版本号 / 副本与模板的 diff 视图 / LTC 重置端点 → 后续按需扩展

## 6. 禁止项

- **禁止改 `code` 或 `id`** — 即使是初始化阶段的"重命名",也应删后重建并清理引用
- **禁止用 `name` 作为外键** — 一律用 `code` / `id`
- **禁止直接 `rm` 有数据的 LTC** — 必须走归档
- **禁止跳过 `validate_data_files.py` 校验保存**

## 7. 扩展方式

- 多 PDT 聚合视图:超出单实例范围,不在本约束内
- LTC 子分组(如按车厂/平台分组):新增可选字段 `group`,默认 `null`,前端按 group 折叠展示
- 里程碑分层展示(如 LTC 时间轴上叠加 PDT 基线):未来如需 cross-scope 叠加显示,需新增独立约束章节,本版本明确**不支持**

## 8. 关联文档

- 上位:`02-项目看板系统全局设计大纲.md`
- 下游:`05-模块与状态模型基础规则.md`、`06-modules配置Schema约束.md`
- 数据隔离:`03-代码与数据分离约束.md`
