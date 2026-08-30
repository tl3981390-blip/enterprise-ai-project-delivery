#!/usr/bin/env python3
"""Skill-side mock for Harness contract; does not modify the Harness project."""
import argparse,json,sys
from pathlib import Path
LEGAL={"UNDERSTANDING":{"UNDERSTANDING_BLOCKED","UNDERSTANDING_COMPLETE"},"UNDERSTANDING_COMPLETE":{"READY_TO_PLAN"},"READY_TO_PLAN":{"PLANNING"},"PLANNING":{"PLAN_BLOCKED","PLAN_COMPLETE"},"PLAN_COMPLETE":{"READY_TO_EXECUTE"},"READY_TO_EXECUTE":{"EXECUTING"},"EXECUTING":{"EXECUTION_BLOCKED","VERIFYING"},"VERIFYING":{"COMPLETED"}}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--manifest",required=True,type=Path); p.add_argument("--request",required=True,type=Path); a=p.parse_args(); m=json.loads(a.manifest.read_text(encoding="utf-8")); r=json.loads(a.request.read_text(encoding="utf-8")); e=[]; op=r.get("operation")
 if op not in m.get("operations",[]): e.append("operation_unsupported")
 if op=="discover" and not (a.manifest.parent/m.get("entrypoint","")).is_file(): e.append("entrypoint_missing")
 if op=="invoke" and r.get("state")!="UNDERSTANDING": e.append("invoke_must_start_understanding")
 if op=="advance" and r.get("to") not in LEGAL.get(r.get("from"),set()): e.append("illegal_transition")
 if op in {"suspend","resume"} and not r.get("checkpoint"): e.append("checkpoint_missing")
 requested=set(r.get("permissions",[])); allowed=set(m["permissions"]["understanding"] if r.get("state")=="UNDERSTANDING" else m["permissions"]["execute"])
 if not requested.issubset(allowed): e.append("permission_denied")
 print(json.dumps({"status":"PASS" if not e else "FAIL","operation":op,"errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__":sys.exit(main())
