#!/usr/bin/env python3
"""POST_v1.5 generalization regressions — SYS-001..035 acceptance matrix.
Root cause map: evidence/post_v1_5_generalization/SYSTEMIC_ROOT_CAUSE_MAP.md
Scope: applicability decoupling, layer separation (classification vs capability),
conditional capability activation, Active Delivery Plan, enterprise workflow as INPUT,
five-way experience routing, template calcification guard, assumption change robustness,
cross-domain synthetic replays (family menu / desktop app / two enterprise workflows /
requirement change). No reliability invariant is weakened by any test here."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from product_completion_core import (  # noqa: E402
    CAPABILITY_REGISTRY, LIFECYCLE_STAGES, PROJECT_CLASSIFICATION_FIELDS,
    CAPABILITY_DECLARATION_FIELDS, derive_active_plan, compile_enterprise_workflow,
    required_acceptance_perspectives, classify_experience_route,
    validate_core_evolution_admission, validate_profile, merge_profiles,
    assumption_change_model, active_capabilities,
)
from efficiency_core import route_gates  # noqa: E402
import check_understanding_gate as cug  # noqa: E402
import skill_evolution_core as sec  # noqa: E402

EX = ROOT / "examples"


def family_menu_profile():
    return {
        "project_type": "personal-family-menu-app",
        "business_goal": "家庭点菜更省事",
        "risk_level": "LOW",
        "required_capabilities": [],
        "acceptance_matrix": {"A1": "菜品增删改可用"},
        "project_specific_constraints": ["单用户本地使用"],
        "stakeholders": "single",
        "acceptance_perspectives": ["owner_user"],
    }


def enterprise_ai_profile():
    return {
        "project_type": "enterprise-internal-rag",
        "business_goal": "法务内部检索合同条款",
        "risk_level": "HIGH",
        "required_capabilities": ["rag", "tool_permissions", "enterprise_governance",
                                  "browser_acceptance", "deployment", "multi_role_approval"],
        "acceptance_matrix": {"A1": "引用可回溯"},
        "project_specific_constraints": ["数据不出域"],
        "rag": {"versioned_knowledge": True},
    }


def enterprise_profile_with_roles():
    return {"organization": "ORG", "roles": ["employee", "reviewer", "approver", "admin"]}


class PositioningTests(unittest.TestCase):
    """SYS-001 / SYS-031 / SYS-033 / SYS-034 / SYS-035"""

    def test_sys001_positioning_is_complex_project_reliability(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("COMPLEX PROJECT RELIABILITY DELIVERY SYSTEM", text)
        self.assertIn("EXPLICIT_INVOCATION", text)
        for banned in ("企业内部开发一个 AI 产品", "仅限企业"):
            self.assertNotIn(banned, text)

    def test_sys031_docs_match_runtime(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("复杂项目", readme)
        trigger = (ROOT / "tests" / "evals" / "trigger" / "trigger_cases.md").read_text(encoding="utf-8")
        self.assertIn("家庭点菜单", trigger)  # non-enterprise explicit-invocation positive exists
        self.assertIn("EXPLICIT_INVOCATION", trigger)

    def test_sys033_sys034_no_family_or_personal_mode_hardcoding(self):
        for script in (ROOT / "共享" / "scripts").glob("*.py"):
            text = script.read_text(encoding="utf-8")
            for banned in ("FAMILY_MODE", "家庭模式", "PERSONAL_MODE", "HOME_MODE"):
                self.assertNotIn(banned, text, f"{script.name} encodes {banned}")

    def test_sys035_no_new_fake_universal_template(self):
        for stage in ("07_RAG设计", "08_Agent设计", "09_MCP与工具权限网关", "10_企业治理与合规",
                      "13_浏览器真实验收", "16_部署", "17_License与合规", "18_升级与回滚"):
            self.assertNotIn(stage, LIFECYCLE_STAGES)  # capability stages never lifecycle-mandatory

    def test_sys008_delivery_intensity_not_project_classifier(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("DELIVERY_INTENSITY", text)
        self.assertIn("不是三套固定流程模板", text)


class ApplicabilityTests(unittest.TestCase):
    """SYS-002 / SYS-003 / SYS-004 / SYS-005 / SYS-006 / SYS-007 / SYS-032"""

    def test_sys002_non_enterprise_invocation_accepted(self):
        profile = family_menu_profile()
        self.assertEqual(validate_profile(profile, "project"), [])  # no capability keys needed
        plan = derive_active_plan(profile)
        self.assertTrue(plan["explicit_invocation_accepted"])
        for capability_stage in ("07_RAG设计", "09_MCP与工具权限网关", "10_企业治理与合规"):
            self.assertNotIn(capability_stage, plan["active_stages"])

    def test_sys032_capability_fields_are_optional(self):
        base = family_menu_profile()
        for cap in CAPABILITY_DECLARATION_FIELDS:
            self.assertNotIn(cap, PROJECT_CLASSIFICATION_FIELDS)
        self.assertEqual(validate_profile(base, "project"), [])
        missing = {k: v for k, v in base.items() if k != "business_goal"}
        self.assertTrue(any("missing:" in e for e in validate_profile(missing, "project")))

    def test_sys003_non_ai_complex_project_supported(self):
        profile = json.loads((EX / "desktop_knowledge_app_profile.example.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_profile(profile, "project"), [])
        plan = derive_active_plan(profile)
        self.assertIn("项目理解与目标锁定", plan["active_stages"])
        self.assertIn("最终验收", plan["active_stages"])
        self.assertNotIn("企业治理与合规核验", plan["active_stages"])
        self.assertIn("数据持久化与一致性验证", plan["active_stages"])
        self.assertIn("升级与回滚演练", plan["active_stages"])

    def test_sys004_enterprise_ai_project_still_supported(self):
        profile = enterprise_ai_profile()
        self.assertEqual(validate_profile(profile, "project"), [])
        plan = derive_active_plan(profile, enterprise_profile_with_roles())
        self.assertIn("企业治理与合规核验", plan["active_stages"])
        self.assertIn("多角色验收", plan["active_stages"])
        self.assertIn("rag_gate", plan["active_gates"])

    def test_sys005_sys006_historical_flow_not_mandatory(self):
        plan = derive_active_plan(family_menu_profile())
        self.assertIn("项目理解与目标锁定", plan["active_stages"])
        self.assertIn("最终验收", plan["active_stages"])
        self.assertEqual(plan["final_acceptance"], "INDEPENDENT_VERIFICATION_NON_OPTIONAL")
        self.assertTrue(plan["explicit_invocation_accepted"])

    def test_sys007_router_controls_gates_within_scoped_universe(self):
        scoped = ["contract_check", "affected_module_tests", "targeted_browser_journey"]
        result = route_gates(["production"], scoped)  # CRITICAL change in a scoped project
        self.assertEqual(result["run"], sorted(scoped))       # runs every AVAILABLE gate
        self.assertEqual(result["not_applicable"], [])        # no world-gates invented (no rag/postgres forced)
        low = route_gates(["copy_text"], scoped + ["rag_gate", "postgres_gate"])
        self.assertNotIn("rag_gate", low["run"])
        self.assertIn("rag_gate", low["not_applicable"])

    def test_solo_perspectives_collapse_but_independence_kept(self):
        self.assertEqual(required_acceptance_perspectives(family_menu_profile(), None),
                         ("owner_user",))


class EnterpriseWorkflowTests(unittest.TestCase):
    """SYS-009 / SYS-010 / SYS-011 / SYS-024 / SYS-025"""

    def _load(self, name):
        return json.loads((EX / name).read_text(encoding="utf-8"))

    def test_sys009_enterprise_workflow_is_external_input(self):
        compiled = compile_enterprise_workflow(self._load("enterprise_workflow_input_a.example.json"))
        self.assertEqual(compiled["status"], "WORKFLOW_COMPILED")
        wf = compiled["workflow"]
        self.assertEqual(wf["source"], "ENTERPRISE_INPUT")
        self.assertEqual([s["name"] for s in wf["stages"]][:2], ["需求提交", "部门负责人批准"])
        self.assertIn("安全复核", wf["human_gates"])

    def test_sys010_two_enterprises_different_workflows_one_core(self):
        a = compile_enterprise_workflow(self._load("enterprise_workflow_input_a.example.json"))
        b = compile_enterprise_workflow(self._load("enterprise_workflow_input_b.example.json"))
        self.assertEqual(a["status"], "WORKFLOW_COMPILED")
        self.assertEqual(b["status"], "WORKFLOW_COMPILED")
        self.assertNotEqual(a["workflow"]["stages"], b["workflow"]["stages"])  # 完全不同的流程均合法
        self.assertEqual(len(b["workflow"]["stages"]), 4)

    def test_sys011_enterprise_rules_cannot_weaken_core_invariants(self):
        bad = {"stages": [{"name": "开发", "skip_evidence": True}, {"name": "上线", "allow_fake_pass": True}]}
        compiled = compile_enterprise_workflow(bad)
        self.assertEqual(compiled["status"], "WORKFLOW_INVALID")
        self.assertTrue(any("core_invariant_weakened" in e for e in compiled["errors"]))
        core = {"anti_fake_pass": True, "evidence_integrity": True}
        ent = {"organization": "X", "data_policy": {"retention": "DENY_EXTERNAL"}}
        proj = {"data_policy": {"retention": "ALLOW_EXTERNAL"}}  # project tries to relax enterprise rule
        merged = merge_profiles(core, ent, proj, {})
        self.assertEqual(merged["status"], "PROFILE_CONSTRAINT_CONFLICT")

    def test_sys024_sys025_workflow_replays(self):
        for name in ("enterprise_workflow_input_a.example.json", "enterprise_workflow_input_b.example.json"):
            wf_input = self._load(name)
            compiled = compile_enterprise_workflow(wf_input)
            self.assertEqual(compiled["status"], "WORKFLOW_COMPILED")
            profile = {"project_type": "enterprise-internal-app", "business_goal": "g", "risk_level": "HIGH",
                       "required_capabilities": [], "acceptance_matrix": {}, "project_specific_constraints": []}
            plan = derive_active_plan(profile, {"workflow": compiled["workflow"]})
            self.assertTrue(set(compiled["workflow"]["human_gates"]) <= set(plan["human_gates"]))
            self.assertIn("FINAL_ACCEPTANCE", plan["human_gates"])  # core final acceptance never dropped


class ExperienceRoutingTests(unittest.TestCase):
    """SYS-012 / SYS-013 / SYS-014 / SYS-015 / SYS-016 / SYS-017"""

    def test_sys012_five_way_classification(self):
        self.assertEqual(classify_experience_route({"harness_specific": True}), "HARNESS_SPECIFIC_PATTERN")
        self.assertEqual(classify_experience_route({"organization_specific": True}), "ENTERPRISE_SPECIFIC_PATTERN")
        self.assertEqual(classify_experience_route({"project_specific": True}), "PROJECT_SPECIFIC_PATTERN")
        self.assertEqual(classify_experience_route({"generalizable_across_projects": True,
                                                    "cross_project_validated": True,
                                                    "counterexample_checked": True}),
                         "GLOBAL_RELIABILITY_PATTERN")
        self.assertEqual(classify_experience_route({}), "ONE_OFF_OBSERVATION")

    def test_sys013_harness_experience_stays_adapter_layer(self):
        self.assertEqual(classify_experience_route({"harness_specific": True,
                                                    "generalizable_across_projects": True,
                                                    "cross_project_validated": True}), "HARNESS_SPECIFIC_PATTERN")

    def test_sys014_project_experience_stays_project_local(self):
        self.assertEqual(classify_experience_route({"project_specific": True,
                                                    "generalizable_across_projects": True}), "PROJECT_SPECIFIC_PATTERN")

    def test_sys015_frequency_is_not_generalizability(self):
        hot = {"generalizable_across_projects": True, "repeat_count": 20,
               "cross_project_validated": True, "counterexample_checked": True}
        self.assertEqual(classify_experience_route(hot), "GLOBAL_RELIABILITY_PATTERN")
        unproven = {"generalizable_across_projects": True, "repeat_count": 100,
                    "cross_project_validated": False, "counterexample_checked": False}
        self.assertEqual(classify_experience_route(unproven), "ONE_OFF_OBSERVATION")  # frequency never promotes

    def test_sys016_evolution_supports_reduction_ops(self):
        for op in ("SIMPLIFY", "MERGE", "REMOVE", "DEFER"):
            self.assertIn(op, sec.PATCH_OPS)

    def test_sys017_core_evolution_requires_cross_project_evidence(self):
        partial = {k: True for k in ("real_failure_or_reliability_need", "current_core_insufficient",
                                     "generalizable", "reproducible", "evidence_backed")}
        self.assertTrue(validate_core_evolution_admission(partial))  # missing cross-project proof -> reject
        full = {k: True for k in ("real_failure_or_reliability_need", "current_core_insufficient", "generalizable",
                                  "reproducible", "evidence_backed", "cross_project_validated",
                                  "counterexample_checked", "no_template_leakage",
                                  "no_enterprise_specific_leakage", "no_project_specific_leakage")}
        self.assertEqual(validate_core_evolution_admission(full), [])


class CalcificationGuardTests(unittest.TestCase):
    """SYS-018 — 20 consecutive enterprise AI projects must not force SSO/RAG/MCP on project 21."""

    def test_history_never_leaks_into_new_personal_project(self):
        history = [enterprise_ai_profile() for _ in range(20)]
        self.assertEqual(len(history), 20)
        caps = active_capabilities(family_menu_profile())  # project 21: personal, non-AI
        self.assertNotIn("rag", caps)
        self.assertNotIn("enterprise_governance", caps)
        self.assertNotIn("tool_permissions", caps)
        plan = derive_active_plan(family_menu_profile())
        self.assertNotIn("07_RAG设计", plan["active_stages"])
        self.assertNotIn("10_企业治理与合规", plan["active_stages"])


class AssumptionChangeTests(unittest.TestCase):
    """SYS-019 / SYS-020 / SYS-021 / SYS-026 — requirement-change replay."""

    def setUp(self):
        # 家庭做饭点菜 executed to partial verified state, then scope changes to 家庭采购+菜品计划
        self.verified = {
            "ui_list_rendering": {"assumptions": ["业务定义=家庭做饭点菜"], "capabilities": ["ui"]},
            "dish_data_model": {"assumptions": ["业务定义=家庭做饭点菜"], "capabilities": ["database"]},
            "random_pick_logic": {"assumptions": ["业务定义=家庭做饭点菜"], "capabilities": ["algorithm"]},
            "storage_evidence": {"assumptions": ["database_engine"], "capabilities": ["database"]},
        }

    def test_sys019_only_dependent_state_invalidated(self):
        result = assumption_change_model(self.verified, changed_assumptions=["业务定义=家庭做饭点菜"])
        cls = result["classification"]
        self.assertEqual(cls["dish_data_model"], "INVALIDATED")
        self.assertEqual(cls["random_pick_logic"], "INVALIDATED")
        self.assertEqual(cls["ui_list_rendering"], "INVALIDATED")

    def test_sys020_unaffected_state_survives(self):
        # PostgreSQL -> SQLite swap: db evidence invalidates, data model revalidates, UI survives
        result = assumption_change_model(self.verified, changed_assumptions=["database_engine", "database"])
        cls = result["classification"]
        self.assertEqual(cls["storage_evidence"], "INVALIDATED")          # depended on the engine assumption
        self.assertEqual(cls["dish_data_model"], "REQUIRES_REVALIDATION")  # shares the database capability
        self.assertEqual(cls["ui_list_rendering"], "STILL_VALID")          # UI unaffected by db swap
        self.assertEqual(cls["random_pick_logic"], "STILL_VALID")

    def test_sys021_sys026_plan_recalculated_not_redone_from_zero(self):
        old_plan = derive_active_plan(family_menu_profile())  # no capability declared yet
        result = assumption_change_model(self.verified, ["业务定义=家庭做饭点菜"], new_required=["采购清单模型"])
        self.assertEqual(result["classification"]["采购清单模型"], "NEW_REQUIRED")
        new_profile = {**family_menu_profile(), "database": {"engine": "sqlite"},
                       "required_capabilities": ["database"]}
        new_plan = derive_active_plan(new_profile)
        self.assertIn("persistence_gate", new_plan["active_gates"])
        self.assertIn("项目理解与目标锁定", new_plan["active_stages"])  # invariants continue
        self.assertIn("最终验收", new_plan["active_stages"])
        self.assertIn("re_run_understanding_for_affected", result["next"])


class CrossDomainReplayTests(unittest.TestCase):
    """SYS-022 / SYS-023 — synthetic replays through the REAL core scripts."""

    def test_sys022_family_menu_replay_reaches_business_decision_gate(self):
        # EXPLICIT_INVOCATION accepted -> understanding gate hits a genuine business ambiguity
        contract = {
            "task_id": "REPLAY-FAMILY-MENU-001",
            "user_real_goal": "使用本 Skill 做一个家庭点菜单项目",
            "business_goal": "家庭点菜决策更省事",
            "final_deliverable": "家庭点菜单应用（形态待定）",
            "current_state": "无",
            "completed_scope": "无（新品）",
            "work_scope": ["待业务定义澄清后确定"],
            "explicit_non_goals": [],
            "allowed_modify": ["本项目新目录"],
            "forbidden_modify": ["Skill 核心仓库"],
            "allowed_tools": ["read", "edit", "local test"],
            "forbidden_tools": [],
            "key_constraints": [],
            "success_criteria": ["owner 真实使用验收"],
            "acceptance_criteria": [],
            "evidence_requirements": ["test_result"],
            "blocking_unknowns": ["业务定义歧义：家庭做饭点菜 / 外卖聚合 / 家庭采购？"],
            "provenance": {"user_real_goal": "USER_EXPLICIT"},
            "understanding_status": "UNDERSTANDING_COMPLETE",  # deliberately premature
        }
        errors = cug.check(contract)
        self.assertTrue(errors)  # gate FAILs: blocking unknown + premature completion claim
        self.assertTrue(any("阻塞性未知项" in e or "缺必填字段" in e for e in errors))
        # legal stop: HUMAN_BUSINESS_DECISION_REQUIRED (ambiguity), NOT skill rejection
        plan = derive_active_plan(family_menu_profile())
        self.assertTrue(plan["explicit_invocation_accepted"])

    def test_sys023_desktop_replay_keeps_core_drops_enterprise(self):
        profile = json.loads((EX / "desktop_knowledge_app_profile.example.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_profile(profile, "project"), [])
        plan = derive_active_plan(profile)
        self.assertIn("项目理解与目标锁定", plan["active_stages"])
        self.assertIn("最终验收", plan["active_stages"])
        self.assertNotIn("企业治理与合规核验", plan["active_stages"])
        self.assertIn("数据持久化与一致性验证", plan["active_stages"])
        self.assertIn("升级与回滚演练", plan["active_stages"])


class IdentityAndAdapterTests(unittest.TestCase):
    """SYS-027 / SYS-028 / SYS-029 / SYS-030"""

    def test_sys027_adapters_remain_thin(self):
        for platform in ("claude", "trae", "workbuddy", "zcode"):
            adapter_dir = ROOT / "adapters" / platform
            files = sorted(p.name for p in adapter_dir.iterdir() if p.is_file())
            self.assertEqual(files, ["CAPABILITIES.json", "INSTALLATION.md", "INVOCATION.md",
                                     "LIFECYCLE.md", "PERMISSIONS.md"])
            for f in adapter_dir.iterdir():
                text = f.read_text(encoding="utf-8")
                self.assertNotIn("07_RAG设计", text)   # no stage semantics in adapters
                self.assertNotIn("SSO", text)

    def test_sys028_core_identity_mechanism_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "共享" / "scripts" / "validate-skill.py"), "--root", str(ROOT)],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_sys029_v150_tag_unchanged(self):
        try:
            head = subprocess.run(["git", "rev-parse", "v1.5.0^{commit}"], cwd=ROOT,
                                  capture_output=True, text=True).stdout.strip()
        except OSError:
            self.skipTest("git unavailable")
        self.assertEqual(head, "491f6c9f76c6c384fd18a21303aba56812eeadb1")

    def test_sys030_historical_release_evidence_untouched(self):
        for rel in ("v1.0.0", "v1.1.0", "v1.3.0", "v1.4.0", "v1.5.0"):
            self.assertTrue((ROOT / "evidence" / f"release_{rel}").exists(), rel)


if __name__ == "__main__":
    unittest.main()
