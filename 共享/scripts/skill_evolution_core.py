"""Deterministic rules for evidence-driven skill evolution (proposal-side only, never runtime mutation)."""
from __future__ import annotations

INBOX_REQUIRED_FIELDS = (
    "experience_id", "observed_event", "expected_behavior", "actual_behavior",
    "evidence_refs", "root_cause_candidate", "classification", "generalizable",
)
VALID_CLASSIFICATIONS = {
    "CORE_SKILL_DEFECT", "PROJECT_IMPLEMENTATION_GAP", "ENVIRONMENT_BLOCKER",
    "PLATFORM_ADAPTER_GAP", "BENCHMARK_DESIGN_DEFECT", "USER_EXPERIENCE_DEFECT",
    "EXPECTED_HUMAN_GATE", "UNKNOWN",
}
LEDGER_STATUSES = ("OBSERVED", "CANDIDATE", "VALIDATED", "ADOPTED", "REJECTED", "NEEDS_MORE_DATA")
LEGAL_TRANSITIONS = {
    "OBSERVED": {"CANDIDATE", "REJECTED", "NEEDS_MORE_DATA"},
    "CANDIDATE": {"VALIDATED", "REJECTED", "NEEDS_MORE_DATA"},
    "VALIDATED": {"ADOPTED", "REJECTED"},
    "ADOPTED": set(),
    "REJECTED": set(),
    "NEEDS_MORE_DATA": {"CANDIDATE", "REJECTED"},
}
PATCH_OPS = ("ADD", "REPLACE", "DELETE", "REFINE")
PATCH_DECLARATION_FIELDS = (
    "patch_id", "source_experience", "affected_capability", "op", "target",
    "old_behavior", "new_behavior", "expected_benefit", "possible_regression",
)
VALIDATION_REQUIREMENTS = ("optimization_improved", "heldout_no_regression", "rescue_regression_pass", "round1_regression_pass")


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
