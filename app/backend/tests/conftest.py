"""测试公共 fixtures。

每个测试用例独立的 DATA_DIR(tmp_path),预置 6 类身份的 open_id
便于 role_matrix 参数化测试(详见 design/10)。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


SUPER_OID = "ou_super_001"
PDT_ADMIN_OID = "ou_pdt_001"
LTC_ADMIN_THIS_OID = "ou_ltc_this"
LTC_ADMIN_OTHER_OID = "ou_ltc_other"
OWNER_THIS_OID = "ou_owner_this"
GUEST_OID = "ou_guest_001"

SAMPLE_LTC_ID = "ltc-this"
OTHER_LTC_ID = "ltc-other"
SAMPLE_MODULE_ID = "mod-this"


def _seed_data_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / "weekly_snapshots").mkdir(exist_ok=True)
    (d / "pdt.json").write_text(json.dumps({
        "code": "demo", "name": "Demo PDT", "description": "",
        "milestones": [], "updated_at": "2026-05-22T00:00:00+08:00", "metadata": {},
    }), encoding="utf-8")
    (d / "ltcs.json").write_text(json.dumps([
        {"id": SAMPLE_LTC_ID, "name": "Sample LTC", "order": 1, "archived": False,
         "created_at": "2026-05-22T00:00:00+08:00", "updated_at": "2026-05-22T00:00:00+08:00", "metadata": {}},
        {"id": OTHER_LTC_ID, "name": "Other LTC", "order": 2, "archived": False,
         "created_at": "2026-05-22T00:00:00+08:00", "updated_at": "2026-05-22T00:00:00+08:00", "metadata": {}},
    ]), encoding="utf-8")
    (d / "modules.json").write_text(json.dumps([
        {
            "id": SAMPLE_MODULE_ID, "scope": "ltc", "ltc_id": SAMPLE_LTC_ID,
            "group": "G1", "name": "Sample Module", "order": 1,
            "owner_open_id": OWNER_THIS_OID,
            "kpi_fields": [], "sub_items": [],
            "created_at": "2026-05-22T00:00:00+08:00",
            "updated_at": "2026-05-22T00:00:00+08:00",
            "metadata": {},
        }
    ]), encoding="utf-8")
    (d / "module_status.json").write_text("{}", encoding="utf-8")
    (d / "module_updates.jsonl").write_text("", encoding="utf-8")
    (d / "super_admins.json").write_text(json.dumps([{"open_id": SUPER_OID, "name": "Super"}]), encoding="utf-8")
    (d / "pdt_admins.json").write_text(json.dumps([PDT_ADMIN_OID]), encoding="utf-8")
    (d / "ltc_admins.json").write_text(json.dumps({SAMPLE_LTC_ID: [LTC_ADMIN_THIS_OID], OTHER_LTC_ID: [LTC_ADMIN_OTHER_OID]}), encoding="utf-8")
    (d / "user_registry.json").write_text(json.dumps([]), encoding="utf-8")
    (d / "config.json").write_text(json.dumps({"port": 18080, "instance_name": "test"}), encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "design"
    _seed_data_dir(d)
    return d


@pytest.fixture
def client(data_dir: Path, monkeypatch):
    """每个测试一个独立 app(DATA_DIR 隔离)。"""
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("DEV_LOGIN", "0")  # 测试不走 dev 后门,显式塞 cookie
    # 强制重载 main 以拾取新 DATA_DIR
    for mod in list(sys.modules):
        if mod == "main" or mod.startswith("main."):
            del sys.modules[mod]
    import main as backend_main  # noqa: WPS433
    return TestClient(backend_main.app), backend_main


def _login_cookie(backend_main, open_id: str) -> dict:
    token = backend_main._create_jwt(open_id, name=open_id)
    return {backend_main.COOKIE_NAME: token}


@pytest.fixture
def as_super(client):
    c, m = client
    c.cookies.update(_login_cookie(m, SUPER_OID))
    return c


@pytest.fixture
def as_pdt_admin(client):
    c, m = client
    c.cookies.update(_login_cookie(m, PDT_ADMIN_OID))
    return c


@pytest.fixture
def as_ltc_admin_this(client):
    c, m = client
    c.cookies.update(_login_cookie(m, LTC_ADMIN_THIS_OID))
    return c


@pytest.fixture
def as_ltc_admin_other(client):
    c, m = client
    c.cookies.update(_login_cookie(m, LTC_ADMIN_OTHER_OID))
    return c


@pytest.fixture
def as_owner_this(client):
    c, m = client
    c.cookies.update(_login_cookie(m, OWNER_THIS_OID))
    return c


@pytest.fixture
def as_guest(client):
    c, m = client
    c.cookies.update(_login_cookie(m, GUEST_OID))
    return c
