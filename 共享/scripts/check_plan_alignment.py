#!/usr/bin/env python3
"""check_plan_alignment.py — 计划-合同对账检查（PLAN_CONTRACT_ALIGNMENT_CHECK）。

用法：
  python check_plan_alignment.py --plan plan.json --contract contract.json
  python check_plan_alignment.py --help
退出码：0 = 对齐 PASS（READY_TO_EXECUTE 候选）；1 = 对齐 FAIL（计划必须修正）。
检查：每个施工动作是否服务于目标、是否在本轮范围、是否违反禁止项、是否扩大权限、是否新增未授权能力。
业务含义由 AI 判定；本脚本做机械可检查的冲突判定。
"""
import argparse
import json
import re
import sys

# 写改/高风险动作特征 → 触发更严格检查
WRITE_ACTION_TOKEN = re.compile(r"(修改|写入|新建|删除|deploy|migration|install|alter|drop|truncate|update|delete)", re.I)
FORBIDDEN_TOKEN = re.compile(r"(Harness|harness|生产库|生产系统|ERP|CRM|OA|root|admin)", re.I)


def check(plan: dict, contract: dict):
    errors = []
    forbidden = set(contract.get("forbidden_modify") or []) | set(contract.get("forbidden_tools") or [])
    work_scope = set(contract.get("work_scope") or [])
    allowed = set(contract.get("allowed_modify") or [])
    non_goals = set(contract.get("explicit_non_goals") or [])

    for action in plan.get("actions", []):
        desc = action.get("description", "")
        target = action.get("target", "")
        name = action.get("name", "?")
        # 触碰明确禁止项（关键词 + 结构字段）
        hit = [f for f in forbidden if f and (f in desc or f in target)]
        if hit:
            errors.append(f"动作[{name}]违反禁止项: {hit}")
            continue
        if FORBIDDEN_TOKEN.search(desc + " " + target) and ("未获授权" not in desc):
            # 放宽：若 explicitly 标记未授权则交由上层决策，否则视为冲突
            errors.append(f"动作[{name}]疑似触碰高风险/禁止区域: {desc}")
        # 明确非目标
        hit_ng = [f for f in non_goals if f and f in desc]
        if hit_ng:
            errors.append(f"动作[{name}]落在明确非目标: {hit_ng}")
        # 写改动作属范围外且不在允许区
        if WRITE_ACTION_TOKEN.search(desc) and work_scope:
            if not any(s in desc or s in target for s in work_scope) and not any(s in desc or s in target for s in allowed):
                errors.append(f"动作[{name}]为写改但不在 work_scope/allowed 内: {desc}")

    return errors


def main():
    p = argparse.ArgumentParser(description="计划-合同对账检查")
    p.add_argument("--plan", required=True, help="计划 JSON（含 actions[]）")
    p.add_argument("--contract", required=True, help="任务理解合同 JSON")
    args = p.parse_args()

    plan = json.load(open(args.plan, encoding="utf-8"))
    contract = json.load(open(args.contract, encoding="utf-8"))
    errors = check(plan, contract)

    if errors:
        for e in errors:
            print(json.dumps({"level": "error", "msg": e}, ensure_ascii=False))
        print(json.dumps({"alignment": "FAIL", "count": len(errors)}, ensure_ascii=False))
        return 1
    print(json.dumps({"alignment": "PASS", "count": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())