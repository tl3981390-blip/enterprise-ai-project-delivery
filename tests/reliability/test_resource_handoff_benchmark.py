#!/usr/bin/env python3
"""v1.2 gap-closing regressions: resource guard, model handoff, benchmark contamination, safe rollback."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from continuation_core import decide, resource_guard, validate_model_handoff_package, verify_handoff
from check_benchmark_contamination import check
from telemetry_core import validate_event


def handoff_package(task_id="T"):
    checkpoint = {"task_id": task_id, "stage_id": "RH-7", "contract_hash": "c1", "git_head": "h1", "worktree_identity": "w1", "runtime_identity": "r1", "last_passed_gate": "G", "evidence_anchor": "a1", "timestamp": "2026-08-30T00:00:00Z"}
    return {
        "task_id": task_id, "goal": "reliable delivery", "business_goal": "no stalling", "task_contract": "contract.json",
        "current_stage": "RH-7", "current_state": "EXECUTING", "current_model": "model-a", "handoff_reason": "resource exhaustion risk",
        "resource_status": "RED", "last_known_good_checkpoint": checkpoint, "current_git_head": "h1", "worktree_state": "w1",
        "build_identity": "b1", "runtime_identity": "r1", "completed_work": ["RH-1"], "partial_unverified_work": [],
        "remaining_work": ["RH-11"], "current_blockers": [], "failure_history": [], "recovery_history": [],
        "permissions": "local repo only", "evidence_index": "index.json", "telemetry_anchor": "anchor",
        "files_must_read": ["handoff.md"], "files_must_not_rework": ["frozen.md"], "next_legal_action": "finish release verification",
        "resume_condition": "verify identities", "resume_verification": "verify_handoff", "known_risks": ["risk"],
    }


def current_state(**overrides):
    state = {"git_head": "h1", "worktree_identity": "w1", "contract_hash": "c1", "evidence_anchor": "a1", "runtime_identity": "r1", "task_id": "T"}
    state.update(overrides)
    return state


class ResourceGuardTests(unittest.TestCase):
    def test_resource_001_provider_warning_prepares_handoff_no_large_stage(self):
        result = resource_guard({"visibility": "GREEN", "provider_warning": True})
        self.assertEqual(result["decision"], "PREPARE_CHECKPOINT"); self.assertEqual(result["resource_state"], "YELLOW")
        self.assertIn("RESOURCE_BUDGET_WARNING", result["required_events"])

    def test_resource_002_user_reported_exhaustion_triggers_proactive_handoff(self):
        result = resource_guard({"visibility": "GREEN", "user_reported_exhaustion_risk": True})
        self.assertEqual(result["decision"], "PROACTIVE_MODEL_HANDOFF"); self.assertEqual(result["resource_state"], "RED")
        self.assertIn("PROACTIVE_HANDOFF_STARTED", result["required_events"]); self.assertIn("MODEL_HANDOFF_READY", result["required_events"])

    def test_resource_003_atomic_unit_completes_then_handoff(self):
        result = resource_guard({"visibility": "RED", "atomic_unit_in_progress": True, "atomic_unit_safe_to_complete": True})
        self.assertEqual(result["decision"], "COMPLETE_ATOMIC_UNIT_THEN_HANDOFF"); self.assertTrue(result["can_continue"])

    def test_resource_004_uncompletable_unit_stops_new_writes(self):
        result = resource_guard({"visibility": "RED", "atomic_unit_in_progress": True, "atomic_unit_safe_to_complete": False})
        self.assertEqual(result["decision"], "STOP_NEW_WRITES"); self.assertFalse(result["can_continue"])
        self.assertIn("UNVERIFIED_PARTIAL_WORK", result["required_events"])

    def test_invisible_resource_is_not_estimated(self):
        result = resource_guard({"visibility": "NOT_AVAILABLE"})
        self.assertEqual(result["resource_state"], "UNKNOWN"); self.assertEqual(result["decision"], "CONTINUE")
        self.assertIn("no estimation", result["reason"])


class ModelHandoffTests(unittest.TestCase):
    def test_handoff_001_matching_identity_resumes_same_task(self):
        result = verify_handoff(handoff_package(), current_state())
        self.assertEqual(result["decision"], "HANDOFF_VERIFICATION_PASS"); self.assertTrue(result["can_continue"]); self.assertEqual(result["errors"], [])

    def test_handoff_002_head_mismatch_is_rejected(self):
        result = verify_handoff(handoff_package(), current_state(git_head="different"))
        self.assertEqual(result["decision"], "HANDOFF_VERIFICATION_FAIL")
        self.assertIn("handoff_identity_mismatch:git_head", result["errors"])

    def test_incomplete_handoff_package_cannot_go_ready(self):
        broken = handoff_package(); del broken["next_legal_action"]
        result = decide({"model_handoff_request": True, "model_handoff_package": broken})
        self.assertEqual(result["decision"], "CONSTRAINT_CONFLICT"); self.assertIn("missing:next_legal_action", result["handoff_package_errors"])

    def test_complete_package_goes_handoff_ready_not_human_wait(self):
        result = decide({"model_handoff_request": True, "model_handoff_package": handoff_package()})
        self.assertEqual(result["decision"], "MODEL_HANDOFF_READY"); self.assertFalse(result["can_continue"])

    def test_package_head_conflicts_with_checkpoint(self):
        broken = handoff_package(); broken["current_git_head"] = "other"
        self.assertIn("package_head_conflicts_checkpoint", validate_model_handoff_package(broken))


class RecoveryEscalationTests(unittest.TestCase):
    def test_rec_002_safe_rollback_attempted_before_exhaustion(self):
        result = decide({"blocker": {"unrecoverable": True}, "safe_rollback": {"available": True, "reversible": True, "contract_allowed": True}})
        self.assertEqual(result["decision"], "SAFE_ROLLBACK_ATTEMPT"); self.assertTrue(result["can_continue"])
        self.assertIn("original_gate_revalidation", result["requires"])

    def test_rec_003_contract_compliant_alternative_recovery(self):
        result = decide({"blocker": {"unrecoverable": True}, "alternative_recovery": {"available": True, "scope_unchanged": True, "acceptance_unchanged": True, "bypasses_permission": False, "bypasses_human_gate": False}})
        self.assertEqual(result["decision"], "ALTERNATIVE_RECOVERY"); self.assertTrue(result["can_continue"])

    def test_alternative_recovery_bypassing_permission_is_rejected(self):
        result = decide({"blocker": {"unrecoverable": True}, "alternative_recovery": {"available": True, "scope_unchanged": True, "acceptance_unchanged": True, "bypasses_permission": True, "bypasses_human_gate": False}})
        self.assertEqual(result["decision"], "RECOVERY_EXHAUSTED")


class BenchmarkContaminationTests(unittest.TestCase):
    def test_bench_001_controller_exposure_is_contaminated(self):
        spec = {"private_markers": ["USER_SCOPE_CHANGE", "DRIFT_DETECTED"], "public_text": "现在测试 USER_SCOPE_CHANGE 事件的触发。"}
        result = check(spec, spec["public_text"])
        self.assertEqual(result["status"], "CONTROLLER_CONTAMINATED"); self.assertIn("USER_SCOPE_CHANGE", result["leaked_markers"])

    def test_business_voice_stays_clean(self):
        spec = {"private_markers": ["USER_SCOPE_CHANGE", "DRIFT_DETECTED"], "public_text": "业务方提出以下真实需求变化：法务条目需要增加英文字段。"}
        result = check(spec, spec["public_text"])
        self.assertEqual(result["status"], "PASS"); self.assertEqual(result["leaked_markers"], [])


class NewTelemetryEventTests(unittest.TestCase):
    def test_resource_and_handoff_events_pass_canonical_validation(self):
        base = {"task_id": "T", "stage_id": "S", "timestamp": "2026-08-30T00:00:00Z", "timestamp_source": "SYSTEM_CLOCK", "detected_by": "test", "evidence_refs": ["e"]}
        for n, event_type in enumerate(("RESOURCE_BUDGET_WARNING", "PROACTIVE_HANDOFF_STARTED", "MODEL_HANDOFF_READY", "MODEL_HANDOFF_COMPLETED", "HANDOFF_VERIFICATION_FAIL", "UNVERIFIED_PARTIAL_WORK")):
            event = {**base, "event_id": f"r{n}", "event_type": event_type, "correlation_id": f"c-{n}"}
            self.assertEqual(validate_event(event, []), [], event_type)

    def test_new_event_types_are_schema_enumerated(self):
        import json
        schema = json.loads((ROOT / "共享" / "schema" / "project_reliability_event.schema.json").read_text(encoding="utf-8"))
        enum = schema["properties"]["event_type"]["enum"]
        for event_type in ("RESOURCE_BUDGET_WARNING", "PROACTIVE_HANDOFF_STARTED", "MODEL_HANDOFF_READY", "MODEL_HANDOFF_COMPLETED", "HANDOFF_VERIFICATION_FAIL", "UNVERIFIED_PARTIAL_WORK"):
            self.assertIn(event_type, enum)


if __name__ == "__main__":
    unittest.main(verbosity=2)
