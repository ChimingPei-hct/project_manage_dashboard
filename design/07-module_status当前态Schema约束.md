# module_status 当前态 Schema 约束

## 1. 模块目标

定义 `module_status.json`(当前态层)的字段、约束、校验规则。这是"此刻每个模块的灯/KPI/风险说明"的权威载体,被频繁覆写。

## 2. 边界

### 管什么

- `module_status.json` 字段定义与校验
- 当前态与配置层、历史流的一致性约束

### 不管什么

- 模块结构 → `06`
- 历史流 → `08`
- 周快照 → `09`

## 3. 文件格式

- 路径:`DATA_DIR/module_status.json`
- 顶层类型:**对象**,键为 **status key**(定义见 §5.1)
- main 分支模板:`{}`

## 4. 完整字段定义

```jsonc
{
  // scope=pdt:key = module.id
  "pdt-quality": {
    "module_color": "green",
    "updated_by": "ou_xxxxxx",
    "updated_at": "2026-05-22T15:30:00+08:00",
    "metadata": {}
  },
  // scope=ltc:key = module.id
  "ltc-as33-bench": {
    "module_color": "yellow",
    "risk_note": "测试台架交付延期",
    "updated_by": "ou_xxxxxx",
    "updated_at": "2026-05-22T15:30:00+08:00",
    "metadata": {}
  },
  // scope=ltc_template:key = "<ltc_id>::<module.id>",每个 LTC 独立填报
  "as33::ltc-tpl-mcu-bsw": {
    "module_color": "yellow",                // 必填,枚举
    "sub_items_color": {                     // 可空对象;键须存在于 modules[id].sub_items[].id
      "autosar-bsw": "green",
      "rte": "yellow"
    },
    "kpi_values": {                          // 可空对象;键须存在于 modules[id].kpi_fields[].key
      "miles": "38%(目标 50%)"
    },
    "risk_note": "RTE 阻塞,等待供应商 5.16 提供新版本",  // 当存在非绿态时必填
    "updated_by": "ou_xxxxxx",
    "updated_at": "2026-05-22T15:30:00+08:00",
    "metadata": {}
  }
}
```

## 5. 字段规则

### 5.1 status key

按模块 `scope` 区分:

| 模块 scope | key 格式 | 示例 |
|-----------|---------|------|
| `pdt` | `module.id` | `pdt-quality` |
| `ltc` | `module.id` | `ltc-as33-bench` |
| `ltc_template` | `<ltc_id>::<module.id>`(分隔符固定为双冒号) | `as33::ltc-tpl-mcu-bsw` |

- 复合 key 中 `ltc_id` 必须存在于 `ltcs.json`,`module.id` 必须对应 `scope=ltc_template` 的模块
- 平铺 key 必须存在于 `modules.json`,且对应模块的 scope 不能是 `ltc_template`(否则视为非法 key)
- 删除模块 / 删除 LTC 时,本对象中所有命中的 key 同步删除(模板模块被删 → 所有 `<*>::<module_id>` 键清理;LTC 被删 → 所有 `<该 ltc_id>::<*>` 与 `ltc_id == 该 LTC` 的平铺键清理)
- API 路径中 key 须 URL-encode(`::` → `%3A%3A`),后端按 URL-decode 后解析

### 5.2 `module_color`

- 必填,枚举:`"green"` / `"yellow"` / `"red"`
- 严禁存色值

### 5.3 `sub_items_color`

- 可空对象;键 = `modules[id].sub_items[].id`
- 缺失的子项视为未填报(前端显示"灰底问号"或与 `module_color` 同色,详见 `13`)
- 任意值必须是 `"green"`/`"yellow"`/`"red"`

### 5.4 `kpi_values`

- 可空对象;键 = `modules[id].kpi_fields[].key`
- 值为字符串,长度 0–200
- 后端不解析,只透传

### 5.4b `kpi_items`(新结构化数组,优先于 `kpi_values`)

- 数组,元素为对象,字段:
  - `goal`(string,可空,**目标**描述,自由文本,示例 `"CPU 占用率 ≤70%"`)
  - `actual`(string,可空,**现状**描述,自由文本,示例 `"78%"`)
  - `color`(string,可空,枚举 `"green"`/`"yellow"`/`"red"` 或 `""`;**组级红绿灯**,挂在该组现状一侧,由 Owner/PDT Admin 在编辑弹窗下拉选择;为空表示未标灯)
- 写入语义:`goal` 与 `actual` 同时为空字符串的元素由后端 `_normalize_kpi_items()` 丢弃;其余只保留上述三字段
- 读侧兼容(过渡期):若元素含旧字段 `label/value` 而无 `goal/actual`,后端读时透明映射 `label→goal` / `value→actual`,`target` 字段一律丢弃。该兼容片段标注"过渡期",待 data 分支迁移完成后删除
- 前端 `useStatusHelpers.kpiItemsOf()` 返回项保证含 `goal/actual/color` 三字段(缺失字段回填 `""`),同时具备同一份读侧兼容映射

### 5.5 `risk_note`

- 字符串,长度 0–500
- **必填条件**(后端校验,违反返 422):
  - `module_color != "green"` 时必填
  - 任一 `sub_items_color[*] != "green"` 时必填
- 都为绿时可空
- **前端兜底校验位置**:`StatusEditDialog.vue` 的 `noteMissing` 计算属性 —— 弹窗内任一色变为非绿即在文本域下方红字提示且禁用「保存」按钮;不依赖 422 才提示。后端 422 仍然兜底,前端收到时 inline 显示 `payload.detail`

### 5.6 `updated_by`

- 必填,字符串,本次填报者 open_id

### 5.7 `updated_at`

- 必填,ISO 8601 with timezone,由后端写入(忽略客户端值,防伪)

### 5.8 `metadata`

- 自由 JSON 对象

## 6. 一致性不变量

- `module_status.json` 每个 key 都能按 §5.1 解析出唯一 `(ltc_id?, module_id)` 二元组,且引用都成立
- `sub_items_color` 的键 ⊆ 对应模块 `sub_items[].id` 集合(模板模块取定义本身)
- `kpi_values` 的键 ⊆ 对应模块 `kpi_fields[].key` 集合
- 任意 entry 的存在都对应至少一行 `module_updates.jsonl` 历史记录(后端写入保证)

## 7. 执行约束

### 7.1 写当前态(`PUT /api/status/{status_key}`)

`{status_key}` 即 §5.1 定义的 key(URL-encoded)。

后端必须**事务式**:

1. 读 `module_status.json`,获取旧 entry(或 `null`)
2. 校验颜色枚举、键引用、风险说明必填规则
3. 计算 `before` / `after`(用于历史流)
4. 覆写 `module_status.json`(原子 rename)
5. 追加 `module_updates.jsonl`(详见 `08`)
6. 广播 SSE `status:reload`

任意步骤失败 = 回滚,不允许只写一头。

### 7.2 删除模块时

- 同步删除 `module_status[id]`
- 写入历史流一行 `kind="deleted"` 记录(详见 `08`)

### 7.3 校验

- `validate_data_files.py` 必须检查上述一致性
- 任何写操作前后端都做校验,失败返 422

## 8. 禁止项

- **禁止前端直接 PATCH 单字段**(必须 PUT 全 entry,确保一致性)
- **禁止跳过历史流写入**
- **禁止 `risk_note` 在非绿态下为空**(后端拒绝)
- **禁止存储色值或额外颜色**

## 9. 扩展方式

- 增加颜色:先改 `05`,再改本文件;数据迁移要把存量值映射到新枚举
- 多字段并发编辑冲突:增加 `version` 字段做乐观锁;v1 不做,凭文件锁串行化

## 10. 关联文档

- 基础规则:`05-模块与状态模型基础规则.md`
- 配置 Schema:`06`
- 历史流 Schema:`08`
- 后端实现:`11`
