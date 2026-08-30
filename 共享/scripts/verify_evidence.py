#!/usr/bin/env python3
"""Verify every evidence index against current files and manifest."""
import argparse,hashlib,json,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("--evidence-dir",required=True,type=Path); a=p.parse_args(); e=[]; checked=0
 for index in a.evidence_dir.glob("*/index.json"):
  d=json.loads(index.read_text(encoding="utf-8")); stage=index.parent
  expected=[]
  for x in d.get("files",[]):
   path=stage/x["name"]
   if not path.is_file(): e.append(f"missing:{stage.name}/{x['name']}"); continue
   digest=hashlib.sha256(path.read_bytes()).hexdigest(); expected.append(f"{digest}  {x['name']}")
   if digest!=x.get("sha256"): e.append(f"hash:{stage.name}/{x['name']}")
   checked+=1
  manifest=stage/"manifest.sha256"
  if not manifest.is_file(): e.append(f"manifest_missing:{stage.name}")
  else:
   actual=[line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
   if not expected and len(actual)==1 and len(actual[0])==64:
    legacy=[x for x in stage.iterdir() if x.is_file() and x.name not in {"index.json","manifest.sha256"}]
    if len(legacy)!=1 or hashlib.sha256(legacy[0].read_bytes()).hexdigest().lower()!=actual[0].lower(): e.append(f"legacy_manifest_mismatch:{stage.name}")
    else: checked+=1
   elif actual!=expected: e.append(f"manifest_mismatch:{stage.name}")
 print(json.dumps({"status":"PASS" if not e else "FAIL","checked":checked,"errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__":sys.exit(main())
