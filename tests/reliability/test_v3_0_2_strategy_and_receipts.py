"""v3.0.2 behavioral differentials and trusted Evidence ingress attacks."""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_runtime import (advance, approve_plan, claim_completion, get_strategy_guidance,
                              record_evidence, record_failure, record_recovery,
                              request_capability_invocation, select_next_legal_work,
                              update_adaptive_strategy, _acceptance_items, _start_delivery_from_facts)
from evidence_core import register_harness_execution_receipt
from understanding_core import begin_understanding
from receipt_support import record_test_receipt

USER = {"origin": "USER", "harness": "pytest", "conversation_id": "v302", "message_id": "m"}


def _session(*, strategy=None, facts=None, upstream_plan=None, registry=None, upstream=None):
    return _start_delivery_from_facts(
        facts=facts or {"goal": "交付真实结果", "deployment_requirement": False},
        adaptive_strategy_state=strategy, upstream_plan=upstream_plan,
        capability_registry=registry, upstream_capabilities=upstream)


def _approved(session):
    return approve_plan(session, intent_record={
        "intent": "APPROVAL", "consequential_ambiguity": False,
        "context_refs": [f"plan_revision:{session['revision']}", f"plan_scope:{session['session_id']}"]},
        user_origin_ref=USER)


def _record(session, receipt_id, *, status="PASS", work_id=None, acceptance_items=None,
            invocation_id=None, tool_or_capability="pytest"):
    work = work_id or session["plan"]["stages"][0]["name"]
    rid, metadata = record_test_receipt(session, receipt_id=receipt_id, work_id=work,
                                        status=status, acceptance_items=acceptance_items,
                                        invocation_id=invocation_id,
                                        tool_or_capability=tool_or_capability)
    return record_evidence(session, receipt_id=rid, evidence_metadata=metadata)


def test_strategy_behavior_q_same_unknowns_produce_different_consequential_questions():
    dimensions = ["users", "user_journeys", "final_deliverable", "acceptance_requirements"]
    many = begin_understanding(raw_goal="做一个产品", required_dimensions=dimensions,
                               adaptive_strategy_state={"question_strategy": "ask_only_consequential_unknowns"})
    one = begin_understanding(raw_goal="做一个产品", required_dimensions=dimensions,
                              adaptive_strategy_state={"question_strategy": "ask_one_highest_impact_first"})
    assert len(many["questions"]) > 1
    assert len(one["questions"]) == 1
    assert many["questions"] != one["questions"]
    assert all(question["why"] for question in many["questions"] + one["questions"])


def test_strategy_behavior_p_same_work_has_risk_first_real_order_without_new_governance():
    upstream = {"stages": [
        {"name": "低风险真实工作", "goal": "实现界面", "work": ["实现界面"], "risk": "LOW"},
        {"name": "高风险真实工作", "goal": "迁移数据", "work": ["迁移数据"], "risk": "HIGH"},
    ]}
    minimal = _session(strategy={"planning_strategy": "minimal_real_work_units"}, upstream_plan=upstream)
    risk = _session(strategy={"planning_strategy": "risk_first_real_work_units"}, upstream_plan=upstream)
    assert [x["name"] for x in minimal["plan"]["stages"]] == ["低风险真实工作", "高风险真实工作"]
    assert [x["name"] for x in risk["plan"]["stages"]] == ["高风险真实工作", "低风险真实工作"]
    assert {x["name"] for x in risk["plan"]["stages"]} == {x["name"] for x in upstream["stages"]}


def test_strategy_behavior_c_only_reorders_eligible_capability_candidates():
    facts = {"goal": "浏览器验收", "required_capabilities": ["browser_acceptance"],
             "deployment_requirement": False}
    registry = {"browser_acceptance": {"maturity": 2, "validation_status": "VALIDATED",
                "source_identity_verified": True, "compatible": True, "license_compatible": True,
                "permission_granted": True}}
    upstream = {"mature-provider": {"capabilities": ["browser_acceptance"], "maturity": 9,
                "validation_status": "VALIDATED", "source_identity_verified": True,
                "compatible": True, "license_compatible": True, "permission_granted": True}}
    mature = _session(strategy={"capability_preference": "mature_compatible_authorized_first"},
                      facts=facts, registry=registry, upstream=upstream)
    local = _session(strategy={"capability_preference": "local_authorized_first"},
                     facts=facts, registry=registry, upstream=upstream)
    assert mature["capability_resolutions"]["browser_acceptance"]["resolution"] == "mature-provider"
    assert local["capability_resolutions"]["browser_acceptance"]["resolution"] == "LOCAL_CORE"
    assert all(s["capability_resolutions"]["browser_acceptance"]["readiness"] == "READY"
               for s in (mature, local))


def test_strategy_behavior_r_changes_real_recovery_sequence_not_success_standard():
    root = _approved(_session(strategy={"recovery_strategy": "root_cause_then_revalidate"}))
    isolate = _approved(_session(strategy={"recovery_strategy": "isolate_then_root_cause_revalidate"}))
    for session in (root, isolate):
        work = session["plan"]["stages"][0]["name"]
        failed = _record(session, f"failure-{session['session_id']}", status="FAIL", work_id=work)
        failed = record_failure(failed, work_id=work,
                                evidence_ids=[failed["evidence_ledger"][-1]["evidence_id"]],
                                root_cause="test")
        repaired = _record(failed, f"repair-{failed['session_id']}", work_id=work)
        blocker = _record(repaired, f"blocker-{repaired['session_id']}", work_id=work)
        regression = _record(blocker, f"regression-{blocker['session_id']}", work_id=work)
        recovered = record_recovery(regression, failure_id=regression["failures"][0]["failure_id"],
                                    action="bounded fix",
                                    recovery_evidence_ids=[repaired["evidence_ledger"][-1]["evidence_id"]],
                                    blocker_evidence_ids=[blocker["evidence_ledger"][-1]["evidence_id"]],
                                    regression_evidence_ids=[regression["evidence_ledger"][-1]["evidence_id"]])
        assert recovered["status"] == "EXECUTING"
        if session is root:
            root_attempt = recovered["failures"][0]["recovery_attempts"][-1]
        else:
            isolate_attempt = recovered["failures"][0]["recovery_attempts"][-1]
    assert root_attempt["execution_sequence"] != isolate_attempt["execution_sequence"]
    assert isolate_attempt["execution_sequence"][0] == "ISOLATE_IMPACT"


def test_repeated_unverified_recovery_switches_to_alternate_strategy():
    session = _approved(_session(strategy={"recovery_strategy": "root_cause_then_revalidate"}))
    work = session["plan"]["stages"][0]["name"]
    failed = _record(session, "repeat-failure", status="FAIL", work_id=work)
    failed = record_failure(failed, work_id=work,
                            evidence_ids=[failed["evidence_ledger"][-1]["evidence_id"]],
                            root_cause="still unknown")
    repair_1 = _record(failed, "repair-1", work_id=work)
    blocker_1 = _record(repair_1, "blocker-1", status="FAIL", work_id=work)
    first = record_recovery(
        blocker_1, failure_id=blocker_1["failures"][0]["failure_id"], action="same approach",
        recovery_evidence_ids=[repair_1["evidence_ledger"][-1]["evidence_id"]],
        blocker_evidence_ids=[blocker_1["evidence_ledger"][-1]["evidence_id"]])
    assert first["status"] == "RECOVERING"
    repair_2 = _record(first, "repair-2", work_id=work)
    blocker_2 = _record(repair_2, "blocker-2", work_id=work)
    regression_2 = _record(blocker_2, "regression-2", work_id=work)
    second = record_recovery(
        regression_2, failure_id=regression_2["failures"][0]["failure_id"], action="alternate approach",
        recovery_evidence_ids=[repair_2["evidence_ledger"][-3]["evidence_id"]],
        blocker_evidence_ids=[blocker_2["evidence_ledger"][-2]["evidence_id"]],
        regression_evidence_ids=[regression_2["evidence_ledger"][-1]["evidence_id"]])
    attempts = second["failures"][0]["recovery_attempts"]
    assert attempts[0]["strategy"] == "root_cause_then_revalidate"
    assert attempts[1]["strategy"] == "isolate_then_root_cause_revalidate"
    assert attempts[1]["execution_sequence"][0] == "ISOLATE_IMPACT"


def test_strategy_behavior_e_orders_only_dependency_legal_work_differently():
    plan = {"stages": [
        {"name": "低风险", "goal": "low", "work": ["low"], "risk": "LOW"},
        {"name": "高风险", "goal": "high", "work": ["high"], "risk": "HIGH"},
        {"name": "依赖高风险", "goal": "after", "work": ["after"], "dependencies": ["高风险"]},
    ]}
    dependency = _approved(_session(strategy={"execution_order_preference": "dependency_order"},
                                    upstream_plan=plan))
    risk = _approved(_session(strategy={"execution_order_preference": "dependency_and_risk_aware"},
                              upstream_plan=plan))
    assert select_next_legal_work(dependency, "dependency_order") == "低风险"
    assert select_next_legal_work(risk, "dependency_and_risk_aware") == "高风险"
    assert advance(risk)["current_work"] == "高风险"


def test_strategy_behavior_i_returns_different_structured_host_guidance():
    concise = _record(_session(strategy={"interaction_strategy": "concise_evidence_backed_updates"}), "i-concise")
    milestone = _record(_session(strategy={"interaction_strategy": "milestone_evidence_updates"}), "i-milestone")
    a = get_strategy_guidance(concise, phase="INTERACTION")
    b = get_strategy_guidance(milestone, phase="INTERACTION")
    assert a["detail_level"] == "CONCISE" and a["should_update"] is False
    assert b == {**b, "detail_level": "MILESTONE", "should_update": True,
                 "update_reason": "MILESTONE_EVIDENCE", "required_evidence_ids": ["i-milestone"]}
    assert a != b


def _raw_receipt(session, receipt_id="raw", **overrides):
    payload = b"real captured output"
    base = {"receipt_id": receipt_id, "origin": "HARNESS_EXECUTION", "harness": "pytest-adapter",
            "session_id": session["session_id"], "candidate_id": session["candidate_id"],
            "work_id": session["plan"]["stages"][0]["name"], "tool_or_capability": "pytest",
            "execution_id": f"exec:{receipt_id}", "producer": "TEST_RUNNER",
            "source_ref": f"harness://pytest/{receipt_id}", "observed_at": "2026-09-01T00:00:00+00:00",
            "status": "PASS", "content_hash": hashlib.sha256(payload).hexdigest(),
            "artifact_refs": [{"kind": "HARNESS_CAPTURE", "artifact_id": receipt_id,
                               "captured_content": payload,
                               "content_hash": hashlib.sha256(payload).hexdigest()}]}
    base.update(overrides)
    return base


def test_evidence_ingress_rejects_raw_forgery_and_untrusted_or_mismatched_receipts():
    session = _session()
    with pytest.raises(TypeError):
        record_evidence(session, evidence={"status": "PASS"})
    with pytest.raises(ValueError, match="receipt_origin"):
        register_harness_execution_receipt(_raw_receipt(session, "bad-origin", origin="HOST_MODEL"))
    for field, value, error in (("session_id", "other", "receipt_session_mismatch"),
                                ("candidate_id", "other", "receipt_candidate_mismatch"),
                                ("work_id", "other", "receipt_work_mismatch")):
        receipt = _raw_receipt(session, f"bad-{field}", **{field: value})
        rid = register_harness_execution_receipt(receipt)
        with pytest.raises(PermissionError, match=error):
            record_evidence(session, receipt_id=rid)


def test_evidence_ingress_rejects_bad_execution_and_artifact_hash_and_receipt_reuse():
    session = _approved(_session(facts={"goal": "cap", "required_capabilities": ["x"],
                                         "deployment_requirement": False},
                                 registry={"x": {"maturity": 1, "validation_status": "VALIDATED",
                                                 "source_identity_verified": True, "compatible": True,
                                                 "license_compatible": True, "permission_granted": True}}))
    invocation = request_capability_invocation(session, work_id=session["plan"]["stages"][0]["name"],
                                               capability="x", input_payload={})
    bad_execution = _raw_receipt(invocation, "bad-execution", invocation_id="missing",
                                 execution_id="missing", tool_or_capability="x")
    rid = register_harness_execution_receipt(bad_execution)
    with pytest.raises(PermissionError, match="receipt_invocation_not_requested"):
        record_evidence(invocation, receipt_id=rid)
    with tempfile.NamedTemporaryFile(delete=False) as artifact:
        artifact.write(b"actual")
        artifact_path = artifact.name
    try:
        bad_file = _raw_receipt(invocation, "bad-file", artifact_refs=[{
            "kind": "FILE", "path": artifact_path, "content_hash": "0" * 64}], content_hash="0" * 64)
        with pytest.raises(ValueError, match="artifact_hash_mismatch"):
            register_harness_execution_receipt(bad_file)
    finally:
        Path(artifact_path).unlink()
    rid, metadata = record_test_receipt(invocation, receipt_id="once", work_id=invocation["plan"]["stages"][0]["name"],
                                        invocation_id=invocation["capability_invocations"][0]["invocation_id"],
                                        tool_or_capability="x")
    recorded = record_evidence(invocation, receipt_id=rid, evidence_metadata=metadata)
    with pytest.raises(ValueError, match="already_consumed"):
        record_evidence(recorded, receipt_id=rid, evidence_metadata=metadata)


def test_evidence_ingress_real_receipt_e2e_drives_ledger_strategy_and_completion():
    session = _approved(_session(facts={"goal": "交付", "acceptance_requirements": ["真实结果"],
                                         "deployment_requirement": False}))
    items = _acceptance_items(session["acceptance"])
    bindings = {}
    for index, acceptance_item in enumerate(items):
        evidence_id = f"real-e2e-{index}"
        session = _record(session, evidence_id, acceptance_items=[acceptance_item])
        bindings[acceptance_item] = [evidence_id]
    session = update_adaptive_strategy(session,
        patch={"interaction_strategy": "milestone_evidence_updates"}, evidence_ids=[next(iter(bindings.values()))[0]])
    complete = claim_completion(session, bindings)
    assert complete["completion_gate"]["pass"] is True
    assert complete["evidence_ledger"][0]["receipt_id"] == "real-e2e-0"


def test_evidence_ingress_pending_receipt_stays_pending_not_pass():
    session = _session()
    pending = _record(session, "pending", status="PENDING_EXTERNAL_VALIDATION")
    assert pending["evidence_ledger"][0]["status"] == "PENDING_EXTERNAL_VALIDATION"
