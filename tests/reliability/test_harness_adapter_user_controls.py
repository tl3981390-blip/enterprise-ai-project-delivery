"""Real user-control events must change persisted delivery state, not model prose."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from harness_adapter_core import HarnessAdapterController, sign_trusted_event


SECRET = "user-control-test-secret"


def event(kind, ident, *, session="user-control-session"):
    return sign_trusted_event({"harness": "fixture", "session_id": session,
        "conversation_id": session, "event_id": ident, "event_type": kind,
        "timestamp": "2026-09-02T00:00:00+00:00", "source": "HARNESS", "payload": {}},
        transport_secret=SECRET)


def controller(tmp_path):
    return HarnessAdapterController(harness="fixture", state_path=tmp_path / "session.json",
                                    transport_secret=SECRET)


def start(tmp_path):
    contract = [{"ac_id": "A", "description": "artifact A", "verification_method": "file",
                 "required_evidence": "artifact", "status": "OPEN", "source_revision": 1}]
    return controller(tmp_path).start_session(event("UserPromptSubmit", "start"),
        original_user_request="deliver artifact A", acceptance_contract=contract, auto_approve=True)


def current_evidence(tmp_path, state):
    bridge = controller(tmp_path)
    recorded = bridge.record_tool_success(event("PostToolUse", "checkpoint"),
        work_id=state["runtime"]["plan"]["stages"][0]["name"], tool="test", output=b"checkpoint")
    return recorded["events"][-1]["evidence_id"]


def identity():
    return {"git_head": "a", "worktree_identity": "b", "runtime_identity": "c",
            "contract_hash": "d", "evidence_anchor": "e"}


def test_model_prose_cannot_forge_user_correction_or_cancel(tmp_path):
    start(tmp_path)
    bridge = controller(tmp_path)
    with pytest.raises(PermissionError, match="event_type_not_allowed"):
        bridge.apply_user_correction(event("ItemCompleted", "model-correction"),
            expected_contract_revision=1, description="model says user corrected it",
            violated_requirements=["A"], root_cause_class="model prose", related_checks=["A"])
    with pytest.raises(PermissionError, match="event_type_not_allowed"):
        bridge.apply_user_cancel(event("ItemCompleted", "model-cancel"), expected_contract_revision=1)


def test_trusted_user_correction_is_persisted_and_blocks_completion(tmp_path):
    start(tmp_path)
    bridge = controller(tmp_path)
    changed = bridge.apply_user_correction(event("USER_CORRECTION", "user-correction"),
        expected_contract_revision=1, description="用户指出统计口径错误", violated_requirements=["A"],
        root_cause_class="acceptance gap", related_checks=["summary verifier"])
    assert changed["runtime"]["correction_ledger"][0]["status"] == "OPEN"
    assert bridge.before_completion(event("Stop", "blocked"))["allow_completion"] is False
    assert "USER_CORRECTION_APPLIED" in [item.get("type") for item in changed["events"]]


def test_user_pause_cannot_auto_resume_and_trusted_resume_is_bound_to_same_package(tmp_path):
    state = start(tmp_path)
    evidence_id = current_evidence(tmp_path, state)
    bridge = controller(tmp_path)
    paused = bridge.apply_user_pause(event("USER_PAUSE", "user-pause"), expected_contract_revision=1,
        reason="用户要求暂停", checkpoint_identity=identity(), evidence_ids=[evidence_id])
    assert paused["runtime"]["status"] == "SUSPENDED"
    package = paused["runtime"]["suspensions"][0]
    with pytest.raises(PermissionError, match="event_type_not_allowed"):
        bridge.apply_user_resume(event("TurnCompleted", "model-resume"), expected_contract_revision=paused["contract_revision"],
            suspension_id=package["suspension_id"], current_identity=identity(),
            revalidation_evidence_ids=[evidence_id])
    resumed = bridge.apply_user_resume(event("USER_RESUME", "user-resume"), expected_contract_revision=paused["contract_revision"],
        suspension_id=package["suspension_id"], current_identity=identity(),
        revalidation_evidence_ids=[evidence_id])
    assert resumed["runtime"]["status"] == "EXECUTING"


def test_trusted_user_cancel_is_terminal(tmp_path):
    start(tmp_path)
    cancelled = controller(tmp_path).apply_user_cancel(event("USER_CANCEL", "user-cancel"),
        expected_contract_revision=1)
    assert cancelled["runtime"]["status"] == "CANCELLED"
    assert "USER_CANCEL_APPLIED" in [item.get("type") for item in cancelled["events"]]
