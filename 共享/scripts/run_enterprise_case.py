#!/usr/bin/env python3
"""Run a realistic enterprise case through the mechanical delivery gates."""
import argparse,json,subprocess,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("--case",required=True,type=Path); p.add_argument("--root",required=True,type=Path); a=p.parse_args(); scripts=a.root/"共享"/"scripts"
 checks=[("requirements",[scripts/"check_requirements.py","--input",a.case/"requirements.json"]),("spec",[scripts/"validate_design.py","--kind","spec","--input",a.case/"spec.json"]),("rag",[scripts/"check_governance.py","--kind","rag","--input",a.case/"rag.json"]),("permission",[scripts/"check_governance.py","--kind","permission","--input",a.case/"permission.json"]),("execution",[scripts/"check_execution.py","--input",a.case/"execution.json"]),("acceptance",[scripts/"check_acceptance.py","--root",a.root,"--input",a.case/"acceptance.json"])]
 results=[]
 for name,args in checks:
  run=subprocess.run([sys.executable,*map(str,args)],capture_output=True,text=True,encoding="utf-8")
  results.append({"name":name,"exit_code":run.returncode,"stdout":run.stdout.strip()})
 status="PASS" if all(x["exit_code"]==0 for x in results) else "FAIL"; print(json.dumps({"status":status,"results":results},ensure_ascii=False)); return 0 if status=="PASS" else 1
if __name__=="__main__":sys.exit(main())
