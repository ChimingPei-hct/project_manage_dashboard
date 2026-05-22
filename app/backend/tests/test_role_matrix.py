"""端点 × 角色 权限矩阵测试(详见 design/10)。

骨架阶段覆盖最关键写端点;新增写端点时必须在此补用例(pre-push hook 兜底)。
"""
from __future__ import annotations

import pytest

from .conftest import (
    SAMPLE_LTC_ID,
    SAMPLE_MODULE_ID,
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


def test_put_status_requires_risk_note_when_not_green(as_owner_this):
    r = as_owner_this.put(f"/api/status/{SAMPLE_MODULE_ID}", json={
        "module_color": "red",
        "risk_note": "",
    })
    assert r.status_code == 422


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
