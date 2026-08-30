#!/usr/bin/env python3
"""Check RAG, agent separation, permissions and enterprise governance."""
import argparse,json,sys
from pathlib import Path
def check(kind,d):
 e=[]
 if kind=="rag":
  for i,c in enumerate(d.get("claims",[])):
   if not c.get("source") or not c.get("locator") or not c.get("supports_claim"): e.append(f"claim_unverified:{i}")
   if not c.get("authorized"): e.append(f"claim_unauthorized:{i}")
   if c.get("superseded"): e.append(f"claim_superseded:{i}")
  if not d.get("claims") and not d.get("refusal"): e.append("no_evidence_without_refusal")
 elif kind=="permission":
  allowed={"READ","WRITE","DELETE","EXECUTE","ADMIN","EXTERNAL"}
  for i,x in enumerate(d.get("requests",[])):
   if x.get("action") not in allowed: e.append(f"unknown_action:{i}")
   if not x.get("matched_rule") or x.get("decision")!="ALLOW": e.append(f"denied:{i}")
   if x.get("action") in {"DELETE","ADMIN","EXTERNAL"} and not x.get("approval"): e.append(f"approval_missing:{i}")
   if x.get("production"): e.append(f"production_forbidden:{i}")
 elif kind=="agent":
  for i,x in enumerate(d.get("roles",[])):
   duties=set(x.get("duties",[]))
   if "execute" in duties and "approve" in duties: e.append(f"self_approval:{i}")
  if not d.get("roles"): e.append("roles_empty")
 else:
  for k in ("data_classification","purpose","retention","owner","audit","incident_response","change_approval"):
   if not d.get(k): e.append(f"missing:{k}")
 return e
def main():
 p=argparse.ArgumentParser(); p.add_argument("--kind",choices=("rag","permission","agent","governance"),required=True); p.add_argument("--input",type=Path,required=True); a=p.parse_args(); e=check(a.kind,json.loads(a.input.read_text(encoding="utf-8"))); print(json.dumps({"status":"PASS" if not e else "FAIL","errors":e},ensure_ascii=False)); return 1 if e else 0
if __name__=="__main__": sys.exit(main())
