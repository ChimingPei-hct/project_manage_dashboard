"""自动周快照单元测试(design/09 §6.1)。

只测纯函数与端点;不在测试里跑 60s 循环。
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest


CN_TZ = timezone(timedelta(hours=8))


def test_next_auto_freeze_dt_same_day_future(client):
    _, m = client
    cfg = {"enabled": True, "weekday": 4, "hour": 18, "minute": 0}
    now = datetime(2026, 5, 22, 10, 0, tzinfo=CN_TZ)  # 周五早上 10 点
    nxt = m._next_auto_freeze_dt(now, cfg)
    assert nxt == datetime(2026, 5, 22, 18, 0, tzinfo=CN_TZ)


def test_next_auto_freeze_dt_same_day_past_rolls_to_next_week(client):
    _, m = client
    cfg = {"enabled": True, "weekday": 4, "hour": 18, "minute": 0}
    now = datetime(2026, 5, 22, 19, 0, tzinfo=CN_TZ)  # 周五已过 18 点
    nxt = m._next_auto_freeze_dt(now, cfg)
    assert nxt == datetime(2026, 5, 29, 18, 0, tzinfo=CN_TZ)


def test_next_auto_freeze_dt_cross_week(client):
    _, m = client
    cfg = {"enabled": True, "weekday": 4, "hour": 18, "minute": 0}
    now = datetime(2026, 5, 20, 10, 0, tzinfo=CN_TZ)  # 周三
    nxt = m._next_auto_freeze_dt(now, cfg)
    assert nxt == datetime(2026, 5, 22, 18, 0, tzinfo=CN_TZ)


def test_auto_freeze_cfg_defaults(client):
    _, m = client
    cfg = m._auto_freeze_cfg()
    assert cfg == {"enabled": False, "weekday": 4, "hour": 18, "minute": 0}


def test_put_auto_freeze_persists(client, as_super):
    c, m = client[0], client[1]
    r = as_super.put("/api/config/auto_freeze", json={"enabled": True, "hour": 9, "minute": 30, "weekday": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is True
    assert body["hour"] == 9
    # 再读一次
    r2 = as_super.get("/api/config/auto_freeze")
    assert r2.json()["minute"] == 30
    assert r2.json()["next_run_at"] is not None


def test_put_auto_freeze_validates_range(as_super):
    r = as_super.put("/api/config/auto_freeze", json={"hour": 99})
    assert r.status_code == 422


def test_auto_freeze_loop_writes_snapshot_when_due(client, monkeypatch):
    _, m = client
    # 配置:enabled,目标 = 当下 weekday/hour/minute → 必定触发
    now = datetime.now(CN_TZ)
    cfg = {"enabled": True, "weekday": now.weekday(), "hour": now.hour, "minute": now.minute}
    # 写 config.json 让 _auto_freeze_cfg 读到
    p = m.DATA_DIR / "config.json"
    p.write_text(json.dumps({"auto_freeze": cfg}), encoding="utf-8")

    # 模拟一次 loop 体内的核心检查(不真跑 sleep)
    week_str = m._iso_week_str(now)
    assert not m._snapshot_path(week_str).exists()

    async def run_once():
        cfg2 = m._auto_freeze_cfg()
        if cfg2["enabled"] and now.weekday() == cfg2["weekday"]:
            await m._freeze_snapshot(week_str, frozen_by="system:auto", trigger="auto", force=False)

    asyncio.run(run_once())
    assert m._snapshot_path(week_str).exists()
    doc = json.loads(m._snapshot_path(week_str).read_text(encoding="utf-8"))
    assert doc["trigger"] == "auto"
    assert doc["frozen_by"] == "system:auto"
