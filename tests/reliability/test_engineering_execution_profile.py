from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_runtime import _start_delivery_from_facts, get_engineering_execution_profile


def test_profile_is_not_applied_to_non_software_delivery():
    session = _start_delivery_from_facts(facts={"goal": "整理客户访谈纪要"})
    profile = get_engineering_execution_profile(session)
    assert profile["status"] == "NOT_APPLICABLE"
    assert profile["practices"] == []


def test_profile_is_factual_optional_guidance_for_existing_code_change():
    session = _start_delivery_from_facts(facts={
        "goal": "修复已有结算服务的税率错误",
        "existing_codebase": {"state": "OBSERVED", "value": True},
        "source_change": {"state": "DECLARED", "value": True},
        "bug_fix": {"state": "DECLARED", "value": True},
        "automated_tests": {"state": "OBSERVED", "value": True},
        "git_workspace": {"state": "OBSERVED", "value": True},
    })
    profile = get_engineering_execution_profile(session)
    ids = {practice["id"] for practice in profile["practices"]}
    assert profile["status"] == "APPLICABLE"
    assert {"BASELINE_BEFORE_CHANGE", "MINIMAL_CHANGE_WITH_TEST",
            "TDD_RED_GREEN_REFACTOR", "SYSTEMATIC_DEBUG_AND_REVALIDATE",
            "VERIFICATION_BEFORE_COMPLETION", "INDEPENDENT_ENGINEERING_REVIEW",
            "WORK_UNIT_REVIEW", "FINISH_CHANGE_CONTEXT",
            "ISOLATED_CHANGE_CONTEXT"}.issubset(ids)
    assert profile["core_invariants_unchanged"] is True
    assert session["plan"]["authority"] == "AI_GENERATED_HUMAN_OWNED"
