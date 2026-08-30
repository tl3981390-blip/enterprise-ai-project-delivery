#!/usr/bin/env python3
"""check_declared_adapter.py — DECLARED_RUNTIME_ADAPTER_GATE（声明运行时适配器门禁）。

来源：Round 1 CAND-004（compose/架构声明 PostgreSQL 而 adapter 故意不可用）。
规则：声明的生产运行时在 Release 声明时必须有"已启用"的适配器；否则 BLOCKED（架构文档不得冒充交付）。
静默回退（如未声明却用 SQLite 顶替声明栈）是 FAIL，比 BLOCKED 更严重。
开发阶段（release_claimed=false）允许缺适配器，但逐项报告 PENDING。

用法：
  python check_declared_adapter.py --input <runtime_declaration.json>
输入示例：
  {"release_claimed": true, "declared_runtimes": ["postgresql"],
   "adapters": [{"runtime": "postgresql", "enabled": false}],
   "silent_fallback": false}
输出：{"status":"PASS|BLOCKED|FAIL","pending":[...],"missing":[...]}
"""
import argparse, json, sys
from pathlib import Path


def check(declaration: dict) -> dict:
    declared = declaration.get("declared_runtimes") or []
    adapters = {a.get("runtime"): a for a in (declaration.get("adapters") or []) if isinstance(a, dict)}
    missing = sorted(r for r in declared if not adapters.get(r, {}).get("enabled"))
    pending = [] if declaration.get("release_claimed") else list(missing)
    if declaration.get("silent_fallback"):
        return {"status": "FAIL", "missing": missing, "pending": pending, "reason": "silent_fallback_forbidden"}
    if not missing:
        return {"status": "PASS", "missing": [], "pending": []}
    if declaration.get("release_claimed"):
        return {"status": "BLOCKED", "missing": missing, "pending": [], "reason": "declared_runtime_without_enabled_adapter"}
    return {"status": "PASS", "missing": missing, "pending": pending, "reason": "development_state_declared_pending"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    args = p.parse_args()
    result = check(json.loads(args.input.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False))
    return {"PASS": 0, "BLOCKED": 1, "FAIL": 2}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
