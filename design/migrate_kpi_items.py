#!/usr/bin/env python3
"""一次性脚本:把 module_status.json 里 kpi_items[*] 的旧字段迁移到新字段。

label  → goal
value  → actual
target → 丢弃
color  → 保留

跨多个 DATA_DIR(main 模板 / data 分支 worktree)反复执行幂等。

用法:
  python3 design/migrate_kpi_items.py <module_status.json 路径> [...]
不传参时默认改本仓库的 design/module_status.json。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def migrate_one(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return 0
    data = json.loads(raw)
    if not isinstance(data, dict):
        return 0
    changed = 0
    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        items = entry.get("kpi_items")
        if not isinstance(items, list):
            continue
        new_items = []
        touched = False
        for it in items:
            if not isinstance(it, dict):
                continue
            has_old = "label" in it or "value" in it or "target" in it
            has_new = "goal" in it or "actual" in it
            goal = (it.get("goal") if "goal" in it else it.get("label")) or ""
            actual = (it.get("actual") if "actual" in it else it.get("value")) or ""
            color = it.get("color") or ""
            goal = str(goal).strip()
            actual = str(actual).strip()
            if not goal and not actual:
                touched = True  # 丢弃空行
                continue
            new_items.append({"goal": goal, "actual": actual, "color": color})
            if has_old or not has_new or set(it.keys()) != {"goal", "actual", "color"}:
                touched = True
        if touched:
            entry["kpi_items"] = new_items
            changed += 1
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        targets = [Path(p) for p in argv[1:]]
    else:
        targets = [Path(__file__).resolve().parent / "module_status.json"]
    total = 0
    for p in targets:
        if not p.exists():
            print(f"[skip] {p} (not found)")
            continue
        n = migrate_one(p)
        print(f"[ok] {p}: {n} entries migrated")
        total += n
    print(f"done. total entries migrated: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
