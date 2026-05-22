# 后端 API 约束

## 1. 模块目标

定义后端 FastAPI 实现的稳定接口契约、文件读写规范、认证模型、事件广播,确保前端可基于本约束独立开发。

## 2. 边界

### 管什么

- 技术栈与目录约束
- 数据 I/O 模式(文件锁、原子 rename、事务式双写)
- 认证(飞书 OAuth + JWT Cookie + Dev 后门)
- API 路由命名规则、错误返回、SSE
- 启动方式与环境变量

### 不管什么

- 字段语义 → `06`–`09`
- 权限矩阵 → `10`
- 前端实现 → `12`

## 3. 技术栈

- Python 3.11+
- FastAPI ≥ 0.115
- Uvicorn(--reload 仅 dev)
- PyJWT(JWT 签发与校验)
- lark-oapi(可选,飞书通讯录)
- pytest + httpx(测试)

## 4. 目录布局

```
app/backend/
├── main.py              # 单文件入口(认证 + 路由 + 数据 I/O)
├── requirements.txt
├── start-instance.sh    # 多实例启动
├── tests/
│   ├── conftest.py
│   └── test_role_matrix.py
└── .venv/               # gitignore
```

**单文件原则**:v1 不拆模块,所有路由与中间件集中在 `main.py`,便于全局观察与重构。超过 ~6000 行再考虑拆分(对齐 oversea_projects 经验)。

## 5. 数据 I/O 规范

### 5.1 路径解析

- 所有数据文件读写路径 = `Path(os.environ["DATA_DIR"]) / "<file>"`
- 未设 `DATA_DIR`:仅 dev 环境回退到仓库内 `./design`;生产启动脚本必须显式注入

### 5.2 文件锁与原子写

复用 oversea_projects 模式(参见 `oversea_projects/app/backend/main.py:550-592`):

- 跨进程互斥:`fcntl.flock(LOCK_FD, fcntl.LOCK_EX)`,每类文件一把锁(`_pdt_lock`、`_modules_lock`、`_status_lock`、`_updates_lock`、`_snapshots_lock`)
- 原子覆写:写到 `<file>.tmp` → `os.fsync` → `os.replace(<file>.tmp, <file>)`
- JSONL 追加:`open(..., "a")` + flock

### 5.3 双写事务(status + updates)

任意 `PUT /api/status/{module_id}`:

```
with _status_lock, _updates_lock:
    status = read_status()
    before = status.get(module_id)
    after = build_after(...)
    validate(after)
    status[module_id] = after
    write_status_atomic(status)
    append_update(jsonl_line(before, after, ...))
broadcast_sse("status:reload")
```

任意中间失败 → 抛 HTTPException;不允许只写一头。

## 6. 认证

### 6.1 飞书 OAuth

**端点**

- `GET /api/feishu/login_url?redirect_uri=&state=` → `{ login_url, state }`,前端拿到后 `window.location.href` 过去。`redirect_uri` 缺省走 `FEISHU_REDIRECT_URI` 环境变量,再缺省 `http://localhost:15173/feishu/callback`
- `POST /api/feishu/callback`,body `{ code }` → 服务端依次:
  1. `POST /open-apis/auth/v3/app_access_token/internal` 拿 `app_access_token`
  2. `POST /open-apis/authen/v1/oidc/access_token` 用 code + app_token 换 `user_access_token`
  3. `GET /open-apis/authen/v1/user_info` 拿 `{ open_id, name, avatar_url, tenant_key }`
  4. 校验 `tenant_key ∈ allowed_tenant_keys`(配置见 `design/03 §4.2`;允许空 = 暂不限制)
  5. upsert `user_registry.json`(open_id 为主键,name/avatar_url/last_login 覆盖)
  6. 签 JWT 写 cookie
- 端点未配凭证(无 `FEISHU_APP_ID/SECRET`)→ 501 `{ code: "feishu_disabled" }`
- 上游飞书错误 → 502 `{ code: "feishu_upstream" }`
- 租户不在白名单 → 403 `{ code: "tenant_forbidden" }`

**JWT 与 Cookie**

- JWT payload:`{ open_id, name, avatar_url, iat, exp }`,**不存角色**
- 有效期 30 天;剩余 < 7 天自动续期(在 `auth_middleware` 出口判定)

**凭证环境变量**

- 主名:`FEISHU_APP_ID` / `FEISHU_APP_SECRET`
- 回退名:`LARK_APP_ID` / `LARK_APP_SECRET`(便于复用 lark-cli 现有应用,详见 `系统/飞书app申请清单.md`)
- Secret 严禁写入 `config.json` 或代码

**`/api/auth/me` 字段补充**

返回字段含 `feishu_configured: bool`,前端据此决定是否展示"飞书登录"按钮(配置缺失则走 dev 后门)。

### 6.2 Cookie

- 名:`pmd_token_<port>`(多实例端口隔离)
- `HttpOnly` + `Secure`(生产) + `SameSite=Lax`
- 路径 `/`,Domain 不显式设(留浏览器默认)

### 6.3 AuthMiddleware

- 拦截所有 `/api/*`
- 白名单:`/api/feishu/*`、`/api/health`
- 未携带或无效 cookie → 401(`{"detail": "unauthenticated"}`)
- 携带 cookie 时,把 `request.state.open_id` 注入

### 6.4 Dev 后门

- 触发:`DEV_LOGIN=1` 且客户端 IP ∈ `127.0.0.1` / `::1`
- 行为:无 cookie 时自动注入 `dev_admin`(open_id `ou_dev_admin`),角色判定中 `is_super("ou_dev_admin")` 返回 True
- 生产部署不通过 `start-instance.sh` 注入 `DEV_LOGIN`,且 IP 校验兜底
- `super_admins.json` **不**因 dev 后门被污染(动态 patch 在代码里)

## 7. API 命名规则

- 所有业务端点前缀 `/api/`
- 资源用复数(`/api/ltcs`、`/api/modules`)
- 单资源带 id(`/api/ltcs/{id}`)
- 动作语义不适合 REST 的用动词(`/api/snapshots/freeze`)
- 查询参数走 query string,不在 path 里塞

## 8. 端点清单(v1)

```
# 健康/认证
GET    /api/health
GET    /api/feishu/login_url
POST   /api/feishu/callback
POST   /api/auth/logout
GET    /api/auth/me

# PDT
GET    /api/pdt
PUT    /api/pdt

# LTC
GET    /api/ltcs                          # ?include_archived=true 可选
POST   /api/ltcs
PUT    /api/ltcs/{id}
DELETE /api/ltcs/{id}

# Module
GET    /api/modules                       # ?scope=&ltc_id=
POST   /api/modules
PUT    /api/modules/{id}
DELETE /api/modules/{id}

# 状态
GET    /api/status                        # 全量当前态
PUT    /api/status/{module_id}            # 当前态 + 历史流双写
GET    /api/status/history                # ?module_id=&limit=&before_ts=

# 快照
GET    /api/snapshots                     # 列表 (元数据)
GET    /api/snapshots/{week}              # ?week=2026-W21 详情
POST   /api/snapshots/freeze              # body: {week?, force?}

# 自动冻结(后台 asyncio scheduler;design/09 §6.1)
GET    /api/config/auto_freeze            # 所有已登录角色可读;返 {enabled, weekday, hour, minute, next_run_at}
PUT    /api/config/auto_freeze            # 仅 Super;支持部分字段更新;422 校验范围

# 用户与权限
GET    /api/users/search                  # ?q=&limit=  v1 数据源 user_registry.json,v2 接飞书 contact_cache
GET    /api/admins
PUT    /api/admins/{role}                 # role ∈ super | pdt | ltc

# Onboarding
POST   /api/seed/demo                     # 仅 Super,且仅空实例(ltcs+modules 都空);已有数据返 409

# SSE
GET    /api/events                        # text/event-stream
```

读端点默认所有登录用户可访问。写端点权限按 `10` 矩阵。

## 9. 错误返回

统一使用 FastAPI `HTTPException`:

| 状态 | 用法 |
|------|------|
| 400 | 请求格式错误(JSON 解析失败、字段类型不对) |
| 401 | 未登录 |
| 403 | 已登录但无权限(角色不足、历史周下写) |
| 404 | 资源不存在 |
| 409 | 冲突(快照已存在且未 force、id 重复) |
| 422 | 业务校验失败(风险说明必填、引用不存在) |
| 500 | 服务器内部错误(I/O 失败) |

响应体:`{"detail": "<message>", "code": "<machine_readable>", ...}`。`code` 字段约定值见 `app/backend/main.py` 注释。

## 10. SSE 事件

- 单一通道 `/api/events`(text/event-stream)
- 事件名:`status:reload` / `config:reload` / `snapshot:created`
- 数据:JSON,如 `{"module_id": "...", "ts": "..."}`
- 重连:前端 `sseBus.js` 指数退避;后端不维护客户端 session

## 11. 启动

### 11.1 dev

```bash
cd app && ./start.sh
# 实际:
DEV_LOGIN=1 DATA_DIR=$PWD/../design uvicorn main:app --reload --port 8000
```

### 11.2 生产多实例

```bash
DATA_DIR=/srv/pmd-instances/<name>/design \
FEISHU_APP_SECRET=xxx \
bash app/backend/start-instance.sh
```

`start-instance.sh` 读 `$DATA_DIR/config.json` 取 port,启动 uvicorn(无 --reload)。

## 12. 测试

- `tests/test_role_matrix.py`:对每个写端点 × 6 类身份(super / pdt_admin / ltc_admin_of_this / ltc_admin_of_other / owner_of_this / guest)断言期望状态码
- `tests/conftest.py`:fixture 用临时 `DATA_DIR` 隔离测试数据
- 跑 `pytest -v`;pre-push hook 拦截红用例

## 13. 禁止项

- **禁止硬编码 `./design` 路径**(全部走 `DATA_DIR`)
- **禁止角色判定散落**(必须复用 `is_*` / `can_*` 函数,见 `10`)
- **禁止跨端点共享 mutable 全局变量**(用文件 + 锁,不用内存状态)
- **禁止跳过 flock 写文件**
- **禁止把 JWT secret 写入代码或 design/**(用 `.jwt_secret` 文件,gitignore)
- **禁止在端点里直接读 raw json 跳过校验函数**
- **禁止把 SSE 当 RPC 用**(只用于广播,客户端不应基于 SSE 做强一致同步)

## 14. 扩展方式

- 接 SQLite/Postgres:新增 `db.py`,把 `_read_/_write_` 函数换成 ORM/SQL;路径解析改 `DATABASE_URL`
- 鉴权改 OIDC/AD:新增 `auth_oidc.py`,中间件保持不变,只换签发逻辑
- 拆模块:`main.py` 超过 6000 行时按 `routes/`、`auth/`、`io/` 拆分

## 15. 关联文档

- 数据隔离:`03-代码与数据分离约束.md`
- Schema:`06`–`09`
- 权限矩阵:`10`
- 前端实现:`12`
- 启动脚本:`app/start.sh`、`app/backend/start-instance.sh`
