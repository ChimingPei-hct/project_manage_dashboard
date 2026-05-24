"""端点 × 角色 权限矩阵测试(详见 design/10)。

骨架阶段覆盖最关键写端点;新增写端点时必须在此补用例(pre-push hook 兜底)。
"""
from __future__ import annotations

import pytest

from .conftest import (
    CREATOR_LTC_ID,
    CREATOR_MODULE_ID,
    SAMPLE_LTC_ID,
    SAMPLE_MODULE_ID,
    SUPER_OID,
    _login_cookie,
)


def _do(client_fixture, method: str, url: str, **kwargs):
    return client_fixture.request(method, url, **kwargs)


# ---------------------------------------------------------------------------
# 健康 / 认证
# ---------------------------------------------------------------------------

def test_health_open(client):
    c, _ = client
    assert c.get("/api/health").status_code == 200


def test_me_requires_login(client):
    c, _ = client
    # 没塞 cookie,DEV_LOGIN=0,应当 401
    assert c.get("/api/auth/me").status_code == 401


def test_me_logged_in(as_super):
    r = as_super.get("/api/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["is_super"] is True


# ---------------------------------------------------------------------------
# PUT /api/pdt — Super/PDT Admin ✅;其他 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_put_pdt(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.put("/api/pdt", json={"name": "X"})
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# POST /api/ltcs — Super/PDT Admin ✅;其他 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_post_ltc(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post("/api/ltcs", json={"id": f"ltc-new-{role_fixture}", "name": "N"})
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# POST /api/modules scope=ltc — Super/PDT/对应 LTC Admin ✅;其他 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_post_module_ltc_scope(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post("/api/modules", json={
        "id": f"mod-new-{role_fixture}", "scope": "ltc", "ltc_id": SAMPLE_LTC_ID,
        "group": "G", "name": "N",
    })
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# PUT /api/status/{module_id} — Super/PDT/本 LTC Admin/本模块 Owner ✅;其他 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 200),
    ("as_guest", 403),
])
def test_put_status(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.put(f"/api/status/{SAMPLE_MODULE_ID}", json={
        "module_color": "green",
        "sub_items_color": {},
        "kpi_values": {},
        "risk_note": "",
    })
    assert r.status_code == expected


def test_put_status_allows_empty_risk_when_not_green(as_owner_this):
    """风险列表允许为空,即使整体非绿(2026-05 放开校验)"""
    r = as_owner_this.put(f"/api/status/{SAMPLE_MODULE_ID}", json={
        "module_color": "red",
        "risk_note": "",
    })
    assert r.status_code == 200


def test_put_status_writes_history(as_owner_this):
    r = as_owner_this.put(f"/api/status/{SAMPLE_MODULE_ID}", json={
        "module_color": "green",
        "risk_note": "",
    })
    assert r.status_code == 200
    h = as_owner_this.get(f"/api/status/history?module_id={SAMPLE_MODULE_ID}")
    assert h.status_code == 200
    rows = h.json()
    assert len(rows) >= 1
    assert rows[0]["kind"] == "status_update"
    assert rows[0]["after"]["module_color"] == "green"


# ---------------------------------------------------------------------------
# Creator 维度 — 资源创建者对自己创建的 module / ltc 有 PUT/DELETE 权限
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),         # admin 越权
    ("as_pdt_admin", 200),     # admin 越权
    ("as_creator_this", 200),  # 创建者
    ("as_owner_this", 403),    # 非创建者非 admin
    ("as_ltc_admin_other", 403),
    ("as_guest", 403),
])
def test_put_module_creator(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.put(f"/api/modules/{CREATOR_MODULE_ID}", json={"name": "renamed"})
    assert r.status_code == expected


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_creator_this", 200),
    ("as_owner_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_guest", 403),
])
def test_delete_module_creator(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.delete(f"/api/modules/{CREATOR_MODULE_ID}")
    assert r.status_code == expected


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_creator_this", 200),
    ("as_owner_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_guest", 403),
])
def test_put_ltc_creator(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.put(f"/api/ltcs/{CREATOR_LTC_ID}", json={"name": "renamed"})
    assert r.status_code == expected


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_creator_this", 200),
    ("as_owner_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_guest", 403),
])
def test_delete_ltc_creator(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.delete(f"/api/ltcs/{CREATOR_LTC_ID}")
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# POST /api/modules scope=ltc_template — Super/PDT Admin ✅;其他 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_post_module_ltc_template_scope(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post("/api/modules", json={
        "id": f"mod-tpl-{role_fixture}", "scope": "ltc_template",
        "group": "G", "name": "T",
    })
    assert r.status_code == expected


def test_post_module_ltc_template_rejects_ltc_id(as_super):
    r = as_super.post("/api/modules", json={
        "id": "mod-tpl-bad", "scope": "ltc_template", "ltc_id": SAMPLE_LTC_ID,
        "group": "G", "name": "T",
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/status/{ltc_id}::{module_id} on ltc_template — Super/PDT/对应 LTC Admin ✅
# ---------------------------------------------------------------------------

TPL_MODULE_ID = "mod-tpl-shared"


def _seed_template_module(client_tuple):
    c, m = client_tuple
    from .conftest import SUPER_OID, _login_cookie
    saved = dict(c.cookies)
    c.cookies.clear()
    c.cookies.update(_login_cookie(m, SUPER_OID))
    r = c.post("/api/modules", json={
        "id": TPL_MODULE_ID, "scope": "ltc_template",
        "group": "G", "name": "Template",
    })
    assert r.status_code == 200
    c.cookies.clear()
    c.cookies.update(saved)


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),  # 模板模块未设 owner
    ("as_guest", 403),
])
def test_put_status_ltc_template(request, client, role_fixture, expected):
    _seed_template_module(client)
    c = request.getfixturevalue(role_fixture)
    r = c.put(f"/api/status/{SAMPLE_LTC_ID}::{TPL_MODULE_ID}", json={
        "module_color": "green",
        "risk_note": "",
    })
    assert r.status_code == expected


def test_put_status_ltc_template_requires_compound_key(client, as_super):
    _seed_template_module(client)
    # 平铺键访问模板模块 → 422
    r = as_super.put(f"/api/status/{TPL_MODULE_ID}", json={"module_color": "green"})
    assert r.status_code == 422


def test_put_status_compound_key_on_non_template_module(as_super):
    # 普通 LTC 模块用复合键 → 422
    r = as_super.put(f"/api/status/{SAMPLE_LTC_ID}::{SAMPLE_MODULE_ID}", json={"module_color": "green"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/ltc/{ltc_id}/init-from-template
#   Super / PDT Admin / 本 LTC Admin ✅;其他 403;重复初始化 → 409
# ---------------------------------------------------------------------------

def _seed_template_pool(client_tuple):
    """直接写文件级 seed 模板池(category + module),不走端点。

    同时清理 conftest 预置的 SAMPLE_LTC_ID 的 scope=ltc 模块,
    确保 init-from-template 的「无已有数据」前置条件成立。
    """
    import json
    c, m = client_tuple
    base = m.DATA_DIR
    cats = json.loads((base / "categories.json").read_text(encoding="utf-8")) if (base / "categories.json").exists() else []
    mods = json.loads((base / "modules.json").read_text(encoding="utf-8"))
    cats = [x for x in cats if not (x.get("scope") == "ltc" and x.get("ltc_id") == SAMPLE_LTC_ID)]
    mods = [x for x in mods if not (x.get("scope") == "ltc" and x.get("ltc_id") == SAMPLE_LTC_ID)]
    cats.append({
        "id": "cat-tpl-x", "name": "X", "owner_open_id": None, "order": 1,
        "scope": "ltc_template", "ltc_id": None,
        "created_at": "2026-05-24T00:00:00+08:00", "updated_at": "2026-05-24T00:00:00+08:00",
        "metadata": {},
    })
    mods.append({
        "id": "mod-tpl-x", "scope": "ltc_template", "ltc_id": None,
        "group": "X", "category_id": "cat-tpl-x", "name": "X-Mod", "order": 1,
        "owner_open_id": None, "kpi_fields": [], "sub_items": [],
        "created_at": "2026-05-24T00:00:00+08:00", "updated_at": "2026-05-24T00:00:00+08:00",
        "metadata": {},
    })
    (base / "categories.json").write_text(json.dumps(cats), encoding="utf-8")
    (base / "modules.json").write_text(json.dumps(mods), encoding="utf-8")


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_init_ltc_from_template(request, client, role_fixture, expected):
    _seed_template_pool(client)
    c = request.getfixturevalue(role_fixture)
    r = c.post(f"/api/ltc/{SAMPLE_LTC_ID}/init-from-template")
    assert r.status_code == expected
    if expected == 200:
        body = r.json()
        assert body["copied_categories"] >= 1
        assert body["copied_modules"] >= 1


def test_init_ltc_from_template_rejects_unknown_ltc(client, as_super):
    _seed_template_pool(client)
    r = as_super.post("/api/ltc/no-such-ltc/init-from-template")
    assert r.status_code == 404


def test_init_ltc_from_template_rejects_repeat(client, as_super):
    _seed_template_pool(client)
    r = as_super.post(f"/api/ltc/{SAMPLE_LTC_ID}/init-from-template")
    assert r.status_code == 200
    r2 = as_super.post(f"/api/ltc/{SAMPLE_LTC_ID}/init-from-template")
    assert r2.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/snapshots/freeze — Super/PDT Admin ✅;其他 403
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_freeze_snapshot(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post(f"/api/snapshots/freeze?week=2026-W{30 + ord(role_fixture[-1]) % 10:02d}")
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# PUT /api/admins/super — 仅 Super
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 403),
    ("as_ltc_admin_this", 403),
    ("as_guest", 403),
])
def test_put_admins_super(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.put("/api/admins/super", json=[])
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# GET /api/config/auto_freeze — 所有已登录角色可读
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_owner_this", 200),
    ("as_guest", 200),
])
def test_get_auto_freeze(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.get("/api/config/auto_freeze")
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# PUT /api/config/auto_freeze — 仅 Super 可写
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 403),
    ("as_ltc_admin_this", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_put_auto_freeze(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.put("/api/config/auto_freeze", json={"enabled": True, "weekday": 4, "hour": 18, "minute": 0})
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# POST /api/pdt/icon — Super/PDT Admin/任一 LTC Admin ✅;Owner / 访客 403
# ---------------------------------------------------------------------------

_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0"
    b"\xf0\x1f\x00\x05\x00\x01\xfeu\xb8b\x06\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_ltc_admin_other", 200),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_post_pdt_icon(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post("/api/pdt/icon", files={"file": ("icon.png", _TINY_PNG, "image/png")})
    assert r.status_code == expected, r.text


def test_post_pdt_icon_rejects_bad_mime(as_super):
    r = as_super.post("/api/pdt/icon", files={"file": ("evil.txt", b"hello", "text/plain")})
    assert r.status_code == 422


def test_post_pdt_icon_writes_field_and_serves_asset(as_pdt_admin):
    r = as_pdt_admin.post("/api/pdt/icon", files={"file": ("icon.png", _TINY_PNG, "image/png")})
    assert r.status_code == 200
    rel = r.json()["icon"]
    assert rel.startswith("assets/") and rel.endswith("/icon.png")
    pdt = as_pdt_admin.get("/api/pdt").json()
    assert pdt["icon"] == rel
    asset = as_pdt_admin.get(f"/{rel}")
    assert asset.status_code == 200
    assert asset.content == _TINY_PNG


def test_get_asset_rejects_path_traversal(as_pdt_admin):
    r = as_pdt_admin.get("/assets/../pdt.json")
    # path traversal 被 URL 解析后,FastAPI 路由也无法匹配到 /assets/{path};
    # 关键是绝不返 200 + pdt.json 内容
    assert r.status_code in (400, 404)


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_delete_pdt_icon(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.delete("/api/pdt/icon")
    assert r.status_code == expected


# ---------------------------------------------------------------------------
# Categories CRUD — scope=ltc_template 仅 Super/PDT Admin;scope=ltc 含本 LTC Admin
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_post_category_template_scope(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post("/api/categories", json={
        "id": f"cat-tpl-{role_fixture.replace('_', '-')}",
        "name": f"大类-{role_fixture}", "scope": "ltc_template", "order": 1,
    })
    assert r.status_code == expected, r.text


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 200),
    ("as_ltc_admin_other", 403),
    ("as_owner_this", 403),
    ("as_guest", 403),
])
def test_post_category_ltc_scope(request, role_fixture, expected):
    c = request.getfixturevalue(role_fixture)
    r = c.post("/api/categories", json={
        "id": f"cat-ltc-{role_fixture.replace('_', '-')}",
        "name": f"L-{role_fixture}", "scope": "ltc", "ltc_id": SAMPLE_LTC_ID, "order": 1,
    })
    assert r.status_code == expected, r.text


def test_post_category_rejects_pdt_scope(as_super):
    r = as_super.post("/api/categories", json={
        "id": "cat-bad", "name": "X", "scope": "pdt",
    })
    assert r.status_code == 422


def test_post_category_rejects_ltc_id_on_template(as_super):
    r = as_super.post("/api/categories", json={
        "id": "cat-bad-tpl", "name": "X", "scope": "ltc_template", "ltc_id": SAMPLE_LTC_ID,
    })
    assert r.status_code == 422


def _seed_template_category(client_tuple, cid="cat-shared-tpl"):
    c, m = client_tuple
    saved = dict(c.cookies)
    c.cookies.clear()
    c.cookies.update(_login_cookie(m, SUPER_OID))
    r = c.post("/api/categories", json={
        "id": cid, "name": f"共享-{cid}", "scope": "ltc_template", "order": 1,
    })
    assert r.status_code == 200, r.text
    c.cookies.clear()
    c.cookies.update(saved)
    return cid


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_guest", 403),
])
def test_put_category_template(request, client, role_fixture, expected):
    cid = _seed_template_category(client, "cat-put-tpl")
    c = request.getfixturevalue(role_fixture)
    r = c.put(f"/api/categories/{cid}", json={"name": "改名"})
    assert r.status_code == expected, r.text


@pytest.mark.parametrize("role_fixture,expected", [
    ("as_super", 200),
    ("as_pdt_admin", 200),
    ("as_ltc_admin_this", 403),
    ("as_guest", 403),
])
def test_delete_category_template(request, client, role_fixture, expected):
    cid = _seed_template_category(client, f"cat-del-{role_fixture.replace('_', '-')}")
    c = request.getfixturevalue(role_fixture)
    r = c.delete(f"/api/categories/{cid}")
    assert r.status_code == expected, r.text


def test_delete_category_blocked_by_module_ref(client, as_super):
    cid = _seed_template_category(client, "cat-with-ref")
    # 创建一个 module 引用该 category
    r = as_super.post("/api/modules", json={
        "id": "mod-cat-ref", "scope": "ltc_template",
        "group": "G", "name": "M", "category_id": cid,
    })
    assert r.status_code == 200, r.text
    r = as_super.delete(f"/api/categories/{cid}")
    assert r.status_code == 409


def test_get_categories_open_to_all(as_guest):
    r = as_guest.get("/api/categories")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# sub_items_risk 校验:非绿子项必填风险文本
# ---------------------------------------------------------------------------

def _seed_module_with_sub_items(client_tuple, mid="mod-with-subs"):
    c, m = client_tuple
    saved = dict(c.cookies)
    c.cookies.clear()
    c.cookies.update(_login_cookie(m, SUPER_OID))
    r = c.post("/api/modules", json={
        "id": mid, "scope": "ltc", "ltc_id": SAMPLE_LTC_ID,
        "group": "G", "name": "M",
        "sub_items": [{"id": "s1", "name": "S1", "order": 1}],
    })
    assert r.status_code == 200, r.text
    c.cookies.clear()
    c.cookies.update(saved)
    return mid


def test_put_status_non_green_sub_item_requires_risk(client, as_super):
    mid = _seed_module_with_sub_items(client, "mod-sub-risk")
    # 子项标红但 sub_items_risk 缺失 → 422
    r = as_super.put(f"/api/status/{mid}", json={
        "module_color": "red",
        "sub_items_color": {"s1": "red"},
        "risk_note": "模块红",
    })
    assert r.status_code == 422
    # 补上 sub_items_risk → 200
    r = as_super.put(f"/api/status/{mid}", json={
        "module_color": "red",
        "sub_items_color": {"s1": "red"},
        "sub_items_risk": {"s1": "子项阻塞"},
        "risk_note": "模块红",
    })
    assert r.status_code == 200
