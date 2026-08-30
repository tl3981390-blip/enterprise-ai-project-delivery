#!/usr/bin/env python3
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/"共享"/"scripts"; FIX=Path(__file__).parent

def base(event_id="x",typ="STAGE_STARTED",corr="c"):
 return {"event_id":event_id,"task_id":"NEG-TASK","stage_id":"S","timestamp":"2026-08-30T00:00:00Z","timestamp_source":"SYSTEM_CLOCK","event_type":typ,"detected_by":"test","evidence_refs":["fixture"],"correlation_id":corr}
class TelemetryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.dir=Path(self.tmp.name); self.log=self.dir/"events.jsonl"; self.anchor=self.dir/"anchor.json"
 def tearDown(self): self.tmp.cleanup()
 def record(self,event):
  f=self.dir/"event.json"; f.write_text(json.dumps(event),encoding="utf-8"); return subprocess.run([sys.executable,str(SCRIPTS/"record_delivery_event.py"),"--event",str(f),"--log",str(self.log),"--anchor",str(self.anchor)],capture_output=True,text=True,encoding="utf-8")
 def calculate(self,expected=None):
  cmd=[sys.executable,str(SCRIPTS/"calculate_delivery_metrics.py"),"--log",str(self.log),"--anchor",str(self.anchor)]
  if expected: cmd += ["--assert-metrics",str(expected)]
  return subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8")
 def populate(self,events):
  for event in events: self.assertEqual(self.record(event).returncode,0)
 def test_positive_simulation(self):
  events=json.loads((FIX/"positive_simulation_events.json").read_text(encoding="utf-8")); self.populate(events)
  result=self.calculate(FIX/"positive_expected_metrics.json"); self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_A_claimed_three_drifts_log_has_one(self):
  event=base("d1","DRIFT_DETECTED","drift1"); event.update({"drift_type":"scope","expected":"a","actual":"b"}); self.populate([event]); expected=self.dir/"expected.json"; expected.write_text(json.dumps({"reliability":{"drift_detected_count":3}}),encoding="utf-8"); self.assertEqual(self.calculate(expected).returncode,1)
 def test_B_user_change_cannot_be_ai_rework(self):
  event=base("r1","AI_REWORK_EVENT","r1"); event.update({"root_cause":"user changed scope","root_cause_category":"USER_CHANGE","affected_work":["x"],"recovery_action":"change","outcome":"done"}); self.assertEqual(self.record(event).returncode,1)
 def test_C_token_unavailable_cannot_be_zero(self):
  self.populate([base()]); expected=self.dir/"expected.json"; expected.write_text(json.dumps({"token_metrics":{"status":"NOT_AVAILABLE","total_tokens":0}}),encoding="utf-8"); self.assertEqual(self.calculate(expected).returncode,1)
 def test_D_drift_corrected_requires_detected(self):
  event=base("c1","DRIFT_CORRECTED","c1"); event["source_drift_event_id"]="missing"; self.assertEqual(self.record(event).returncode,1)
 def test_E_auto_recovery_requires_new_test_evidence(self):
  failure=base("f1","FAILURE_EVENT","f1"); attempt=base("a1","RECOVERY_ATTEMPT","a1"); self.populate([failure,attempt]); event=base("s1","AUTO_RECOVERY_SUCCESS","s1"); event.update({"failure_event_id":"f1","recovery_attempt_event_id":"a1","new_test_evidence":[]}); self.assertEqual(self.record(event).returncode,1)
 def test_F_deleted_history_fails_integrity(self):
  self.populate([base("a","STAGE_STARTED","a"),base("b","STAGE_STARTED","b")]); lines=self.log.read_text(encoding="utf-8").splitlines(); self.log.write_text(lines[1]+"\n",encoding="utf-8"); self.assertEqual(self.calculate().returncode,2)
 def test_G_fake_pass_must_be_reported(self):
  self.populate([base("fp","FAKE_PASS_BLOCKED","fp")]); expected=self.dir/"expected.json"; expected.write_text(json.dumps({"reliability":{"fake_pass_blocked_count":0}}),encoding="utf-8"); self.assertEqual(self.calculate(expected).returncode,1)
 def test_H_resume_does_not_reset_metrics(self):
  self.populate([base("su","SUSPEND_EVENT","su"),base("re","RESUME_EVENT","re")]); expected=self.dir/"expected.json"; expected.write_text(json.dumps({"continuity":{"suspend_count":0,"resume_count":0}}),encoding="utf-8"); self.assertEqual(self.calculate(expected).returncode,1)
 def test_I_external_failure_cannot_be_ai_rework(self):
  event=base("r1","AI_REWORK_EVENT","r1"); event.update({"root_cause":"network","root_cause_category":"EXTERNAL_FAILURE","affected_work":["request"],"recovery_action":"retry","outcome":"done"}); self.assertEqual(self.record(event).returncode,1)
 def test_J_duplicate_correlation_rejected(self):
  self.assertEqual(self.record(base("a","FAILURE_EVENT","same-error")).returncode,0); self.assertEqual(self.record(base("b","FAILURE_EVENT","same-error")).returncode,1)
 def test_token_available_is_exact_not_estimated(self):
  event=base("tok","TOKEN_USAGE_RECORDED","tok"); event["token_usage"]={"input_tokens":10,"output_tokens":5,"cached_tokens":2,"total_tokens":15,"provider_evidence":"provider-usage-id"}; self.populate([event]); result=self.calculate(); self.assertEqual(result.returncode,0); metrics=json.loads(result.stdout)["metrics"]; self.assertEqual(metrics["token_metrics"]["total_tokens"],15)
 def test_correction_voids_metric_without_rewriting_history(self):
  drift=base("d","DRIFT_DETECTED","d"); drift.update({"drift_type":"scope","expected":"a","actual":"b"}); correction=base("c","CORRECTION_EVENT","c"); correction.update({"source_event_id":"d","correction_action":"VOID","reason":"classification was wrong"}); self.populate([drift,correction]); result=self.calculate(); self.assertEqual(result.returncode,0); self.assertEqual(json.loads(result.stdout)["metrics"]["reliability"]["drift_detected_count"],0)
 def test_false_first_pass_is_rejected(self):
  failed=base("gf","GATE_FAILED","gf"); failed.update({"gate_id":"S","reason":"failed","blocking_condition":"test"}); self.populate([failed]); passed=base("sp","STAGE_PASSED","sp"); passed["first_pass"]=True; self.assertEqual(self.record(passed).returncode,1)
if __name__=="__main__": unittest.main(verbosity=2)
