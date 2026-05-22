# modules 配置 Schema 约束

## 1. 模块目标

定义 `modules.json`(配置层)的字段、约束、不变量。这是看板"骨架"的稳定结构。

## 2. 边界

### 管什么

- `modules.json` 的字段定义
- 增删改的合法性规则
- 与 `ltcs.json`、`module_status.json`、`module_updates.jsonl` 的引用关系

### 不管什么

- 状态字段 → `07`
- 历史流 → `08`
- 谁能改 → `10`

## 3. 文件格式

- 路径:`DATA_DIR/modules.json`
- 顶层类型:**数组**
- main 分支模板:`[]`

## 4. 完整字段定义

```jsonc
{
  "id": "ltc-as33-mcu-bsw",          // 必填,稳定标识
  "scope": "ltc",                     // 必填,枚举:"pdt" | "ltc"
  "ltc_id": "as33",                   // scope=ltc 必填且引用 ltcs[].id;scope=pdt 必须为 null
  "group": "硬件和底软",                // 必填,分组名(字符串)
  "name": "MCU 底软",                   // 必填,显示名
  "order": 1,                         // 必填,整数,同 group 内排序
  "owner_open_id": "ou_xxxxxx",       // 可空(未指派)
  "kpi_fields": [                     // 可空数组,PDT 级常用
    { "key": "miles", "label": "自动驾驶里程", "hint": "全口径累计" }
  ],
  "sub_items": [                      // 可空数组,LTC 级常用
    { "id": "autosar-bsw", "name": "Autosar BSW", "order": 1 },
    { "id": "rte", "name": "RTE", "order": 2 }
  ],
  "created_at": "2026-05-22T10:00:00+08:00",
  "updated_at": "2026-05-22T10:00:00+08:00",
  "metadata": {}
}
```

## 5. 字段规则

### 5.1 `id`

- 必填,字符串,正则 `^[a-z][a-z0-9-]{1,63}$`
- 创建后不可改
- 全局唯一(跨 scope 唯一)
- 推荐命名:`<scope>-<ltc_id?>-<slug>`,例如 `pdt-quality`、`ltc-as33-perception`

### 5.2 `scope`

- 枚举 `"pdt"` 或 `"ltc"`,不可空,不可改

### 5.3 `ltc_id`

- `scope=ltc`:必填,且必须存在于 `ltcs.json` 的 `id` 集合中
- `scope=pdt`:必须为 `null`
- 创建后不可改(LTC 间不可"搬移"模块,如需变更:删除重建)

### 5.4 `group`

- 必填,字符串,长度 1–32
- 用于前端分组,同一 `(scope, ltc_id)` 下可有多个 group
- 允许中文
- 修改 group 视为重组,刷新 `updated_at`,但不删除状态

### 5.5 `name`

- 必填,字符串,长度 1–80
- 可以包含中文、空格

### 5.6 `order`

- 必填,整数;同 group 内排序
- 不要求连续,允许 `[1, 2, 5]`
- 拖拽改序时后端可批量更新

### 5.7 `owner_open_id`

- 可空,字符串
- 若非空,必须存在于 `user_registry.json` 或飞书联系人缓存
- 修改 owner = 修改"谁能改本模块的状态",写权限即时生效

### 5.8 `kpi_fields`

- 可空数组;空数组等价于无 KPI
- 每项:`{ key, label, hint? }`
  - `key`:正则 `^[a-z][a-z0-9_]{0,31}$`,同一模块内唯一
  - `label`:显示文本,1–40 字符
  - `hint`:可空,鼠标 hover 提示
- 删除 `kpi_fields[i]` 时,`module_status` 中对应 `kpi_values[key]` 同步删除

### 5.9 `sub_items`

- 可空数组;空数组等价于无子项
- 每项:`{ id, name, order }`
  - `id`:正则 `^[a-z][a-z0-9-]{0,63}$`,**模块内**唯一
  - `name`:1–40 字符
  - `order`:整数
- 删除 `sub_items[i]` 时,`module_status` 中对应 `sub_items_color[id]` 同步删除
- `kpi_fields` 与 `sub_items` 可同时存在,但 v1 UI 默认不显示同模块的二者并存(只展示更"主导"的一种)

### 5.10 `metadata`

- 自由 JSON 对象,后端不解析,只透传
- 用于前端实验性字段、未纳入正式 Schema 的扩展

## 6. 引用一致性

- `ltc_id` → 必须在 `ltcs.json` 中存在
- `owner_open_id` → 推荐在 `user_registry.json` 中存在(校验时 warning,不阻断)
- 删除 LTC 时:必须先删除/迁移所有 `ltc_id == 该 LTC` 的模块(归档 LTC 不强制)
- 校验脚本 `validate_data_files.py` 必须覆盖上述引用一致性

## 7. 执行约束

### 7.1 创建模块

- 必填:`id`、`scope`、`group`、`name`
- 默认:`order=同 group 最大 order + 1`、`owner_open_id=null`、`kpi_fields=[]`、`sub_items=[]`、`metadata={}`
- 自动写入 `created_at`、`updated_at`

### 7.2 修改模块

- 可改:`group`、`name`、`order`、`owner_open_id`、`kpi_fields`、`sub_items`、`metadata`
- 不可改:`id`、`scope`、`ltc_id`、`created_at`
- 任何修改刷新 `updated_at`

### 7.3 删除模块

- 必须连带删除 `module_status[id]`
- `module_updates.jsonl` 历史保留(append-only 不可删)
- 已有 snapshot 保留

## 8. 禁止项

- **禁止改 `id` / `scope` / `ltc_id`**
- **禁止跨 scope 复用同一 id**
- **禁止 owner_open_id 写成人名/邮箱**(必须 open_id;显示名走 `user_registry`)
- **禁止同一模块的 `sub_items[].id` 重复**

## 9. 扩展方式

- 跨 LTC 横切模块:新增 `scope="shared"` 配合 `ltc_ids: []`
- 模块层级嵌套(模块下挂子模块而非子项):升级本文件,定义 `parent_id` 字段

## 10. 关联文档

- 基础概念:`05-模块与状态模型基础规则.md`
- 状态:`07-module_status当前态Schema约束.md`
- 历史:`08-module_updates历史流Schema约束.md`
- PDT/LTC:`04-PDT与LTC管理规范.md`
- 校验:`design/validate_data_files.py`
