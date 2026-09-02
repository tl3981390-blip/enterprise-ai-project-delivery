"""HAD-001..010: contract tests for the thin, trusted Harness bridge."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from harness_adapter_core import HarnessAdapterController, sign_trusted_event


SECRET = "adapter-test-secret"


def event(kind, ident="e1", *, session="h1"):
    return sign_trusted_event({"harness": "fixture", "session_id": session,
        "conversation_id": "conversation-1", "event_id": ident, "event_type": kind,
        "timestamp": "2026-09-02T00:00:00+00:00", "source": "HARNESS", "payload": {}},
        transport_secret=SECRET)


def contract():
    return [{"ac_id": "A", "description": "artifact A exists", "verification_method": "file",
             "required_evidence": "artifact", "status": "OPEN", "source_revision": 1},
            {"ac_id": "B", "description": "artifact B exists", "verification_method": "file",
             "required_evidence": "artifact", "status": "OPEN", "source_revision": 1}]


def controller(tmp_path):
    return HarnessAdapterController(harness="fixture", state_path=tmp_path / "state.json",
                                    transport_secret=SECRET)


def started(tmp_path):
    return controller(tmp_path).start_session(event("UserPromptSubmit"),
        original_user_request="deliver artifact A exists and artifact B exists", acceptance_contract=contract(),
        auto_approve=True)


def work_id(state):
    return state["runtime"]["plan"]["stages"][0]["name"]


def test_had001_trusted_event_mapping_and_had002_candidate_cannot_forge(tmp_path):
    started(tmp_path)
    forged = event("Stop", "forged")
    forged["payload"] = {"complete": True}
    with pytest.raises(PermissionError, match="signature_invalid"):
        controller(tmp_path).before_completion(forged)


def test_had003_identity_and_had004_resume_same_session(tmp_path):
    state = started(tmp_path)
    assert controller(tmp_path).resume_session(event("SessionStart", "resume"))["delivery_session_id"] == state["delivery_session_id"]
    with pytest.raises(PermissionError, match="identity_mismatch"):
        controller(tmp_path).resume_session(event("SessionStart", "other", session="other"))


def test_had005_owner_revision_only(tmp_path):
    started(tmp_path)
    with pytest.raises(PermissionError):
        controller(tmp_path).revise_contract(event("UserPromptSubmit", "no-owner"), replacement=contract(), reason="no")
    revised = controller(tmp_path).revise_contract(event("ACCEPTANCE_CHANGE", "owner-change"), replacement=contract(), reason="owner")
    assert revised["contract_revision"] == 2


def test_had006_to_008_failed_or_missing_ac_blocks_completion(tmp_path):
    state = started(tmp_path)
    bridge = controller(tmp_path)
    state = bridge.record_tool_success(event("PostToolUse", "a"), work_id=work_id(state), tool="test",
                                       output=b"green", ac_ids=["A"])
    blocked = bridge.before_completion(event("Stop", "host-claims-complete"))
    assert blocked["allow_completion"] is False
    assert any("artifact B exists" in item for item in blocked["blocker"]["missing"])
    assert any(item["ac_id"] == "B" and item["source"] == "MECHANICAL_VERIFICATION"
               for item in blocked["open_blockers"])
    failed = bridge.record_tool_failure(event("PostToolUseFailure", "b"), work_id=work_id(state), tool="test",
                                        output=b"bad", root_cause="B missing", ac_ids=["B"])
    assert failed["completion_status"] == "BLOCKED"
    assert bridge.before_completion(event("Stop", "again"))["allow_completion"] is False


def test_had007_restart_and_had009_old_failure_preserved(tmp_path):
    state = started(tmp_path)
    bridge = controller(tmp_path)
    bridge.record_tool_failure(event("PostToolUseFailure", "fail"), work_id=work_id(state), tool="test",
                               output=b"failure", root_cause="bad artifact", ac_ids=["A"])
    restored = HarnessAdapterController(harness="fixture", state_path=tmp_path / "state.json", transport_secret=SECRET).restore_state()
    assert restored["runtime"]["evidence_ledger"][0]["status"] == "FAIL"
    assert restored["recovery_history"]


def test_had010_original_request_immutable_and_completion_passes_only_with_all_ac(tmp_path):
    state = started(tmp_path)
    bridge = controller(tmp_path)
    assert state["original_user_request"] == "deliver artifact A exists and artifact B exists"
    bridge.record_tool_success(event("PostToolUse", "a"), work_id=work_id(state), tool="test", output=b"A", ac_ids=["A"])
    bridge.record_tool_success(event("PostToolUse", "b"), work_id=work_id(state), tool="test", output=b"B", ac_ids=["B"])
    # Runtime also requires its generated final-evidence items: no Host prose can fill those.
    assert bridge.before_completion(event("Stop", "claim"))["allow_completion"] is False


def test_integration_events_fail_closed_for_model_text_and_replay(tmp_path):
    state = started(tmp_path)
    bridge = controller(tmp_path)
    fake = event("ItemCompleted", "model-text")
    with pytest.raises(PermissionError, match="event_type_not_allowed"):
        bridge.accept_owner_external_condition(fake, expected_contract_revision=1, condition_ref="OWNER_APPROVED")
    owner = event("OWNER_CONDITION", "owner-1")
    accepted = bridge.accept_owner_external_condition(owner, expected_contract_revision=1, condition_ref="owner-input")
    assert accepted["external_conditions"][0]["condition_ref"] == "owner-input"
    with pytest.raises(PermissionError, match="event_replay"):
        bridge.accept_owner_external_condition(owner, expected_contract_revision=1, condition_ref="owner-input")
    assert bridge.restore_state()["delivery_session_id"] == state["delivery_session_id"]


def test_trusted_recovery_uses_runtime_and_preserves_failure(tmp_path):
    state = started(tmp_path)
    bridge = controller(tmp_path)
    failed = bridge.record_tool_failure(event("PostToolUseFailure", "failure"), work_id=work_id(state),
                                        tool="runner", output=b"failure", root_cause="fixture")
    failure_id = failed["runtime"]["failures"][0]["failure_id"]
    with pytest.raises(PermissionError):
        bridge.record_controller_recovery(event("ItemCompleted", "model-recovery"), expected_contract_revision=1,
            failure_id=failure_id, action="model claims recovered", recovery_evidence_ids=[], blocker_evidence_ids=[], regression_evidence_ids=[])
    passed = bridge.record_tool_success(event("PostToolUse", "revalidate"), work_id=work_id(state),
                                        tool="runner", output=b"revalidated", ac_ids=["A"])
    evidence_id = passed["events"][-1]["evidence_id"]
    recovered = bridge.record_controller_recovery(event("RECOVERY_EVENT", "trusted-recovery"), expected_contract_revision=1,
        failure_id=failure_id, action="trusted external repair", recovery_evidence_ids=[evidence_id],
        blocker_evidence_ids=[evidence_id], regression_evidence_ids=[evidence_id])
    assert recovered["runtime"]["failures"][0]["status"] == "RECOVERED_REVALIDATED"
    assert any(item["status"] == "FAIL" for item in recovered["runtime"]["evidence_ledger"])
