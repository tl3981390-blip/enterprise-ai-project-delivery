#!/usr/bin/env python3
"""check_understanding_gate.py — 施工前理解门禁 / 任务理解合同结构校验。

用法：
  python check_understanding_gate.py --contract <task_understanding_contract.json>
  python check_understanding_gate.py --help
退出码：0 = 结构 PASS；1 = 结构 FAIL（缺必填字段/来源不完整）。
说明：本脚本只做结构与字段完整性检查；业务含义是否被真正理解由 AI + 人工判定（不替代）。
"""
import argparse
import json
import sys

REQUIRED_FIELDS = [
    "task_id", "user_real_goal", "business_goal", "final_deliverable", "current_state",
    "completed_scope", "work_scope", "explicit_non_goals", "allowed_modify", "forbidden_modify",
    "allowed_tools", "forbidden_tools", "key_constraints", "success_criteria",
    "acceptance_criteria", "evidence_requirements", "blocking_unknowns",
    "provenance", "understanding_status",
]
VALID_STATUS = {"UNDERSTANDING_COMPLETE", "UNDERSTANDING_BLOCKED", "BLOCKED"}
VALID_SOURCES = {"USER_EXPLICIT", "USER_PREVIOUSLY_CONFIRMED", "PROJECT_EVIDENCE", "SYSTEM_OBSERVED", "AI_INFERRED"}
VALID_DISPOSITIONS = {"ADOPT", "REJECT", "NEEDS_MORE_DATA", "DEFERRED"}


def check_requirement_coverage(contract: dict):
    """CONTRACT_SCOPE_COMPLETENESS：合同若声明了来源需求清单（source_requirements），
    每一条都必须在 requirement_coverage 中有明确处置；缺失处置 = 理解不完整。
    来源：v1.2 任务 V1 合同静默漏掉总指令 5 项显式 MUST 的真实失效（V1_2_REQUIREMENT_GAP_AUDIT）。"""
    errors = []
    requirements = contract.get("source_requirements") or []
    if not requirements:
        return errors
    coverage = contract.get("requirement_coverage") or []
    if not coverage:
        errors.append(f"source_requirements 非空但缺 requirement_coverage（{len(requirements)} 条来源需求未处置）")
        return errors
    covered = {}
    for entry in coverage:
        if not isinstance(entry, dict):
            errors.append("requirement_coverage 含非对象条目")
            continue
        rid = entry.get("requirement_id")
        disposition = entry.get("disposition")
        if not rid:
            errors.append("requirement_coverage 条目缺 requirement_id")
            continue
        if disposition not in VALID_DISPOSITIONS:
            errors.append(f"requirement_coverage[{rid}] 处置非法: {disposition}（合法: {sorted(VALID_DISPOSITIONS)}）")
        if rid in covered:
            errors.append(f"requirement_coverage[{rid}] 重复")
        covered[rid] = disposition
    for rid in requirements:
        if rid not in covered:
            errors.append(f"来源需求 [{rid}] 缺处置 → 理解不完整，禁止 UNDERSTANDING_COMPLETE")
    return errors


def check(contract: dict):
    errors = []

    missing = [f for f in REQUIRED_FIELDS if f not in contract]
    if missing:
        errors.append(f"缺必填字段: {missing}")

    st = contract.get("understanding_status")
    if st is not None and st not in VALID_STATUS:
        errors.append(f"understanding_status 非法: {st}（应为 {sorted(VALID_STATUS)}）")

    blocking = contract.get("blocking_unknowns") or []
    if st == "UNDERSTANDING_COMPLETE" and blocking:
        errors.append("存在阻塞性未知项却声明 UNDERSTANDING_COMPLETE → 应 BLOCKED or UNDERSTANDING_BLOCKED")

    # 来源完整性：provenance 的值须为合法来源码
    prov = contract.get("provenance") or {}
    if not isinstance(prov, dict):
        errors.append("provenance 必须为对象")
    else:
        bad = [k for k, v in prov.items() if v not in VALID_SOURCES]
        if bad:
            errors.append(f"provenance 含非法来源码: {bad}（合法: {sorted(VALID_SOURCES)}）")

    # AI_INFERRED 不能单独支撑重大字段（user_real_goal / forbidden_modify / work_scope）
    for critical in ("user_real_goal", "forbidden_modify", "work_scope", "key_constraints"):
        if prov.get(critical) == "AI_INFERRED":
            errors.append(f"关键字段 '{critical}' 仅由 AI_INFERRED 支撑，不得升级为合同事实，须用户确认")

    errors.extend(check_requirement_coverage(contract))

    return errors


def main():
    p = argparse.ArgumentParser(description="施工前理解门禁结构校验")
    p.add_argument("--contract", required=True, help="任务理解合同 JSON 路径")
    args = p.parse_args()

    with open(args.contract, encoding="utf-8") as f:
        data = json.load(f)

    errors = check(data)
    if errors:
        for e in errors:
            print(json.dumps({"level": "error", "msg": e}, ensure_ascii=False))
        print(json.dumps({"gate": "FAIL", "errors": len(errors)}, ensure_ascii=False))
        return 1
    print(json.dumps({"gate": "PASS", "errors": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())