"""飞书 OAuth 端点测试(design/11 §6.1)。

不打真网络;只验证端点形状、未配置时的 501、code 缺失的 400、租户白名单逻辑。
真实 OAuth 走完需要在浏览器里用 cli_a943bae284f89cd1 登录,详见 系统/飞书app申请清单.md。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from .conftest import _seed_data_dir  # noqa: E402


@pytest.fixture
def feishu_off_client(tmp_path, monkeypatch):
    """没有飞书凭证时的客户端。"""
    d = tmp_path / "design"
    _seed_data_dir(d)
    monkeypatch.setenv("DATA_DIR", str(d))
    monkeypatch.setenv("DEV_LOGIN", "0")
    monkeypatch.delenv("FEISHU_APP_ID", raising=False)
    monkeypatch.delenv("FEISHU_APP_SECRET", raising=False)
    monkeypatch.delenv("LARK_APP_ID", raising=False)
    monkeypatch.delenv("LARK_APP_SECRET", raising=False)
    for mod in list(sys.modules):
        if mod == "main" or mod.startswith("main."):
            del sys.modules[mod]
    import main as backend_main  # noqa: WPS433
    from fastapi.testclient import TestClient
    return TestClient(backend_main.app), backend_main


@pytest.fixture
def feishu_on_client(tmp_path, monkeypatch):
    """有凭证的客户端,但 callback 实际请求会被 monkeypatch 拦截。"""
    d = tmp_path / "design"
    _seed_data_dir(d)
    monkeypatch.setenv("DATA_DIR", str(d))
    monkeypatch.setenv("DEV_LOGIN", "0")
    monkeypatch.setenv("FEISHU_APP_ID", "cli_test_app_id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "test_secret")
    for mod in list(sys.modules):
        if mod == "main" or mod.startswith("main."):
            del sys.modules[mod]
    import main as backend_main  # noqa: WPS433
    from fastapi.testclient import TestClient
    return TestClient(backend_main.app), backend_main, d


def test_login_url_501_when_not_configured(feishu_off_client):
    c, _ = feishu_off_client
    r = c.get("/api/feishu/login_url")
    assert r.status_code == 501
    assert r.json()["detail"]["code"] == "feishu_disabled"


def test_login_url_200_when_configured(feishu_on_client):
    c, _, _ = feishu_on_client
    r = c.get("/api/feishu/login_url?redirect_uri=http://localhost:15173/feishu/callback")
    assert r.status_code == 200
    body = r.json()
    assert "cli_test_app_id" in body["login_url"]
    assert "redirect_uri=" in body["login_url"]
    assert body["state"]


def test_callback_missing_code_400(feishu_on_client):
    c, _, _ = feishu_on_client
    r = c.post("/api/feishu/callback", json={})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "code_missing"


def test_callback_tenant_whitelist(feishu_on_client, monkeypatch):
    c, backend_main, d = feishu_on_client
    # 给 config.json 加白名单
    cfg = json.loads((d / "config.json").read_text("utf-8"))
    cfg["allowed_tenant_keys"] = ["tenant_allow_xyz"]
    (d / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    # 拦截上游飞书调用,模拟返回一个 tenant_key 不在白名单
    def fake_user_info_from_code(code):
        return {
            "open_id": "ou_test_user",
            "name": "测试用户",
            "avatar_url": "",
            "tenant_key": "tenant_NOT_allowed",
        }
    monkeypatch.setattr(backend_main, "_feishu_user_info_from_code", fake_user_info_from_code)
    r = c.post("/api/feishu/callback", json={"code": "fake_code"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "tenant_forbidden"


def test_callback_success_signs_cookie(feishu_on_client, monkeypatch):
    c, backend_main, d = feishu_on_client
    # 白名单设为允许或留空都行,这里测允许
    cfg = json.loads((d / "config.json").read_text("utf-8"))
    cfg["allowed_tenant_keys"] = ["tenant_ok"]
    (d / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    monkeypatch.setattr(backend_main, "_feishu_user_info_from_code", lambda code: {
        "open_id": "ou_new_user",
        "name": "新用户",
        "avatar_url": "https://example/x.png",
        "tenant_key": "tenant_ok",
    })
    r = c.post("/api/feishu/callback", json={"code": "fake_code"})
    assert r.status_code == 200
    body = r.json()
    assert body["open_id"] == "ou_new_user"
    assert body["name"] == "新用户"
    # Cookie 已签
    assert backend_main.COOKIE_NAME in r.cookies
    # user_registry upsert
    users = json.loads((d / "user_registry.json").read_text("utf-8"))
    assert any(u["open_id"] == "ou_new_user" for u in users)

    # 用 cookie 调 /api/auth/me 应通过
    r2 = c.get("/api/auth/me")
    assert r2.status_code == 200
    assert r2.json()["open_id"] == "ou_new_user"
    assert r2.json()["feishu_configured"] is True
