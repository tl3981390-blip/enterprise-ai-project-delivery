#!/usr/bin/env python3
"""Validate incremental execution and honest failure recovery records."""
import argparse,json,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("--input",required=True,type=Path); a=p.parse_args(); d=json.loads(a.input.read_text(encoding="utf-8")); e=[]
 for i,t in enumerate(d.get("tasks",[])):
  for k in ("id","requirement","allowed_scope","failing_test","change","regression","evidence","commit","rollback"):
   if not t.get(k): e.append(f"task[{i}].missing:{k}")
  if t.get("status")=="PASS" and t.get("test_exit_code")!=0: e.append(f"task[{i}].fake_pass")
 for i,f in enumerate(d.get("failures",[])):
  if not f.get("original_evidence"): e.append(f"failure[{i}].evidence_missing")
  if f.get("fix_type") in {"report_only","disable_gate","skip_test"}: e.append(f"failure[{i}].invalid_fix")
  if f.get("attempts",0)>=2 and f.get("status")!="BLOCKED": e.append(f"failure[{i}].must_block")
 if not d.get("tasks"): e.append("tasks_empty")
 print(json.dumps({"status":"PASS" if not e else "FAIL","errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__":sys.exit(main())
