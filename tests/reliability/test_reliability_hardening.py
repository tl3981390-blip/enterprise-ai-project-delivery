#!/usr/bin/env python3
import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from continuation_core import decide, validate_human_package
from telemetry_core import ZERO_HASH, digest_event, verify_chain


def action(identifier="S2"):
    return {"id": identifier, "status": "PENDING", "legal": True}


def package(task_id="T"):
    return {
        "task_id": task_id, "current_stage": "S1", "blocker_id": "B1", "failure_type": "PERMISSION", "what_failed": "credential absent",
        "failure_evidence": ["evidence/failure.json"], "recovery_attempts": ["attempt-1"], "why_auto_recovery_failed": "requires external grant",
        "rollback_status": "NOT_APPLICABLE", "alternative_paths_attempted": ["none within scope"], "exact_user_action_required": "grant scoped access",
        "authorization_required": True, "minimum_required_permission": "read:target", "resume_condition": "permission visible",
        "resume_verification": "read-only access check", "next_safe_action_after_resume": "rerun failed gate", "fallback_if_resume_fails": "remain suspended",
        "last_known_good_checkpoint": {"task_id": task_id, "stage_id": "S1", "contract_hash": "c", "git_head": "h", "worktree_identity": "clean", "runtime_identity": "r", "last_passed_gate": "G", "evidence_anchor": "a", "timestamp": "2026-08-30T00:00:00Z"}
    }


class ContinuationTests(unittest.TestCase):
    def test_1_stage_pass_auto_continues(self):
        self.assertEqual(decide({"actions": [action()]} )["decision"], "AUTONOMOUS_CONTINUATION")

    def test_2_three_passes_need_no_human_continue(self):
        workflow = {"actions": [action("S1"), action("S2"), action("S3")]}
        for expected in ("S1", "S2", "S3"):
            result = decide(workflow); self.assertEqual(result["decision"], "AUTONOMOUS_CONTINUATION"); self.assertEqual(result["next_action"]["id"], expected)
            result["next_action"]["status"] = "PASSED"

    def test_3_recovered_failure_continues(self):
        self.assertEqual(decide({"actions": [action("after-revalidation")], "blocker": {"unrecoverable": False}})["decision"], "AUTONOMOUS_CONTINUATION")

    def test_4_recovery_exhaustion_has_complete_human_package(self):
        result = decide({"human_gate": "RECOVERY_EXHAUSTED", "human_recovery_package": package()})
        self.assertEqual(result["decision"], "SUSPENDED_AWAITING_HUMAN"); self.assertEqual(result["human_package_errors"], [])

    def test_5_continue_after_real_resolution_revalidates(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "B"}, "resume_audit": {"blocker_resolved": True, "candidate_identity_match": True, "contract_hash_match": True, "runtime_identity_match": True, "evidence_identity_match": True}, "actions": [action()]})
        self.assertEqual(result["decision"], "RESUME_VERIFICATION_PASS"); self.assertTrue(result["can_continue"])

    def test_6_unresolved_continue_does_not_resume(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "B"}, "resume_audit": {"blocker_resolved": False, "candidate_identity_match": True}, "actions": [action()]})
        self.assertEqual(result["decision"], "RESUME_VERIFICATION_FAIL")

    def test_7_new_permission_requires_human_gate(self):
        self.assertEqual(decide({"human_gate": "HUMAN_AUTHORIZATION_REQUIRED", "human_recovery_package": package()})["decision"], "SUSPENDED_AWAITING_HUMAN")

    def test_8_continue_does_not_grant_permission(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "permission"}, "resume_audit": {"blocker_resolved": False, "candidate_identity_match": True}})
        self.assertEqual(result["decision"], "RESUME_VERIFICATION_FAIL")

    def test_9_user_pause_requires_recovery_package(self):
        result = decide({"human_gate": "USER_REQUESTED_PAUSE", "human_recovery_package": package()})
        self.assertEqual(result["decision"], "SUSPENDED_AWAITING_HUMAN"); self.assertEqual(result["human_package_errors"], [])

    def test_10_final_complete_does_not_restart(self):
        self.assertEqual(decide({"task_complete": True, "actions": [action()]})["decision"], "FINAL_COMPLETE")

    def test_passive_stop_is_rejected(self):
        self.assertEqual(decide({"actions": [action()], "passive_stop_claim": True})["decision"], "ILLEGAL_PASSIVE_STOP")

    def test_bad_human_package_is_not_acceptable(self):
        bad = package(); del bad["resume_condition"]
        self.assertIn("missing:resume_condition", validate_human_package(bad))

    def test_rescue_old_evidence_cannot_prove_new_candidate(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "B"}, "resume_audit": {"blocker_resolved": True, "candidate_identity_match": False}, "actions": [action()]})
        self.assertEqual(result["reason"], "candidate_identity_mismatch")

    def test_rescue_old_runtime_is_blocked(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "B"}, "resume_audit": {"blocker_resolved": True, "candidate_identity_match": True, "runtime_identity_match": False}, "actions": [action()]})
        self.assertEqual(result["reason"], "runtime_identity_match")

    def test_rescue_contract_hash_mismatch_is_blocked(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "B"}, "resume_audit": {"blocker_resolved": True, "candidate_identity_match": True, "contract_hash_match": False}, "actions": [action()]})
        self.assertEqual(result["reason"], "contract_hash_match")

    def test_rescue_governance_conflict_is_blocked(self):
        result = decide({"request": "CONTINUE", "suspended": True, "blocker": {"id": "B"}, "resume_audit": {"blocker_resolved": True, "candidate_identity_match": True, "governance_conflict": True}, "actions": [action()]})
        self.assertEqual(result["reason"], "governance_conflict")

    def test_agent_completion_claim_does_not_override_incomplete_plan(self):
        result = decide({"completion_claim": "PASS", "actions": [action()]})
        self.assertEqual(result["decision"], "AUTONOMOUS_CONTINUATION")

    def test_repair_without_revalidation_is_blocked(self):
        result = decide({"recovery_claimed": True, "original_failure_revalidated": False, "regression_passed": True, "actions": [action()]})
        self.assertEqual(result["reason"], "recovery_not_revalidated")

    def test_user_only_gate_never_becomes_agent_pass(self):
        result = decide({"human_gate": "USER_ONLY_ACCEPTANCE_REQUIRED", "human_recovery_package": {}})
        self.assertEqual(result["decision"], "SUSPENDED_AWAITING_HUMAN"); self.assertTrue(result["human_package_errors"])

    def test_resume_state_loss_is_blocked(self):
        result = decide({"request": "RESUME", "suspended": True, "actions": [action()]})
        self.assertEqual(result["reason"], "suspended_blocker_missing")


class TelemetryRegressionTests(unittest.TestCase):
    def test_canonical_telemetry_binding_accepts_signed_core_artifacts(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); log = root / "events.jsonl"; anchor = root / "anchor.json"
            event = {"event_id": "e1", "task_id": "T", "stage_id": "S", "timestamp": "2026-08-30T00:00:00Z", "timestamp_source": "SYSTEM_CLOCK", "event_type": "STAGE_STARTED", "detected_by": "test", "evidence_refs": ["e"], "correlation_id": "c", "prev_hash": ZERO_HASH}
            event["event_hash"] = digest_event(event)
            log.write_text(json.dumps(event) + "\n", encoding="utf-8")
            anchor.write_text(json.dumps({"event_count": 1, "last_hash": event["event_hash"], "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}), encoding="utf-8")
            recorder = ROOT / "共享" / "scripts" / "record_delivery_event.py"; verifier = ROOT / "共享" / "scripts" / "calculate_delivery_metrics.py"
            manifest = root / "manifest.json"; manifest.write_text(json.dumps({"skill_id": "enterprise-ai-project-delivery", "recorder_sha256": hashlib.sha256(recorder.read_bytes()).hexdigest(), "verifier_sha256": hashlib.sha256(verifier.read_bytes()).hexdigest(), "log": str(log), "anchor": str(anchor)}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "共享" / "scripts" / "check_telemetry_binding.py"), "--manifest", str(manifest), "--core-root", str(ROOT)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_round_1_style_unanchored_local_log_fails_core_integrity(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); log = root / "events.jsonl"; anchor = root / "anchor.json"
            log.write_text(json.dumps({"event_type": "TASK_STARTED", "task_id": "T"}) + "\n", encoding="utf-8")
            anchor.write_text("{}", encoding="utf-8")
            _events, errors = verify_chain(log, anchor)
            self.assertTrue(any("event_type_invalid" in item for item in errors))

    def test_duplicate_correlation_fails_core_integrity(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); log = root / "events.jsonl"; anchor = root / "anchor.json"; events = []
            for n in ("a", "b"):
                event = {"event_id": n, "task_id": "T", "stage_id": "S", "timestamp": "2026-08-30T00:00:00Z", "timestamp_source": "SYSTEM_CLOCK", "event_type": "USER_SCOPE_CHANGE", "detected_by": "test", "evidence_refs": ["e"], "correlation_id": "same", "root_cause_category": "USER_CHANGE", "prev_hash": events[-1]["event_hash"] if events else ZERO_HASH}
                event["event_hash"] = digest_event(event); events.append(event)
            log.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
            anchor.write_text(json.dumps({"event_count": 2, "last_hash": events[-1]["event_hash"], "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}), encoding="utf-8")
            _events, errors = verify_chain(log, anchor)
            self.assertTrue(any("duplicate_event_correlation" in item for item in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
