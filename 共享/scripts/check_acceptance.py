#!/usr/bin/env python3
"""Validate browser applicability, four-role signoff and evidence integrity."""
import argparse,hashlib,json,sys
from pathlib import Path
ALLOWED={"test_result","browser_capture","api_response","file_observation","git_record","database_readback","role_signoff","manifest"}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--input",required=True,type=Path); p.add_argument("--root",required=True,type=Path); a=p.parse_args(); d=json.loads(a.input.read_text(encoding="utf-8")); e=[]
 browser=d.get("browser",{})
 if browser.get("status")=="NOT_APPLICABLE" and not (browser.get("reason") and browser.get("surface_evidence") and browser.get("reviewer")): e.append("browser_na_unsubstantiated")
 elif browser.get("status")!="PASS" and browser.get("status")!="NOT_APPLICABLE": e.append("browser_not_passed")
 roles={x.get("role"):x for x in d.get("roles",[])}
 for role in ("product","engineering","security","end_user"):
  x=roles.get(role,{})
  if x.get("decision")!="PASS" or not x.get("reviewer") or not x.get("evidence") or x.get("blocking_findings"): e.append(f"role_invalid:{role}")
 for i,x in enumerate(d.get("evidence",[])):
  if x.get("type") not in ALLOWED: e.append(f"evidence_type_invalid:{i}"); continue
  path=a.root/x.get("path","")
  if not path.is_file(): e.append(f"evidence_missing:{i}"); continue
  if hashlib.sha256(path.read_bytes()).hexdigest()!=x.get("sha256"): e.append(f"evidence_hash_mismatch:{i}")
 print(json.dumps({"status":"PASS" if not e else "FAIL","errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__":sys.exit(main())
