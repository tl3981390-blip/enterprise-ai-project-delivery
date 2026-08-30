"""Deterministic continuation and resume decisions for managed delivery tasks."""
from __future__ import annotations

LEGAL_HUMAN_GATES = {
    "HUMAN_AUTHORIZATION_REQUIRED", "HUMAN_BUSINESS_DECISION_REQUIRED",
    "CONSTRAINT_CONFLICT_REQUIRES_HUMAN", "RECOVERY_EXHAUSTED",
    "EXTERNAL_HUMAN_ACTION_REQUIRED", "USER_ONLY_ACCEPTANCE_REQUIRED",
    "USER_REQUESTED_PAUSE", "FINAL_COMPLETE",
}
HUMAN_PACKAGE_FIELDS = (
    "task_id", "current_stage", "last_known_good_checkpoint", "blocker_id", "failure_type",
    "what_failed", "failure_evidence", "recovery_attempts", "why_auto_recovery_failed",
    "rollback_status", "alternative_paths_attempted", "exact_user_action_required",
    "authorization_required", "minimum_required_permission", "resume_condition",
    "resume_verification", "next_safe_action_after_resume", "fallback_if_resume_fails",
)
LKG_FIELDS = ("task_id", "stage_id", "contract_hash", "git_head", "worktree_identity", "runtime_identity", "last_passed_gate", "evidence_anchor", "timestamp")
MODEL_HANDOFF_PACKAGE_FIELDS = (
    "task_id", "goal", "business_goal", "task_contract", "current_stage", "current_state",
    "current_model", "handoff_reason", "resource_status", "last_known_good_checkpoint",
    "current_git_head", "worktree_state", "build_identity", "runtime_identity",
    "completed_work", "partial_unverified_work", "remaining_work", "current_blockers",
    "failure_history", "recovery_history", "permissions", "evidence_index",
    "telemetry_anchor", "files_must_read", "files_must_not_rework", "next_legal_action",
    "resume_condition", "resume_verification", "known_risks",
)
HANDOFF_IDENTITY_FIELDS = ("git_head", "worktree_identity", "contract_hash", "evidence_anchor", "runtime_identity")


def next_legal_action(workflow: dict) -> dict | None:
    for action in workflow.get("actions", []):
        if action.get("status") in {"PENDING", "READY"} and action.get("legal", True):
            return action
    return None


def validate_human_package(package: dict) -> list[str]:
    errors = [f"missing:{key}" for key in HUMAN_PACKAGE_FIELDS if not package.get(key)]
    checkpoint = package.get("last_known_good_checkpoint") or {}
    if not isinstance(checkpoint, dict):
        errors.append("last_known_good_checkpoint_invalid")
    else:
        errors.extend(f"checkpoint_missing:{key}" for key in LKG_FIELDS if not checkpoint.get(key))
        if checkpoint.get("task_id") and package.get("task_id") and checkpoint["task_id"] != package["task_id"]:
            errors.append("checkpoint_task_id_mismatch")
    return errors


def _absent(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def validate_model_handoff_package(package: dict) -> list[str]:
    errors = [f"missing:{key}" for key in MODEL_HANDOFF_PACKAGE_FIELDS if _absent(package.get(key))]
    checkpoint = package.get("last_known_good_checkpoint") or {}
    if not isinstance(checkpoint, dict):
        errors.append("last_known_good_checkpoint_invalid")
    else:
        errors.extend(f"checkpoint_missing:{key}" for key in LKG_FIELDS if _absent(checkpoint.get(key)))
        if checkpoint.get("task_id") and package.get("task_id") and checkpoint["task_id"] != package["task_id"]:
            errors.append("checkpoint_task_id_mismatch")
    if package.get("current_git_head") and isinstance(checkpoint, dict) and checkpoint.get("git_head") and package["current_git_head"] != checkpoint["git_head"]:
        errors.append("package_head_conflicts_checkpoint")
    return errors


def verify_handoff(package: dict, current: dict) -> dict:
    """NO_FAKE_CONTINUITY: a successor must re-verify real project state before inheriting it."""
    errors = validate_model_handoff_package(package)
    checks = {}
    checkpoint = package.get("last_known_good_checkpoint") or {}
    for field in HANDOFF_IDENTITY_FIELDS:
        expected = current.get(field)
        actual = checkpoint.get(field) or package.get("current_git_head" if field == "git_head" else field)
        if field == "git_head":
            actual = package.get("current_git_head") or checkpoint.get("git_head")
        if field == "worktree_identity":
            actual = package.get("worktree_state") or checkpoint.get("worktree_identity")
        if expected is not None and actual != expected:
            checks[field] = "MISMATCH"
            errors.append(f"handoff_identity_mismatch:{field}")
        elif expected is not None:
            checks[field] = "MATCH"
    if package.get("task_id") and current.get("task_id") and package["task_id"] != current["task_id"]:
        errors.append("handoff_task_id_mismatch")
    decision = "HANDOFF_VERIFICATION_PASS" if not errors else "HANDOFF_VERIFICATION_FAIL"
    return {"decision": decision, "can_continue": not errors, "errors": errors, "identity_checks": checks}


def resource_guard(signals: dict) -> dict:
    """NO_RESOURCE_CLIFF: map only visible resource signals to bounded decisions; never estimate invisible ones."""
    visibility = signals.get("visibility", "NOT_AVAILABLE")
    if visibility not in {"GREEN", "YELLOW", "RED", "NOT_AVAILABLE"}:
        return {"decision": "CONSTRAINT_CONFLICT", "can_continue": False, "reason": "invalid_resource_visibility"}
    state = "UNKNOWN" if visibility == "NOT_AVAILABLE" else visibility
    required_events = []
    if signals.get("user_reported_exhaustion_risk"):
        state = "RED"
    elif signals.get("provider_warning") and state != "RED":
        state = "YELLOW" if state in {"GREEN", "UNKNOWN"} else state
    if state == "YELLOW":
        required_events.append("RESOURCE_BUDGET_WARNING")
    if state == "RED":
        required_events.extend(["RESOURCE_BUDGET_WARNING", "PROACTIVE_HANDOFF_STARTED"])
    atomic = signals.get("atomic_unit_in_progress")
    if state == "RED":
        if atomic:
            if signals.get("atomic_unit_safe_to_complete"):
                return {"decision": "COMPLETE_ATOMIC_UNIT_THEN_HANDOFF", "can_continue": True, "resource_state": state, "required_events": required_events + ["MODEL_HANDOFF_READY"], "reason": "atomic unit completable within remaining budget"}
            return {"decision": "STOP_NEW_WRITES", "can_continue": False, "resource_state": state, "required_events": required_events + ["UNVERIFIED_PARTIAL_WORK", "MODEL_HANDOFF_READY"], "reason": "atomic unit cannot complete safely"}
        return {"decision": "PROACTIVE_MODEL_HANDOFF", "can_continue": False, "resource_state": state, "required_events": required_events + ["MODEL_HANDOFF_READY"], "reason": "insufficient resource for next work unit"}
    if state == "YELLOW":
        return {"decision": "PREPARE_CHECKPOINT", "can_continue": True, "resource_state": state, "required_events": required_events, "reason": "no new large stages; checkpoint and handoff metadata ready"}
    return {"decision": "CONTINUE", "can_continue": True, "resource_state": state, "required_events": required_events, "reason": "resource sufficient or visibility NOT_AVAILABLE; no estimation"}


def decide(workflow: dict) -> dict:
    if workflow.get("task_complete"):
        return {"decision": "FINAL_COMPLETE", "can_continue": False, "reason": "task_complete"}
    request = workflow.get("request", "RUN")
    human_gate = workflow.get("human_gate")
    blocker = workflow.get("blocker") or {}
    action = next_legal_action(workflow)

    if request in {"CONTINUE", "RESUME"} and workflow.get("suspended"):
        if not blocker:
            return {"decision": "RESUME_VERIFICATION_FAIL", "can_continue": False, "reason": "suspended_blocker_missing"}
        if not workflow.get("resume_audit"):
            return {"decision": "RESUME_REQUEST", "can_continue": False, "reason": "current_state_audit_required"}
        if not workflow["resume_audit"].get("blocker_resolved"):
            return {"decision": "RESUME_VERIFICATION_FAIL", "can_continue": False, "reason": "blocking_condition_still_present"}
        if not workflow["resume_audit"].get("candidate_identity_match"):
            return {"decision": "RESUME_VERIFICATION_FAIL", "can_continue": False, "reason": "candidate_identity_mismatch"}
        if workflow["resume_audit"].get("governance_conflict"):
            return {"decision": "RESUME_VERIFICATION_FAIL", "can_continue": False, "reason": "governance_conflict"}
        for field in ("contract_hash_match", "runtime_identity_match", "evidence_identity_match"):
            if workflow["resume_audit"].get(field) is False:
                return {"decision": "RESUME_VERIFICATION_FAIL", "can_continue": False, "reason": field}
        return {"decision": "RESUME_VERIFICATION_PASS", "can_continue": bool(action), "next_action": action, "reason": "revalidate_original_failure_then_regression"}

    if workflow.get("model_handoff_request") or human_gate == "MODEL_HANDOFF_REQUIRED":
        package_errors = validate_model_handoff_package(workflow.get("model_handoff_package") or {})
        if package_errors:
            return {"decision": "CONSTRAINT_CONFLICT", "can_continue": False, "reason": "model_handoff_package_incomplete", "handoff_package_errors": package_errors}
        return {"decision": "MODEL_HANDOFF_READY", "can_continue": False, "reason": "handoff_package_complete_successor_must_verify_before_inheriting"}

    if human_gate:
        if human_gate not in LEGAL_HUMAN_GATES:
            return {"decision": "CONSTRAINT_CONFLICT", "can_continue": False, "reason": "human_gate_invalid"}
        if human_gate == "FINAL_COMPLETE":
            return {"decision": "FINAL_COMPLETE", "can_continue": False, "reason": "declared_terminal_gate"}
        package_errors = validate_human_package(workflow.get("human_recovery_package") or {})
        return {"decision": "SUSPENDED_AWAITING_HUMAN", "can_continue": False, "reason": human_gate, "human_package_errors": package_errors}

    if blocker.get("unrecoverable"):
        rollback = workflow.get("safe_rollback") or {}
        if rollback.get("available") and rollback.get("reversible") and rollback.get("contract_allowed"):
            return {"decision": "SAFE_ROLLBACK_ATTEMPT", "can_continue": True, "next_action": action, "reason": "recovery_exhausted_safe_rollback_available", "requires": ["candidate_identity", "original_gate_revalidation", "regression"]}
        alternative = workflow.get("alternative_recovery") or {}
        if alternative.get("available") and alternative.get("scope_unchanged") and alternative.get("acceptance_unchanged") and not alternative.get("bypasses_permission") and not alternative.get("bypasses_human_gate"):
            return {"decision": "ALTERNATIVE_RECOVERY", "can_continue": True, "next_action": action, "reason": "contract_compliant_alternative_recovery_path", "requires": ["verification_then_continue"]}
        return {"decision": "RECOVERY_EXHAUSTED", "can_continue": False, "reason": blocker.get("reason", "unrecoverable_blocker")}
    if workflow.get("recovery_claimed") and not (workflow.get("original_failure_revalidated") and workflow.get("regression_passed")):
        return {"decision": "CONSTRAINT_CONFLICT", "can_continue": False, "reason": "recovery_not_revalidated"}
    if action:
        if workflow.get("passive_stop_claim"):
            return {"decision": "ILLEGAL_PASSIVE_STOP", "can_continue": True, "next_action": action, "reason": "legal_next_action_exists_without_human_gate"}
        return {"decision": "AUTONOMOUS_CONTINUATION", "can_continue": True, "next_action": action, "reason": "legal_next_action_exists"}
    return {"decision": "CONSTRAINT_CONFLICT", "can_continue": False, "reason": "incomplete_task_without_legal_next_action_or_human_gate"}
