"""PMD 后端单文件入口。

约束对齐:
- design/11-后端API约束.md     技术栈、I/O、认证、API、错误返回、SSE、启动
- design/10-权限与角色约束.md   五角色、矩阵、is_* / can_* 判定
- design/03-代码与数据分离约束.md  DATA_DIR 注入、空模板、main/data 分支隔离
- design/05-09 数据模型 / Schema
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import urllib.parse

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse


# ---------------------------------------------------------------------------
# 配置与路径
# ---------------------------------------------------------------------------

CN_TZ = timezone(timedelta(hours=8))


def _resolve_data_dir() -> Path:
    """优先 DATA_DIR 环境变量;dev 场景回退到仓库内 design/。

    生产部署必须显式注入 DATA_DIR(见 03-代码与数据分离约束)。
    """
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env).resolve()
    # dev fallback:本文件位置 → app/backend/main.py
    here = Path(__file__).resolve()
    return (here.parent.parent.parent / "design").resolve()


DATA_DIR = _resolve_data_dir()
DEV_LOGIN = os.environ.get("DEV_LOGIN") == "1"
DEV_OPEN_ID = "ou_dev_admin"
DEV_NAME = "Dev Admin"

# JWT secret:本地文件持久化,首次启动自动生成;不入 git
_JWT_SECRET_FILE = Path(__file__).resolve().parent / ".jwt_secret"
if not _JWT_SECRET_FILE.exists():
    _JWT_SECRET_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
JWT_SECRET = _JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
JWT_ALG = "HS256"
JWT_TTL = timedelta(days=30)
JWT_RENEW_WINDOW = timedelta(days=7)

PORT = int(os.environ.get("PORT", "18080"))
COOKIE_NAME = f"pmd_token_{PORT}"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"

# 飞书 OAuth(design/11 §6.1)
# 优先读 FEISHU_*,回退 LARK_*(兼容复用 lark-cli 的现有 app 凭证)
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID") or os.environ.get("LARK_APP_ID") or ""
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET") or os.environ.get("LARK_APP_SECRET") or ""
FEISHU_OAUTH_DEFAULT_REDIRECT = os.environ.get(
    "FEISHU_REDIRECT_URI", "http://localhost:15173/feishu/callback"
)
_FEISHU_AUTHORIZE = "https://open.feishu.cn/open-apis/authen/v1/authorize"
_FEISHU_APP_TOKEN = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
_FEISHU_OIDC_ACCESS_TOKEN = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
_FEISHU_USER_INFO = "https://open.feishu.cn/open-apis/authen/v1/user_info"


# ---------------------------------------------------------------------------
# 文件 I/O 工具(fcntl.flock + 原子 rename,详见 design/11 §5.2)
# ---------------------------------------------------------------------------

_LOCK_DIR = Path("/tmp") / f"pmd-locks-{os.getuid()}"
_LOCK_DIR.mkdir(exist_ok=True)


def _lock_fd(name: str) -> int:
    """打开或创建一个锁文件,返回 fd(进程级保持打开)。"""
    p = _LOCK_DIR / f"{name}.lock"
    fd = os.open(str(p), os.O_RDWR | os.O_CREAT, 0o600)
    return fd


_LOCKS: dict[str, int] = {
    "pdt": _lock_fd("pdt"),
    "ltcs": _lock_fd("ltcs"),
    "modules": _lock_fd("modules"),
    "status": _lock_fd("status"),
    "updates": _lock_fd("updates"),
    "snapshots": _lock_fd("snapshots"),
    "admins": _lock_fd("admins"),
    "config": _lock_fd("config"),
}


class _FileLock:
    def __init__(self, *names: str):
        self.fds = [_LOCKS[n] for n in names]

    def __enter__(self):
        for fd in self.fds:
            fcntl.flock(fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        for fd in self.fds:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception:  # pragma: no cover
                pass


def _path(name: str) -> Path:
    return DATA_DIR / name


def _read_json(name: str, default):
    p = _path(name)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json_atomic(name: str, data: Any) -> None:
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def _append_jsonl(name: str, row: dict) -> None:
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with open(p, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def _read_jsonl(name: str) -> list[dict]:
    p = _path(name)
    if not p.exists():
        return []
    out: list[dict] = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


# 高层读写
def read_pdt() -> dict:
    return _read_json("pdt.json", {})


def write_pdt(data: dict) -> None:
    _write_json_atomic("pdt.json", data)


def read_ltcs() -> list[dict]:
    return _read_json("ltcs.json", [])


def write_ltcs(data: list[dict]) -> None:
    _write_json_atomic("ltcs.json", data)


def read_modules() -> list[dict]:
    return _read_json("modules.json", [])


def write_modules(data: list[dict]) -> None:
    _write_json_atomic("modules.json", data)


def read_status() -> dict:
    return _read_json("module_status.json", {})


def write_status(data: dict) -> None:
    _write_json_atomic("module_status.json", data)


def read_super_admins() -> list[dict]:
    return _read_json("super_admins.json", [])


def read_pdt_admins() -> list[str]:
    return _read_json("pdt_admins.json", [])


def read_ltc_admins() -> dict[str, list[str]]:
    return _read_json("ltc_admins.json", {})


def read_instance_config() -> dict:
    """读 DATA_DIR/config.json,返回部署配置(见 design/03 §4.2)。"""
    return _read_json("config.json", {})


def _upsert_user_registry(open_id: str, name: str, avatar_url: str = "") -> None:
    """飞书首次登录时把用户写进 user_registry.json,供 /api/users/search 使用。

    幂等:同 open_id 已存在则只更新 name/avatar,不覆盖其他字段。
    """
    if not open_id:
        return
    with _FileLock("admins"):  # 共用 admins 锁,避免新加锁名
        users = _read_json("user_registry.json", [])
        for u in users:
            if u.get("open_id") == open_id:
                if name:
                    u["name"] = name
                if avatar_url:
                    u["avatar_url"] = avatar_url
                u["last_login"] = now_iso()
                break
        else:
            users.append({
                "open_id": open_id,
                "name": name or open_id,
                "avatar_url": avatar_url,
                "last_login": now_iso(),
            })
        _write_json_atomic("user_registry.json", users)


# ---------------------------------------------------------------------------
# 时间戳与 ID
# ---------------------------------------------------------------------------

def now_iso() -> str:
    # microseconds 精度,防止同一秒多次写入时 history 排序不稳
    return datetime.now(CN_TZ).isoformat(timespec="microseconds")


def new_id(prefix: str = "upd") -> str:
    """简易 ULID 风格 ID:时间戳 + 短 UUID。"""
    return f"{prefix}-{int(time.time() * 1000):x}-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# 角色判定(design/10)
# ---------------------------------------------------------------------------

def is_super(open_id: str | None) -> bool:
    if not open_id:
        return False
    if DEV_LOGIN and open_id == DEV_OPEN_ID:
        return True
    return any(a.get("open_id") == open_id for a in read_super_admins())


def is_pdt_admin(open_id: str | None) -> bool:
    if not open_id:
        return False
    if is_super(open_id):
        return True
    return open_id in read_pdt_admins()


def is_ltc_admin(open_id: str | None, ltc_id: str | None) -> bool:
    if not open_id or not ltc_id:
        return False
    if is_pdt_admin(open_id):
        return True
    return open_id in read_ltc_admins().get(ltc_id, [])


def is_module_owner(open_id: str | None, module_id: str | None) -> bool:
    if not open_id or not module_id:
        return False
    for m in read_modules():
        if m.get("id") == module_id:
            return m.get("owner_open_id") == open_id
    return False


def can_edit_module_status(open_id: str | None, module_id: str | None) -> bool:
    if is_super(open_id) or is_pdt_admin(open_id):
        return True
    for m in read_modules():
        if m.get("id") != module_id:
            continue
        if m.get("owner_open_id") == open_id:
            return True
        ltc_id = m.get("ltc_id")
        if ltc_id and is_ltc_admin(open_id, ltc_id):
            return True
        return False
    return False


def can_freeze_snapshot(open_id: str | None) -> bool:
    return is_super(open_id) or is_pdt_admin(open_id)


def can_force_freeze(open_id: str | None) -> bool:
    return is_super(open_id)


# ---------------------------------------------------------------------------
# 认证(JWT + Cookie + Dev 后门)
# ---------------------------------------------------------------------------

def _create_jwt(open_id: str, name: str = "", avatar: str = "") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "open_id": open_id,
        "name": name,
        "avatar_url": avatar,
        "iat": int(now.timestamp()),
        "exp": int((now + JWT_TTL).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def _decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return ""


AUTH_WHITELIST = {"/api/health", "/api/feishu/login_url", "/api/feishu/callback"}


# ---------------------------------------------------------------------------
# FastAPI 应用 + 中间件
# ---------------------------------------------------------------------------

app = FastAPI(title="PMD Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:15173", "http://127.0.0.1:15173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """注入 request.state.open_id;非白名单未认证返 401。"""
    path = request.url.path
    request.state.open_id = None
    request.state.user_name = ""

    token = request.cookies.get(COOKIE_NAME)
    if token:
        payload = _decode_jwt(token)
        if payload:
            request.state.open_id = payload.get("open_id")
            request.state.user_name = payload.get("name", "")

    # Dev 后门:本机 + DEV_LOGIN=1 + 无 cookie → 注入 dev_admin
    if not request.state.open_id and DEV_LOGIN and _client_ip(request) in {"127.0.0.1", "::1", "localhost"}:
        request.state.open_id = DEV_OPEN_ID
        request.state.user_name = DEV_NAME

    if path.startswith("/api/") and path not in AUTH_WHITELIST:
        if not request.state.open_id:
            return JSONResponse({"detail": "unauthenticated", "code": "unauth"}, status_code=401)

    response = await call_next(request)
    # 滑动续期
    if token and request.state.open_id:
        payload = _decode_jwt(token) or {}
        exp = payload.get("exp", 0)
        remaining = exp - int(datetime.now(timezone.utc).timestamp())
        if remaining < int(JWT_RENEW_WINDOW.total_seconds()):
            new_token = _create_jwt(request.state.open_id, request.state.user_name)
            response.set_cookie(
                COOKIE_NAME, new_token, max_age=int(JWT_TTL.total_seconds()),
                httponly=True, secure=COOKIE_SECURE, samesite="lax",
            )
    return response


def current_open_id(request: Request) -> str:
    oid = getattr(request.state, "open_id", None)
    if not oid:
        raise HTTPException(401, "unauthenticated")
    return oid


# ---------------------------------------------------------------------------
# SSE 广播
# ---------------------------------------------------------------------------

_sse_subscribers: set[asyncio.Queue] = set()


async def _broadcast(event: str, data: dict) -> None:
    payload = {"event": event, "data": data}
    for q in list(_sse_subscribers):
        try:
            q.put_nowait(payload)
        except Exception:  # pragma: no cover
            pass


# ---------------------------------------------------------------------------
# 健康检查 / 认证端点
# ---------------------------------------------------------------------------

@app.get("/api/health")
def api_health():
    return {"ok": True, "ts": now_iso(), "data_dir": str(DATA_DIR)}


@app.get("/api/auth/me")
def api_me(request: Request):
    return {
        "open_id": request.state.open_id,
        "name": request.state.user_name,
        "is_super": is_super(request.state.open_id),
        "is_pdt_admin": is_pdt_admin(request.state.open_id),
        "dev_login": DEV_LOGIN,
        "feishu_configured": bool(FEISHU_APP_ID and FEISHU_APP_SECRET),
    }


@app.post("/api/auth/logout")
def api_logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


def _feishu_app_access_token() -> str:
    """换企业自建应用的 app_access_token。"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise HTTPException(501, detail={"detail": "feishu oauth not configured", "code": "feishu_disabled"})
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(_FEISHU_APP_TOKEN, json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET})
        data = r.json()
    except Exception as e:  # pragma: no cover  网络异常
        raise HTTPException(502, detail={"detail": f"feishu app_token network: {e}", "code": "feishu_upstream"})
    if data.get("code") != 0:
        raise HTTPException(502, detail={"detail": f"feishu app_token: {data.get('msg')}", "code": "feishu_upstream"})
    return data["app_access_token"]


def _feishu_user_info_from_code(code: str) -> dict:
    """code → user_access_token → user_info。返回 dict 含 open_id/name/avatar_url/tenant_key。"""
    app_token = _feishu_app_access_token()
    try:
        with httpx.Client(timeout=10.0) as client:
            r1 = client.post(
                _FEISHU_OIDC_ACCESS_TOKEN,
                json={"grant_type": "authorization_code", "code": code},
                headers={"Authorization": f"Bearer {app_token}"},
            )
            d1 = r1.json()
            if d1.get("code") != 0:
                raise HTTPException(502, detail={"detail": f"feishu code→token: {d1.get('msg')}", "code": "feishu_upstream"})
            user_access_token = d1["data"]["access_token"]
            r2 = client.get(
                _FEISHU_USER_INFO,
                headers={"Authorization": f"Bearer {user_access_token}"},
            )
            d2 = r2.json()
            if d2.get("code") != 0:
                raise HTTPException(502, detail={"detail": f"feishu user_info: {d2.get('msg')}", "code": "feishu_upstream"})
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(502, detail={"detail": f"feishu network: {e}", "code": "feishu_upstream"})
    return d2["data"]


@app.get("/api/feishu/login_url")
def api_feishu_login_url(redirect_uri: str | None = None, state: str | None = None):
    """构造飞书授权 URL,前端拿到后 window.location.href 过去。"""
    if not FEISHU_APP_ID:
        raise HTTPException(501, detail={"detail": "feishu oauth not configured", "code": "feishu_disabled"})
    redirect = redirect_uri or FEISHU_OAUTH_DEFAULT_REDIRECT
    st = state or secrets.token_urlsafe(16)
    url = (
        f"{_FEISHU_AUTHORIZE}"
        f"?app_id={FEISHU_APP_ID}"
        f"&redirect_uri={urllib.parse.quote(redirect, safe='')}"
        f"&response_type=code"
        f"&state={st}"
    )
    return {"login_url": url, "state": st}


@app.post("/api/feishu/callback")
async def api_feishu_callback(request: Request, response: Response):
    """收 code → 换用户信息 → 校验 tenant 白名单 → 签 JWT 写 cookie。"""
    body = await request.json()
    code = (body.get("code") or "").strip()
    if not code:
        raise HTTPException(400, detail={"detail": "code required", "code": "code_missing"})

    info = _feishu_user_info_from_code(code)
    open_id = info.get("open_id") or ""
    if not open_id:
        raise HTTPException(502, detail={"detail": "feishu user_info missing open_id", "code": "feishu_upstream"})
    name = info.get("name") or ""
    avatar_url = info.get("avatar_url") or ""
    tenant_key = info.get("tenant_key") or ""

    # 租户白名单(允许空 = 暂不限制,详见 design/03 §4.2 + design/10)
    allowed = read_instance_config().get("allowed_tenant_keys") or []
    if allowed and tenant_key not in allowed:
        raise HTTPException(403, detail={"detail": "tenant not allowed", "code": "tenant_forbidden"})

    _upsert_user_registry(open_id, name, avatar_url)

    token = _create_jwt(open_id, name, avatar_url)
    response.set_cookie(
        COOKIE_NAME, token, max_age=int(JWT_TTL.total_seconds()),
        httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/",
    )
    return {"open_id": open_id, "name": name, "avatar_url": avatar_url, "tenant_key": tenant_key}


# ---------------------------------------------------------------------------
# PDT
# ---------------------------------------------------------------------------

@app.get("/api/pdt")
def api_get_pdt():
    return read_pdt()


@app.put("/api/pdt")
async def api_put_pdt(request: Request):
    oid = current_open_id(request)
    if not is_pdt_admin(oid):
        raise HTTPException(403, "forbidden")
    body = await request.json()
    with _FileLock("pdt"):
        cur = read_pdt()
        cur.update(body or {})
        cur["updated_at"] = now_iso()
        write_pdt(cur)
    await _broadcast("config:reload", {"kind": "pdt"})
    return cur


# ---------------------------------------------------------------------------
# LTCs
# ---------------------------------------------------------------------------

@app.get("/api/ltcs")
def api_get_ltcs(include_archived: bool = False):
    rows = read_ltcs()
    if not include_archived:
        rows = [r for r in rows if not r.get("archived")]
    return rows


@app.post("/api/ltcs")
async def api_create_ltc(request: Request):
    oid = current_open_id(request)
    if not is_pdt_admin(oid):
        raise HTTPException(403, "forbidden")
    body = await request.json()
    if not body.get("id") or not body.get("name"):
        raise HTTPException(422, "id and name required")
    with _FileLock("ltcs"):
        rows = read_ltcs()
        if any(r["id"] == body["id"] for r in rows):
            raise HTTPException(409, "ltc id exists")
        row = {
            "id": body["id"],
            "name": body["name"],
            "order": body.get("order", len(rows) + 1),
            "archived": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "metadata": body.get("metadata", {}),
        }
        rows.append(row)
        write_ltcs(rows)
    await _broadcast("config:reload", {"kind": "ltcs"})
    return row


@app.put("/api/ltcs/{ltc_id}")
async def api_update_ltc(ltc_id: str, request: Request):
    oid = current_open_id(request)
    if not is_pdt_admin(oid):
        raise HTTPException(403, "forbidden")
    body = await request.json()
    with _FileLock("ltcs"):
        rows = read_ltcs()
        for r in rows:
            if r["id"] == ltc_id:
                for k in ("name", "order", "archived", "metadata"):
                    if k in body:
                        r[k] = body[k]
                r["updated_at"] = now_iso()
                write_ltcs(rows)
                await _broadcast("config:reload", {"kind": "ltcs"})
                return r
    raise HTTPException(404, "ltc not found")


@app.delete("/api/ltcs/{ltc_id}")
async def api_delete_ltc(ltc_id: str, request: Request):
    oid = current_open_id(request)
    if not is_pdt_admin(oid):
        raise HTTPException(403, "forbidden")
    with _FileLock("ltcs", "modules"):
        if any(m.get("ltc_id") == ltc_id for m in read_modules()):
            raise HTTPException(422, "ltc has modules; archive instead")
        rows = [r for r in read_ltcs() if r["id"] != ltc_id]
        write_ltcs(rows)
    await _broadcast("config:reload", {"kind": "ltcs"})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------

VALID_SCOPES = {"pdt", "ltc"}
VALID_COLORS = {"green", "yellow", "red"}


@app.get("/api/modules")
def api_get_modules(scope: str | None = None, ltc_id: str | None = None):
    rows = read_modules()
    if scope:
        rows = [r for r in rows if r.get("scope") == scope]
    if ltc_id:
        rows = [r for r in rows if r.get("ltc_id") == ltc_id]
    return rows


def _check_create_module_perm(oid: str, body: dict) -> None:
    """先做字段校验(422),通过后再判断权限(403)。

    422 早于 403:body 不合法时无论谁来都返 422,避免攻击者用 403 探测端点形态。
    """
    scope = body.get("scope")
    if scope not in VALID_SCOPES:
        raise HTTPException(422, "invalid scope")
    if scope == "ltc" and not body.get("ltc_id"):
        raise HTTPException(422, "ltc_id required for scope=ltc")
    if scope == "pdt":
        if not is_pdt_admin(oid):
            raise HTTPException(403, "forbidden")
    else:
        if not is_ltc_admin(oid, body["ltc_id"]):
            raise HTTPException(403, "forbidden")


@app.post("/api/modules")
async def api_create_module(request: Request):
    oid = current_open_id(request)
    body = await request.json()
    if not body.get("id") or not body.get("name") or not body.get("group"):
        raise HTTPException(422, "id/name/group required")
    _check_create_module_perm(oid, body)
    with _FileLock("modules"):
        rows = read_modules()
        if any(r["id"] == body["id"] for r in rows):
            raise HTTPException(409, "module id exists")
        row = {
            "id": body["id"],
            "scope": body["scope"],
            "ltc_id": body.get("ltc_id") if body["scope"] == "ltc" else None,
            "group": body["group"],
            "name": body["name"],
            "order": body.get("order", len(rows) + 1),
            "owner_open_id": body.get("owner_open_id"),
            "kpi_fields": body.get("kpi_fields", []),
            "sub_items": body.get("sub_items", []),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "metadata": body.get("metadata", {}),
        }
        rows.append(row)
        write_modules(rows)
    await _broadcast("config:reload", {"kind": "modules"})
    return row


def _check_edit_module_perm(oid: str, module: dict) -> None:
    if is_pdt_admin(oid):
        return
    if module.get("scope") == "ltc" and is_ltc_admin(oid, module.get("ltc_id")):
        return
    raise HTTPException(403, "forbidden")


@app.put("/api/modules/{module_id}")
async def api_update_module(module_id: str, request: Request):
    oid = current_open_id(request)
    body = await request.json()
    with _FileLock("modules"):
        rows = read_modules()
        for r in rows:
            if r["id"] != module_id:
                continue
            _check_edit_module_perm(oid, r)
            for k in ("group", "name", "order", "owner_open_id", "kpi_fields", "sub_items", "metadata"):
                if k in body:
                    r[k] = body[k]
            r["updated_at"] = now_iso()
            write_modules(rows)
            await _broadcast("config:reload", {"kind": "modules"})
            return r
    raise HTTPException(404, "module not found")


@app.delete("/api/modules/{module_id}")
async def api_delete_module(module_id: str, request: Request):
    oid = current_open_id(request)
    with _FileLock("modules", "status", "updates"):
        rows = read_modules()
        target = next((r for r in rows if r["id"] == module_id), None)
        if not target:
            raise HTTPException(404, "module not found")
        _check_edit_module_perm(oid, target)
        new_rows = [r for r in rows if r["id"] != module_id]
        write_modules(new_rows)
        # 同步删除 status,并写入 module_deleted 历史
        status = read_status()
        before = status.pop(module_id, None)
        write_status(status)
        _append_jsonl("module_updates.jsonl", {
            "id": new_id(),
            "ts": now_iso(),
            "module_id": module_id,
            "kind": "module_deleted",
            "before": before,
            "after": None,
            "updated_by": oid,
            "client": "api",
        })
    await _broadcast("config:reload", {"kind": "modules"})
    await _broadcast("status:reload", {"module_id": module_id})
    return {"ok": True}


# ---------------------------------------------------------------------------
# 模块状态(双写:status + updates)
# ---------------------------------------------------------------------------

def _validate_status_entry(module: dict, entry: dict) -> None:
    color = entry.get("module_color")
    if color not in VALID_COLORS:
        raise HTTPException(422, "invalid module_color")
    sub_colors = entry.get("sub_items_color", {}) or {}
    valid_sub_ids = {s["id"] for s in module.get("sub_items", [])}
    for sid, sc in sub_colors.items():
        if sid not in valid_sub_ids:
            raise HTTPException(422, f"sub_item {sid} not in module")
        if sc not in VALID_COLORS:
            raise HTTPException(422, f"invalid sub_items_color for {sid}")
    kpi_values = entry.get("kpi_values", {}) or {}
    valid_kpi_keys = {k["key"] for k in module.get("kpi_fields", [])}
    for k in kpi_values:
        if k not in valid_kpi_keys:
            raise HTTPException(422, f"kpi key {k} not in module")
    # 风险说明必填规则
    any_non_green = color != "green" or any(v != "green" for v in sub_colors.values())
    if any_non_green and not (entry.get("risk_note") or "").strip():
        raise HTTPException(422, "risk_note required when not all green")


@app.get("/api/status")
def api_get_status():
    return read_status()


@app.put("/api/status/{module_id}")
async def api_put_status(module_id: str, request: Request):
    oid = current_open_id(request)
    if not can_edit_module_status(oid, module_id):
        raise HTTPException(403, "forbidden")
    body = await request.json()
    modules = read_modules()
    module = next((m for m in modules if m["id"] == module_id), None)
    if not module:
        raise HTTPException(404, "module not found")
    entry = {
        "module_color": body.get("module_color"),
        "sub_items_color": body.get("sub_items_color", {}) or {},
        "kpi_values": body.get("kpi_values", {}) or {},
        "risk_note": (body.get("risk_note") or "").strip(),
        "updated_by": oid,
        "updated_at": now_iso(),
        "metadata": body.get("metadata", {}) or {},
    }
    _validate_status_entry(module, entry)
    with _FileLock("status", "updates"):
        status = read_status()
        before = status.get(module_id)
        status[module_id] = entry
        write_status(status)
        _append_jsonl("module_updates.jsonl", {
            "id": new_id(),
            "ts": now_iso(),
            "module_id": module_id,
            "kind": "status_update",
            "before": before,
            "after": entry,
            "updated_by": oid,
            "client": "api",
        })
    await _broadcast("status:reload", {"module_id": module_id})
    return entry


@app.get("/api/status/history")
def api_get_status_history(module_id: str, limit: int = 50, before_ts: str | None = None):
    rows = [r for r in _read_jsonl("module_updates.jsonl") if r.get("module_id") == module_id]
    if before_ts:
        rows = [r for r in rows if r.get("ts", "") < before_ts]
    # (ts, id) 双键保证同时间戳下稳定;id 单调(含时间戳前缀)
    rows.sort(key=lambda r: (r.get("ts", ""), r.get("id", "")), reverse=True)
    return rows[: max(1, min(limit, 500))]


# ---------------------------------------------------------------------------
# 周快照
# ---------------------------------------------------------------------------

def _iso_week_str(d: datetime | None = None) -> str:
    d = d or datetime.now(CN_TZ)
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"


def _snapshot_path(week: str) -> Path:
    return DATA_DIR / "weekly_snapshots" / f"snapshot-{week}.json"


@app.get("/api/snapshots")
def api_list_snapshots():
    folder = DATA_DIR / "weekly_snapshots"
    if not folder.exists():
        return []
    out = []
    for p in sorted(folder.glob("snapshot-*.json"), reverse=True):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
            out.append({
                "week": doc.get("week"),
                "frozen_at": doc.get("frozen_at"),
                "frozen_by": doc.get("frozen_by"),
                "trigger": doc.get("trigger"),
            })
        except json.JSONDecodeError:
            continue
    return out


@app.get("/api/snapshots/{week}")
def api_get_snapshot(week: str):
    p = _snapshot_path(week)
    if not p.exists():
        raise HTTPException(404, "snapshot not found")
    return json.loads(p.read_text(encoding="utf-8"))


async def _freeze_snapshot(
    week: str | None,
    *,
    frozen_by: str,
    trigger: str,
    force: bool,
) -> dict:
    """Freeze the given (or current) ISO week into a snapshot file.

    被手动端点和定时任务共同复用。约束:design/09。
    返回 {"week": ..., "ok": True}。
    Raises HTTPException 409 当文件已存在且 force=False。
    """
    week_str = week or _iso_week_str()
    p = _snapshot_path(week_str)
    if p.exists() and not force:
        raise HTTPException(409, "snapshot exists; use force=true to overwrite")
    with _FileLock("snapshots"):
        snap = {
            "week": week_str,
            "frozen_at": now_iso(),
            "frozen_by": frozen_by,
            "trigger": trigger,
            "pdt": read_pdt(),
            "ltcs": read_ltcs(),
            "modules": read_modules(),
            "module_status": read_status(),
            "metadata": {},
        }
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    await _broadcast("snapshot:created", {"week": week_str})
    return {"week": week_str, "ok": True}


@app.post("/api/snapshots/freeze")
async def api_freeze_snapshot(request: Request, week: str | None = None, force: bool = False):
    oid = current_open_id(request)
    if not can_freeze_snapshot(oid):
        raise HTTPException(403, "forbidden")
    if force and not can_force_freeze(oid):
        raise HTTPException(403, "only super can force freeze")
    return await _freeze_snapshot(week, frozen_by=oid, trigger="manual", force=force)


# ---------------------------------------------------------------------------
# 自动周快照(design/09 §6.1)
# ---------------------------------------------------------------------------

AUTO_FREEZE_DEFAULTS = {"enabled": False, "weekday": 4, "hour": 18, "minute": 0}


def _auto_freeze_cfg() -> dict:
    """读 config.json.auto_freeze,字段缺失时用默认值兜底。"""
    cfg = read_instance_config().get("auto_freeze") or {}
    out = dict(AUTO_FREEZE_DEFAULTS)
    for k in ("enabled", "weekday", "hour", "minute"):
        if k in cfg:
            out[k] = cfg[k]
    # 数值范围兜底
    out["weekday"] = max(0, min(6, int(out["weekday"])))
    out["hour"] = max(0, min(23, int(out["hour"])))
    out["minute"] = max(0, min(59, int(out["minute"])))
    out["enabled"] = bool(out["enabled"])
    return out


def _next_auto_freeze_dt(now: datetime, cfg: dict) -> datetime:
    """计算下次自动冻结的 CN_TZ 时间。"""
    target_w = cfg["weekday"]
    days = (target_w - now.weekday()) % 7
    candidate = now.replace(hour=cfg["hour"], minute=cfg["minute"], second=0, microsecond=0) + timedelta(days=days)
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


@app.get("/api/config/auto_freeze")
def api_get_auto_freeze(request: Request):
    cfg = _auto_freeze_cfg()
    now = datetime.now(CN_TZ)
    return {
        **cfg,
        "next_run_at": _next_auto_freeze_dt(now, cfg).isoformat() if cfg["enabled"] else None,
    }


@app.put("/api/config/auto_freeze")
async def api_put_auto_freeze(request: Request):
    oid = current_open_id(request)
    if not is_super(oid):
        raise HTTPException(403, "forbidden")
    body = await request.json()
    incoming = {}
    for k in ("enabled", "weekday", "hour", "minute"):
        if k in body:
            incoming[k] = body[k]
    # 字段校验
    try:
        if "enabled" in incoming:
            incoming["enabled"] = bool(incoming["enabled"])
        if "weekday" in incoming and not (0 <= int(incoming["weekday"]) <= 6):
            raise ValueError("weekday must be 0..6")
        if "hour" in incoming and not (0 <= int(incoming["hour"]) <= 23):
            raise ValueError("hour must be 0..23")
        if "minute" in incoming and not (0 <= int(incoming["minute"]) <= 59):
            raise ValueError("minute must be 0..59")
    except (ValueError, TypeError) as e:
        raise HTTPException(422, f"invalid auto_freeze config: {e}")
    with _FileLock("config"):
        cfg = read_instance_config()
        merged = {**(cfg.get("auto_freeze") or {}), **incoming}
        cfg["auto_freeze"] = merged
        _write_json_atomic("config.json", cfg)
    await _broadcast("config:reload", {"kind": "auto_freeze"})
    return _auto_freeze_cfg()


_auto_freeze_task: asyncio.Task | None = None


async def _auto_freeze_loop() -> None:
    """后台循环:按 config.auto_freeze 调度冻结。

    每 60s 检查一次"是否到达 weekday=H:M 且当周尚未冻结"。
    最小化复杂度,不依赖外部 cron 库。
    """
    while True:
        try:
            cfg = _auto_freeze_cfg()
            if cfg["enabled"]:
                now = datetime.now(CN_TZ)
                # 触发窗口:当前是目标 weekday 且 (h, m) 已到 且当周未冻结
                if (
                    now.weekday() == cfg["weekday"]
                    and (now.hour, now.minute) >= (cfg["hour"], cfg["minute"])
                ):
                    week_str = _iso_week_str(now)
                    if not _snapshot_path(week_str).exists():
                        try:
                            await _freeze_snapshot(
                                week_str,
                                frozen_by="system:auto",
                                trigger="auto",
                                force=False,
                            )
                        except HTTPException:
                            pass  # 同周已存在
                        except Exception:  # pragma: no cover
                            pass
        except Exception:  # pragma: no cover
            pass
        await asyncio.sleep(60)


@app.on_event("startup")
async def _on_startup_scheduler() -> None:
    global _auto_freeze_task
    if os.environ.get("PMD_DISABLE_SCHEDULER") == "1":
        return  # 测试场景显式关闭
    if _auto_freeze_task is None or _auto_freeze_task.done():
        _auto_freeze_task = asyncio.create_task(_auto_freeze_loop())


@app.on_event("shutdown")
async def _on_shutdown_scheduler() -> None:
    global _auto_freeze_task
    if _auto_freeze_task and not _auto_freeze_task.done():
        _auto_freeze_task.cancel()
        try:
            await _auto_freeze_task
        except (asyncio.CancelledError, Exception):  # pragma: no cover
            pass


# ---------------------------------------------------------------------------
# 示例数据(空实例 onboarding 用)
# ---------------------------------------------------------------------------

@app.post("/api/seed/demo")
async def api_seed_demo(request: Request):
    """Super Admin 一键填示例数据,空实例 onboarding 用。"""
    oid = current_open_id(request)
    if not is_super(oid):
        raise HTTPException(403, "forbidden")
    with _FileLock("pdt", "ltcs", "modules", "status"):
        if read_ltcs() or read_modules():
            raise HTTPException(409, "instance already has data; refuse to overwrite")
        ltc_id = uuid.uuid4().hex
        pdt_mod_id = uuid.uuid4().hex
        ltc_mod1_id = uuid.uuid4().hex
        ltc_mod2_id = uuid.uuid4().hex
        sub1 = uuid.uuid4().hex[:12]
        sub2 = uuid.uuid4().hex[:12]
        ts = now_iso()
        write_pdt({
            "code": "demo",
            "name": "PMD 示例产品线",
            "description": "由 /api/seed/demo 自动创建,演示与 onboarding 用",
            "milestones": [
                {"name": "技术评审 TR4", "date": "2026-06-15", "type": "TR", "note": ""},
                {"name": "A 点 SOP", "date": "2026-09-30", "type": "SOP", "note": ""},
            ],
            "updated_at": ts,
            "metadata": {"seeded": True},
        })
        write_ltcs([{
            "id": ltc_id, "name": "示例子项目", "order": 1, "archived": False,
            "created_at": ts, "updated_at": ts, "metadata": {"seeded": True},
        }])
        write_modules([
            {
                "id": pdt_mod_id, "scope": "pdt", "ltc_id": None,
                "group": "质量", "name": "质量总览", "order": 1,
                "owner_open_id": None,
                "kpi_fields": [{"key": "bug_close_rate", "label": "Bug 闭环率", "hint": ""}],
                "sub_items": [],
                "created_at": ts, "updated_at": ts, "metadata": {"seeded": True},
            },
            {
                "id": ltc_mod1_id, "scope": "ltc", "ltc_id": ltc_id,
                "group": "硬件和底软", "name": "MCU 底软", "order": 1,
                "owner_open_id": None, "kpi_fields": [],
                "sub_items": [
                    {"id": sub1, "name": "Autosar BSW", "order": 1},
                    {"id": sub2, "name": "RTE", "order": 2},
                ],
                "created_at": ts, "updated_at": ts, "metadata": {"seeded": True},
            },
            {
                "id": ltc_mod2_id, "scope": "ltc", "ltc_id": ltc_id,
                "group": "感知算法", "name": "示例感知模块", "order": 1,
                "owner_open_id": None, "kpi_fields": [], "sub_items": [],
                "created_at": ts, "updated_at": ts, "metadata": {"seeded": True},
            },
        ])
        write_status({})
    await _broadcast("config:reload", {"kind": "seed"})
    return {"ok": True, "ltc_id": ltc_id}


# ---------------------------------------------------------------------------
# 用户与管理员
# ---------------------------------------------------------------------------

@app.get("/api/users/search")
def api_users_search(q: str = "", limit: int = 200):
    """前端 UserSearchInput 走拼音前端过滤,这里 q 为空时直接返全量(受 limit 上限)。

    数据源 v1:user_registry.json 手动维护;v2 可接飞书通讯录 contact_cache。
    """
    users = _read_json("user_registry.json", [])
    limit = max(1, min(limit, 2000))
    if not q:
        return users[:limit]
    needle = q.lower()
    matched = [u for u in users if needle in (u.get("name", "") + u.get("open_id", "")).lower()]
    return matched[:limit]


@app.get("/api/admins")
def api_get_admins():
    return {
        "super": read_super_admins(),
        "pdt": read_pdt_admins(),
        "ltc": read_ltc_admins(),
    }


@app.put("/api/admins/{role}")
async def api_put_admins(role: str, request: Request):
    oid = current_open_id(request)
    body = await request.json()
    if role == "super":
        if not is_super(oid):
            raise HTTPException(403, "forbidden")
        _write_json_atomic("super_admins.json", body)
    elif role == "pdt":
        if not is_super(oid):
            raise HTTPException(403, "forbidden")
        _write_json_atomic("pdt_admins.json", body)
    elif role == "ltc":
        if not is_pdt_admin(oid):
            raise HTTPException(403, "forbidden")
        _write_json_atomic("ltc_admins.json", body)
    else:
        raise HTTPException(404, "unknown role")
    await _broadcast("config:reload", {"kind": "admins"})
    return {"ok": True}


# ---------------------------------------------------------------------------
# SSE
# ---------------------------------------------------------------------------

@app.get("/api/events")
async def api_events(request: Request):
    """简单 SSE 实现,不依赖外部库。"""
    q: asyncio.Queue = asyncio.Queue(maxsize=64)
    _sse_subscribers.add(q)

    async def gen():
        try:
            yield "event: hello\ndata: {}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"event: {item['event']}\ndata: {json.dumps(item['data'], ensure_ascii=False)}\n\n"
        finally:
            _sse_subscribers.discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# 启动入口(`python main.py` 直接跑;生产走 uvicorn CLI)
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=DEV_LOGIN)
