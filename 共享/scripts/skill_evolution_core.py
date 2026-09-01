"""Deterministic rules for evidence-driven skill evolution (proposal-side only, never runtime mutation)."""
from __future__ import annotations

INBOX_REQUIRED_FIELDS = (
    "experience_id", "observed_event", "expected_behavior", "actual_behavior",
    "evidence_refs", "root_cause_candidate", "classification", "generalizable",
)
VALID_CLASSIFICATIONS = {
    "USER_PREFERENCE", "PROJECT_SPECIFIC", "CAPABILITY_SPECIFIC", "HARNESS_LIMITATION",
    "ENTERPRISE_POLICY", "EXTERNAL_DEPENDENCY", "CORE_RELIABILITY_DEFECT",
    "GENERALIZABLE_IMPROVEMENT", "UNKNOWN",
}
CORE_ADMISSIBLE_CLASSIFICATIONS = {"CORE_RELIABILITY_DEFECT", "GENERALIZABLE_IMPROVEMENT"}
LEDGER_STATUSES = ("OBSERVED", "REPRODUCED", "CLASSIFIED", "CANDIDATE_CREATED",
                   "PATCHED_IN_ISOLATION", "TARGETED_VALIDATION_PASS", "ADVERSARIAL_PASS",
                   "FINAL_GOAL_PASS", "HUMAN_APPROVED", "RELEASED", "REJECTED",
                   "NEEDS_MORE_DATA")
LEGAL_TRANSITIONS = {
    "OBSERVED": {"REPRODUCED", "REJECTED", "NEEDS_MORE_DATA"},
    "REPRODUCED": {"CLASSIFIED", "REJECTED", "NEEDS_MORE_DATA"},
    "CLASSIFIED": {"CANDIDATE_CREATED", "REJECTED", "NEEDS_MORE_DATA"},
    "CANDIDATE_CREATED": {"PATCHED_IN_ISOLATION", "REJECTED"},
    "PATCHED_IN_ISOLATION": {"TARGETED_VALIDATION_PASS", "REJECTED"},
    "TARGETED_VALIDATION_PASS": {"ADVERSARIAL_PASS", "REJECTED"},
    "ADVERSARIAL_PASS": {"FINAL_GOAL_PASS", "REJECTED"},
    "FINAL_GOAL_PASS": {"HUMAN_APPROVED", "REJECTED"},
    "HUMAN_APPROVED": {"RELEASED", "REJECTED"},
    "RELEASED": set(),
    "REJECTED": set(),
    "NEEDS_MORE_DATA": {"REPRODUCED", "REJECTED"},
}
PATCH_OPS = ("ADD", "REPLACE", "DELETE", "REFINE", "SIMPLIFY", "MERGE", "REMOVE", "DEFER")
PATCH_DECLARATION_FIELDS = (
    "patch_id", "source_experience", "affected_capability", "op", "target",
    "old_behavior", "new_behavior", "expected_benefit", "possible_regression",
)
VALIDATION_REQUIREMENTS = ("optimization_improved", "heldout_no_regression", "rescue_regression_pass", "round1_regression_pass")
CANDIDATE_REQUIRED_FIELDS = (
    "candidate_id", "source_evidence", "reproduce_steps", "expected_behavior",
    "actual_behavior", "violated_final_target", "root_cause", "generalization_rationale",
    "counterexample", "affected_core_contract", "expected_blast_radius",
)
# v1.4：减法类 op（SIMPLIFY/MERGE/REMOVE/DEFER）与 ADD/REPLACE/DELETE/REFINE 同受九字段声明约束；
# 减法类额外必须证明 regression 不降低可靠性（VALIDATION_REQUIREMENTS 已含），并在 expected_benefit 中量化治理成本下降。
REDUCTION_OPS = ("SIMPLIFY", "MERGE", "REMOVE", "DEFER")


def validate_experience(entry: dict) -> list[str]:
    errors = [f"missing:{key}" for key in INBOX_REQUIRED_FIELDS if entry.get(key) in (None, "", [])]
    if entry.get("classification") not in (None, *VALID_CLASSIFICATIONS):
        errors.append(f"classification_invalid:{entry.get('classification')}")
    return errors


def validate_transition(current: str, nxt: str) -> list[str]:
    if current not in LEDGER_STATUSES:
        return [f"status_invalid:{current}"]
    if nxt not in LEDGER_STATUSES:
        return [f"status_invalid:{nxt}"]
    if nxt not in LEGAL_TRANSITIONS[current]:
        return [f"transition_illegal:{current}->{nxt}"]
    return []


def validate_patch_declaration(patch: dict) -> list[str]:
    errors = [f"missing:{key}" for key in PATCH_DECLARATION_FIELDS if not patch.get(key)]
    if patch.get("op") not in (None, *PATCH_OPS):
        errors.append(f"op_invalid:{patch.get('op')}")
    return errors


def validate_candidate(evidence: dict) -> list[str]:
    """进入 VALIDATED 的硬门：Optimization 改善 + Held-out 无回归 + Rescue 回归 + Round1 回归。"""
    return [f"not_proven:{key}" for key in VALIDATION_REQUIREMENTS if evidence.get(key) is not True]


def validate_core_candidate(candidate: dict) -> list[str]:
    errors = [f"missing:{key}" for key in CANDIDATE_REQUIRED_FIELDS
              if candidate.get(key) in (None, "", [])]
    classification = candidate.get("classification")
    if classification not in CORE_ADMISSIBLE_CLASSIFICATIONS:
        errors.append(f"core_candidate_classification_not_admissible:{classification}")
    if candidate.get("reproduced") is not True:
        errors.append("core_candidate_not_reproduced")
    if candidate.get("isolated_copy") is not True:
        errors.append("candidate_patch_not_isolated")
    if candidate.get("auto_release") is True:
        errors.append("auto_release_forbidden")
    return errors
