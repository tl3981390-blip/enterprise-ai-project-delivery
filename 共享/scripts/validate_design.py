#!/usr/bin/env python3
"""Mechanical checks for specification and test/architecture decisions."""
import argparse,json,sys
from pathlib import Path
SPEC=("requirement_ids","functional","data","interfaces","errors","boundaries","security","permissions","deployment","rollback","acceptance","signoff")
ARCH=("decision","reason","rejected_alternatives","components","interfaces","trust_boundaries","failure_modes","rollback")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--kind",choices=("spec","architecture","test"),required=True); p.add_argument("--input",type=Path,required=True); a=p.parse_args(); d=json.loads(a.input.read_text(encoding="utf-8")); e=[]
 if a.kind=="spec":
  e += [f"missing:{k}" for k in SPEC if not d.get(k)]
  for rid in d.get("requirement_ids",[]):
   ac=d.get("acceptance",{}).get(rid,{})
   if not {"normal","negative"}.issubset(ac): e.append(f"acceptance_incomplete:{rid}")
 elif a.kind=="architecture": e += [f"missing:{k}" for k in ARCH if not d.get(k)]
 else:
  for item in d.get("items",[]):
   if item.get("core") and not item.get("automated"): e.append(f"core_not_automated:{item.get('id')}")
  if not d.get("items"): e.append("test_items_empty")
 print(json.dumps({"status":"PASS" if not e else "FAIL","errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__": sys.exit(main())
