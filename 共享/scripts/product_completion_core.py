"""Deterministic cores for PRODUCT_CORE_COMPLETION (v1.5.0-dev):
harness conformance levels, mid-project attachment, telemetry closed loop, enterprise customization.
One Core / Multiple Thin Adapters — platform specifics never live here."""
from __future__ import annotations

# ==================== PART A: HARNESS CONFORMANCE ====================
HARNESS_CAPABILITIES = (
    "skill_discovery", "skill_explicit_invocation", "automatic_activation", "read_project_state",
    "write_project_state", "tool_execution", "permission_boundary", "subagent_support",
    "resume_support", "handoff_support", "usage_visibility", "telemetry_write",
    "filesystem_scope", "browser_support", "human_gate_support",
)
# Level ladder: each level requires its capability evidence (L10 = all prior + full suite pass).
CONFORMANCE_LEVELS = ("L1_DISCOVER", "L2_INVOKE", "L3_CONTRACT_AND_GATE", "L4_TOOL_EXECUTION",
                      "L5_TELEMETRY", "L6_RESUME", "L7_HANDOFF", "L8_MID_PROJECT_ATTACH",
                      "L9_CLOSED_LOOP_CONTROL", "L10_FULL_CONFORMANCE")
LEVEL_REQUIREMENTS = {
    "L1_DISCOVER": ("skill_discovery",),
    "L2_INVOKE": ("skill_explicit_invocation",),
    "L3_CONTRACT_AND_GATE": ("read_project_state", "permission_boundary"),
    "L4_TOOL_EXECUTION": ("tool_execution", "write_project_state"),
    "L5_TELEMETRY": ("telemetry_write",),
    "L6_RESUME": ("resume_support",),
    "L7_HANDOFF": ("handoff_support",),
    "L8_MID_PROJECT_ATTACH": ("filesystem_scope",),
    "L9_CLOSED_LOOP_CONTROL": ("automatic_activation",),
    "L10_FULL_CONFORMANCE": ("usage_visibility", "browser_support", "human_gate_support", "subagent_support"),
}


def conformance_level(verified: dict) -> str:
    """Highest contiguous level whose capability evidence is all VERIFIED; unknown = NOT_AVAILABLE (never fake)."""
    best = "L0_NONE"
    for level in CONFORMANCE_LEVELS:
        caps = LEVEL_REQUIREMENTS[level]
        statuses = [verified.get(c, "NOT_AVAILABLE") for c in caps]
        if any(s not in ("VERIFIED", "NOT_APPLICABLE_BRIDGED") for s in statuses):
            break
        best = level
    return best


def validate_capability_claim(claims: dict) -> list[str]:
    errors = []
    for cap, status in claims.items():
        if cap not in HARNESS_CAPABILITIES:
            errors.append(f"unknown_capability:{cap}")
        if status not in ("VERIFIED", "NOT_AVAILABLE", "NOT_APPLICABLE_BRIDGED", "NOT_TESTED_HERE"):
            errors.append(f"invalid_status:{cap}:{status}")
    return errors


# ==================== PART B: MID-PROJECT SKILL ATTACHMENT ====================
ATTACHMENT_DISCOVERY_FIELDS = (
    "current_goal", "current_git_head", "worktree", "existing_requirements", "existing_contracts",
    "current_runtime", "current_database", "current_tests", "current_evidence", "current_failures",
    "existing_agent_claims", "current_stage", "partial_work", "known_blockers",
)
ADOPTION_BOUNDARY_FIELDS = (
    "attachment_id", "attachment_timestamp", "task_id", "git_head_at_attachment",
    "runtime_identity", "project_snapshot", "skill_version", "harness",
)
PRE_ATTACHMENT_STATUSES = ("VERIFIED_PRE_ATTACHMENT", "UNVERIFIED_PRE_ATTACHMENT", "FAILED_PRE_ATTACHMENT", "UNKNOWN_PRE_ATTACHMENT")
ATTACH_PHASES = ("ATTACHMENT_DISCOVERY", "ADOPTION_BOUNDARY", "GOVERNED_EXECUTION")


def classify_pre_attachment(claim: dict) -> str:
    """Historical state is never laundered: an old agent 'done' claim is not PASS."""
    status = claim.get("verification_status")
    if status in ("MECHANICALLY_VERIFIED",):
        return "VERIFIED_PRE_ATTACHMENT"
    if status in ("MECHANICALLY_FAILED", "EVIDENCE_CONTRADICTS"):
        return "FAILED_PRE_ATTACHMENT"
    if status == "NO_RECORD":
        return "UNKNOWN_PRE_ATTACHMENT"
    return "UNVERIFIED_PRE_ATTACHMENT"  # includes narrative-only claims


def lazy_verify_plan(pre_states: dict, next_stage_dependencies: list[str]) -> dict:
    """Only verify history the future work actually depends on; the rest stays unverified (§15)."""
    to_verify = sorted(set(next_stage_dependencies) & set(pre_states))
    skipped = sorted(set(pre_states) - set(to_verify))
    return {"verify_now": to_verify, "keep_status": {k: pre_states[k] for k in skipped},
            "reason_code": "LAZY_HISTORICAL_VERIFICATION"}


def attach_allowed(discovery: dict) -> dict:
    """Phase 1 is READ-ONLY: no construction before the adoption boundary exists."""
    missing = [f for f in ATTACHMENT_DISCOVERY_FIELDS if discovery.get(f) in (None, "")]
    if missing:
        return {"decision": "ATTACHMENT_DISCOVERY_INCOMPLETE", "can_write": False, "missing": missing}
    boundary = discovery.get("adoption_boundary") or {}
    bmissing = [f for f in ADOPTION_BOUNDARY_FIELDS if not boundary.get(f)]
    if bmissing:
        return {"decision": "ADOPTION_BOUNDARY_REQUIRED", "can_write": False, "missing": bmissing}
    return {"decision": "GOVERNED_EXECUTION", "can_write": True,
            "task_continuity": "existing_project_plus_reconstructed_task", "reason_code": "NO_NEW_PROJECT"}


def attachment_value_report_scope() -> dict:
    return {"pre_attachment": "PARTIALLY_OBSERVABLE (no full causal attribution)",
            "post_attachment": "FULLY_GOVERNED (full skill value accounting)"}


# ==================== PART C: TELEMETRY CLOSED LOOP ====================
# OBSERVE -> DECIDE -> ACT -> VERIFY. Runtime closed loop only; Skill Evolution stays gated (§20).
LEGAL_LOOP_ACTIONS = ("CONTRACT_REVALIDATION", "AUTO_CONTINUE", "LEGAL_STOP_CHECK", "CHECKPOINT",
                      "HANDOFF_PREPARATION", "MISSING_ACCEPTANCE_REENTRY", "REVERIFY_RELEVANT_GATE",
                      "DELTA_CONTEXT_ENFORCEMENT", "BOUNDED_RECOVERY", "FREEZE_EVIDENCE",
                      "SCOPE_RESTORE", "CLASSIFY")
FORBIDDEN_LOOP_ACTIONS = ("RELEASE_TAG", "PRODUCTION_MUTATION", "BYPASS_HUMAN_GATE", "MODIFY_SKILL_CORE",
                          "DELETE_EVIDENCE", "SELF_PASS")
HUMAN_GATE_EVENTS = ("HUMAN_AUTHORIZATION_REQUIRED", "HUMAN_BUSINESS_DECISION_REQUIRED",
                     "USER_ONLY_ACCEPTANCE_REQUIRED", "EXTERNAL_HUMAN_ACTION_REQUIRED", "IRREVERSIBLE_PRODUCTION")
TELEMETRY_CONTROL_POLICY = {
    "DRIFT_DETECTED": ["FREEZE_EVIDENCE", "CLASSIFY", "SCOPE_RESTORE", "CONTRACT_REVALIDATION"],
    "ILLEGAL_PASSIVE_STOP": ["LEGAL_STOP_CHECK", "AUTO_CONTINUE"],
    "RESOURCE_BUDGET_WARNING": ["CHECKPOINT", "HANDOFF_PREPARATION"],
    "FAKE_PASS_BLOCKED": ["MISSING_ACCEPTANCE_REENTRY"],
    "CACHE_INVALID": ["REVERIFY_RELEVANT_GATE"],
    "REPEATED_CONTEXT_LOAD": ["DELTA_CONTEXT_ENFORCEMENT"],
    "FAILURE_DETECTED": ["FREEZE_EVIDENCE", "CLASSIFY", "BOUNDED_RECOVERY", "REVALIDATE_ORIGINAL_BLOCKER", "REGRESSION_THEN_CONTINUE"],
    "GOVERNANCE_COST_ANOMALY": ["DELTA_CONTEXT_ENFORCEMENT", "REVERIFY_RELEVANT_GATE"],
}
LOOP_VERIFICATION = {  # every action must be mechanically revalidated before a PASS result event (§25)
    "CONTRACT_REVALIDATION": "alignment_check_pass",
    "AUTO_CONTINUE": "next_legal_action_executing",
    "CHECKPOINT": "snapshot_written",
    "MISSING_ACCEPTANCE_REENTRY": "acceptance_item_rerun",
    "REVERIFY_RELEVANT_GATE": "gate_rerun_pass",
    "DELTA_CONTEXT_ENFORCEMENT": "full_reload_count_not_increased",
    "SCOPE_RESTORE": "mechanical_scope_check_pass",
    "BOUNDED_RECOVERY": "original_blocker_revalidated",
}


def loop_decision(event_type: str, context: dict) -> dict:
    """Closed loop with human-gale protection, bounded attempts, and mandatory verification."""
    if event_type in HUMAN_GATE_EVENTS:
        return {"action": "HALT_AT_HUMAN_GATE", "can_act": False, "reason_code": "HUMAN_GATE_NOT_BYPASSABLE"}
    actions = TELEMETRY_CONTROL_POLICY.get(event_type)
    if not actions:
        return {"action": "NO_POLICY", "can_act": False, "reason_code": "no_policy_for_event"}
    illegal = [a for a in actions if a in FORBIDDEN_LOOP_ACTIONS]
    if illegal:
        return {"action": "REJECTED", "can_act": False, "reason_code": f"forbidden_action_in_policy:{illegal}"}
    attempts = context.get("loop_attempts", 0)
    budget = context.get("max_attempts", 3)
    if attempts >= budget:
        return {"action": "HUMAN_ESCALATION", "can_act": False, "reason_code": "MAX_ATTEMPTS_REACHED",
                "package_required": True}
    return {"action": actions, "can_act": True, "verification_required": [LOOP_VERIFICATION.get(a, "mechanical_revalidation") for a in actions if a in LOOP_VERIFICATION],
            "result_event_required": True, "remaining_attempts": budget - attempts - 1}


def loop_result(action_taken: str, verification: dict) -> dict:
    """Telemetry -> Policy -> Action -> Mechanical Revalidation -> Result Event (§25). Assume-success forbidden."""
    method = LOOP_VERIFICATION.get(action_taken, "mechanical_revalidation")
    if verification.get(method) is not True:
        return {"outcome": "LOOP_ACTION_UNVERIFIED", "pass": False, "expected": method, "result_event": "LOOP_VERIFY_FAIL"}
    return {"outcome": "LOOP_ACTION_VERIFIED", "pass": True, "result_event": "LOOP_VERIFY_PASS"}


# ==================== PART D: ENTERPRISE CUSTOMIZATION ====================
# CORE + HARNESS ADAPTER + ENTERPRISE PROFILE + PROJECT PROFILE. No company forks (§29).
ENTERPRISE_PROFILE_FIELDS = (
    "organization", "roles", "approval_policy", "model_policy", "tool_policy", "data_policy",
    "security_policy", "evidence_policy", "environment_policy", "deployment_policy",
    "human_gate_policy", "retention_policy", "audit_policy",
)
PROJECT_PROFILE_FIELDS = (
    "project_type", "business_goal", "risk_level", "required_capabilities", "acceptance_matrix",
    "runtime", "database", "rag", "agent", "workflow", "deployment_target", "project_specific_constraints",
)
NON_OVERRIDABLE_CORE_INVARIANTS = (
    "evidence_integrity", "candidate_identity_verification", "human_authorization_boundary",
    "anti_fake_pass", "recovery_evidence", "scope_authority", "telemetry_integrity",
)
MERGE_PRIORITY = ("CORE_INVARIANTS", "ENTERPRISE_PROFILE", "PROJECT_PROFILE", "TASK_CONTRACT")
LEARNING_LINES = ("GLOBAL_FAILURE_PATTERN", "COMPANY_SPECIFIC_PATTERN")


def validate_profile(profile: dict, kind: str) -> list[str]:
    fields = ENTERPRISE_PROFILE_FIELDS if kind == "enterprise" else PROJECT_PROFILE_FIELDS if kind == "project" else None
    if fields is None:
        return [f"profile_kind_invalid:{kind}"]
    errors = [f"missing:{f}" for f in fields if profile.get(f) in (None, "")]
    for inv in NON_OVERRIDABLE_CORE_INVARIANTS:
        if profile.get(inv) is not None and profile.get(inv) is not True:
            errors.append(f"core_invariant_override_attempt:{inv}")
    if profile.get("allow_fake_pass") is True:
        errors.append("core_invariant_override_attempt:anti_fake_pass")
    return errors


def merge_profiles(core: dict, enterprise: dict, project: dict, task: dict) -> dict:
    """Lower layers must not violate higher ones; conflicts are explicit (§33)."""
    conflicts = []
    for inv in NON_OVERRIDABLE_CORE_INVARIANTS:
        for layer_name, layer in (("enterprise", enterprise), ("project", project), ("task", task)):
            if layer.get(inv) is False or (inv == "anti_fake_pass" and layer.get("allow_fake_pass") is True):
                conflicts.append(f"PROFILE_CONSTRAINT_CONFLICT:{layer_name}:{inv}")
    if conflicts:
        return {"status": "PROFILE_CONSTRAINT_CONFLICT", "conflicts": conflicts}
    merged = dict(core)
    for layer in (enterprise, project, task):
        merged.update({k: v for k, v in layer.items() if v is not None})
    return {"status": "MERGED", "effective": merged, "priority": MERGE_PRIORITY}


def classify_learning(pattern: dict) -> str:
    """Company-specific rules never become global core (§34)."""
    if pattern.get("generalizable_across_organizations") is True and pattern.get("organization_specific") is not True:
        return "GLOBAL_FAILURE_PATTERN"
    return "COMPANY_SPECIFIC_PATTERN"
