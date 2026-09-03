"""Single orchestration runtime for reliable, human-owned project delivery."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
import hashlib
import json

from adaptive_strategy_core import (STRATEGY_FIELDS, apply_verified_strategy_patch,
                                     load_strategy)
from engineering_execution_profile import derive_engineering_execution_profile

from delivery_planning_core import (complexity_from_facts, compose_stages,
                                    derive_final_acceptance, make_fact_model,
                                    reason_capability_needs)
from evidence_core import (append_evidence, canonical_evidence_from_receipt,
                           consume_harness_receipt, evidence_by_id, reclassify_evidence,
                           require_current_evidence)
from plan_governance_core import (apply_human_plan, apply_plan_edit, classify_verified_state,
                                  replan_respecting_locks,
                                  resolve_capability_need)
from understanding_core import planning_facts

RUNTIME_SCHEMA_VERSION = "3.0"
TERMINAL_EVIDENCE_STATES = {"PASS", "FAIL", "PENDING_EXTERNAL_VALIDATION"}
AUTHORITY_ORIGINS = {"USER", "ENTERPRISE", "SYSTEM", "PROJECT"}
CHANGE_SOURCES = {"USER_REQUIREMENT_CHANGE", "ENTERPRISE_REQUIREMENT_CHANGE",
                  "PROJECT_OBSERVED_CHANGE", "SYSTEM_OBSERVED_CHANGE", "AI_INFERENCE"}


def start_from_understanding(*, understanding: dict, **kwargs) -> dict:
    """The only legal multi-turn boundary from natural-language understanding to planning."""
    kwargs.setdefault("adaptive_strategy_state", understanding.get("adaptive_strategy"))
    session = _start_delivery_from_facts(facts=planning_facts(understanding), **kwargs)
    session["understanding"] = deepcopy(understanding)
    session["events"].append({"type": "UNDERSTANDING_BOUND_TO_FACT_MODEL", "at": _now(),
                              "details": {"understanding_id": understanding["understanding_id"],
                                          "fact_events": len(understanding["fact_events"])}})
    return session


def start_delivery(*, understanding: dict | None = None, **kwargs) -> dict:
    """Public entry. Caller-manufactured facts are never accepted as a gate bypass."""
    if understanding is None:
        raise PermissionError("understanding_session_required")
    return start_from_understanding(understanding=understanding, **kwargs)


def _start_delivery_from_facts(*, facts: dict, human_plan: dict | None = None,
                   human_plan_authority_ref: dict | None = None,
                   upstream_plan: dict | None = None, capability_registry: dict | None = None,
                   upstream_capabilities: dict | None = None,
                   harness_capabilities: dict | None = None,
                   adaptive_strategy_state: dict | None = None) -> dict:
    """Create a project-derived session. Human plans are authoritative when supplied."""
    strategy = load_strategy(adaptive_strategy_state)
    model = make_fact_model(**facts)
    complexity = complexity_from_facts(model)
    declared_capabilities = model.get("required_capabilities", {}).get("value") or []
    if not isinstance(declared_capabilities, list):
        raise ValueError("required_capabilities_must_be_list")
    needs = reason_capability_needs(model, declared=declared_capabilities)
    if human_plan:
        expected = "ENTERPRISE" if human_plan.get("source") == "enterprise" else "USER"
        _require_authority(human_plan_authority_ref, expected)
        plan = apply_human_plan(human_plan, model)
    else:
        plan = compose_stages(model, complexity, needs, upstream_plan=upstream_plan,
                              strategy=strategy["planning_strategy"])
        plan["authority"] = "AI_GENERATED_HUMAN_OWNED"
    resolutions = {}
    for name, need in needs["capabilities"].items():
        if need["required"] is True:
            resolutions[name] = resolve_capability_need(
                name, capability_registry or {}, upstream_capabilities or {},
                harness_capabilities or {}, strategy=strategy["capability_preference"])
    now = _now()
    session_id = str(uuid4())
    plan["strategy_guidance"] = strategy["planning_strategy"]
    engineering_profile = derive_engineering_execution_profile(model)
    return {"schema_version": RUNTIME_SCHEMA_VERSION, "session_id": session_id,
            "candidate_id": session_id,
            "revision": 1, "created_at": now, "updated_at": now,
            "facts": model, "complexity": complexity, "capability_needs": needs,
            "adaptive_strategy": strategy,
            "strategy_consumption": {
                "UNDERSTANDING": strategy["question_strategy"],
                "PLANNING": strategy["planning_strategy"],
                "CAPABILITY_SELECTION": strategy["capability_preference"],
                "RECOVERY": strategy["recovery_strategy"],
                "EXECUTION_ORDER": strategy["execution_order_preference"],
                "INTERACTION": strategy["interaction_strategy"],
            },
            "capability_resolutions": resolutions, "plan": plan,
            "engineering_execution_profile": engineering_profile,
            "capability_sources": {"registry": deepcopy(capability_registry or {}),
                                   "upstream": deepcopy(upstream_capabilities or {}),
                                   "harness": deepcopy(harness_capabilities or {})},
            "acceptance": derive_final_acceptance(model, complexity),
            "verified_state": {}, "failures": [], "events": [],
            "status": "PLAN_REVIEW_REQUIRED", "current_work": None,
            "execution_context": {"task": None, "workspace": None, "project": None},
            "plan_review": {"status": "REVIEW_REQUIRED", "approved_revision": None,
                            "approval_source": None, "waiver_scope": None},
            "recovery_policy": {"max_attempts_per_failure": 3,
                                "strategy": strategy["recovery_strategy"],
                                "require_regression_evidence": True},
            "capability_invocations": [], "evidence_ledger": [], "suspensions": [],
            "confirmed_requirement_baseline": _confirmed_requirement_baseline(model),
            "correction_ledger": []}


def record_evidence(session: dict, *, receipt_id: str,
                    evidence_metadata: dict | None = None) -> dict:
    """Append canonical Evidence from one trusted Harness Execution Receipt only."""
    out = deepcopy(session)
    evidence = canonical_evidence_from_receipt(out, receipt_id=receipt_id,
                                                evidence_metadata=evidence_metadata)
    append_evidence(out, evidence, work_id=evidence["work_id"])
    consume_harness_receipt(out, receipt_id, evidence["evidence_id"])
    _event(out, "EVIDENCE_RECORDED", {"evidence_id": evidence["evidence_id"],
                                       "work_id": evidence["work_id"],
                                       "receipt_id": receipt_id})
    return _bump(out, carry_evidence=True)


def get_adaptive_strategy(session: dict) -> dict:
    return deepcopy(session["adaptive_strategy"])


def get_engineering_execution_profile(session: dict) -> dict:
    """Expose optional software-delivery guidance without relaxing any Core gate."""
    return deepcopy(session.get("engineering_execution_profile", {
        "status": "NOT_APPLICABLE", "reason": "profile_not_recorded",
        "core_invariants_unchanged": True, "practices": [],
    }))


def get_strategy_guidance(session: dict, *, phase: str) -> dict:
    guidance = session.get("strategy_consumption", {})
    if phase not in guidance:
        raise ValueError("strategy_phase_invalid")
    catalog_id = guidance[phase]
    result = {"phase": phase, "catalog_id": catalog_id,
              "core_invariants_unchanged": True}
    if phase == "INTERACTION":
        latest = session.get("events", [])[-1] if session.get("events") else None
        evidence_ids = list((latest or {}).get("details", {}).get("evidence_ids", []))
        if not evidence_ids and latest and latest.get("type") == "EVIDENCE_RECORDED":
            evidence_ids = [latest["details"]["evidence_id"]]
        milestone = bool(evidence_ids and latest and latest.get("type") in {
            "EVIDENCE_RECORDED", "CAPABILITY_INVOCATION_VERIFIED", "RECOVERY_REVALIDATED"})
        if catalog_id == "milestone_evidence_updates":
            result.update({"should_update": milestone, "update_reason": "MILESTONE_EVIDENCE"
                           if milestone else "NO_VERIFIED_MILESTONE",
                           "required_evidence_ids": evidence_ids if milestone else [],
                           "detail_level": "MILESTONE"})
        else:
            material = latest is not None and latest.get("type") in {
                "CAPABILITY_INVOCATION_FAILED", "RECOVERY_REVALIDATED", "SUSPENDED",
                "RESUMED_VERIFIED", "COMPLETION_VERIFIED", "FAKE_PASS_BLOCKED"}
            result.update({"should_update": material, "update_reason": "MATERIAL_STATE_CHANGE"
                           if material else "NO_MATERIAL_STATE_CHANGE",
                           "required_evidence_ids": evidence_ids if material else [],
                           "detail_level": "CONCISE"})
    return result


def update_adaptive_strategy(session: dict, *, patch: dict,
                             evidence_ids: list[str]) -> dict:
    out = deepcopy(session)
    records = require_current_evidence(out, evidence_ids, status="PASS")
    if any(r.get("validation_status") not in {"CURRENT", "STILL_VALID"} for r in records):
        raise ValueError("strategy_evidence_not_current")
    out["adaptive_strategy"] = apply_verified_strategy_patch(out["adaptive_strategy"], patch)
    for field in patch:
        phase = {"question_strategy": "UNDERSTANDING", "planning_strategy": "PLANNING",
                 "capability_preference": "CAPABILITY_SELECTION", "recovery_strategy": "RECOVERY",
                 "execution_order_preference": "EXECUTION_ORDER",
                 "interaction_strategy": "INTERACTION"}[field]
        out["strategy_consumption"][phase] = out["adaptive_strategy"][field]
    out["plan"]["strategy_guidance"] = out["adaptive_strategy"]["planning_strategy"]
    out["recovery_policy"]["strategy"] = out["adaptive_strategy"]["recovery_strategy"]
    _event(out, "ADAPTIVE_STRATEGY_UPDATED", {"fields": sorted(patch),
                                                "evidence_ids": list(evidence_ids)})
    return _bump(out, carry_evidence=True)


def bind_execution_context(session: dict, *, task: str, workspace: str, project: str) -> dict:
    """Bind state to the isolation already supplied by the Harness."""
    if not all(isinstance(x, str) and x.strip() for x in (task, workspace, project)):
        raise ValueError("execution_context_task_workspace_project_required")
    out = deepcopy(session)
    out["execution_context"] = {"task": task, "workspace": workspace, "project": project}
    _event(out, "EXECUTION_CONTEXT_BOUND", deepcopy(out["execution_context"]))
    return _bump(out)


def approve_plan(session: dict, *, intent_record: dict, user_origin_ref: dict,
                 waive_display: bool = False, waiver_scope: str | None = None) -> dict:
    """Record human review/approval or an explicit, scoped review-display waiver."""
    if session.get("status") not in {"PLAN_REVIEW_REQUIRED", "PLANNING"}:
        raise ValueError("plan_not_awaiting_review")
    if not isinstance(intent_record, dict):
        raise PermissionError("user_intent_record_required")
    if intent_record.get("intent") not in {"APPROVAL", "DIRECTIVE"}:
        raise PermissionError("approval_or_direct_execution_intent_required")
    if intent_record.get("consequential_ambiguity") or intent_record.get("intent") == "AMBIGUOUS":
        raise PermissionError("ambiguous_intent_cannot_authorize_execution")
    _require_authority(user_origin_ref, "USER")
    required_ref = {f"plan_revision:{session['revision']}", f"plan_scope:{session['session_id']}"}
    if not required_ref.issubset(set(intent_record.get("context_refs") or [])):
        raise PermissionError("approval_not_bound_to_current_plan_revision_and_scope")
    if waive_display and not (isinstance(waiver_scope, str) and waiver_scope.strip()):
        raise ValueError("review_waiver_scope_required")
    out = deepcopy(session)
    out["plan_review"] = {
        "status": "DISPLAY_WAIVED_EXECUTION_APPROVED" if waive_display else "REVIEWED_APPROVED",
        "approved_revision": out["revision"] + 1,
        "approval_source": deepcopy(user_origin_ref),
        "intent_record": deepcopy(intent_record),
        "waiver_scope": waiver_scope.strip() if waive_display else None,
    }
    out["approved_plan_baseline"] = deepcopy(out["plan"])
    out["status"] = "EXECUTING"
    _event(out, "PLAN_REVIEW_WAIVED" if waive_display else "PLAN_APPROVED",
           deepcopy(out["plan_review"]))
    return _bump(out)


def record_user_correction(session: dict, *, description: str, violated_requirements: list[str],
                           root_cause_class: str, related_checks: list[str],
                           user_origin_ref: dict) -> dict:
    """Make a confirmed delivery error durable and detect recurrence of the same root cause."""
    if not description.strip() or not violated_requirements or not root_cause_class.strip():
        raise ValueError("correction_description_requirements_root_cause_required")
    _require_authority(user_origin_ref, "USER")
    out = deepcopy(session)
    fingerprint = hashlib.sha256(json.dumps({
        "requirements": sorted(violated_requirements), "root_cause": root_cause_class.strip()},
        ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    previous = [c for c in out.get("correction_ledger", [])
                if c["fingerprint"] == fingerprint]
    correction = {"correction_id": str(uuid4()), "description": description.strip(),
                  "violated_requirements": list(violated_requirements),
                  "root_cause_class": root_cause_class.strip(),
                  "related_checks": list(related_checks), "fingerprint": fingerprint,
                  "status": "OPEN", "recorded_at": _now(),
                  "user_origin_ref": deepcopy(user_origin_ref),
                  "recurrence_of": previous[-1]["correction_id"] if previous else None}
    out.setdefault("correction_ledger", []).append(correction)
    if previous:
        out["status"] = "RECOVERING"
        _event(out, "REPEATED_CONFIRMED_ERROR", {"correction_id": correction["correction_id"],
                                                   "recurrence_of": correction["recurrence_of"]})
    else:
        _event(out, "USER_CORRECTION_RECORDED", {"correction_id": correction["correction_id"]})
    return _bump(out)


def resolve_user_correction(session: dict, *, correction_id: str, root_cause_fix: str,
                            evidence_ids: list[str]) -> dict:
    """Close a correction only with evidence for the systemic fix and related checks."""
    out = deepcopy(session)
    correction = next((c for c in out.get("correction_ledger", [])
                       if c["correction_id"] == correction_id), None)
    if correction is None:
        raise KeyError("correction_not_found")
    if correction["status"] != "OPEN":
        raise ValueError("correction_already_terminal")
    records = require_current_evidence(out, evidence_ids)
    if not records or any(r["status"] != "PASS" for r in records):
        raise ValueError("correction_resolution_requires_pass_evidence")
    correction.update({"status": "RESOLVED_REVALIDATED", "root_cause_fix": root_cause_fix,
                       "evidence_ids": list(evidence_ids), "resolved_at": _now()})
    if out["status"] == "RECOVERING" and not any(
            c["status"] == "OPEN" for c in out["correction_ledger"]):
        out["status"] = "EXECUTING"
    _event(out, "USER_CORRECTION_REVALIDATED", {"correction_id": correction_id})
    return _bump(out, carry_evidence=True)


def request_capability_invocation(session: dict, *, work_id: str, capability: str,
                                  input_payload: dict, permission_scope: list[str] | None = None) -> dict:
    """Create an authorized Harness invocation envelope bound to one Work Unit."""
    out = deepcopy(session)
    if out.get("plan_review", {}).get("status") not in {
            "REVIEWED_APPROVED", "DISPLAY_WAIVED_EXECUTION_APPROVED"}:
        raise PermissionError("plan_approval_required_before_execution")
    if work_id not in _known_work_ids(out["plan"]):
        raise ValueError(f"work_unit_not_in_active_plan:{work_id}")
    resolution = out.get("capability_resolutions", {}).get(capability)
    if not resolution:
        raise ValueError("capability_not_resolved")
    if resolution.get("readiness") != "READY" or resolution.get("action") != "use_capability":
        raise PermissionError(f"capability_not_ready:{resolution.get('action')}")
    provider_record = _provider_record(out, resolution["resolution"], capability)
    invocation = {"invocation_id": str(uuid4()), "session_id": out["session_id"],
                  "plan_revision": out["revision"], "work_id": work_id,
                  "capability": capability, "provider": resolution["resolution"],
                  "capability_version": provider_record.get("version", "NOT_AVAILABLE"),
                  "input": deepcopy(input_payload), "input_scope": sorted(input_payload),
                  "permission_scope": list(permission_scope or []),
                  "lifecycle": ["DISCOVERED", "RESOLVED", "BOUND", "ACTIVATED"],
                  "status": "REQUESTED", "requested_at": _now()}
    out["capability_invocations"].append(invocation)
    out["current_work"] = work_id
    _event(out, "CAPABILITY_INVOCATION_REQUESTED", {"invocation_id": invocation["invocation_id"],
                                                     "work_id": work_id,
                                                     "capability": capability})
    return _bump(out)


def record_capability_result(session: dict, *, invocation_id: str, status: str,
                             output, evidence_ids: list[str]) -> dict:
    """Bind Harness output to its Work Unit; failed invocation enters Recovery."""
    if status not in {"PASS", "FAIL"}:
        raise ValueError("capability_result_status_invalid")
    out = deepcopy(session)
    invocation = next((i for i in out["capability_invocations"]
                       if i["invocation_id"] == invocation_id), None)
    if invocation is None:
        raise KeyError("capability_invocation_not_found")
    if invocation["status"] != "REQUESTED":
        raise ValueError("capability_invocation_already_terminal")
    evidence_records = require_current_evidence(out, evidence_ids, work_id=invocation["work_id"], status=status)
    if any(record.get("invocation_id") != invocation_id for record in evidence_records):
        raise PermissionError("capability_result_requires_matching_execution_receipt")
    input_hash = hashlib.sha256(json.dumps(invocation.get("input"), ensure_ascii=False,
                                           sort_keys=True).encode("utf-8")).hexdigest()
    invocation.update({"status": status, "output": deepcopy(output),
                       "evidence_ids": list(evidence_ids), "completed_at": _now(),
                       "lifecycle": invocation["lifecycle"] + ["INVOKED", "RESULT_RECORDED",
                                                                "EVIDENCE_BOUND", "DEACTIVATED"],
                       "active_instruction_context": False,
                       "temporary_authorization_active": False,
                       "input_hash": input_hash, "input_scope": [], "permission_scope": []})
    invocation.pop("input", None)
    if status == "FAIL":
        failure = {"failure_id": str(uuid4()), "work_id": invocation["work_id"],
                   "evidence_ids": list(evidence_ids), "root_cause": None, "status": "OPEN",
                   "recorded_at": _now(), "recovery_attempts": [],
                   "source_invocation_id": invocation_id}
        out["failures"].append(failure)
        out["status"] = "RECOVERING"
        _event(out, "CAPABILITY_INVOCATION_FAILED", {"invocation_id": invocation_id,
                                                      "failure_id": failure["failure_id"]})
    else:
        out["verified_state"][invocation["work_id"]] = {
            "status": "PASS", "candidate": out["session_id"],
            "capability": invocation["capability"], "evidence_ids": list(evidence_ids),
            "output": deepcopy(output)}
        out["status"] = "EXECUTING"
        _event(out, "CAPABILITY_INVOCATION_VERIFIED", {"invocation_id": invocation_id,
                                                        "work_id": invocation["work_id"]})
    return _bump(out, carry_evidence=True)


def edit_plan(session: dict, edit: dict) -> dict:
    """Apply an explicitly attributed edit; missing or untrusted authority fails closed."""
    out = deepcopy(session)
    semantic_edit = dict(edit)
    if "actor" not in semantic_edit:
        raise PermissionError("plan_edit_actor_required")
    actor = semantic_edit["actor"]
    if actor in {"HUMAN_EXPLICIT", "ENTERPRISE_AUTHORIZED"}:
        authority_ref = semantic_edit.get("authority_ref")
        expected = "USER" if actor == "HUMAN_EXPLICIT" else "ENTERPRISE"
        if not isinstance(authority_ref, dict) or authority_ref.get("origin") != expected:
            raise PermissionError("trusted_plan_edit_authority_ref_required")
        if not all(isinstance(authority_ref.get(k), str) and authority_ref[k].strip()
                   for k in ("harness", "conversation_id", "message_id")):
            raise PermissionError("plan_edit_authority_ref_incomplete")
    elif actor != "AI_AUTOMATIC":
        raise PermissionError("plan_edit_actor_not_authorized")
    out["plan"] = apply_plan_edit(out["plan"], semantic_edit)
    if semantic_edit["actor"] in {"HUMAN_EXPLICIT", "ENTERPRISE_AUTHORIZED"}:
        out["approved_plan_baseline"] = deepcopy(out["plan"])
        out["plan_review"] = {"status": "REVIEWED_APPROVED",
                              "approved_revision": out["revision"] + 1,
                              "approval_source": deepcopy(semantic_edit["authority_ref"]),
                              "waiver_scope": None}
    else:
        out["status"] = "PLAN_REVIEW_REQUIRED"
        out["plan_review"] = {"status": "REVIEW_REQUIRED", "approved_revision": None,
                              "approval_source": None, "waiver_scope": None}
    _event(out, "PLAN_EDITED", {"op": semantic_edit.get("op"),
                                 "affected": out["plan"].get("affected_assumptions", [])})
    return _bump(out)


def change_conditions(session: dict, *, changed_facts: dict,
                      change_source: str, authority_ref: dict | None = None,
                      evidence_ids: list[str] | None = None,
                      replanned_work_units: dict | None = None,
                      capability_registry: dict | None = None,
                      upstream_capabilities: dict | None = None,
                      harness_capabilities: dict | None = None) -> dict:
    """Replace affected AI work with a planner-produced fragment and reclassify evidence.

    The host model/mature planning Skill supplies `replanned_work_units` keyed by the old
    work-unit name. Core validates scope and human authority; it does not emulate a planner
    with project-type rules.
    """
    out = deepcopy(session)
    if change_source not in CHANGE_SOURCES:
        raise ValueError("change_source_invalid")
    if change_source == "AI_INFERENCE":
        raise PermissionError("ai_inference_cannot_change_confirmed_facts")
    if change_source == "USER_REQUIREMENT_CHANGE":
        _require_authority(authority_ref, "USER")
    elif change_source == "ENTERPRISE_REQUIREMENT_CHANGE":
        _require_authority(authority_ref, "ENTERPRISE")
    else:
        _require_authority(authority_ref, "PROJECT" if change_source.startswith("PROJECT") else "SYSTEM")
        require_current_evidence(out, evidence_ids or [], status="PASS")
    raw = {k: deepcopy(v) for k, v in out["facts"].items() if not k.startswith("_")}
    raw.update(changed_facts)
    out["facts"] = make_fact_model(**raw)
    out.setdefault("requirement_history", []).append({
        "event_id": str(uuid4()), "source": change_source,
        "changed_facts": deepcopy(changed_facts), "at": _now()})
    if change_source in {"USER_REQUIREMENT_CHANGE", "ENTERPRISE_REQUIREMENT_CHANGE"}:
        out["confirmed_requirement_baseline"].update({
            key: deepcopy(value.get("value") if isinstance(value, dict) and "value" in value else value)
            for key, value in changed_facts.items()})
    changed = set(changed_facts)
    out["plan"] = replan_respecting_locks(out["plan"], sorted(changed),
        new_facts=changed_facts, regenerated_stages=replanned_work_units)
    out["complexity"] = complexity_from_facts(out["facts"])
    declared_capabilities = out["facts"].get("required_capabilities", {}).get("value") or []
    if not isinstance(declared_capabilities, list):
        raise ValueError("required_capabilities_must_be_list")
    out["capability_needs"] = reason_capability_needs(
        out["facts"], declared=declared_capabilities)
    previous_sources = out.get("capability_sources", {})
    sources = {
        "registry": deepcopy(capability_registry if capability_registry is not None
                             else previous_sources.get("registry", {})),
        "upstream": deepcopy(upstream_capabilities if upstream_capabilities is not None
                             else previous_sources.get("upstream", {})),
        "harness": deepcopy(harness_capabilities if harness_capabilities is not None
                            else previous_sources.get("harness", {})),
    }
    out["capability_sources"] = sources
    out["capability_resolutions"] = {}
    for name, need in out["capability_needs"]["capabilities"].items():
        if need["required"] is True:
            out["capability_resolutions"][name] = resolve_capability_need(
                name, sources["registry"], sources["upstream"], sources["harness"],
                strategy=out["adaptive_strategy"]["capability_preference"])
    out["acceptance"] = derive_final_acceptance(out["facts"], out["complexity"])
    evidence_change_keys = changed | {str(k) for k in changed_facts}
    classification = classify_verified_state(out.get("verified_state", {}), evidence_change_keys)
    out["evidence_classification"] = classification
    out["verified_state"] = {
        **{k: dict(v, validation_status="STILL_VALID") for k, v in classification["preserved"].items()},
        **{k: dict(v, validation_status="INVALIDATED") for k, v in classification["invalidated"].items()},
        **{k: dict(v, validation_status="REQUIRES_REVALIDATION") for k, v in classification["requires_revalidation"].items()},
    }
    next_revision = out["revision"] + 1
    out["evidence_classification"] = {
        **classification,
        "ledger": reclassify_evidence(out, changed_facts=changed, next_revision=next_revision),
    }
    out["status"] = ("PLANNING" if out["plan"].get("replan_input_required")
                     else "EXECUTING")
    _event(out, "CONDITIONS_CHANGED", {"changed_facts": sorted(changed),
                                        "recomputed": out["plan"].get("recomputed", [])})
    return _bump(out, carry_evidence=True)


def record_failure(session: dict, *, work_id: str, evidence_ids: list[str],
                   root_cause: str | None = None) -> dict:
    """Freeze a failure. A report edit cannot turn it into PASS."""
    out = deepcopy(session)
    if work_id not in _known_work_ids(out["plan"]):
        raise ValueError(f"work_unit_not_in_active_plan:{work_id}")
    require_current_evidence(out, evidence_ids, work_id=work_id, status="FAIL")
    failure = {"failure_id": str(uuid4()), "work_id": work_id,
               "evidence_ids": list(evidence_ids),
               "root_cause": root_cause, "status": "OPEN", "recorded_at": _now(),
               "recovery_attempts": []}
    out["failures"].append(failure)
    out["status"] = "RECOVERING"
    _event(out, "FAILURE_FROZEN", {"failure_id": failure["failure_id"], "work_id": work_id})
    return _bump(out, carry_evidence=True)


def record_recovery(session: dict, *, failure_id: str, action: str,
                    recovery_evidence_ids: list[str], blocker_evidence_ids: list[str],
                    regression_evidence_ids: list[str] | None = None) -> dict:
    """Recovery succeeds only when the original blocker is mechanically revalidated."""
    out = deepcopy(session)
    failure = next((f for f in out["failures"] if f["failure_id"] == failure_id), None)
    if failure is None:
        raise KeyError("failure_not_found")
    if failure["status"] in {"RECOVERED_REVALIDATED", "HUMAN_INTERVENTION_REQUIRED"}:
        raise ValueError("failure_already_terminal")
    budget = out.get("recovery_policy", {}).get("max_attempts_per_failure", 3)
    if len(failure["recovery_attempts"]) >= budget:
        failure["status"] = "HUMAN_INTERVENTION_REQUIRED"
        out["status"] = "BLOCKED"
        out["human_recovery_package"] = _recovery_package(failure, "RECOVERY_BUDGET_EXHAUSTED")
        _event(out, "RECOVERY_BUDGET_EXHAUSTED", {"failure_id": failure_id})
        return _bump(out, carry_evidence=True)
    regression_evidence_ids = regression_evidence_ids or []
    require_current_evidence(out, recovery_evidence_ids, work_id=failure["work_id"])
    blocker_records = require_current_evidence(out, blocker_evidence_ids,
                                               work_id=failure["work_id"])
    regression_records = (require_current_evidence(out, regression_evidence_ids)
                          if regression_evidence_ids else [])
    recovery_strategy = out["adaptive_strategy"]["recovery_strategy"]
    recovery_sequence = (["ISOLATE_IMPACT", "ROOT_CAUSE", "BOUNDED_FIX", "ORIGINAL_BLOCKER",
                          "REGRESSION"] if recovery_strategy == "isolate_then_root_cause_revalidate"
                         else ["ROOT_CAUSE", "BOUNDED_FIX", "ORIGINAL_BLOCKER", "REGRESSION"])
    failure["recovery_attempts"].append({"action": action,
        "recovery_evidence_ids": list(recovery_evidence_ids),
        "blocker_evidence_ids": list(blocker_evidence_ids),
        "regression_evidence_ids": list(regression_evidence_ids), "recorded_at": _now(),
        "strategy": recovery_strategy, "execution_sequence": recovery_sequence})
    require_regression = out.get("recovery_policy", {}).get("require_regression_evidence", True)
    passed = (all(item["status"] == "PASS" for item in blocker_records) and
              (bool(regression_records) or not require_regression) and
              all(item["status"] == "PASS" for item in regression_records))
    failure["status"] = "RECOVERED_REVALIDATED" if passed else "RECOVERY_UNVERIFIED"
    out["status"] = "EXECUTING" if passed else "RECOVERING"
    _event(out, "RECOVERY_REVALIDATED" if passed else "RECOVERY_REVALIDATION_FAILED",
           {"failure_id": failure_id, "strategy": recovery_strategy,
            "execution_sequence": recovery_sequence})
    return _bump(out, carry_evidence=True)


def _recovery_package(failure: dict, stop_reason: str) -> dict:
    return {"failure_id": failure["failure_id"], "work_id": failure["work_id"],
            "original_evidence_ids": deepcopy(failure["evidence_ids"]),
            "root_cause": failure.get("root_cause"),
            "attempts": deepcopy(failure["recovery_attempts"]),
            "human_action_required": "提供新的权限、业务判断或外部修复后重新验证原 blocker",
            "resume_verification": "重跑 original blocker 与相关 regression",
            "stop_reason": stop_reason}


def claim_completion(session: dict, evidence_bindings: dict[str, list[str]]) -> dict:
    """Anti-fake-PASS: every acceptance item needs terminal evidence on this candidate."""
    out = deepcopy(session)
    required = _acceptance_items(out["acceptance"])
    missing, failed, pending = [], [], []
    for item in required:
        ids = evidence_bindings.get(item) or []
        try:
            records = require_current_evidence(out, ids, acceptance_item=item)
        except (KeyError, ValueError):
            missing.append(item)
            continue
        if any(record["status"] == "FAIL" for record in records):
            failed.append(item)
        elif any(record["status"] == "PENDING_EXTERNAL_VALIDATION" for record in records):
            pending.append(item)
    open_failures = [f["failure_id"] for f in out["failures"] if f["status"] != "RECOVERED_REVALIDATED"]
    planning_open = out["status"] in {"PLANNING", "UNDERSTANDING", "SUSPENDED", "BLOCKED"}
    invalidated = [item["evidence_id"] for item in out.get("evidence_ledger", [])
                   if item.get("validation_status") in {"INVALIDATED", "REQUIRES_REVALIDATION"}]
    open_corrections = [c["correction_id"] for c in out.get("correction_ledger", [])
                        if c["status"] != "RESOLVED_REVALIDATED"]
    complete = not (missing or failed or pending or open_failures or planning_open or invalidated
                    or open_corrections)
    out["status"] = "COMPLETED" if complete else "NOT_COMPLETE"
    out["completion_gate"] = {"pass": complete, "missing": missing, "failed": failed,
        "pending_external_validation": pending, "open_failures": open_failures,
        "open_corrections": open_corrections, "planning_open": planning_open,
        "invalidated_evidence": invalidated}
    _event(out, "COMPLETION_VERIFIED" if complete else "FAKE_PASS_BLOCKED", out["completion_gate"])
    return _bump(out, carry_evidence=True)


def suspend(session: dict, *, reason: str, checkpoint_identity: dict,
            evidence_ids: list[str], initiator: str = "SYSTEM",
            authority_ref: dict | None = None) -> dict:
    out = deepcopy(session)
    require_current_evidence(out, evidence_ids)
    if initiator not in {"SYSTEM", "RESOURCE", "USER"}:
        raise ValueError("suspension_initiator_invalid")
    if initiator == "USER":
        _require_authority(authority_ref, "USER")
    required_identity = {"git_head", "worktree_identity", "runtime_identity",
                         "contract_hash", "evidence_anchor"}
    missing = sorted(required_identity - set(checkpoint_identity))
    if missing:
        raise ValueError(f"checkpoint_identity_missing:{missing}")
    package = {"suspension_id": str(uuid4()), "session_id": out["session_id"],
               "candidate_id": out["candidate_id"], "revision": out["revision"],
               "reason": reason, "facts": deepcopy(out["facts"]), "plan": deepcopy(out["plan"]),
               "current_work": out.get("current_work"), "verified_state": deepcopy(out["verified_state"]),
               "failures": deepcopy(out["failures"]), "checkpoint_identity": deepcopy(checkpoint_identity),
               "evidence_ids": list(evidence_ids), "next_legal_action": _next_legal_work(out),
               "initiator": initiator, "authority_ref": deepcopy(authority_ref),
               "created_at": _now()}
    out["suspensions"].append(package)
    out["status"] = "SUSPENDED"
    _event(out, "SUSPENDED", {"suspension_id": package["suspension_id"]})
    return _bump(out, carry_evidence=True)


def resume(session: dict, *, package: dict, current_identity: dict,
           revalidation_evidence_ids: list[str], user_origin_ref: dict | None = None) -> dict:
    out = deepcopy(session)
    if out["status"] != "SUSPENDED":
        raise ValueError("session_not_suspended")
    if package.get("session_id") != out["session_id"] or package.get("candidate_id") != out["candidate_id"]:
        raise ValueError("resume_session_or_candidate_mismatch")
    if package.get("initiator") == "USER":
        _require_authority(user_origin_ref, "USER")
    expected = package.get("checkpoint_identity") or {}
    mismatches = sorted(key for key, value in expected.items() if current_identity.get(key) != value)
    if mismatches:
        raise ValueError(f"resume_identity_mismatch:{mismatches}")
    require_current_evidence(out, revalidation_evidence_ids)
    out["status"] = "PLANNING" if out["plan"].get("replan_input_required") else "EXECUTING"
    _event(out, "RESUMED_VERIFIED", {"suspension_id": package.get("suspension_id")})
    return _bump(out, carry_evidence=True)


def advance(session: dict) -> dict:
    out = deepcopy(session)
    if out["status"] in {"RECOVERING", "SUSPENDED", "BLOCKED", "COMPLETED",
                         "PLAN_REVIEW_REQUIRED", "PLANNING"}:
        raise ValueError(f"advance_illegal_status:{out['status']}")
    next_work = select_next_legal_work(out, out["adaptive_strategy"]["execution_order_preference"])
    if next_work is None:
        raise ValueError("no_legal_next_work")
    out["current_work"] = next_work
    out["status"] = "EXECUTING"
    _event(out, "WORK_ADVANCED", {"work_id": next_work,
                                    "strategy": out["adaptive_strategy"]["execution_order_preference"]})
    return _bump(out)


def verify(session: dict, *, evidence_bindings: dict[str, list[str]]) -> dict:
    return claim_completion(session, evidence_bindings)


def cancel_delivery(session: dict, *, intent_record: dict, user_origin_ref: dict) -> dict:
    _require_human_intent(intent_record, user_origin_ref, {"CANCEL", "REJECTION"})
    out = deepcopy(session)
    out["status"] = "CANCELLED"
    _event(out, "DELIVERY_CANCELLED_BY_USER", {"user_origin_ref": deepcopy(user_origin_ref)})
    return _bump(out)


def _require_authority(ref: dict | None, expected_origin: str) -> dict:
    if expected_origin not in AUTHORITY_ORIGINS:
        raise ValueError("authority_origin_invalid")
    if not isinstance(ref, dict) or ref.get("origin") != expected_origin:
        raise PermissionError(f"trusted_{expected_origin.lower()}_origin_ref_required")
    if not all(isinstance(ref.get(k), str) and ref[k].strip()
               for k in ("harness", "conversation_id", "message_id")):
        raise PermissionError("authority_ref_incomplete")
    return ref


def _require_human_intent(intent_record: dict, ref: dict, allowed: set[str]) -> None:
    _require_authority(ref, "USER")
    if not isinstance(intent_record, dict) or intent_record.get("intent") not in allowed:
        raise PermissionError("human_intent_not_authorized")
    if intent_record.get("consequential_ambiguity"):
        raise PermissionError("ambiguous_intent_cannot_change_human_state")


def _acceptance_items(matrix: dict) -> list[str]:
    items = []
    for key, value in matrix.items():
        if key.startswith("_") or isinstance(value, dict):
            continue
        if isinstance(value, list): items.extend(f"{key}:{v}" for v in value)
        elif value not in (None, "", [], {}): items.append(key)
    return items


def _known_work_ids(plan: dict) -> set[str]:
    return {item["name"] for bucket in ("stages", "tasks", "checks")
            for item in plan.get(bucket, []) if item.get("name")}


def _provider_record(session: dict, provider: str, capability: str) -> dict:
    if provider == "LOCAL_CORE":
        record = session.get("capability_sources", {}).get("registry", {}).get(capability)
        return record if isinstance(record, dict) else {}
    for source in ("registry", "upstream", "harness"):
        catalog = session.get("capability_sources", {}).get(source, {})
        if provider in catalog and isinstance(catalog[provider], dict):
            return catalog[provider]
    return {}


def _confirmed_requirement_baseline(model: dict) -> dict:
    """Compact durable view of user/project-confirmed facts; AI proposals never enter it."""
    allowed_sources = {"USER_EXPLICIT", "USER_CONFIRMED", "PROJECT_EVIDENCE",
                       "SYSTEM_OBSERVED"}
    allowed_states = {"DECLARED", "OBSERVED"}
    return {key: deepcopy(value.get("value")) for key, value in model.items()
            if isinstance(value, dict) and value.get("value") is not None and (
                value.get("provenance") in allowed_sources or value.get("state") in allowed_states)}


def _next_legal_work(session: dict) -> str | None:
    return select_next_legal_work(session, "dependency_order")


def select_next_legal_work(session: dict, strategy: str) -> str | None:
    """Choose only dependency-legal real work; strategy orders the legal candidate set."""
    if strategy not in {"dependency_order", "dependency_and_risk_aware"}:
        raise ValueError("execution_order_strategy_invalid")
    completed = {key for key, value in session.get("verified_state", {}).items()
                 if value.get("status") == "PASS"}
    all_items = [item for bucket in ("stages", "tasks", "checks")
                 for item in session["plan"].get(bucket, [])]
    by_name = {item.get("name"): item for item in all_items}
    legal = []
    for item in all_items:
        name = item.get("name")
        if name in completed:
            continue
        dependencies = {dep for dep in item.get("dependencies", []) if dep in by_name}
        if dependencies <= completed:
            legal.append(item)
    if not legal:
        return None
    if strategy == "dependency_and_risk_aware":
        chosen = max(legal, key=_work_risk_priority)
        return chosen.get("name")
    return legal[0].get("name")


def _work_risk_priority(item: dict) -> tuple[int, int]:
    raw = item.get("risk_score", item.get("risk", 0))
    if isinstance(raw, str):
        raw = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(raw.upper(), 0)
    score = int(raw) if isinstance(raw, (int, float)) else 0
    critical = 1 if item.get("critical_dependency") or item.get("failure_cost") == "HIGH" else 0
    return score, critical


def _legacy_next_legal_work(session: dict) -> str | None:
    """Retained only for historical callers; all runtime decisions use select_next_legal_work."""
    completed = {key for key, value in session.get("verified_state", {}).items()
                 if value.get("status") == "PASS"}
    for bucket in ("stages", "tasks", "checks"):
        for item in session["plan"].get(bucket, []):
            if item.get("name") not in completed:
                return item.get("name")
    return None


def _event(session: dict, kind: str, details: dict) -> None:
    session["events"].append({"type": kind, "at": _now(), "details": details})


def _bump(session: dict, *, carry_evidence: bool = False) -> dict:
    session["revision"] += 1
    if carry_evidence:
        for record in session.get("evidence_ledger", []):
            if record.get("valid_for_revision") == session["revision"] - 1 and record.get("validation_status") not in {
                    "INVALIDATED", "REQUIRES_REVALIDATION"}:
                record["valid_for_revision"] = session["revision"]
    session["updated_at"] = _now()
    return session


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
