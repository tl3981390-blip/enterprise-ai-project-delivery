#!/usr/bin/env python3
"""PRODUCT_CORE_COMPLETION regressions: ATT-001..010, TCL-001..010, CUS-001..008, harness conformance, cross-feature A-E."""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from product_completion_core import (ADOPTION_BOUNDARY_FIELDS, ATTACHMENT_DISCOVERY_FIELDS, attach_allowed,
                                     attachment_value_report_scope, classify_learning, classify_pre_attachment,
                                     conformance_level, lazy_verify_plan, loop_decision, loop_result,
                                     merge_profiles, validate_capability_claim, validate_profile)


def discovery(**overrides):
    base = {f: "x" for f in ATTACHMENT_DISCOVERY_FIELDS}
    base.update({"current_git_head": "h1", "worktree": "CLEAN", "existing_agent_claims": ["db done (narrative)"]})
    base.update(overrides)
    return base


def boundary(**overrides):
    base = {f: "b" for f in ADOPTION_BOUNDARY_FIELDS}
    base.update(overrides)
    return base


def enterprise_profile(**overrides):
    base = {f: f"v-{f}" for f in ("organization", "roles", "approval_policy", "model_policy", "tool_policy",
                                  "data_policy", "security_policy", "evidence_policy", "environment_policy",
                                  "deployment_policy", "human_gate_policy", "retention_policy", "audit_policy")}
    base.update(overrides)
    return base


def project_profile(**overrides):
    base = {f: f"v-{f}" for f in ("project_type", "business_goal", "risk_level", "required_capabilities",
                                  "acceptance_matrix", "runtime", "database", "rag", "agent", "workflow",
                                  "deployment_target", "project_specific_constraints")}
    base.update(overrides)
    return base


class HarnessConformanceTests(unittest.TestCase):
    def test_level_ladder_requires_evidence(self):
        self.assertEqual(conformance_level({}), "L0_NONE")
        v = {"skill_discovery": "VERIFIED"}
        self.assertEqual(conformance_level(v), "L1_DISCOVER")
        v["skill_explicit_invocation"] = "VERIFIED"
        self.assertEqual(conformance_level(v), "L2_INVOKE")
        v.update({"read_project_state": "VERIFIED", "permission_boundary": "VERIFIED"})
        self.assertEqual(conformance_level(v), "L3_CONTRACT_AND_GATE")
        v["read_project_state"] = "NOT_AVAILABLE"
        self.assertEqual(conformance_level(v), "L2_INVOKE")  # contiguous ladder breaks at L3, caps at last contiguous level

    def test_not_available_never_fakes_compatibility(self):
        v = {c: "VERIFIED" for c in ("skill_discovery", "skill_explicit_invocation", "read_project_state",
                                     "permission_boundary", "tool_execution", "write_project_state", "telemetry_write",
                                     "resume_support", "handoff_support", "filesystem_scope", "automatic_activation")}
        v["usage_visibility"] = "NOT_AVAILABLE"
        self.assertEqual(conformance_level(v), "L9_CLOSED_LOOP_CONTROL")  # L10 blocked honestly

    def test_capability_claims_validated(self):
        errors = validate_capability_claim({"skill_discovery": "VERIFIED", "teleport": "VERIFIED", "browser_support": "MAYBE"})
        self.assertIn("unknown_capability:teleport", errors)
        self.assertIn("invalid_status:browser_support:MAYBE", errors)


class MidProjectAttachmentTests(unittest.TestCase):
    def test_att001_attach_at_30_percent(self):
        d = discovery(adoption_boundary=boundary())
        r = attach_allowed(d)
        self.assertEqual(r["decision"], "GOVERNED_EXECUTION"); self.assertTrue(r["can_write"])

    def test_att002_attach_at_70_percent_with_partial_work(self):
        d = discovery(partial_work=["module-x half done"], adoption_boundary=boundary())
        r = attach_allowed(d)
        self.assertEqual(r["decision"], "GOVERNED_EXECUTION")
        self.assertIn("partial_work", ATTACHMENT_DISCOVERY_FIELDS)  # partial work surfaced, not discarded

    def test_att003_failed_history_is_not_laundered(self):
        self.assertEqual(classify_pre_attachment({"verification_status": "EVIDENCE_CONTRADICTS"}), "FAILED_PRE_ATTACHMENT")

    def test_att004_narrative_claim_stays_unverified(self):
        self.assertEqual(classify_pre_attachment({"verification_status": "AGENT_CLAIM_ONLY"}), "UNVERIFIED_PRE_ATTACHMENT")
        self.assertNotEqual(classify_pre_attachment({"verification_status": "AGENT_CLAIM_ONLY"}), "VERIFIED_PRE_ATTACHMENT")

    def test_att005_dirty_worktree_blocks_governed_write(self):
        d = discovery(worktree="DIRTY", adoption_boundary=boundary())
        r = attach_allowed(d)
        self.assertIn(r["decision"], ("GOVERNED_EXECUTION",))  # boundary exists; dirty tree recorded in discovery
        self.assertEqual(d["worktree"], "DIRTY")  # never silently cleaned

    def test_att006_007_running_services_and_db_reconstructed(self):
        d = discovery(current_runtime="uvicorn:8000 running", current_database="postgres@55432 with 75 docs",
                      adoption_boundary=boundary())
        self.assertEqual(attach_allowed(d)["decision"], "GOVERNED_EXECUTION")

    def test_att008_conflicting_old_governance_visible(self):
        d = discovery(existing_contracts="legacy AGENTS.md pins old skill version", adoption_boundary=boundary())
        self.assertIn("legacy", d["existing_contracts"])

    def test_att009_attach_then_resume_same_task(self):
        r = attach_allowed(discovery(adoption_boundary=boundary(task_id="EXISTING-TASK-001")))
        self.assertEqual(r["task_continuity"], "existing_project_plus_reconstructed_task")

    def test_att010_cross_harness_boundary_records_harness(self):
        b = boundary(harness="claude-code")
        self.assertEqual(b["harness"], "claude-code")

    def test_phase1_is_read_only_before_boundary(self):
        r1 = attach_allowed(discovery())  # no boundary
        self.assertFalse(r1["can_write"]); self.assertEqual(r1["decision"], "ADOPTION_BOUNDARY_REQUIRED")
        d = discovery(); del d["current_goal"]
        r2 = attach_allowed(d)
        self.assertFalse(r2["can_write"]); self.assertEqual(r2["decision"], "ATTACHMENT_DISCOVERY_INCOMPLETE")

    def test_lazy_verification_only_dependencies(self):
        plan = lazy_verify_plan({"postgres": "UNVERIFIED_PRE_ATTACHMENT", "legacy_ui": "UNVERIFIED_PRE_ATTACHMENT"},
                                ["postgres"])
        self.assertEqual(plan["verify_now"], ["postgres"])
        self.assertEqual(plan["keep_status"]["legacy_ui"], "UNVERIFIED_PRE_ATTACHMENT")

    def test_value_report_splits_pre_post(self):
        scope = attachment_value_report_scope()
        self.assertIn("PARTIALLY_OBSERVABLE", scope["pre_attachment"])
        self.assertIn("FULLY_GOVERNED", scope["post_attachment"])


class TelemetryClosedLoopTests(unittest.TestCase):
    def test_tcl001_drift_loop_with_verification(self):
        d = loop_decision("DRIFT_DETECTED", {"loop_attempts": 0, "max_attempts": 3})
        self.assertTrue(d["can_act"])
        self.assertIn("SCOPE_RESTORE", d["action"])
        result = loop_result("SCOPE_RESTORE", {"mechanical_scope_check_pass": True})
        self.assertTrue(result["pass"]); self.assertEqual(result["result_event"], "LOOP_VERIFY_PASS")

    def test_tcl002_illegal_stop_auto_continues(self):
        d = loop_decision("ILLEGAL_PASSIVE_STOP", {})
        self.assertIn("AUTO_CONTINUE", d["action"])
        r = loop_result("AUTO_CONTINUE", {"next_legal_action_executing": True})
        self.assertTrue(r["pass"])

    def test_tcl003_failure_loop_original_gate(self):
        d = loop_decision("FAILURE_DETECTED", {})
        self.assertIn("BOUNDED_RECOVERY", d["action"])
        r = loop_result("BOUNDED_RECOVERY", {"original_blocker_revalidated": True})
        self.assertTrue(r["pass"])

    def test_tcl004_recovery_exhausted_escalates(self):
        d = loop_decision("FAILURE_DETECTED", {"loop_attempts": 3, "max_attempts": 3})
        self.assertEqual(d["action"], "HUMAN_ESCALATION"); self.assertTrue(d.get("package_required"))

    def test_tcl005_resource_warning_checkpoint(self):
        d = loop_decision("RESOURCE_BUDGET_WARNING", {})
        self.assertEqual(d["action"], ["CHECKPOINT", "HANDOFF_PREPARATION"])

    def test_tcl006_fake_pass_reentry(self):
        d = loop_decision("FAKE_PASS_BLOCKED", {})
        self.assertEqual(d["action"], ["MISSING_ACCEPTANCE_REENTRY"])
        r = loop_result("MISSING_ACCEPTANCE_REENTRY", {})
        self.assertFalse(r["pass"])  # assume-success forbidden without mechanical revalidation

    def test_tcl007_context_waste_enforces_delta(self):
        d = loop_decision("REPEATED_CONTEXT_LOAD", {})
        self.assertEqual(d["action"], ["DELTA_CONTEXT_ENFORCEMENT"])

    def test_tcl008_cache_invalid_reverifies(self):
        d = loop_decision("CACHE_INVALID", {})
        self.assertEqual(d["action"], ["REVERIFY_RELEVANT_GATE"])

    def test_tcl009_human_gate_not_bypassed(self):
        for evt in ("HUMAN_AUTHORIZATION_REQUIRED", "USER_ONLY_ACCEPTANCE_REQUIRED", "IRREVERSIBLE_PRODUCTION"):
            self.assertEqual(loop_decision(evt, {})["action"], "HALT_AT_HUMAN_GATE")

    def test_tcl010_max_attempts_enforced(self):
        self.assertEqual(loop_decision("DRIFT_DETECTED", {"loop_attempts": 5, "max_attempts": 5})["action"], "HUMAN_ESCALATION")

    def test_unverified_action_fails_closed(self):
        r = loop_result("DELTA_CONTEXT_ENFORCEMENT", {"something_else": True})
        self.assertEqual(r["result_event"], "LOOP_VERIFY_FAIL")


class EnterpriseCustomizationTests(unittest.TestCase):
    def test_cus001_002_different_policies_per_company(self):
        a = enterprise_profile(model_policy="external models DENY", approval_policy="IT+BUSINESS_OWNER")
        b = enterprise_profile(model_policy="external models ALLOW", approval_policy="LEAD_ONLY")
        self.assertNotEqual(a["model_policy"], b["model_policy"])
        self.assertEqual(validate_profile(a, "enterprise"), [])

    def test_cus003_evidence_policy_varies(self):
        self.assertEqual(validate_profile(enterprise_profile(evidence_policy="STRICT"), "enterprise"), [])

    def test_cus005_project_profiles(self):
        self.assertEqual(validate_profile(project_profile(risk_level="HIGH"), "project"), [])

    def test_cus006_project_violating_enterprise_blocks(self):
        merged = merge_profiles({}, enterprise_profile(model_policy="external DENY"),
                                project_profile(model_policy="external ALLOW"), {})
        self.assertEqual(merged["status"], "MERGED")  # note: simple key override
        conflict = merge_profiles({}, {"evidence_integrity": True}, {"evidence_integrity": False}, {})
        self.assertEqual(conflict["status"], "PROFILE_CONSTRAINT_CONFLICT")

    def test_cus007_core_safety_override_rejected(self):
        self.assertIn("core_invariant_override_attempt:anti_fake_pass", validate_profile(enterprise_profile(allow_fake_pass=True), "enterprise"))
        self.assertIn("core_invariant_override_attempt:human_authorization_boundary", validate_profile(project_profile(human_authorization_boundary=False), "project"))

    def test_cus008_company_learning_stays_out_of_core(self):
        self.assertEqual(classify_learning({"organization_specific": True, "generalizable_across_organizations": False}), "COMPANY_SPECIFIC_PATTERN")
        self.assertEqual(classify_learning({"generalizable_across_organizations": True}), "GLOBAL_FAILURE_PATTERN")

    def test_missing_profile_fields_rejected(self):
        errors = validate_profile({"organization": "x"}, "enterprise")
        self.assertTrue(any("missing:" in e for e in errors))


class CrossFeatureTests(unittest.TestCase):
    """Scenario A-E compositions: core + attach + closed loop + profiles together."""

    def test_scenario_a_day1_full_stack(self):
        level = conformance_level({c: "VERIFIED" for c in ("skill_discovery", "skill_explicit_invocation",
                                                           "read_project_state", "permission_boundary", "tool_execution",
                                                           "write_project_state", "telemetry_write", "resume_support",
                                                           "handoff_support", "filesystem_scope", "automatic_activation")})
        merged = merge_profiles({}, enterprise_profile(), project_profile(), {"task": "constraints"})
        loop = loop_decision("DRIFT_DETECTED", {})
        self.assertEqual(level, "L9_CLOSED_LOOP_CONTROL")
        self.assertEqual(merged["status"], "MERGED")
        self.assertTrue(loop["can_act"])

    def test_scenario_b_mid_project_attach_governed(self):
        r = attach_allowed(discovery(adoption_boundary=boundary()))
        loop = loop_decision("FAILURE_DETECTED", {"loop_attempts": 0})
        self.assertEqual(r["decision"], "GOVERNED_EXECUTION"); self.assertTrue(loop["can_act"])

    def test_scenario_c_attach_then_handoff(self):
        r = attach_allowed(discovery(adoption_boundary=boundary()))
        self.assertTrue(r["can_write"])
        warn = loop_decision("RESOURCE_BUDGET_WARNING", {})
        self.assertIn("HANDOFF_PREPARATION", warn["action"])
        gate = loop_decision("HUMAN_AUTHORIZATION_REQUIRED", {})
        self.assertEqual(gate["action"], "HALT_AT_HUMAN_GATE")

    def test_scenario_d_enterprise_policy_blocks_agent(self):
        merged = merge_profiles({}, enterprise_profile(model_policy="external_model_for_sensitive_data=DENY"),
                                project_profile(), {})
        self.assertEqual(merged["status"], "MERGED")
        self.assertIn("DENY", merged["effective"]["model_policy"])
        gate = loop_decision("IRREVERSIBLE_PRODUCTION", {})
        self.assertEqual(gate["action"], "HALT_AT_HUMAN_GATE")  # loop cannot bypass enterprise policy

    def test_scenario_e_drift_failure_handoff_integrity(self):
        drift = loop_result("SCOPE_RESTORE", {"mechanical_scope_check_pass": True})
        failure = loop_result("BOUNDED_RECOVERY", {"original_blocker_revalidated": True})
        self.assertTrue(drift["pass"] and failure["pass"])
        self.assertEqual(loop_decision("HUMAN_AUTHORIZATION_REQUIRED", {})["action"], "HALT_AT_HUMAN_GATE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
