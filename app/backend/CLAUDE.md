# app/backend/ — 后端代码约束路由

## 进入前必读

- `design/11-后端API约束.md` — 技术栈、目录、I/O、认证、API、错误返回、SSE、启动
- `design/10-权限与角色约束.md` — 五类角色、写端点矩阵、`is_*` / `can_*` 判定函数
- `design/03-代码与数据分离约束.md` — `DATA_DIR` 注入、main/data 分支、空模板

## 单文件原则

v1 所有路由集中在 `main.py`。超过 ~6000 行再讨论拆分。

## 数据文件读写硬约束

- 所有路径走 `Path(os.environ["DATA_DIR"]) / "<file>"`,**严禁**硬编码 `./design`
- 写操作必须文件锁 + 原子 rename(`<file>.tmp` → `os.replace`)
- 状态写入必须**双写**(`module_status.json` + `module_updates.jsonl`)且事务式

## 新增写端点强制流程

1. 在 `design/10` 矩阵添一行,明确各角色 ✅/❌
2. 在 `tests/test_role_matrix.py` 加参数化用例(6 类身份 × 期望状态码)
3. 实现端点,复用 `is_*` / `can_*` 判定函数,不允许散落角色判定逻辑
4. 跑 `pytest -v`,矩阵全绿
5. 若改变了已有 API 契约,同步更新 `design/11`

## 测试

```bash
cd app/backend && source .venv/bin/activate && pytest -v
```

## 常见禁忌

- 跳过 `flock` 写文件
- JWT payload 里存角色(角色应实时查文件)
- 把 `FEISHU_APP_SECRET` 写进代码或 design/
- 在端点函数里直接读 raw JSON 跳过校验
- 把 SSE 用作 RPC(只用于广播事件)
