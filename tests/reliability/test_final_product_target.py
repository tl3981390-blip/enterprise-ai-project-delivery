import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_runtime import (_start_delivery_from_facts, approve_plan, bind_execution_context,
                              claim_completion, record_capability_result, record_evidence,
                              record_user_correction, resolve_user_correction,
                              request_capability_invocation)
from intent_core import INTENT_TYPES, record_intent
from plan_governance_core import plan_authority_order
from skill_evolution_core import validate_core_candidate, validate_transition


def test_intent_contract_is_semantic_and_punctuation_neutral():
    phrases = ["你确定这个可以吗", "你确定这个可以", "这个确定可以", "这样真行"]
    for phrase in phrases:
        result = record_intent(utterance=phrase, intent="QUESTION",
                               context_refs=["turn:previous-proposal"],
                               rationale="asks whether the prior proposal is reliable")
        assert result["intent"] == "QUESTION"
    assert {"APPROVAL", "REJECTION", "CHANGE_REQUEST", "CANCEL"} <= INTENT_TYPES


def test_consequential_ambiguity_asks_exactly_one_minimal_question():
    result = record_intent(utterance="这个就这样", intent="AMBIGUOUS",
                           context_refs=["turn:plan-review"], rationale="could approve or pause",
                           consequential_ambiguity=True,
                           clarification_question="你是批准当前计划并开始执行吗？")
    assert result["next_action"] == "ASK_ONE_MINIMAL_QUESTION"
    assert len(result["clarification_questions"]) == 1
    with pytest.raises(ValueError, match="minimal_clarification_required"):
        record_intent(utterance="这个就这样", intent="AMBIGUOUS",
                      context_refs=["turn:plan-review"], rationale="ambiguous")


def test_authority_and_integrity_are_independent_planes():
    planes = plan_authority_order()
    assert planes["authority_plane"][0] == "AUTHORIZED_HUMAN_DECISIONS"
    assert "NO_FAKE_PASS" in planes["integrity_plane"]
    assert "CORE_RELIABILITY_INVARIANTS" not in planes["authority_plane"]


def _session():
    return _start_delivery_from_facts(
        facts={"goal": "审查报价", "required_capabilities": ["legal_review"],
               "work_units": [{"name": "review", "goal": "review", "class": "TASK",
                               "work": ["review"], "capabilities": ["legal_review"]}]},
        capability_registry={"legal_review": {"maturity": 9, "version": "3.2.1",
            "validation_status": "VALIDATED", "source_identity_verified": True,
            "compatible": True, "license_compatible": True, "permission_granted": True}})


def _approval(session, intent="APPROVAL"):
    return {"intent_record": {"intent": intent, "consequential_ambiguity": False,
            "context_refs": [f"plan_revision:{session['revision']}",
                             f"plan_scope:{session['session_id']}"]},
            "user_origin_ref": {"origin": "USER", "harness": "pytest",
            "conversation_id": "final-target", "message_id": "approval"}}


def test_unreviewed_plan_cannot_execute_and_scoped_waiver_can():
    session = _session()
    assert session["status"] == "PLAN_REVIEW_REQUIRED"
    with pytest.raises(PermissionError, match="plan_approval_required"):
        request_capability_invocation(session, work_id="review", capability="legal_review",
                                      input_payload={})
    with pytest.raises(ValueError, match="review_waiver_scope_required"):
        approve_plan(session, **_approval(session), waive_display=True)
    approved = approve_plan(session, **_approval(session), waive_display=True,
                            waiver_scope="current generated plan revision")
    assert approved["plan_review"]["status"] == "DISPLAY_WAIVED_EXECUTION_APPROVED"


def test_capability_full_work_scoped_lifecycle_deactivates_context():
    session = bind_execution_context(_session(), task="task-1", workspace="ws-1", project="p-1")
    session = approve_plan(session, **_approval(session))
    session = request_capability_invocation(session, work_id="review", capability="legal_review",
                                            input_payload={"document": "quote"},
                                            permission_scope=["read:quote"])
    invocation = session["capability_invocations"][0]
    assert invocation["session_id"] == session["session_id"]
    assert invocation["capability_version"] == "3.2.1"
    assert invocation["permission_scope"] == ["read:quote"]
    session = record_evidence(session, evidence={
        "evidence_id": "result", "type": "TEST_RESULT", "producer": "TEST_RUNNER",
        "source_ref": "pytest://result", "candidate_id": session["candidate_id"],
        "work_id": "review", "observed_at": "2026-09-01T00:00:00+00:00",
        "content_hash": "a" * 64, "status": "PASS", "session_revision": session["revision"],
        "dependencies": [], "acceptance_items": [],
    })
    session = record_capability_result(session, invocation_id=invocation["invocation_id"],
                                       status="PASS", output={"ok": True},
                                       evidence_ids=["result"])
    terminal = session["capability_invocations"][0]
    assert terminal["lifecycle"][-1] == "DEACTIVATED"
    assert terminal["active_instruction_context"] is False
    assert terminal["temporary_authorization_active"] is False
    assert "input" not in terminal
    assert terminal["input_scope"] == []
    assert terminal["permission_scope"] == []


def test_evolution_candidate_requires_reproduction_isolation_and_human_release():
    base = {key: key for key in (
        "candidate_id", "source_evidence", "reproduce_steps", "expected_behavior",
        "actual_behavior", "violated_final_target", "root_cause", "generalization_rationale",
        "counterexample", "affected_core_contract", "expected_blast_radius")}
    preference = dict(base, classification="USER_PREFERENCE", reproduced=True,
                      isolated_copy=True, auto_release=False)
    assert any("classification_not_admissible" in e for e in validate_core_candidate(preference))
    valid = dict(base, classification="CORE_RELIABILITY_DEFECT", reproduced=True,
                 isolated_copy=True, auto_release=False)
    assert validate_core_candidate(valid) == []
    assert validate_transition("FINAL_GOAL_PASS", "RELEASED")
    assert validate_transition("FINAL_GOAL_PASS", "HUMAN_APPROVED") == []
    assert "auto_release_forbidden" in validate_core_candidate(dict(valid, auto_release=True))


def test_confirmed_requirements_and_corrections_survive_beyond_model_prose():
    session = _session()
    session = approve_plan(session, **_approval(session))
    assert "goal" in session["confirmed_requirement_baseline"]
    session = record_user_correction(session, description="review skipped required price check",
                                     violated_requirements=["price must be checked"],
                                     root_cause_class="CHECKLIST_NOT_BOUND_TO_WORK",
                                     related_checks=["price regression"])
    first = session["correction_ledger"][0]
    assert first["status"] == "OPEN"
    # An open confirmed correction blocks a narrative completion claim.
    out = claim_completion(session, {})
    assert first["correction_id"] in out["completion_gate"]["open_corrections"]


def test_repeated_confirmed_error_enters_recovery_and_resolution_needs_evidence():
    session = _session()
    session = approve_plan(session, **_approval(session))
    kwargs = dict(description="same missed price check",
                  violated_requirements=["price must be checked"],
                  root_cause_class="CHECKLIST_NOT_BOUND_TO_WORK",
                  related_checks=["price regression"])
    session = record_user_correction(session, **kwargs)
    work_id = "review"
    session = record_evidence(session, evidence={
        "evidence_id": "correction-proof", "type": "TEST_RESULT", "producer": "TEST_RUNNER",
        "source_ref": "pytest://correction", "candidate_id": session["candidate_id"],
        "work_id": work_id, "observed_at": "2026-09-01T00:00:00+00:00",
        "content_hash": "b" * 64, "status": "PASS", "session_revision": session["revision"],
        "dependencies": [], "acceptance_items": [],
    })
    session = resolve_user_correction(session,
        correction_id=session["correction_ledger"][0]["correction_id"],
        root_cause_fix="bind price checklist to review work", evidence_ids=["correction-proof"])
    session = record_user_correction(session, **kwargs)
    assert session["status"] == "RECOVERING"
    assert any(e["type"] == "REPEATED_CONFIRMED_ERROR" for e in session["events"])
