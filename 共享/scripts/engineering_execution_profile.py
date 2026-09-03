"""Optional engineering execution guidance for software-delivery Work Units.

This is a profile, not a second planner or a Core invariant. It helps a Host
choose a disciplined implementation path only after facts establish that the
work changes an existing codebase.
"""
from __future__ import annotations

from copy import deepcopy


ENGINEERING_SIGNALS = (
    "existing_codebase", "source_change", "automated_tests", "bug_fix",
    "parallel_engineering_work", "git_workspace",
)


def _declared_true(facts: dict, name: str) -> bool:
    entry = facts.get(name, {})
    return entry.get("state") in {"DECLARED", "OBSERVED"} and bool(entry.get("value"))


def derive_engineering_execution_profile(facts: dict) -> dict:
    """Return safe structured guidance only when engineering facts warrant it."""
    signals = {name: _declared_true(facts, name) for name in ENGINEERING_SIGNALS}
    applicable = any(signals[name] for name in ("existing_codebase", "source_change", "bug_fix"))
    if not applicable:
        return {"status": "NOT_APPLICABLE", "reason": "no_confirmed_software_delivery_signal",
                "core_invariants_unchanged": True, "practices": []}
    practices = [
        {"id": "BASELINE_BEFORE_CHANGE", "when": "always_for_existing_or_changed_code",
         "action": "inspect relevant code and tests; run a relevant baseline when feasible",
         "evidence": "captured inspection or test receipt"},
        {"id": "MINIMAL_CHANGE_WITH_TEST", "when": "new_or_changed_business_logic",
         "action": "add or update a focused edge test, make the minimal change, then run it green",
         "evidence": "real test receipt; never delete tests merely to obtain green"},
        {"id": "TDD_RED_GREEN_REFACTOR", "when": "testable_code_change",
         "action": "write a failing focused test first, implement the smallest fix, then refactor only with green tests",
         "evidence": "red and green test receipts linked to the same Work Unit"},
        {"id": "SYSTEMATIC_DEBUG_AND_REVALIDATE", "when": "test_or_runtime_failure",
         "action": "preserve/reproduce, isolate root cause, check environment and assumptions, repair in scope, rerun blocker and regression",
         "evidence": "failure plus blocker-revalidation and regression receipts"},
        {"id": "VERIFICATION_BEFORE_COMPLETION", "when": "before_any_completion_claim",
         "action": "run the relevant acceptance and regression checks against the current candidate; claims are not evidence",
         "evidence": "current candidate verification receipt"},
        {"id": "INDEPENDENT_ENGINEERING_REVIEW", "when": "before_completion_for_material_code_change",
         "action": "check plan/scope compliance separately from quality, error handling and regression impact",
         "evidence": "independent review evidence appropriate to the Harness"},
        {"id": "WORK_UNIT_REVIEW", "when": "after_each_material_work_unit",
         "action": "review the completed Work Unit against its acceptance and changed-scope boundaries before advancing",
         "evidence": "review receipt bound to Work Unit and plan revision"},
        {"id": "FINISH_CHANGE_CONTEXT", "when": "after_code_work_is_complete",
         "action": "report changed files, verification, remaining risk and an explicit merge/keep/rollback disposition",
         "evidence": "final change-context report and workspace identity"},
    ]
    if signals["parallel_engineering_work"] or signals["git_workspace"]:
        practices.append({"id": "ISOLATED_CHANGE_CONTEXT", "when": "parallel_or_reversible_change_work",
                          "action": "use a Harness-supported isolated branch/worktree; never assume one exists",
                          "evidence": "Harness-captured workspace identity"})
    return {"status": "APPLICABLE", "reason": "confirmed_software_delivery_facts",
            "core_invariants_unchanged": True, "practices": deepcopy(practices),
            "source_signals": [name for name, value in signals.items() if value]}
