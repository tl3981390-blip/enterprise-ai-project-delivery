"""Deterministic integrity and semantic rules for delivery telemetry."""
from __future__ import annotations
import hashlib, json
from datetime import datetime
from pathlib import Path

ZERO_HASH="0"*64
EVENT_TYPES={"AI_REWORK_EVENT","DRIFT_DETECTED","DRIFT_CORRECTED","FAILURE_EVENT","RECOVERY_ATTEMPT","AUTO_RECOVERY_SUCCESS","HUMAN_INTERVENTION_REQUIRED","FAKE_PASS_BLOCKED","GATE_FAILED","REGRESSION_DETECTED","SUSPEND_EVENT","RESUME_EVENT","HANDOFF_EVENT","USER_SCOPE_CHANGE","EXTERNAL_FAILURE","APPROVED_ARCHITECTURE_CHANGE","CORRECTION_EVENT","STAGE_STARTED","STAGE_PASSED","STAGE_REOPENED","TOKEN_USAGE_RECORDED","PROJECT_COMPLETED"}
COMMON=("event_id","task_id","stage_id","timestamp","timestamp_source","event_type","detected_by","evidence_refs","correlation_id")

def canonical(event):
    clean={k:v for k,v in event.items() if k!="event_hash"}
    return json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def digest_event(event): return hashlib.sha256(canonical(event)).hexdigest()
def digest_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_event(event, prior):
    errors=[]
    for key in COMMON:
        if key not in event or event[key] in (None,""): errors.append(f"missing:{key}")
    if event.get("event_type") not in EVENT_TYPES: errors.append("event_type_invalid")
    if event.get("timestamp_source") not in {"SYSTEM_CLOCK","PROVIDER"}: errors.append("timestamp_source_invalid")
    try: datetime.fromisoformat(str(event.get("timestamp","")).replace("Z","+00:00"))
    except ValueError: errors.append("timestamp_invalid")
    if not isinstance(event.get("evidence_refs"),list): errors.append("evidence_refs_invalid")
    ids={x.get("event_id") for x in prior}
    if event.get("event_id") in ids: errors.append("duplicate_event_id")
    if prior and event.get("task_id")!=prior[0].get("task_id"): errors.append("task_id_changed")
    if any(x.get("event_type")==event.get("event_type") and x.get("correlation_id")==event.get("correlation_id") for x in prior): errors.append("duplicate_event_correlation")
    typ=event.get("event_type")
    if typ=="AI_REWORK_EVENT":
        for k in ("root_cause","affected_work","recovery_action","outcome"):
            if not event.get(k): errors.append(f"rework_missing:{k}")
        if event.get("root_cause_category")!="AI_ERROR": errors.append("rework_not_ai_error")
    if typ=="USER_SCOPE_CHANGE" and event.get("root_cause_category") not in (None,"USER_CHANGE"): errors.append("scope_change_category_invalid")
    if typ=="EXTERNAL_FAILURE" and event.get("root_cause_category") not in (None,"EXTERNAL_FAILURE"): errors.append("external_failure_category_invalid")
    if typ=="DRIFT_DETECTED" and not all(k in event for k in ("drift_type","expected","actual")): errors.append("drift_fields_missing")
    if typ=="DRIFT_CORRECTED":
        source=event.get("source_drift_event_id")
        if not any(x.get("event_id")==source and x.get("event_type")=="DRIFT_DETECTED" for x in prior): errors.append("source_drift_missing")
        if any(x.get("event_type")=="DRIFT_CORRECTED" and x.get("source_drift_event_id")==source for x in prior): errors.append("drift_already_corrected")
    if typ=="AUTO_RECOVERY_SUCCESS":
        failure=event.get("failure_event_id"); attempt=event.get("recovery_attempt_event_id")
        if not any(x.get("event_id")==failure and x.get("event_type") in {"FAILURE_EVENT","GATE_FAILED"} for x in prior): errors.append("failure_reference_missing")
        if not any(x.get("event_id")==attempt and x.get("event_type")=="RECOVERY_ATTEMPT" for x in prior): errors.append("recovery_attempt_reference_missing")
        if not event.get("new_test_evidence"): errors.append("new_test_evidence_missing")
        if any(x.get("event_type")=="AUTO_RECOVERY_SUCCESS" and x.get("failure_event_id")==failure for x in prior): errors.append("failure_already_recovered")
    if typ=="GATE_FAILED" and not all(event.get(k) for k in ("gate_id","reason","blocking_condition","evidence_refs")): errors.append("gate_failure_fields_missing")
    if typ=="CORRECTION_EVENT":
        if event.get("source_event_id") not in ids: errors.append("correction_source_missing")
        if event.get("correction_action")!="VOID" or not event.get("reason"): errors.append("correction_invalid")
    if typ=="STAGE_PASSED" and not isinstance(event.get("first_pass"),bool): errors.append("first_pass_missing")
    if typ=="STAGE_PASSED" and event.get("first_pass") and any(x.get("stage_id")==event.get("stage_id") and x.get("event_type") in {"GATE_FAILED","STAGE_REOPENED"} for x in prior): errors.append("false_first_pass")
    if typ=="TOKEN_USAGE_RECORDED":
        usage=event.get("token_usage",{})
        if set(usage)!={"input_tokens","output_tokens","cached_tokens","total_tokens","provider_evidence"}: errors.append("token_usage_fields_invalid")
        elif not usage["provider_evidence"] or any(not isinstance(usage[k],int) or usage[k]<0 for k in ("input_tokens","output_tokens","cached_tokens","total_tokens")): errors.append("token_usage_invalid")
    if typ=="RESUME_EVENT" and sum(x.get("event_type")=="SUSPEND_EVENT" for x in prior)<=sum(x.get("event_type")=="RESUME_EVENT" for x in prior): errors.append("resume_without_suspend")
    return errors

def read_events(log):
    if not log.exists(): return []
    events=[]
    for number,line in enumerate(log.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: events.append(json.loads(line))
        except json.JSONDecodeError as exc: raise ValueError(f"jsonl_invalid:{number}:{exc}") from exc
    return events

def verify_chain(log,anchor):
    try: events=read_events(log)
    except ValueError as exc: return [],[str(exc)]
    errors=[]; prior=[]; previous=ZERO_HASH
    for index,event in enumerate(events):
        if event.get("prev_hash")!=previous: errors.append(f"prev_hash_mismatch:{index}")
        if event.get("event_hash")!=digest_event(event): errors.append(f"event_hash_mismatch:{index}")
        errors.extend(f"event[{index}].{x}" for x in validate_event(event,prior))
        previous=event.get("event_hash",""); prior.append(event)
    if not anchor.exists(): errors.append("anchor_missing")
    else:
        try: state=json.loads(anchor.read_text(encoding="utf-8"))
        except json.JSONDecodeError: state={}; errors.append("anchor_invalid")
        if state.get("event_count")!=len(events): errors.append("anchor_count_mismatch")
        if state.get("last_hash")!=(previous if events else ZERO_HASH): errors.append("anchor_hash_mismatch")
        if log.exists() and state.get("log_sha256")!=digest_file(log): errors.append("anchor_log_digest_mismatch")
    return events,errors
