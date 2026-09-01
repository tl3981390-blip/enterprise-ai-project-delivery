"""Runtime adaptive execution strategy state contract.

This module changes execution preferences only.  It cannot modify Core invariants,
source code, versions, commits, tags or releases.  The Harness owns optional physical
storage; absence of saved state always yields a portable default strategy.
"""
from __future__ import annotations

from copy import deepcopy

STRATEGY_FIELDS = (
    "question_strategy", "planning_strategy", "capability_preference",
    "recovery_strategy", "execution_order_preference", "interaction_strategy",
)
STRATEGY_CATALOG = {
    "question_strategy": {"ask_only_consequential_unknowns", "ask_one_highest_impact_first"},
    "planning_strategy": {"minimal_real_work_units", "risk_first_real_work_units"},
    "capability_preference": {"mature_compatible_authorized_first", "local_authorized_first"},
    "recovery_strategy": {"root_cause_then_revalidate", "isolate_then_root_cause_revalidate"},
    "execution_order_preference": {"dependency_and_risk_aware", "dependency_order"},
    "interaction_strategy": {"concise_evidence_backed_updates", "milestone_evidence_updates"},
}
FORBIDDEN_KEYS = {
    "core_invariants", "permissions", "authority", "evidence_rules", "release",
    "version", "commit", "tag", "source_path", "workspace_path", "storage_path",
}


def default_strategy() -> dict:
    return {
        "question_strategy": "ask_only_consequential_unknowns",
        "planning_strategy": "minimal_real_work_units",
        "capability_preference": "mature_compatible_authorized_first",
        "recovery_strategy": "root_cause_then_revalidate",
        "execution_order_preference": "dependency_and_risk_aware",
        "interaction_strategy": "concise_evidence_backed_updates",
    }


def load_strategy(state: dict | None = None) -> dict:
    """Load optional Harness-provided state, otherwise use safe defaults."""
    if state is None:
        return default_strategy()
    errors = validate_strategy(state)
    if errors:
        raise ValueError(f"adaptive_strategy_invalid:{errors}")
    return {**default_strategy(), **deepcopy(state)}


def apply_verified_strategy_patch(current: dict | None, patch: dict) -> dict:
    """Apply a patch already authorized by Delivery Runtime's canonical ledger gate."""
    unknown = sorted(set(patch) - set(STRATEGY_FIELDS))
    if unknown or set(patch) & FORBIDDEN_KEYS:
        raise PermissionError(f"core_or_unknown_strategy_change_forbidden:{unknown}")
    out = load_strategy(current)
    for key, value in patch.items():
        if value not in STRATEGY_CATALOG[key]:
            raise ValueError(f"strategy_value_invalid:{key}")
        out[key] = value
    return out


def validate_strategy(state: dict) -> list[str]:
    if not isinstance(state, dict):
        return ["strategy_state_must_be_object"]
    errors = [f"unknown_or_forbidden:{key}" for key in state
              if key not in STRATEGY_FIELDS or key in FORBIDDEN_KEYS]
    errors += [f"invalid_value:{key}" for key, value in state.items()
               if key in STRATEGY_FIELDS and value not in STRATEGY_CATALOG[key]]
    return errors
