"""Single orchestration runtime for reliable, human-owned project delivery."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from delivery_planning_core import (complexity_from_facts, compose_stages,
                                    derive_final_acceptance, make_fact_model,
                                    reason_capability_needs)
from plan_governance_core import (apply_human_plan, apply_plan_edit, classify_verified_state,
                                  replan_respecting_locks,
                                  resolve_capability_need)
from understanding_core import planning_facts

RUNTIME_SCHEMA_VERSION = "1.0"
TERMINAL_EVIDENCE_STATES = {"PASS", "FAIL", "PENDING_EXTERNAL_VALIDATION"}


def start_from_understanding(*, understanding: dict, **kwargs) -> dict:
    """The only legal multi-turn boundary from natural-language understanding to planning."""
    session = start_delivery(facts=planning_facts(understanding), **kwargs)
    session["understanding"] = deepcopy(understanding)
    session["events"].append({"type": "UNDERSTANDING_BOUND_TO_FACT_MODEL", "at": _now(),
                              "details": {"understanding_id": understanding["understanding_id"],
                                          "fact_events": len(understanding["fact_events"])}})
    return session


def start_delivery(*, facts: dict, human_plan: dict | None = None,
                   upstream_plan: dict | None = None, capability_registry: dict | None = None,
                   upstream_capabilities: dict | None = None,
                   harness_capabilities: dict | None = None) -> dict:
    """Create a project-derived session. Human plans are authoritative when supplied."""
    model = make_fact_model(**facts)
    complexity = complexity_from_facts(model)
    declared_capabilities = model.get("required_capabilities", {}).get("value") or []
    if not isinstance(declared_capabilities, list):
        raise ValueError("required_capabilities_must_be_list")
    needs = reason_capability_needs(model, declared=declared_capabilities)
    if human_plan:
        plan = apply_human_plan(human_plan, model)
    else:
        plan = compose_stages(model, complexity, needs, upstream_plan=upstream_plan)
        plan["authority"] = "AI_GENERATED_HUMAN_OWNED"
    resolutions = {}
    for name, need in needs["capabilities"].items():
        if need["required"] is True:
            resolutions[name] = resolve_capability_need(
                name, capability_registry or {}, upstream_capabilities or {},
                harness_capabilities or {})
    now = _now()
    return {"schema_version": RUNTIME_SCHEMA_VERSION, "session_id": str(uuid4()),
            "revision": 1, "created_at": now, "updated_at": now,
            "facts": model, "complexity": complexity, "capability_needs": needs,
            "capability_resolutions": resolutions, "plan": plan,
            "capability_sources": {"registry": deepcopy(capability_registry or {}),
                                   "upstream": deepcopy(upstream_capabilities or {}),
                                   "harness": deepcopy(harness_capabilities or {})},
            "acceptance": derive_final_acceptance(model, complexity),
            "verified_state": {}, "failures": [], "events": [],
            "status": "PLANNED", "current_work": None,
            "recovery_policy": {"max_attempts_per_failure": 3,
                                "require_regression_evidence": True},
            "capability_invocations": []}


def request_capability_invocation(session: dict, *, work_id: str, capability: str,
                                  input_payload: dict) -> dict:
    """Create an authorized Harness invocation envelope bound to one Work Unit."""
    out = deepcopy(session)
    resolution = out.get("capability_resolutions", {}).get(capability)
    if not resolution:
        raise ValueError("capability_not_resolved")
    if resolution.get("readiness") != "READY" or resolution.get("action") != "use_capability":
        raise PermissionError(f"capability_not_ready:{resolution.get('action')}")
    invocation = {"invocation_id": str(uuid4()), "work_id": work_id,
                  "capability": capability, "provider": resolution["resolution"],
                  "input": deepcopy(input_payload), "status": "REQUESTED", "requested_at": _now()}
    out["capability_invocations"].append(invocation)
    out["current_work"] = work_id
    _event(out, "CAPABILITY_INVOCATION_REQUESTED", {"invocation_id": invocation["invocation_id"],
                                                     "work_id": work_id,
                                                     "capability": capability})
    return _bump(out)


def record_capability_result(session: dict, *, invocation_id: str, status: str,
                             output, evidence: list) -> dict:
    """Bind Harness output to its Work Unit; failed invocation enters Recovery."""
    if status not in {"PASS", "FAIL"}:
        raise ValueError("capability_result_status_invalid")
    if not evidence:
        raise ValueError("capability_result_evidence_required")
    out = deepcopy(session)
    invocation = next((i for i in out["capability_invocations"]
                       if i["invocation_id"] == invocation_id), None)
    if invocation is None:
        raise KeyError("capability_invocation_not_found")
    if invocation["status"] != "REQUESTED":
        raise ValueError("capability_invocation_already_terminal")
    invocation.update({"status": status, "output": deepcopy(output),
                       "evidence": deepcopy(evidence), "completed_at": _now()})
    if status == "FAIL":
        failure = {"failure_id": str(uuid4()), "work_id": invocation["work_id"],
                   "evidence": deepcopy(evidence), "root_cause": None, "status": "OPEN",
                   "recorded_at": _now(), "recovery_attempts": [],
                   "source_invocation_id": invocation_id}
        out["failures"].append(failure)
        out["status"] = "RECOVERING"
        _event(out, "CAPABILITY_INVOCATION_FAILED", {"invocation_id": invocation_id,
                                                      "failure_id": failure["failure_id"]})
    else:
        out["verified_state"][invocation["work_id"]] = {
            "status": "PASS", "candidate": out["session_id"],
            "capability": invocation["capability"], "evidence": deepcopy(evidence),
            "output": deepcopy(output)}
        out["status"] = "EXECUTING"
        _event(out, "CAPABILITY_INVOCATION_VERIFIED", {"invocation_id": invocation_id,
                                                        "work_id": invocation["work_id"]})
    return _bump(out)


def edit_plan(session: dict, edit: dict) -> dict:
    """Apply a semantic edit translated from natural language; human is default actor."""
    out = deepcopy(session)
    semantic_edit = dict(edit)
    semantic_edit.setdefault("actor", "HUMAN_EXPLICIT")
    out["plan"] = apply_plan_edit(out["plan"], semantic_edit)
    _event(out, "PLAN_EDITED", {"op": semantic_edit.get("op"),
                                 "affected": out["plan"].get("affected_assumptions", [])})
    return _bump(out)


def change_conditions(session: dict, *, changed_facts: dict,
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
    raw = {k: deepcopy(v) for k, v in out["facts"].items() if not k.startswith("_")}
    raw.update(changed_facts)
    out["facts"] = make_fact_model(**raw)
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
                name, sources["registry"], sources["upstream"], sources["harness"])
    out["acceptance"] = derive_final_acceptance(out["facts"], out["complexity"])
    evidence_change_keys = changed | {str(k) for k in changed_facts}
    classification = classify_verified_state(out.get("verified_state", {}), evidence_change_keys)
    out["evidence_classification"] = classification
    out["verified_state"] = {
        **{k: dict(v, validation_status="STILL_VALID") for k, v in classification["preserved"].items()},
        **{k: dict(v, validation_status="INVALIDATED") for k, v in classification["invalidated"].items()},
        **{k: dict(v, validation_status="REQUIRES_REVALIDATION") for k, v in classification["requires_revalidation"].items()},
    }
    out["status"] = ("PLANNING" if out["plan"].get("replan_input_required")
                     else "EXECUTING")
    _event(out, "CONDITIONS_CHANGED", {"changed_facts": sorted(changed),
                                        "recomputed": out["plan"].get("recomputed", [])})
    return _bump(out)


def record_failure(session: dict, *, work_id: str, evidence: list,
                   root_cause: str | None = None) -> dict:
    """Freeze a failure. A report edit cannot turn it into PASS."""
    if not evidence:
        raise ValueError("failure_evidence_required")
    out = deepcopy(session)
    failure = {"failure_id": str(uuid4()), "work_id": work_id, "evidence": evidence,
               "root_cause": root_cause, "status": "OPEN", "recorded_at": _now(),
               "recovery_attempts": []}
    out["failures"].append(failure)
    out["status"] = "RECOVERING"
    _event(out, "FAILURE_FROZEN", {"failure_id": failure["failure_id"], "work_id": work_id})
    return _bump(out)


def record_recovery(session: dict, *, failure_id: str, action: str,
                    evidence: list, blocker_revalidation: dict,
                    regression_evidence: list | None = None) -> dict:
    """Recovery succeeds only when the original blocker is mechanically revalidated."""
    out = deepcopy(session)
    failure = next((f for f in out["failures"] if f["failure_id"] == failure_id), None)
    if failure is None:
        raise KeyError("failure_not_found")
    budget = out.get("recovery_policy", {}).get("max_attempts_per_failure", 3)
    if len(failure["recovery_attempts"]) >= budget:
        failure["status"] = "HUMAN_INTERVENTION_REQUIRED"
        out["status"] = "BLOCKED"
        out["human_recovery_package"] = _recovery_package(failure, "RECOVERY_BUDGET_EXHAUSTED")
        _event(out, "RECOVERY_BUDGET_EXHAUSTED", {"failure_id": failure_id})
        return _bump(out)
    regression_evidence = regression_evidence or []
    failure["recovery_attempts"].append({"action": action, "evidence": evidence,
        "blocker_revalidation": blocker_revalidation,
        "regression_evidence": deepcopy(regression_evidence), "recorded_at": _now()})
    require_regression = out.get("recovery_policy", {}).get("require_regression_evidence", True)
    passed = (bool(evidence) and blocker_revalidation.get("status") == "PASS" and
              (bool(regression_evidence) or not require_regression))
    failure["status"] = "RECOVERED_REVALIDATED" if passed else "RECOVERY_UNVERIFIED"
    out["status"] = "EXECUTING" if passed else "RECOVERING"
    _event(out, "RECOVERY_REVALIDATED" if passed else "RECOVERY_REVALIDATION_FAILED",
           {"failure_id": failure_id})
    return _bump(out)


def _recovery_package(failure: dict, stop_reason: str) -> dict:
    return {"failure_id": failure["failure_id"], "work_id": failure["work_id"],
            "original_evidence": deepcopy(failure["evidence"]),
            "root_cause": failure.get("root_cause"),
            "attempts": deepcopy(failure["recovery_attempts"]),
            "human_action_required": "提供新的权限、业务判断或外部修复后重新验证原 blocker",
            "resume_verification": "重跑 original blocker 与相关 regression",
            "stop_reason": stop_reason}


def claim_completion(session: dict, evidence_results: dict) -> dict:
    """Anti-fake-PASS: every acceptance item needs terminal evidence on this candidate."""
    out = deepcopy(session)
    required = _acceptance_items(out["acceptance"])
    missing, failed, pending = [], [], []
    for item in required:
        result = evidence_results.get(item)
        if not result or result.get("status") not in TERMINAL_EVIDENCE_STATES or not result.get("evidence"):
            missing.append(item)
        elif result["status"] == "FAIL": failed.append(item)
        elif result["status"] == "PENDING_EXTERNAL_VALIDATION": pending.append(item)
    open_failures = [f["failure_id"] for f in out["failures"] if f["status"] != "RECOVERED_REVALIDATED"]
    complete = not (missing or failed or pending or open_failures)
    out["status"] = "COMPLETED" if complete else "NOT_COMPLETE"
    out["completion_gate"] = {"pass": complete, "missing": missing, "failed": failed,
        "pending_external_validation": pending, "open_failures": open_failures}
    _event(out, "COMPLETION_VERIFIED" if complete else "FAKE_PASS_BLOCKED", out["completion_gate"])
    return _bump(out)


def _acceptance_items(matrix: dict) -> list[str]:
    items = []
    for key, value in matrix.items():
        if key.startswith("_") or isinstance(value, dict):
            continue
        if isinstance(value, list): items.extend(f"{key}:{v}" for v in value)
        elif value not in (None, "", [], {}): items.append(key)
    return items


def _event(session: dict, kind: str, details: dict) -> None:
    session["events"].append({"type": kind, "at": _now(), "details": details})


def _bump(session: dict) -> dict:
    session["revision"] += 1
    session["updated_at"] = _now()
    return session


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
