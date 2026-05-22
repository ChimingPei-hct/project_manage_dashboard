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
- 顶层类型:**对象**,键为 `module.id`
- main 分支模板:`{}`

## 4. 完整字段定义

```jsonc
{
  "ltc-as33-mcu-bsw": {
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

### 5.1 键(`module.id`)

- 必须存在于 `modules.json` 的 `id` 集合
- `modules.json` 删除某模块时,本对象对应键同步删除

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

### 5.5 `risk_note`

- 字符串,长度 0–500
- **必填条件**(后端校验,违反返 422):
  - `module_color != "green"` 时必填
  - 任一 `sub_items_color[*] != "green"` 时必填
- 都为绿时可空

### 5.6 `updated_by`

- 必填,字符串,本次填报者 open_id

### 5.7 `updated_at`

- 必填,ISO 8601 with timezone,由后端写入(忽略客户端值,防伪)

### 5.8 `metadata`

- 自由 JSON 对象

## 6. 一致性不变量

- `module_status.json` 中键的集合 ⊆ `modules.json` 中 id 的集合
- `sub_items_color` 的键 ⊆ 对应 `modules[id].sub_items[].id` 集合
- `kpi_values` 的键 ⊆ 对应 `modules[id].kpi_fields[].key` 集合
- 任意 entry 的存在都对应至少一行 `module_updates.jsonl` 历史记录(后端写入保证)

## 7. 执行约束

### 7.1 写当前态(`PUT /api/status/{module_id}`)

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
