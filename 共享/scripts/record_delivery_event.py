#!/usr/bin/env python3
"""Append one validated delivery event and advance the integrity anchor."""
import argparse,json,os,sys
from pathlib import Path
from telemetry_core import ZERO_HASH,digest_event,digest_file,read_events,validate_event,verify_chain
def main():
 p=argparse.ArgumentParser(); p.add_argument("--event",required=True,type=Path); p.add_argument("--log",required=True,type=Path); p.add_argument("--anchor",required=True,type=Path); p.add_argument("--dry-run",action="store_true"); a=p.parse_args()
 event=json.loads(a.event.read_text(encoding="utf-8")); events=[]
 if a.log.exists() or a.anchor.exists():
  events,integrity=verify_chain(a.log,a.anchor)
  if integrity: print(json.dumps({"status":"INTEGRITY_FAIL","errors":integrity},ensure_ascii=False)); return 2
 errors=validate_event(event,events)
 if errors: print(json.dumps({"status":"FAIL","errors":errors},ensure_ascii=False)); return 1
 event["prev_hash"]=events[-1]["event_hash"] if events else ZERO_HASH; event["event_hash"]=digest_event(event)
 if a.dry_run: print(json.dumps({"status":"DRY_RUN","event":event},ensure_ascii=False)); return 0
 a.log.parent.mkdir(parents=True,exist_ok=True); a.anchor.parent.mkdir(parents=True,exist_ok=True)
 with a.log.open("a",encoding="utf-8",newline="\n") as stream:
  stream.write(json.dumps(event,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"); stream.flush(); os.fsync(stream.fileno())
 state={"task_id":event["task_id"],"event_count":len(events)+1,"last_hash":event["event_hash"],"log_sha256":digest_file(a.log)}
 temp=a.anchor.with_suffix(a.anchor.suffix+".tmp"); temp.write_text(json.dumps(state,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8"); os.replace(temp,a.anchor)
 print(json.dumps({"status":"APPENDED","event_id":event["event_id"],"event_hash":event["event_hash"],"event_count":len(events)+1},ensure_ascii=False)); return 0
if __name__=="__main__":sys.exit(main())
