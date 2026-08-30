#!/usr/bin/env python3
"""Restore one file inside an explicitly allowed root; supports dry-run."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser(); p.add_argument("--source",required=True,type=Path); p.add_argument("--target",required=True,type=Path); p.add_argument("--allowed-root",required=True,type=Path); p.add_argument("--dry-run",action="store_true"); a=p.parse_args()
 root=a.allowed_root.resolve(); src=a.source.resolve(); dst=a.target.resolve()
 if root not in dst.parents or not src.is_file(): print(json.dumps({"status":"DENY"})); return 2
 if not a.dry_run: dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 digest=hashlib.sha256(src.read_bytes()).hexdigest(); print(json.dumps({"status":"DRY_RUN" if a.dry_run else "RESTORED","sha256":digest})); return 0
if __name__=="__main__":sys.exit(main())
