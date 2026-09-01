#!/usr/bin/env python3
"""v1.3.0-dev candidate patch regressions: evolution engine rules, contract scope completeness, declared adapter gate."""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from skill_evolution_core import validate_candidate, validate_experience, validate_patch_declaration, validate_transition
from check_understanding_gate import check as gate_check, check_requirement_coverage
from check_declared_adapter import check


def experience(**overrides):
    base = {
        "experience_id": "EXP-X", "observed_event": "event", "expected_behavior": "expected",
        "actual_behavior": "actual", "evidence_refs": ["evidence/x.md"],
        "root_cause_candidate": "cause", "classification": "CORE_RELIABILITY_DEFECT", "generalizable": True,
    }
    base.update(overrides)
    return base


def patch(**overrides):
    base = {
        "patch_id": "PATCH-X", "source_experience": "EXP-X", "affected_capability": "gate",
        "op": "ADD", "target": "共享/scripts/x.py", "old_behavior": "none",
        "new_behavior": "enforced", "expected_benefit": "prevents failure X", "possible_regression": "extra gate cost",
    }
    base.update(overrides)
    return base


def full_contract(**overrides):
    base = {
        "task_id": "T", "user_real_goal": "g", "business_goal": "g", "final_deliverable": "d", "current_state": "s",
        "completed_scope": "c", "work_scope": ["w"], "explicit_non_goals": ["n"], "allowed_modify": ["a"],
        "forbidden_modify": ["f"], "allowed_tools": ["t"], "forbidden_tools": ["x"], "key_constraints": ["k"],
        "success_criteria": ["s"], "acceptance_criteria": ["a"], "evidence_requirements": ["e"],
        "blocking_unknowns": [], "provenance": {"user_real_goal": "USER_EXPLICIT"},
        "understanding_status": "UNDERSTANDING_COMPLETE",
    }
    base.update(overrides)
    return base


class EvolutionEngineTests(unittest.TestCase):
    def test_valid_experience_passes(self):
        self.assertEqual(validate_experience(experience()), [])

    def test_experience_missing_evidence_is_rejected(self):
        broken = experience(); broken["evidence_refs"] = []
        self.assertIn("missing:evidence_refs", validate_experience(broken))

    def test_experience_bad_classification_is_rejected(self):
        self.assertIn("classification_invalid:EVERYTHING_IS_CORE", validate_experience(experience(classification="EVERYTHING_IS_CORE")))

    def test_ledger_legal_transition(self):
        self.assertEqual(validate_transition("OBSERVED", "REPRODUCED"), [])
        self.assertEqual(validate_transition("REPRODUCED", "CLASSIFIED"), [])
        self.assertEqual(validate_transition("FINAL_GOAL_PASS", "HUMAN_APPROVED"), [])

    def test_ledger_illegal_transitions_rejected(self):
        self.assertEqual(validate_transition("OBSERVED", "RELEASED"), ["transition_illegal:OBSERVED->RELEASED"])
        self.assertEqual(validate_transition("RELEASED", "CANDIDATE_CREATED"), ["transition_illegal:RELEASED->CANDIDATE_CREATED"])
        self.assertEqual(validate_transition("REJECTED", "CANDIDATE_CREATED"), ["transition_illegal:REJECTED->CANDIDATE_CREATED"])

    def test_validated_requires_all_four_proofs(self):
        partial = {"optimization_improved": True, "heldout_no_regression": True, "rescue_regression_pass": True}
        self.assertIn("not_proven:round1_regression_pass", validate_candidate(partial))
        self.assertEqual(validate_candidate({k: True for k in ("optimization_improved", "heldout_no_regression", "rescue_regression_pass", "round1_regression_pass")}), [])

    def test_patch_declaration_requires_all_fields_and_legal_op(self):
        self.assertEqual(validate_patch_declaration(patch()), [])
        broken = patch(); del broken["possible_regression"]
        self.assertIn("missing:possible_regression", validate_patch_declaration(broken))
        self.assertIn("op_invalid:REWRITE_EVERYTHING", validate_patch_declaration(patch(op="REWRITE_EVERYTHING")))


class ContractScopeCompletenessTests(unittest.TestCase):
    def test_full_coverage_passes(self):
        contract = {"source_requirements": ["MUST-1", "MUST-2"], "requirement_coverage": [
            {"requirement_id": "MUST-1", "disposition": "ADOPT"}, {"requirement_id": "MUST-2", "disposition": "NEEDS_MORE_DATA"}]}
        self.assertEqual(check_requirement_coverage(contract), [])
        self.assertEqual(gate_check(full_contract(source_requirements=["MUST-1", "MUST-2"], requirement_coverage=contract["requirement_coverage"])), [])

    def test_missing_disposition_fails_the_gate(self):
        contract = {"source_requirements": ["MUST-1", "MUST-2"], "requirement_coverage": [
            {"requirement_id": "MUST-1", "disposition": "ADOPT"}]}
        errors = check_requirement_coverage(contract)
        self.assertTrue(any("MUST-2" in e and "缺处置" in e for e in errors))
        self.assertTrue(any("MUST-2" in e for e in gate_check(full_contract(**contract))))

    def test_requirements_without_coverage_fails(self):
        errors = check_requirement_coverage({"source_requirements": ["MUST-1"]})
        self.assertTrue(any("缺 requirement_coverage" in e for e in errors))

    def test_invalid_disposition_fails(self):
        contract = {"source_requirements": ["MUST-1"], "requirement_coverage": [{"requirement_id": "MUST-1", "disposition": "MAYBE"}]}
        self.assertTrue(any("处置非法" in e for e in check_requirement_coverage(contract)))

    def test_absent_requirements_field_keeps_legacy_contracts_passing(self):
        self.assertEqual(check_requirement_coverage({}), [])
        self.assertEqual(gate_check(full_contract()), [])


class DeclaredRuntimeAdapterGateTests(unittest.TestCase):
    def test_declared_without_enabled_adapter_blocks_release(self):
        result = check({"release_claimed": True, "declared_runtimes": ["postgresql"], "adapters": [{"runtime": "postgresql", "enabled": False}]})
        self.assertEqual(result["status"], "BLOCKED"); self.assertEqual(result["missing"], ["postgresql"])

    def test_silent_fallback_is_failure_not_block(self):
        result = check({"release_claimed": True, "declared_runtimes": ["postgresql"], "silent_fallback": True})
        self.assertEqual(result["status"], "FAIL"); self.assertIn("silent_fallback_forbidden", result["reason"])

    def test_enabled_adapter_passes(self):
        result = check({"release_claimed": True, "declared_runtimes": ["postgresql"], "adapters": [{"runtime": "postgresql", "enabled": True}]})
        self.assertEqual(result["status"], "PASS")

    def test_development_state_is_pending_not_blocked(self):
        result = check({"release_claimed": False, "declared_runtimes": ["postgresql"], "adapters": []})
        self.assertEqual(result["status"], "PASS"); self.assertIn("postgresql", result["pending"])

    def test_multiple_declared_runtimes_all_enforced(self):
        result = check({"release_claimed": True, "declared_runtimes": ["postgresql", "redis"], "adapters": [{"runtime": "postgresql", "enabled": True}]})
        self.assertEqual(result["status"], "BLOCKED"); self.assertEqual(result["missing"], ["redis"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
