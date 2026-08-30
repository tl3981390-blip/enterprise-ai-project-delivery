#!/usr/bin/env python3
"""check_role_workflow_coverage.py — ROLE_WORKFLOW_E2E_COVERAGE_GATE（角色工作流 E2E 覆盖门禁）。

来源：Round 1 CAND-003 + Phase B 复发（EXP-012）——冒烟/API 测试不暴露角色能力面缺口，
      只有真实旅程才发现（Round 1：reviewer→approver 链路断裂；Phase B：跨会话审核发现 + Admin 面）。
规则：工作流声明中的每个 required 转换（from→to×roles）必须被至少一条浏览器旅程以匹配角色覆盖；
      缺失即 FAIL——浏览器验收不得在覆盖不全时宣称通过。

用法：
  python check_role_workflow_coverage.py --workflow <workflow.json> --journeys <journeys.json>
输入：
  workflow: {"roles": [...], "transitions": [{"from","to","roles":[...],"required":true|false}, ...]}
  journeys: [{"journey_id": "...", "covers": [{"from","to","role"}, ...]}, ...]
输出：{"status":"PASS|FAIL","required":N,"covered":N,"missing":[{"from","to","roles"}]}
"""
import argparse, json, sys
from pathlib import Path


def check(workflow: dict, journeys: list) -> dict:
    required = [t for t in (workflow.get("transitions") or []) if t.get("required", True)]
    covered = set()
    for journey in journeys or []:
        for c in journey.get("covers") or []:
            covered.add((c.get("from"), c.get("to"), c.get("role")))
    missing = []
    for t in required:
        roles = t.get("roles") or []
        if not any((t.get("from"), t.get("to"), role) in covered for role in roles):
            missing.append({"from": t.get("from"), "to": t.get("to"), "roles": roles})
    return {
        "status": "FAIL" if missing else "PASS",
        "required": len(required),
        "covered": len(required) - len(missing),
        "missing": missing,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", required=True, type=Path)
    p.add_argument("--journeys", required=True, type=Path)
    args = p.parse_args()
    result = check(json.loads(args.workflow.read_text(encoding="utf-8")), json.loads(args.journeys.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
