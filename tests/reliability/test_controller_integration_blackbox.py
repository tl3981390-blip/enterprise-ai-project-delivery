"""EXP-DRIVER-001 deterministic black-box for the trusted Controller integration.

The fixture intentionally exercises the public controller boundary only.  It never calls the
Runtime, Evidence Core, or completion gate directly.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from harness_adapter_core import HarnessAdapterController, sign_trusted_event


SECRET = "integration-blackbox-secret"


def trusted(kind, ident, *, payload=None):
    return sign_trusted_event({"harness": "blackbox", "session_id": "blackbox-session",
        "conversation_id": "blackbox-conversation", "event_id": ident, "event_type": kind,
        "timestamp": "2026-09-02T00:00:00+00:00", "source": "HARNESS", "payload": payload or {}},
        transport_secret=SECRET)


def controller(tmp_path):
    return HarnessAdapterController(harness="blackbox", state_path=tmp_path / "persistent-state.json",
                                    transport_secret=SECRET)


def verifier(payload):
    return payload == b"PASS", {"expected": "PASS", "actual": payload.decode("utf-8", "replace")}


def test_exp_driver_001_trusted_delivery_survives_failure_owner_boundary_and_recovery(tmp_path):
    """Artifact-to-AC mapping, evidence-bound recovery and final completion are one durable chain."""
    contract = [
        {"ac_id": "AC-REPORT", "description": "report artifact exists", "verification_method": "file",
         "required_evidence": "artifact", "status": "OPEN", "source_revision": 1},
        {"ac_id": "AC-SUMMARY", "description": "summary artifact exists", "verification_method": "file",
         "required_evidence": "artifact", "status": "OPEN", "source_revision": 1},
    ]
    state = controller(tmp_path).start_session(trusted("UserPromptSubmit", "start"),
        original_user_request="deliver report and summary", acceptance_contract=contract, auto_approve=True)
    work_id = state["runtime"]["plan"]["stages"][0]["name"]
    report, summary = tmp_path / "report.out", tmp_path / "summary.out"
    report.write_bytes(b"PASS"); summary.write_bytes(b"BROKEN")
    registry = {"exact-pass": verifier}

    state = controller(tmp_path).verify_registered_artifact(trusted("ARTIFACT_VERIFICATION_REQUEST", "report-v1"),
        expected_contract_revision=1, work_id=work_id, path=report, ac_ids=["AC-REPORT"],
        verifier_id="exact-pass", verifier_registry=registry)
    state = controller(tmp_path).verify_registered_artifact(trusted("ARTIFACT_VERIFICATION_REQUEST", "summary-v1"),
        expected_contract_revision=1, work_id=work_id, path=summary, ac_ids=["AC-SUMMARY"],
        verifier_id="exact-pass", verifier_registry=registry)
    failed_evidence = state["events"][-1]["evidence_id"]
    state = controller(tmp_path).record_controller_failure(trusted("FAILURE_EVENT", "failure"),
        expected_contract_revision=1, work_id=work_id, root_cause="summary artifact verifier failed",
        evidence_ids=[failed_evidence])
    failure_id = state["runtime"]["failures"][-1]["failure_id"]
    blocked = controller(tmp_path).before_completion(trusted("Stop", "blocked-completion"))
    assert not blocked["allow_completion"] and blocked["open_blockers"]

    with pytest.raises(PermissionError):
        controller(tmp_path).accept_owner_external_condition(trusted("ItemCompleted", "model-owner"),
            expected_contract_revision=1, condition_ref="guessed-owner-input")
    with pytest.raises(PermissionError, match="trusted_test_owner_authority_required"):
        controller(tmp_path).accept_owner_external_condition(trusted("OWNER_CONDITION", "missing-authority"),
            expected_contract_revision=1, condition_ref="missing-authority")
    state = controller(tmp_path).accept_owner_external_condition(trusted("OWNER_CONDITION", "owner-input",
        payload={"authority": "TRUSTED_TEST_OWNER_AUTHORITY"}), expected_contract_revision=1,
        condition_ref="owner-authorized-repair")
    assert state["completion_status"] == "NOT_COMPLETE"

    summary.write_bytes(b"PASS")
    state = controller(tmp_path).verify_registered_artifact(trusted("ARTIFACT_VERIFICATION_REQUEST", "summary-v2"),
        expected_contract_revision=1, work_id=work_id, path=summary, ac_ids=["AC-SUMMARY"],
        verifier_id="exact-pass", verifier_registry=registry)
    recovered_evidence = state["events"][-1]["evidence_id"]
    state = controller(tmp_path).record_controller_recovery(trusted("RECOVERY_EVENT", "recovery"),
        expected_contract_revision=1, failure_id=failure_id, action="replace invalid summary artifact",
        recovery_evidence_ids=[recovered_evidence], blocker_evidence_ids=[recovered_evidence],
        regression_evidence_ids=[recovered_evidence])
    assert state["runtime"]["failures"][-1]["status"] == "RECOVERED_REVALIDATED"
    assert any(item["evidence_id"] == failed_evidence and item["status"] == "FAIL"
               for item in state["runtime"]["evidence_ledger"])

    controller(tmp_path).record_final_verification(trusted("ArtifactVerified", "final-bundle"), work_id=work_id,
        bundle={"fixture": "EXP-DRIVER-001", "report": "PASS", "summary": "PASS"})
    final = controller(tmp_path).before_completion(trusted("Stop", "verified-completion"))
    assert final["allow_completion"] is True
    persisted = controller(tmp_path).restore_state()
    assert persisted["completion_status"] == "VERIFIED_DELIVERY_COMPLETE"
    assert persisted["external_conditions"][0]["condition_ref"] == "owner-authorized-repair"
