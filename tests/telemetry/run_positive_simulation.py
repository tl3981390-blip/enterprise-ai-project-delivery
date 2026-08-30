#!/usr/bin/env python3
"""Materialize the isolated positive simulation through the production CLIs."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/"共享"/"scripts"; FIX=Path(__file__).parent
def main():
 p=argparse.ArgumentParser(); p.add_argument("--output-dir",required=True,type=Path); a=p.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True); log=a.output_dir/"events.jsonl"; anchor=a.output_dir/"events.anchor.json"; metrics=a.output_dir/"metrics.json"; report=a.output_dir/"final_reliability_report.md"
 if log.exists() or anchor.exists(): print("output already exists",file=sys.stderr); return 2
 events=json.loads((FIX/"positive_simulation_events.json").read_text(encoding="utf-8"))
 with tempfile.TemporaryDirectory() as td:
  event_file=Path(td)/"event.json"
  for event in events:
   event_file.write_text(json.dumps(event),encoding="utf-8")
   run=subprocess.run([sys.executable,str(SCRIPTS/"record_delivery_event.py"),"--event",str(event_file),"--log",str(log),"--anchor",str(anchor)],capture_output=True,text=True,encoding="utf-8")
   if run.returncode: print(run.stdout+run.stderr,file=sys.stderr); return run.returncode
 run=subprocess.run([sys.executable,str(SCRIPTS/"calculate_delivery_metrics.py"),"--log",str(log),"--anchor",str(anchor),"--output",str(metrics),"--report",str(report),"--assert-metrics",str(FIX/"positive_expected_metrics.json")],capture_output=True,text=True,encoding="utf-8")
 print(run.stdout.strip()); return run.returncode
if __name__=="__main__":sys.exit(main())
