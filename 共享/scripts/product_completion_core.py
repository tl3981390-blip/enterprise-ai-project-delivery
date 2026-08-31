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
# POST_V1.5_CORE_DEFECT_FIX (generalization): project CLASSIFICATION (who is this project,
# what risk) and CAPABILITY DECLARATION (which conditional capabilities are in scope) are
# different layers. Classification is required for every project; capability keys are
# OPTIONAL — absence means the capability is NOT_IN_SCOPE for this project. Previously all
# 12 fields were mandatory, structurally forcing AI/enterprise vocabulary onto every project.
PROJECT_CLASSIFICATION_FIELDS = (
    "project_type", "business_goal", "risk_level", "required_capabilities",
    "acceptance_matrix", "project_specific_constraints",
)
CAPABILITY_DECLARATION_FIELDS = (
    "runtime", "database", "rag", "agent", "workflow", "deployment_target",
)
PROJECT_PROFILE_FIELDS = PROJECT_CLASSIFICATION_FIELDS + CAPABILITY_DECLARATION_FIELDS
NON_OVERRIDABLE_CORE_INVARIANTS = (
    "evidence_integrity", "candidate_identity_verification", "human_authorization_boundary",
    "anti_fake_pass", "recovery_evidence", "scope_authority", "telemetry_integrity",
)
MERGE_PRIORITY = ("CORE_INVARIANTS", "ENTERPRISE_PROFILE", "PROJECT_PROFILE", "TASK_CONTRACT")
LEARNING_LINES = ("GLOBAL_FAILURE_PATTERN", "COMPANY_SPECIFIC_PATTERN")


def validate_profile(profile: dict, kind: str) -> list[str]:
    if kind == "enterprise":
        fields = ENTERPRISE_PROFILE_FIELDS
    elif kind == "project":
        fields = PROJECT_CLASSIFICATION_FIELDS  # capability declarations are optional
    else:
        return [f"profile_kind_invalid:{kind}"]
    errors = [f"missing:{f}" for f in fields if profile.get(f) in (None, "")]
    for cap in CAPABILITY_DECLARATION_FIELDS:
        value = profile.get(cap)
        if value is not None and value != {} and not isinstance(value, (dict, list, str, bool)):
            errors.append(f"capability_declaration_invalid:{cap}")
    for inv in NON_OVERRIDABLE_CORE_INVARIANTS:
        if profile.get(inv) is not None and profile.get(inv) is not True:
            errors.append(f"core_invariant_override_attempt:{inv}")
    if profile.get("allow_fake_pass") is True:
        errors.append("core_invariant_override_attempt:anti_fake_pass")
    return errors


_RESTRICTIVE_MARKERS = ("DENY", "HALT", "REQUIRED", "STRICT", "DENIED", "BLOCK")


def _is_restrictive(value) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, str):
        return any(m in value.upper() for m in _RESTRICTIVE_MARKERS)
    return False


def merge_profiles(core: dict, enterprise: dict, project: dict, task: dict) -> dict:
    """Lower layers must not violate higher ones; conflicts are explicit (§33).

    CORE_DEFECT fix (EXP-018, proven by HARNESS acceptance §12 profile-block test):
    a lower layer overriding a same-key higher-layer RESTRICTIVE value is a
    PROFILE_CONSTRAINT_CONFLICT — previously merged silently (= policy bypass)."""
    conflicts = []
    for inv in NON_OVERRIDABLE_CORE_INVARIANTS:
        for layer_name, layer in (("enterprise", enterprise), ("project", project), ("task", task)):
            if layer.get(inv) is False or (inv == "anti_fake_pass" and layer.get("allow_fake_pass") is True):
                conflicts.append(f"PROFILE_CONSTRAINT_CONFLICT:{layer_name}:{inv}")
    def _restrictive_overrides(hi: dict, lo: dict, path: str) -> list[str]:
        found = []
        for key, hval in hi.items():
            if key not in lo:
                continue
            lval = lo[key]
            here = f"{path}.{key}" if path else key
            if isinstance(hval, dict) and isinstance(lval, dict):
                found.extend(_restrictive_overrides(hval, lval, here))
            elif hval != lval and _is_restrictive(hval):
                found.append(here)
        return found

    layers = (("ENTERPRISE_PROFILE", enterprise), ("PROJECT_PROFILE", project), ("TASK_CONTRACT", task))
    for i in range(len(layers)):
        for j in range(i + 1, len(layers)):
            higher_name, higher = layers[i]
            lower_name, lower = layers[j]
            for spot in _restrictive_overrides(higher, lower, ""):
                conflicts.append(f"PROFILE_CONSTRAINT_CONFLICT:{lower_name}:{spot}_overrides_{higher_name}")
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


# ==================== PART E: PROJECT ORCHESTRATION & GENERALIZATION ====================
# POST_V1.5_CORE_DEFECT_FIX: the skill's applicability is COMPLEX PROJECT RELIABILITY DELIVERY,
# not "enterprise AI internal products". Capability modules are CONDITIONAL: a project declares
# which capabilities are in scope; the Active Delivery Plan is derived per project. Enterprise
# workflow is EXTERNAL INPUT compiled into an Enterprise Profile, never a built-in core template.
# Layers: 1 Reliability Core (invariants) / 2 Capability Registry / 3 Project Understanding /
# 4 Active Delivery Plan / 5 Enterprise Profile / 6 Project Profile / 7 Task Contract.

# Layer 1 — lifecycle stages every governed project executes (reliability lifecycle, domain-neutral).
LIFECYCLE_STAGES = (
    "00_总控", "01_项目理解", "02_当前状态审计", "03_需求与范围", "04_SDD规格",
    "05_TDD与测试策略", "06_架构设计", "11_施工管理与增量实现", "12_失败处理与恢复",
    "14_多角色验收", "15_Evidence与防假验收", "19_最终交付与经验沉淀",
)
EVENT_DRIVEN_STAGES = ("12_失败处理与恢复",)  # entered on failure, exit of the plan, not skipped

# Layer 2 — conditional capability registry: capability -> {stages, gates}.
CAPABILITY_REGISTRY = {
    "rag": {"stages": ["07_RAG设计"], "gates": ["rag_gate", "citation_gate"]},
    "agent": {"stages": ["08_Agent设计"], "gates": []},
    "tool_permissions": {"stages": ["09_MCP与工具权限网关"], "gates": ["permission_gate"]},
    "enterprise_governance": {"stages": ["10_企业治理与合规"], "gates": ["governance_gate"]},
    "browser_acceptance": {"stages": ["13_浏览器真实验收"], "gates": ["targeted_browser_journey"]},
    "deployment": {"stages": ["16_部署"], "gates": ["deployment_gate"]},
    "license_compliance": {"stages": ["17_License与合规"], "gates": ["license_gate"]},
    "upgrade_rollback": {"stages": ["18_升级与回滚"], "gates": ["migration_gate", "rollback_gate"]},
    "database": {"stages": [], "gates": ["persistence_gate", "restart_gate"]},
    "workflow": {"stages": [], "gates": ["workflow_gate", "role_e2e_gate"]},
    "multi_role_approval": {"stages": [], "gates": ["role_e2e_gate"]},
    "runtime": {"stages": [], "gates": ["adapter_gate", "restart_gate"]},
}
# Profile declaration key -> registry key (deployment_target declares the deployment capability).
CAPABILITY_DECLARATION_ALIASES = {"deployment_target": "deployment"}
ALWAYS_GATES = ("contract_check",)
NOT_APPLICABLE_REASON = "capability_not_in_scope"
CAPABILITY_REGISTRY_STAGES = sorted({s for spec in CAPABILITY_REGISTRY.values() for s in spec["stages"]})


def active_capabilities(project_profile: dict, enterprise_profile: dict | None = None) -> dict:
    """Which registry capabilities are in scope: declared capability objects (non-empty) plus
    required_capabilities strings; an enterprise profile may ADD capabilities, never remove."""
    active: set[str] = set()
    for cap in CAPABILITY_DECLARATION_FIELDS:
        value = (project_profile or {}).get(cap)
        if value not in (None, "", {}, []):
            active.add(CAPABILITY_DECLARATION_ALIASES.get(cap, cap))
    for cap in (project_profile or {}).get("required_capabilities") or []:
        if cap in CAPABILITY_REGISTRY:
            active.add(cap)
    for cap in ((enterprise_profile or {}).get("required_capabilities") or []):
        if cap in CAPABILITY_REGISTRY:
            active.add(cap)
    return {cap: CAPABILITY_REGISTRY[cap] for cap in sorted(active)}


def derive_active_plan(project_profile: dict, enterprise_profile: dict | None = None) -> dict:
    """DEPRECATED COMPATIBILITY WRAPPER (v1.7.1): delegates to the canonical dynamic
    planner. The old fixed lifecycle template (LIFECYCLE_STAGES) is no longer the plan
    source; stages are composed from the project's facts. This wrapper preserves the
    historical return shape for existing callers/tests only — it must NOT be extended
    as a second plan model."""
    from delivery_planning_core import (assess_complexity, compose_stages, make_fact_model,
                                        reason_capability_needs)
    facts = make_fact_model(
        goal=project_profile.get("business_goal", ""),
        interfaces=project_profile.get("interface_types") or project_profile.get("interfaces") or [],
        interface_types=project_profile.get("interface_types") or project_profile.get("interfaces") or [],
        persistence=bool(project_profile.get("database")),
        existing_database=bool(project_profile.get("database")),
        data=project_profile.get("database") or None,
        deployment_requirement=bool(project_profile.get("deployment_target")),
        compliance=project_profile.get("compliance") or [],
        roles=(enterprise_profile or {}).get("roles") or project_profile.get("roles") or [],
        enterprise_policy_present=bool((enterprise_profile or {}).get("required_capabilities")),
        approval_requirement=bool(project_profile.get("workflow")),
        migration_requirements=bool(project_profile.get("migration_requirements")),
        retrieval_requirement=bool(project_profile.get("rag")),
        workflow=project_profile.get("workflow") or None,
    )
    caps = reason_capability_needs(facts, declared=list(project_profile.get("required_capabilities") or []))
    complexity = assess_complexity({})
    composed = compose_stages(facts, complexity, caps)
    active_stage_names = [s["name"] for s in composed["stages"]]
    gates = set(ALWAYS_GATES)
    for cap, info in caps["capabilities"].items():
        if info["required"] is True:
            gates.update(CAPABILITY_REGISTRY.get(cap, {}).get("gates", []))
    workflow = (enterprise_profile or {}).get("workflow") or {}
    human_gates = list(workflow.get("human_gates") or [])
    return {
        "active_stages": active_stage_names,
        "not_applicable_stages": {cap: "capability_not_in_scope" for cap, info in caps["capabilities"].items()
                                  if info["required"] is not True},
        "active_gates": sorted(gates),
        "required_evidence": ["task_understanding_contract", "gate_results", "acceptance_evidence"],
        "human_gates": human_gates + ["FINAL_ACCEPTANCE"],
        "final_acceptance": "INDEPENDENT_VERIFICATION_NON_OPTIONAL",
        "explicit_invocation_accepted": True,
        "planner": "delivery_planning_core.compose_stages (dynamic, fact-derived)",
    }


# Layer 5 — enterprise workflow is INPUT, compiled into an Enterprise Profile entry.
WORKFLOW_STAGE_FIELDS = ("name",)
FORBIDDEN_WORKFLOW_KEYS = {"allow_fake_pass", "skip_evidence", "bypass_human_gate", "self_acceptance"}


def compile_enterprise_workflow(workflow: dict) -> dict:
    """Compile a company's REAL delivery workflow (its own stages/roles/approvals/entry-exit
    conditions/evidence/human gates) into an Enterprise Profile `workflow` entry. Different
    enterprises may compile completely different workflows on ONE reliability core. The
    compilation rejects any attempt to weaken NON_OVERRIDABLE_CORE_INVARIANTS."""
    errors = []
    stages = workflow.get("stages")
    if not stages or not isinstance(stages, list):
        return {"status": "WORKFLOW_INVALID", "errors": ["missing:stages"]}
    for i, stage in enumerate(stages):
        if not isinstance(stage, dict) or not stage.get("name"):
            errors.append(f"stage[{i}]:missing:name")
        for key in FORBIDDEN_WORKFLOW_KEYS:
            if stage.get(key) is True:
                errors.append(f"stage[{i}]:core_invariant_weakened:{key}")
    if workflow.get("allow_fake_pass") is True:
        errors.append("core_invariant_weakened:allow_fake_pass")
    if errors:
        return {"status": "WORKFLOW_INVALID", "errors": errors}
    human_gates = [s["name"] for s in stages if s.get("human_gate") is True]
    return {"status": "WORKFLOW_COMPILED",
            "workflow": {"stages": stages, "human_gates": human_gates,
                         "source": "ENTERPRISE_INPUT", "profile_line": "COMPANY_SPECIFIC"}}


# Layer 1/5 boundary — acceptance perspectives scale with real stakeholders; the INVARIANT is
# independent verification (executor self-attestation is never sufficient), not the role count.
DEFAULT_ENTERPRISE_PERSPECTIVES = ("product", "engineering", "security", "end_user")
SOLO_PROJECT_PERSPECTIVES = ("owner_user",)


def required_acceptance_perspectives(project_profile: dict, enterprise_profile: dict | None = None) -> tuple:
    declared = (project_profile or {}).get("acceptance_perspectives")
    if declared:
        return tuple(declared)
    if (enterprise_profile or {}).get("roles"):
        return DEFAULT_ENTERPRISE_PERSPECTIVES
    if (project_profile or {}).get("stakeholders") in (None, [], 1, "single"):
        return SOLO_PROJECT_PERSPECTIVES
    return DEFAULT_ENTERPRISE_PERSPECTIVES


# Layer 1 evolution boundary — five-way experience routing with FREQUENCY != GENERALIZABILITY.
EXPERIENCE_ROUTES = (
    "GLOBAL_RELIABILITY_PATTERN", "HARNESS_SPECIFIC_PATTERN", "ENTERPRISE_SPECIFIC_PATTERN",
    "PROJECT_SPECIFIC_PATTERN", "ONE_OFF_OBSERVATION",
)


def classify_experience_route(pattern: dict) -> str:
    """Route an experience by WHERE it belongs, never by HOW OFTEN it was seen. Frequency /
    repeat_count can never promote a pattern to GLOBAL: global admission additionally requires
    cross-project validation and a counterexample check (directive §19/§21)."""
    if pattern.get("harness_specific") is True:
        return "HARNESS_SPECIFIC_PATTERN"
    if pattern.get("organization_specific") is True:
        return "ENTERPRISE_SPECIFIC_PATTERN"
    if pattern.get("project_specific") is True:
        return "PROJECT_SPECIFIC_PATTERN"
    if pattern.get("generalizable_across_projects") is True:
        if pattern.get("cross_project_validated") is True and pattern.get("counterexample_checked") is True:
            return "GLOBAL_RELIABILITY_PATTERN"
        return "ONE_OFF_OBSERVATION"  # plausible but unproven: archive, do not promote
    return "ONE_OFF_OBSERVATION"


CORE_EVOLUTION_ADMISSION_REQUIREMENTS = (
    "real_failure_or_reliability_need", "current_core_insufficient", "generalizable",
    "reproducible", "evidence_backed", "cross_project_validated", "counterexample_checked",
    "no_template_leakage", "no_enterprise_specific_leakage", "no_project_specific_leakage",
)


def validate_core_evolution_admission(evidence: dict) -> list[str]:
    """POST_V1.5 gate: a NEW global core rule must satisfy ALL admission requirements;
    otherwise REJECT / DEFER / RECLASSIFY into the proper layer."""
    return [f"not_proven:{key}" for key in CORE_EVOLUTION_ADMISSION_REQUIREMENTS
            if evidence.get(key) is not True]


# Assumption change model — invalidate ONLY affected verified state, preserve the rest.
ASSUMPTION_CHANGE_CLASSES = ("STILL_VALID", "INVALIDATED", "REQUIRES_REVALIDATION", "NEW_REQUIRED")


def assumption_change_model(verified_state: dict, changed_assumptions: list,
                            new_required: list | None = None) -> dict:
    """verified_state: {item_id: {"assumptions": [...], "capabilities": [...]}}. An item is
    INVALIDATED when an assumption it depends on changed; REQUIRES_REVALIDATION when it shares
    a capability with the changed surface (collateral risk); STILL_VALID otherwise. Never
    'continue the old template' and never 'redo everything from zero'."""
    changed = set(changed_assumptions or [])
    result = {}
    for item_id, spec in (verified_state or {}).items():
        deps = set(spec.get("assumptions") or [])
        caps = set(spec.get("capabilities") or [])
        if deps & changed:
            result[item_id] = "INVALIDATED"
        elif caps & changed:
            result[item_id] = "REQUIRES_REVALIDATION"
        else:
            result[item_id] = "STILL_VALID"
    for item_id in new_required or []:
        result.setdefault(item_id, "NEW_REQUIRED")
    return {"classification": result, "changed_assumptions": sorted(changed),
            "next": "re_run_understanding_for_affected -> recalculate_active_plan -> continue"}
