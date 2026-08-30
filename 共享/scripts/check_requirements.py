#!/usr/bin/env python3
"""Validate requirement JSON for explicit, testable enterprise scope."""
import argparse, json, sys
from pathlib import Path
BANNED=("尽量","基本","适当","大概","优化一下","应该可以")
REQUIRED=("id","priority","statement","acceptance","source")
def check(data):
    errors=[]; items=data.get("requirements",[])
    if not items: errors.append("requirements_empty")
    for i,item in enumerate(items):
        for key in REQUIRED:
            if not item.get(key): errors.append(f"requirements[{i}].{key}_missing")
        if item.get("priority") not in {"MUST","SHOULD","COULD","WONT"}: errors.append(f"requirements[{i}].priority_invalid")
        text=json.dumps(item,ensure_ascii=False)
        for word in BANNED:
            if word in text: errors.append(f"requirements[{i}].ambiguous:{word}")
        if item.get("priority")=="MUST" and not {"normal","negative"}.issubset(set(item.get("acceptance",{}))): errors.append(f"requirements[{i}].must_acceptance_incomplete")
    return errors
def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True,type=Path); a=p.parse_args(); errors=check(json.loads(a.input.read_text(encoding="utf-8")))
    print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors},ensure_ascii=False)); return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
