#!/usr/bin/env python3
"""Evaluate a managed task's legal continuation, wait, resume, resource or handoff decision."""
import argparse, json, sys
from pathlib import Path
from continuation_core import decide, resource_guard, verify_handoff

DECISIONS = ("AUTONOMOUS_CONTINUATION", "ILLEGAL_PASSIVE_STOP", "SUSPENDED_AWAITING_HUMAN", "RESUME_REQUEST", "RESUME_VERIFICATION_PASS", "RESUME_VERIFICATION_FAIL", "RECOVERY_EXHAUSTED", "FINAL_COMPLETE", "CONSTRAINT_CONFLICT", "SAFE_ROLLBACK_ATTEMPT", "ALTERNATIVE_RECOVERY", "MODEL_HANDOFF_READY", "CONTINUE", "PREPARE_CHECKPOINT", "PROACTIVE_MODEL_HANDOFF", "COMPLETE_ATOMIC_UNIT_THEN_HANDOFF", "STOP_NEW_WRITES", "HANDOFF_VERIFICATION_PASS", "HANDOFF_VERIFICATION_FAIL")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--mode", choices=("decide", "guard", "verify-handoff"), default="decide")
    parser.add_argument("--current", type=Path, help="current real project state JSON for verify-handoff")
    parser.add_argument("--expect", choices=DECISIONS)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if args.mode == "guard":
        result = resource_guard(payload)
    elif args.mode == "verify-handoff":
        if not args.current:
            print(json.dumps({"level": "error", "msg": "verify-handoff requires --current"}, ensure_ascii=False), file=sys.stderr)
            return 2
        result = verify_handoff(payload, json.loads(args.current.read_text(encoding="utf-8")))
    else:
        result = decide(payload)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not args.expect or result["decision"] == args.expect else 1


if __name__ == "__main__":
    sys.exit(main())
