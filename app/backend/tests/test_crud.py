"""CRUD 集成测试 — 覆盖创建/查询/修改/删除/一致性。

跟 role_matrix 互补:role_matrix 关注权限,本文件关注业务正确性与不变量。
"""
from __future__ import annotations

import uuid

from .conftest import (
    SAMPLE_LTC_ID,
    SAMPLE_MODULE_ID,
)


# ---------------------------------------------------------------------------
# LTC 生命周期
# ---------------------------------------------------------------------------

def test_ltc_create_list_update_archive_delete(as_super):
    new_id = f"ltc-{uuid.uuid4().hex[:8]}"
    r = as_super.post("/api/ltcs", json={"id": new_id, "name": "新 LTC"})
    assert r.status_code == 200
    assert r.json()["id"] == new_id

    # 默认不带 archived
    r = as_super.get("/api/ltcs")
    assert new_id in [l["id"] for l in r.json()]

    # 改名
    r = as_super.put(f"/api/ltcs/{new_id}", json={"name": "新名"})
    assert r.json()["name"] == "新名"

    # 归档
    r = as_super.put(f"/api/ltcs/{new_id}", json={"archived": True})
    assert r.json()["archived"] is True
    # 默认列表过滤
    assert new_id not in [l["id"] for l in as_super.get("/api/ltcs").json()]
    # include_archived=true 看到
    assert new_id in [l["id"] for l in as_super.get("/api/ltcs?include_archived=true").json()]

    # 删除(无关联模块)
    r = as_super.delete(f"/api/ltcs/{new_id}")
    assert r.status_code == 200
    assert new_id not in [l["id"] for l in as_super.get("/api/ltcs?include_archived=true").json()]


def test_ltc_id_uniqueness(as_super):
    r = as_super.post("/api/ltcs", json={"id": SAMPLE_LTC_ID, "name": "dup"})
    assert r.status_code == 409


def test_ltc_with_modules_cannot_delete(as_super):
    # SAMPLE_LTC_ID 有 SAMPLE_MODULE_ID 关联
    r = as_super.delete(f"/api/ltcs/{SAMPLE_LTC_ID}")
    assert r.status_code == 422
    # 错误码包含 "modules"
    assert "modules" in r.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Module 生命周期
# ---------------------------------------------------------------------------

def test_module_with_sub_items_and_kpi(as_super):
    mid = uuid.uuid4().hex
    body = {
        "id": mid, "scope": "ltc", "ltc_id": SAMPLE_LTC_ID,
        "group": "测试组", "name": "新模块",
        "owner_open_id": None,
        "kpi_fields": [{"key": "rate", "label": "完成率"}],
        "sub_items": [{"id": "s1", "name": "子项 1", "order": 1}],
    }
    r = as_super.post("/api/modules", json=body)
    assert r.status_code == 200

    # 改 sub_items
    r = as_super.put(f"/api/modules/{mid}", json={
        "sub_items": [
            {"id": "s1", "name": "子项 1", "order": 1},
            {"id": "s2", "name": "子项 2", "order": 2},
        ]
    })
    assert len(r.json()["sub_items"]) == 2

    # 状态写入子项
    r = as_super.put(f"/api/status/{mid}", json={
        "module_color": "green",
        "sub_items_color": {"s1": "green", "s2": "green"},
        "kpi_values": {"rate": "80%"},
        "risk_note": "",
    })
    assert r.status_code == 200
    assert r.json()["sub_items_color"] == {"s1": "green", "s2": "green"}

    # 写入未定义子项 → 422
    r = as_super.put(f"/api/status/{mid}", json={
        "module_color": "green",
        "sub_items_color": {"s_unknown": "green"},
        "risk_note": "",
    })
    assert r.status_code == 422

    # 写入未定义 KPI 键 → 422
    r = as_super.put(f"/api/status/{mid}", json={
        "module_color": "green",
        "kpi_values": {"unknown_kpi": "x"},
        "risk_note": "",
    })
    assert r.status_code == 422


def test_module_id_uniqueness(as_super):
    r = as_super.post("/api/modules", json={
        "id": SAMPLE_MODULE_ID, "scope": "ltc", "ltc_id": SAMPLE_LTC_ID,
        "group": "G", "name": "dup",
    })
    assert r.status_code == 409


def test_module_delete_cascades_status_and_history(as_super):
    mid = uuid.uuid4().hex
    as_super.post("/api/modules", json={
        "id": mid, "scope": "ltc", "ltc_id": SAMPLE_LTC_ID,
        "group": "G", "name": "to-delete",
    })
    as_super.put(f"/api/status/{mid}", json={"module_color": "green", "risk_note": ""})
    # 删
    r = as_super.delete(f"/api/modules/{mid}")
    assert r.status_code == 200
    # status 中已无该 module
    assert mid not in as_super.get("/api/status").json()
    # history 中有 module_deleted 行
    h = as_super.get(f"/api/status/history?module_id={mid}").json()
    assert any(row["kind"] == "module_deleted" for row in h)


def test_module_scope_pdt_must_have_null_ltc(as_super):
    """API 行为:创建 scope=pdt 时若带 ltc_id,显式拒绝 422(对齐 design/06 §8)。"""
    mid = uuid.uuid4().hex
    r = as_super.post("/api/modules", json={
        "id": mid, "scope": "pdt", "ltc_id": SAMPLE_LTC_ID,
        "group": "G", "name": "pdt-mod",
    })
    assert r.status_code == 422
    r2 = as_super.post("/api/modules", json={
        "id": mid, "scope": "pdt", "group": "G", "name": "pdt-mod",
    })
    assert r2.status_code == 200
    assert r2.json()["ltc_id"] is None


def test_module_scope_ltc_requires_ltc_id(as_super):
    r = as_super.post("/api/modules", json={
        "id": uuid.uuid4().hex, "scope": "ltc",
        "group": "G", "name": "no-ltc",
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# 状态历史一致性
# ---------------------------------------------------------------------------

def test_status_write_history_consistency(as_super):
    mid = SAMPLE_MODULE_ID
    # 三次写
    for color in ("green", "yellow", "red"):
        body = {"module_color": color, "risk_note": "x" if color != "green" else ""}
        r = as_super.put(f"/api/status/{mid}", json=body)
        assert r.status_code == 200

    h = as_super.get(f"/api/status/history?module_id={mid}").json()
    assert len(h) >= 3
    # 第一行是最新(后端 reverse 排序),其 after.module_color = "red"
    assert h[0]["after"]["module_color"] == "red"
    # 最后一次的 before 应等于上一次 after
    assert h[0]["before"]["module_color"] == "yellow"
    assert h[1]["before"]["module_color"] == "green"

    # 当前态与最新 after 一致
    current = as_super.get("/api/status").json()
    assert current[mid]["module_color"] == "red"


def test_status_color_must_be_valid(as_super):
    r = as_super.put(f"/api/status/{SAMPLE_MODULE_ID}", json={"module_color": "blue", "risk_note": "x"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Users search
# ---------------------------------------------------------------------------

def test_users_search_limit(as_super):
    r = as_super.get("/api/users/search?limit=50")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
