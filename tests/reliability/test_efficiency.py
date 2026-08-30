#!/usr/bin/env python3
"""v1.4 efficiency regressions EFF-001..011 (token/governance cost reduction without reliability loss)."""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from efficiency_core import (EvidenceRegistry, VerifiedStateCache, active_view_valid, batch_evolution,
                             build_active_contract_view, build_handoff_context, capture_experience,
                             decide_context_load, experience_fingerprint, make_snapshot,
                             new_counters, route_gates, should_deep_analyze, token_efficiency_metrics,
                             token_per_unit)
from check_plan_alignment import check as align_check
from skill_evolution_core import validate_patch_declaration


def snap(**overrides):
    base = {"task_id": "T", "goal_hash": "g1", "contract_hash": "c1", "stage_id": "S1", "git_head": "h1",
            "worktree_hash": "w1", "runtime_identity": "r1", "last_gate": "G", "last_evidence_anchor": "a1",
            "last_event_id": "e1", "current_blocker": "", "next_legal_action": "next"}
    base.update(overrides)
    return make_snapshot(base)


class DeltaContextTests(unittest.TestCase):
    def test_eff001_contract_unchanged_is_delta_no_full_reload(self):
        old = snap()
        new = snap(stage_id="S2", last_event_id="e2")  # stage advanced, relevant hashes unchanged
        result = decide_context_load(old, new)
        self.assertEqual(result["mode"], "DELTA"); self.assertEqual(result["reload"], [])
        self.assertEqual(result["reason_code"], "ALL_RELEVANT_HASHES_UNCHANGED")

    def test_first_entry_is_full(self):
        result = decide_context_load(None, snap())
        self.assertEqual(result["mode"], "FULL"); self.assertEqual(result["reason_code"], "FIRST_ENTRY")

    def test_eff003_relevant_file_change_invalidates(self):
        old = snap()
        new = snap(worktree_hash="w2")
        result = decide_context_load(old, new)
        self.assertEqual(result["reason_code"], "RELEVANT_HASH_CHANGED"); self.assertIn("changed_files", result["reload"])


class VerifiedCacheTests(unittest.TestCase):
    def test_eff002_hash_unchanged_is_cache_hit(self):
        cache = VerifiedStateCache()
        inputs = {"contract_hash": "abc", "runtime": "xyz", "evidence_anchor": "123"}
        cache.put("RBAC_GATE", inputs, "PASS")
        self.assertEqual(cache.get("RBAC_GATE", inputs)["result"], "PASS")
        self.assertEqual(cache.counters["cache_hit"], 1)

    def test_eff003_changed_input_is_miss_forcing_reverify(self):
        cache = VerifiedStateCache()
        cache.put("RBAC_GATE", {"contract_hash": "abc"}, "PASS")
        self.assertIsNone(cache.get("RBAC_GATE", {"contract_hash": "CHANGED"}))
        self.assertEqual(cache.counters["cache_miss"], 1)  # strict invalidation: never stale reuse

    def test_only_pass_fail_verdicts_cacheable(self):
        cache = VerifiedStateCache()
        with self.assertRaises(ValueError):
            cache.put("G", {}, "MAYBE")


class RiskRoutingTests(unittest.TestCase):
    GATES = ["contract_check", "affected_module_tests", "targeted_browser_journey", "persistence_gate",
             "restart_gate", "api_gate", "rag_gate", "rbac_gate", "role_e2e_gate", "postgres_gate", "handoff_gate"]

    def test_eff004_low_risk_ui_runs_only_related_gates(self):
        result = route_gates(["ui_cosmetic"], self.GATES)
        self.assertEqual(result["risk"], "LOW")
        self.assertEqual(set(result["run"]), {"affected_module_tests", "targeted_browser_journey", "contract_check"})
        self.assertIn("postgres_gate", result["not_applicable"]); self.assertIn("rag_gate", result["not_applicable"])
        self.assertIn("handoff_gate", result["not_applicable"])

    def test_eff005_database_change_keeps_persistence_restart_api(self):
        result = route_gates(["database"], self.GATES)
        self.assertEqual(result["risk"], "HIGH")
        for gate in ("persistence_gate", "restart_gate", "api_gate", "contract_check"):
            self.assertIn(gate, result["run"])

    def test_critical_keeps_full_chain(self):
        result = route_gates(["production"], self.GATES)
        self.assertEqual(result["risk"], "CRITICAL"); self.assertEqual(result["run"], sorted(self.GATES)); self.assertEqual(result["not_applicable"], [])

    def test_unknown_surface_fails_closed(self):
        with self.assertRaises(ValueError):
            route_gates(["time_travel"], self.GATES)

    def test_risk_takes_maximum_of_surfaces(self):
        self.assertEqual(route_gates(["copy_text", "rbac"], self.GATES)["risk"], "HIGH")


class EvidenceReferenceTests(unittest.TestCase):
    def test_eff006_existing_evidence_uses_ref_not_full_body(self):
        reg = EvidenceRegistry()
        first = reg.register("EV-0001", "x" * 10000, "stage3/fail", "FAIL")
        self.assertFalse(first["deduplicated"])
        second = reg.register("EV-0001", "x" * 10000, "stage3/fail", "FAIL")
        self.assertTrue(second["deduplicated"])
        ref = reg.ref("EV-0001")
        self.assertEqual(set(ref), {"ref", "hash", "source", "result"})  # no body in ref

    def test_unknown_ref_fails(self):
        with self.assertRaises(KeyError):
            EvidenceRegistry().ref("EV-404")


class HotColdHandoffTests(unittest.TestCase):
    def test_eff007_handoff_is_hot_plus_cold_index(self):
        full = {"goal": "g", "task_id": "T", "current_stage": "S", "current_head": "h", "current_state": "EXEC",
                "current_blocker": "", "last_known_good": "lkg", "partial_work": ["unit-3 half done"], "next_legal_action": "next",
                "failure_history": ["f1", "f2"], "full_telemetry": "path", "old_stage_reports": ["r1", "r2"],
                "recovery_history": ["rec1"], "evidence_index": "idx.json", "experience_pack": "pack.md",
                "learning_ledger": "ledger.md", "benchmark_reports": ["b1", "b2"], "handoff_history": ["h1"]}
        result = build_handoff_context(full)
        self.assertEqual(set(result["hot_context"]), {"goal", "task_id", "current_stage", "current_head", "current_state",
                                                      "last_known_good", "partial_work", "next_legal_action"})
        self.assertIn("failure_history", result["cold_context_index"]); self.assertIn("full_telemetry", result["cold_context_index"])
        self.assertGreater(result["cold_refs"], result["hot_items"])


class BatchEvolutionTests(unittest.TestCase):
    def _exp(self, pattern, project="P1", evidence="E1"):
        return {"failure_pattern": pattern, "classification": "CORE_SKILL_DEFECT", "root_cause_class": "X", "affected_capability": "cap", "evidence_ref": evidence, "project_ref": project}

    def test_eff008_repeated_pattern_dedups_with_repeat_count(self):
        inbox = {}
        fp = experience_fingerprint(self._exp("PLAN_STOP"))
        first = capture_experience(inbox, fp, self._exp("PLAN_STOP", "P1", "E1"))
        second = capture_experience(inbox, fp, self._exp("PLAN_STOP", "P2", "E2"))
        self.assertEqual(first["action"], "NEW_PATTERN"); self.assertEqual(second["action"], "DEDUPLICATED")
        self.assertEqual(inbox[fp]["repeat_count"], 2); self.assertEqual(inbox[fp]["project_refs"], ["P1", "P2"])

    def test_no_deep_analysis_without_trigger(self):
        inbox = {}
        fp = experience_fingerprint(self._exp("PLAN_STOP"))
        capture_experience(inbox, fp, self._exp("PLAN_STOP"))
        self.assertFalse(should_deep_analyze("EVERY_EVENT", inbox, fp))

    def test_eff009_multiple_low_severity_batch_on_stage_end(self):
        inbox = {}
        fps = []
        for i, pattern in enumerate(("P1", "P2", "P3")):
            fp = experience_fingerprint(self._exp(pattern)); fps.append(fp); capture_experience(inbox, fp, self._exp(pattern, evidence=f"E{i}"))
        self.assertTrue(all(should_deep_analyze("STAGE_END", inbox, fp) for fp in fps))
        batch = batch_evolution(inbox, fps)
        self.assertEqual(batch["batch_size"], 3); self.assertIn("heldout_protocol", batch["shared_setup"])

    def test_repeated_pattern_needs_two_occurrences(self):
        inbox = {}
        fp = experience_fingerprint(self._exp("ONCE"))
        capture_experience(inbox, fp, self._exp("ONCE"))
        self.assertFalse(should_deep_analyze("REPEATED_PATTERN", inbox, fp))
        capture_experience(inbox, fp, self._exp("ONCE", "P2", "E2"))
        self.assertTrue(should_deep_analyze("REPEATED_PATTERN", inbox, fp))


class LL008WordBoundaryTests(unittest.TestCase):
    def contract(self):
        return {"forbidden_modify": ["Harness main", "real Rescue project"], "work_scope": ["shared scripts and tests"],
                "allowed_modify": ["tests and evidence"], "explicit_non_goals": [], "forbidden_tools": []}

    def plan(self, desc, target="tests"):
        return {"actions": [{"name": "A", "description": desc, "target": target}]}

    def test_eff010_legal_substrings_not_blocked(self):
        c = self.contract()
        for desc in ["修改 EnterpriseReviewLab 模块 via shared scripts and tests",
                     "install alternative recovery adapter via shared scripts and tests",
                     "update PROJECT RELIABILITY SCOREBOARD docs under tests and evidence"]:
            self.assertEqual(align_check(self.plan(desc), c), [], desc)

    def test_eff011_real_forbidden_words_still_block(self):
        c = self.contract()
        for desc in ["修改 Harness main 的配置", "write into production 生产系统 via shared scripts"]:
            errors = align_check(self.plan(desc), c)
            self.assertTrue(errors, desc)


class MetricsAndViewsTests(unittest.TestCase):
    def test_counters_and_not_available_attribution(self):
        counters = new_counters(); counters["gate_execution_count"] = 4; counters["gate_cache_hit"] = 2
        m = token_efficiency_metrics(counters, {"total_token": 1000})
        self.assertEqual(m["gate_execution_count"], 4); self.assertEqual(m["governance_token"], "NOT_AVAILABLE")
        m2 = token_efficiency_metrics(counters, {"total_token": 1000, "governance_token": 250})
        self.assertEqual(m2["governance_token_ratio"], 0.25)

    def test_token_per_unit(self):
        self.assertEqual(token_per_unit(9872301, 14, "TOKEN_PER_ACCEPTED_DELIVERY")["TOKEN_PER_ACCEPTED_DELIVERY"], 705164)
        self.assertEqual(token_per_unit("NOT_AVAILABLE", 14, "X")["X"], "NOT_AVAILABLE")

    def test_active_contract_view_hash_binding(self):
        contract = {"goal": "g", "constraints": ["c1"]}
        view = build_active_contract_view(contract, {"current_goal": "g", "next_action": "n"})["active_view"]
        self.assertTrue(active_view_valid(view, contract))
        self.assertFalse(active_view_valid(view, {"goal": "g", "constraints": ["CHANGED"]}))

    def test_reduction_ops_accepted_with_full_declaration(self):
        patch = {"patch_id": "P-S1", "source_experience": "EXP", "affected_capability": "cap", "op": "SIMPLIFY",
                 "target": "gate set", "old_behavior": "always-on", "new_behavior": "risk-routed",
                 "expected_benefit": "-40% gate tokens", "possible_regression": "missed low-freq risk"}
        self.assertEqual(validate_patch_declaration(patch), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
