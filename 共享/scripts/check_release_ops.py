#!/usr/bin/env python3
"""Validate deployment, license and version-release operations."""
import argparse,json,re,sys
from pathlib import Path
SEMVER=re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-]+)?$")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--kind",choices=("deployment","license","version"),required=True); p.add_argument("--input",required=True,type=Path); a=p.parse_args(); d=json.loads(a.input.read_text(encoding="utf-8")); e=[]
 if a.kind=="deployment":
  for k in ("artifact","install","discover","invoke","restart","logs","rollback"):
   if not d.get(k): e.append(f"missing:{k}")
 elif a.kind=="license":
  for i,x in enumerate(d.get("items",[])):
   if x.get("status") in {"UNKNOWN","CONFLICT","FORBIDDEN"}: e.append(f"license_block:{i}")
  if not d.get("items"): e.append("license_items_empty")
 elif not SEMVER.match(d.get("version","")): e.append("invalid_semver")
 elif "-" not in d.get("version","") and d.get("release_gate")!="PASS": e.append("stable_without_release_gate")
 print(json.dumps({"status":"PASS" if not e else "FAIL","errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__":sys.exit(main())
