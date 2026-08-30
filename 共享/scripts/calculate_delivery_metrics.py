#!/usr/bin/env python3
"""Verify an event log and deterministically calculate delivery metrics/report."""
import argparse,json,sys
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
from telemetry_core import digest_file,verify_chain

def rate(n,d): return round(n/d,6) if d else None
def subset_errors(actual,expected,path=""):
 errors=[]
 for key,value in expected.items():
  here=f"{path}.{key}" if path else key
  if key not in actual: errors.append(f"missing:{here}")
  elif isinstance(value,dict) and isinstance(actual[key],dict): errors.extend(subset_errors(actual[key],value,here))
  elif actual[key]!=value: errors.append(f"mismatch:{here}:expected={value}:actual={actual[key]}")
 return errors
def calculate(events,log):
 voided={e["source_event_id"] for e in events if e.get("event_type")=="CORRECTION_EVENT" and e.get("correction_action")=="VOID"}
 active=[e for e in events if e.get("event_id") not in voided]
 counts=Counter(e["event_type"] for e in active)
 stages={e["stage_id"] for e in active if e["event_type"]=="STAGE_STARTED"}
 first={e["stage_id"] for e in active if e["event_type"]=="STAGE_PASSED" and e.get("first_pass")}
 token_events=[e for e in active if e["event_type"]=="TOKEN_USAGE_RECORDED"]
 if token_events:
  sums={k:sum(e["token_usage"][k] for e in token_events) for k in ("input_tokens","output_tokens","cached_tokens","total_tokens")}; by_stage=defaultdict(int)
  for e in token_events: by_stage[e["stage_id"]]+=e["token_usage"]["total_tokens"]
  rework_corr={e["correlation_id"] for e in active if e["event_type"]=="AI_REWORK_EVENT"}; recovery_corr={e["correlation_id"] for e in active if e["event_type"]=="RECOVERY_ATTEMPT"}
  token={"status":"AVAILABLE",**sums,"tokens_by_stage":dict(sorted(by_stage.items())),"tokens_by_rework":sum(e["token_usage"]["total_tokens"] for e in token_events if e["correlation_id"] in rework_corr),"tokens_by_recovery":sum(e["token_usage"]["total_tokens"] for e in token_events if e["correlation_id"] in recovery_corr)}
 else: token={"status":"NOT_AVAILABLE"}
 times=sorted(datetime.fromisoformat(e["timestamp"].replace("Z","+00:00")) for e in active)
 time_metrics={"status":"AVAILABLE","project_elapsed_seconds":(times[-1]-times[0]).total_seconds()} if len(times)>=2 else {"status":"NOT_AVAILABLE"}
 reliability={"ai_rework_count":counts["AI_REWORK_EVENT"],"drift_detected_count":counts["DRIFT_DETECTED"],"drift_corrected_count":counts["DRIFT_CORRECTED"],"fake_pass_blocked_count":counts["FAKE_PASS_BLOCKED"],"regression_detected_count":counts["REGRESSION_DETECTED"],"gate_failed_count":counts["GATE_FAILED"]}
 recovery={"recovery_attempt_count":counts["RECOVERY_ATTEMPT"],"auto_recovery_success_count":counts["AUTO_RECOVERY_SUCCESS"],"human_intervention_count":counts["HUMAN_INTERVENTION_REQUIRED"]}
 continuity={"suspend_count":counts["SUSPEND_EVENT"],"resume_count":counts["RESUME_EVENT"],"handoff_count":counts["HANDOFF_EVENT"]}
 quality={"total_stages":len(stages),"first_pass_stage_count":len(first),"reopened_stage_count":counts["STAGE_REOPENED"]}
 return {"task_id":events[0]["task_id"] if events else "UNKNOWN","event_count":len(events),"reliability":reliability,"recovery":recovery,"continuity":continuity,"stage_quality":quality,"derived":{"drift_correction_rate":rate(reliability["drift_corrected_count"],reliability["drift_detected_count"]),"auto_recovery_rate":rate(recovery["auto_recovery_success_count"],recovery["recovery_attempt_count"]),"first_pass_stage_rate":rate(quality["first_pass_stage_count"],quality["total_stages"])},"token_metrics":token,"time_metrics":time_metrics,"source_log_sha256":digest_file(log)}
def render(metrics,result):
 t=metrics["token_metrics"]; tm=metrics["time_metrics"]
 return f"""# AI 项目可靠性与交付效率报告

项目：enterprise-ai-project-delivery managed project
Task ID：{metrics['task_id']}
最终结果：{result}

AI返工次数：{metrics['reliability']['ai_rework_count']}
AI漂移次数：{metrics['reliability']['drift_detected_count']}
漂移成功纠正：{metrics['reliability']['drift_corrected_count']}
自动恢复尝试：{metrics['recovery']['recovery_attempt_count']}
自动恢复成功：{metrics['recovery']['auto_recovery_success_count']}
需要人工介入：{metrics['recovery']['human_intervention_count']}
Fake PASS被阻止：{metrics['reliability']['fake_pass_blocked_count']}
Gate失败：{metrics['reliability']['gate_failed_count']}
Regression：{metrics['reliability']['regression_detected_count']}
Stage首次通过：{metrics['stage_quality']['first_pass_stage_count']} / {metrics['stage_quality']['total_stages']}
Stage重新打开：{metrics['stage_quality']['reopened_stage_count']}
Suspend：{metrics['continuity']['suspend_count']}
Resume：{metrics['continuity']['resume_count']}
Handoff：{metrics['continuity']['handoff_count']}
Token：{t['status'] if t['status']=='NOT_AVAILABLE' else t['total_tokens']}
总耗时：{tm.get('project_elapsed_seconds','NOT_AVAILABLE')}
未验证指标：{'Token metrics' if t['status']=='NOT_AVAILABLE' else 'None'}
Evidence：events.jsonl SHA-256 {metrics['source_log_sha256']}
"""
def main():
 p=argparse.ArgumentParser(); p.add_argument("--log",required=True,type=Path); p.add_argument("--anchor",required=True,type=Path); p.add_argument("--output",type=Path); p.add_argument("--report",type=Path); p.add_argument("--result",choices=("PASS","FAIL","BLOCKED"),default="PASS"); p.add_argument("--assert-metrics",type=Path); a=p.parse_args()
 events,errors=verify_chain(a.log,a.anchor)
 if errors: print(json.dumps({"status":"INTEGRITY_FAIL","errors":errors},ensure_ascii=False)); return 2
 metrics=calculate(events,a.log)
 if a.assert_metrics:
  errors=subset_errors(metrics,json.loads(a.assert_metrics.read_text(encoding="utf-8")))
  if errors: print(json.dumps({"status":"METRICS_MISMATCH","errors":errors},ensure_ascii=False)); return 1
 if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 if a.report: a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(render(metrics,a.result),encoding="utf-8")
 print(json.dumps({"status":"PASS","metrics":metrics},ensure_ascii=False)); return 0
if __name__=="__main__":sys.exit(main())
