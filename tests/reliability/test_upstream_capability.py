#!/usr/bin/env python3
"""UP-001..008 — upstream capability-first regressions (v1.7.0)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from plan_governance_core import (  # noqa: E402
    CAPABILITY_SOURCES, INTEGRATION_METHODS, capability_provenance_record,
    capability_regression_guard, resolve_capability_need, upstream_update_reabsorb,
)


class UpstreamCapabilityTests(unittest.TestCase):
    def test_up001_compose_before_reimplement(self):
        rec = capability_provenance_record(
            "planning", "UPSTREAM_SKILL", "spec-kit@0.2", "COMPOSE", "add reliability gates",
            ["understanding_verification", "acceptance_completeness", "evidence", "recovery"],
            "VALIDATED")
        self.assertEqual(rec["source"], "UPSTREAM_SKILL")
        self.assertIn("COMPOSE", INTEGRATION_METHODS)

    def test_up002_provenance_record_required(self):
        with self.assertRaises(ValueError):
            capability_provenance_record("x", "UNKNOWN_SOURCE", "1.0", "COMPOSE", None, [], "VALIDATED")
        with self.assertRaises(ValueError):
            capability_provenance_record("x", "UPSTREAM_SKILL", "1.0", "MAGIC", None, [], "VALIDATED")

    def test_up003_no_capability_regression_on_integration(self):
        upstream = {"project_types": 8, "planning_quality": 7, "user_control": 9, "test_ability": 6,
                    "tool_ability": 7, "context_understanding": 8, "output_flexibility": 8,
                    "executability": 9}
        integrated = {**upstream, "evidence": 8, "recovery": 7, "acceptance": 9,
                      "anti_fake_pass": 9, "scope_control": 8}
        guard = capability_regression_guard(upstream, integrated)
        self.assertTrue(guard["pass"])
        self.assertIn("evidence", guard["reliability_improved"])
        self.assertIn("anti_fake_pass", guard["reliability_improved"])

    def test_up004_capability_regression_detected(self):
        upstream = {"project_types": 8, "user_control": 9}
        integrated = {"project_types": 3, "user_control": 4, "evidence": 9}  # degraded
        guard = capability_regression_guard(upstream, integrated)
        self.assertFalse(guard["pass"])
        self.assertIn("capability_regression:project_types", guard["regressions"][0])

    def test_up005_unknown_capability_discovers_upstream(self):
        registry = {"rag": {}, "database": {}}
        upstream = {"planning_skill": ["task_breakdown"], "browser_skill": ["web_e2e"]}
        self.assertEqual(resolve_capability_need("task_breakdown", registry, upstream)["resolution"],
                         "discover:planning_skill")
        self.assertEqual(resolve_capability_need("database", registry, upstream)["resolution"], "known_adapter")

    def test_up006_capability_not_available_reported_honestly(self):
        result = resolve_capability_need("teleport", {}, {})
        self.assertEqual(result["resolution"], "CAPABILITY_NOT_AVAILABLE")
        self.assertEqual(result["action"], "report_to_user")  # never silent capability=false

    def test_up007_upstream_update_reabsorb(self):
        record = {"capability": "planning", "source_version": "spec-kit@0.2",
                  "capabilities": ["plan", "tasks"]}
        updated = {"source_version": "spec-kit@0.3", "capabilities": ["plan", "tasks", "analyze"]}
        out = upstream_update_reabsorb(record, updated)
        self.assertEqual(out["added"], ["analyze"])
        self.assertEqual(out["action"], "compatibility_check_and_regression")

    def test_up008_wrapper_never_restricts_upstream(self):
        # integration must not shrink the upstream's capability surface
        upstream = {"executability": 9, "output_flexibility": 9, "user_control": 9}
        wrapped = {**upstream}  # a correct wrapper preserves all
        self.assertTrue(capability_regression_guard(upstream, wrapped)["pass"])


if __name__ == "__main__":
    unittest.main()
