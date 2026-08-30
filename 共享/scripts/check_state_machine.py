#!/usr/bin/env python3
"""check_state_machine.py — 状态机合法跳转校验。

用法：
  python check_state_machine.py --legal tests/evals/state_machine/legal_transitions.json --walk walk.json
退出码：0 = 全部合法；1 = 存在非法跳转。
依据：`00_总控/references/状态与权限矩阵.md`。禁止 UNDERSTANDING 直接跳 EXECUTING 等。
"""
import argparse
import json
import sys

# 内置合法跳转集（与状态与权限矩阵.md 一致）
DEFAULT_LEGAL = {
    "UNDERSTANDING": {"UNDERSTANDING_BLOCKED", "UNDERSTANDING_COMPLETE", "BLOCKED"},
    "UNDERSTANDING_BLOCKED": {"UNDERSTANDING", "BLOCKED"},
    "UNDERSTANDING_COMPLETE": {"READY_TO_PLAN", "BLOCKED"},
    "READY_TO_PLAN": {"PLANNING", "BLOCKED"},
    "PLANNING": {"PLAN_BLOCKED", "PLAN_COMPLETE", "BLOCKED"},
    "PLAN_BLOCKED": {"READY_TO_PLAN", "BLOCKED"},
    "PLAN_COMPLETE": {"READY_TO_EXECUTE", "BLOCKED"},
    "READY_TO_EXECUTE": {"EXECUTING", "BLOCKED"},
    "EXECUTING": {"EXECUTION_BLOCKED", "VERIFYING", "BLOCKED"},
    "EXECUTION_BLOCKED": {"EXECUTING", "BLOCKED"},
    "VERIFYING": {"COMPLETED", "EXECUTING", "BLOCKED"},
    "COMPLETED": set(),
}


def check(states: list, legal: dict):
    errors = []
    if not states:
        errors.append("空状态序列")
        return errors
    state = states[0]
    for nxt in states[1:]:
        if state not in legal:
            errors.append(f"未知状态: {state}")
            break
        if nxt not in legal.get(state, set()):
            errors.append(f"非法跳转: {state} -> {nxt}")
            break
        state = nxt
    if not errors and state not in {"COMPLETED", "UNDERSTANDING_BLOCKED", "BLOCKED"}:
        errors.append(f"未停在受理终态（COMPLETED/BLOCKED）: 停在 {state}")
    return errors


def main():
    p = argparse.ArgumentParser(description="状态机合法跳转校验")
    p.add_argument("--legal", default=None, help="合法跳转 JSON（可选）")
    p.add_argument("--walk", required=True, help="待校验的状态序列 JSON（字符串数组或 {to:...} 数组）")
    args = p.parse_args()

    legal = DEFAULT_LEGAL
    if args.legal:
        legal = json.load(open(args.legal, encoding="utf-8"))
    walk = json.load(open(args.walk, encoding="utf-8"))
    errors = check(walk if isinstance(walk, list) else walk.get("transitions", []), legal)

    if errors:
        for e in errors:
            print(json.dumps({"level": "error", "msg": e}, ensure_ascii=False))
        print(json.dumps({"state_machine": "FAIL", "count": len(errors)}, ensure_ascii=False))
        return 1
    print(json.dumps({"state_machine": "PASS", "count": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())