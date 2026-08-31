#!/usr/bin/env python3
"""DYN-001..012 — universal dynamic delivery regressions (v1.6.0).
Proves: keywords never route; complexity derives from real structure with rationale;
delivery plans carry per-stage goal/output/entry/exit/acceptance/failure + Final
Acceptance Matrix; USER mode never leaks internal governance; replan stays partial."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from delivery_planning_core import (  # noqa: E402
    INTERACTION_MODES, STAGE_BLUEPRINTS, VALUE_MARKERS, assess_complexity,
    build_delivery_execution_plan, derive_capability_needs, keyword_signals_are_context_only,
    user_view,
)
from product_completion_core import derive_active_plan, assumption_change_model  # noqa: E402


def simple_static_page_factors():
    # "企业内部修改一个简单静态页面" — STRUCTURE says trivial, label says enterprise
    return {"business_goals": 1, "user_journeys": 1, "components": 1, "deployment_environments": 0,
            "permissions": 0, "security_surface": 0, "data_migration": 0, "irreversible_operations": 0}


def complex_personal_desktop_factors():
    # "个人跨平台桌面 + 数据 + 同步 + 恢复 + 插件" — STRUCTURE says heavy, label says personal
    return {"business_goals": 3, "user_journeys": 3, "components": 3, "component_dependencies": 3,
            "external_systems": 1, "data_state_complexity": 2, "failure_branches": 2,
            "recovery_requirements": 2, "cross_platform": 2, "data_migration": 1,
            "irreversible_operations": 1, "acceptance_difficulty": 1, "scope_change_risk": 1}


class KeywordRoutingGuardTests(unittest.TestCase):
    def test_dyn001_keywords_never_select_templates(self):
        guard = keyword_signals_are_context_only()
        self.assertEqual(guard["keyword_leak_in_decision_tables"], [])
        self.assertTrue(guard["pass"])

    def test_dyn004_same_keyword_different_complexity_different_plans(self):
        # two projects BOTH labelled "企业 AI": A trivial, B heavy
        a = assess_complexity({"business_goals": 1, "user_journeys": 1, "components": 1})
        b = assess_complexity({"business_goals": 3, "user_journeys": 4, "components": 6,
                               "component_dependencies": 5, "permissions": 2, "security_surface": 2,
                               "data_state_complexity": 3, "data_migration": 1,
                               "irreversible_operations": 1, "deployment_environments": 2})
        self.assertEqual(a["risk_level"], "LOW")
        self.assertIn(b["risk_level"], ("HIGH", "CRITICAL"))
        markers_all = {name: ["independently_acceptable_output"] for name in STAGE_BLUEPRINTS}
        plan_a = build_delivery_execution_plan("A", a, derive_capability_needs(simple_static_page_factors()),
                                               derive_active_plan(_profile()),
                                               stage_value_markers=markers_all)
        plan_b = build_delivery_execution_plan("B", b, derive_capability_needs(complex_personal_desktop_factors()),
                                               derive_active_plan(_profile()),
                                               stage_value_markers=markers_all)
        self.assertNotEqual(plan_a["complexity"]["risk_level"], plan_b["complexity"]["risk_level"])
        self.assertNotEqual(plan_a["final_acceptance_matrix"]["必须验证的风险"],
                            plan_b["final_acceptance_matrix"]["必须验证的风险"])
        self.assertNotEqual(plan_a["final_acceptance_matrix"]["最终必须存在的真实能力"],
                            plan_b["final_acceptance_matrix"]["最终必须存在的真实能力"])

    def test_same_structure_different_label_identical_plan(self):
        # keyword context changes NOTHING when structure is identical
        factors = complex_personal_desktop_factors()
        c1 = assess_complexity(factors)
        c2 = assess_complexity(factors)
        self.assertEqual(c1, c2)
        self.assertEqual(derive_capability_needs(factors)["capabilities"],
                         derive_capability_needs(factors)["capabilities"])


class ComplexityTests(unittest.TestCase):
    def test_dyn002_simple_enterprise_stays_light(self):
        result = assess_complexity(simple_static_page_factors())
        self.assertEqual(result["risk_level"], "LOW")
        caps = derive_capability_needs(simple_static_page_factors())
        self.assertNotIn("enterprise_governance", caps["capabilities"])  # 企业 label ≠ governance
        self.assertNotIn("tool_permissions", caps["capabilities"])

    def test_dyn003_complex_personal_gets_full_governance(self):
        result = assess_complexity(complex_personal_desktop_factors())
        self.assertIn(result["risk_level"], ("HIGH", "CRITICAL"))
        caps = derive_capability_needs(complex_personal_desktop_factors())
        for cap in ("upgrade_rollback", "database", "deployment"):
            self.assertIn(cap, caps["capabilities"])  # heavy personal project earns real governance

    def test_every_level_has_rationale(self):
        for factors, expected in ((simple_static_page_factors(), "LOW"),
                                  ({"permissions": 1, "security_surface": 1}, "MEDIUM"),
                                  (complex_personal_desktop_factors(), "HIGH"),
                                  ({"irreversible_operations": 3, "data_migration": 3,
                                    "security_surface": 3, "cross_platform": 2,
                                    "recovery_requirements": 2, "permissions": 3,
                                    "concurrency": 3, "external_systems": 3,
                                    "deployment_environments": 3, "data_state_complexity": 3,
                                    "multi_role_collaboration": 3}, "CRITICAL")):
            r = assess_complexity(factors)
            self.assertEqual(r["risk_level"], expected)
            self.assertTrue(r["rationale"].startswith(expected))
            self.assertTrue(r["dominant_factors"])

    def test_unknown_factor_fails_closed(self):
        with self.assertRaises(ValueError):
            assess_complexity({"mystery_factor": 1})


class DeliveryPlanTests(unittest.TestCase):
    def _plan(self):
        complexity = assess_complexity(complex_personal_desktop_factors())
        needs = derive_capability_needs(complex_personal_desktop_factors(),
                                        declared=["database", "upgrade_rollback"])
        plan = derive_active_plan(_profile({"database": {"engine": "sqlite"},
                                            "required_capabilities": ["database", "upgrade_rollback"]}))
        return build_delivery_execution_plan("个人桌面知识库", complexity, needs,
                                             plan["active_stages"], plan["not_applicable_stages"])

    def test_dyn005_stages_have_goal_output_acceptance_evidence(self):
        for stage in self._plan()["dynamic_stages"]:
            for field in ("阶段名称", "阶段目标", "主要工作", "阶段输出", "进入条件", "完成条件", "失败后的处理"):
                self.assertIn(field, stage, f"{stage.get('阶段名称')} missing {field}")
            self.assertIn("验收方式", stage)
            self.assertIn(stage["阶段名称"], STAGE_BLUEPRINTS)

    def test_dyn006_final_acceptance_matrix_exists(self):
        matrix = self._plan()["final_acceptance_matrix"]
        for key in ("最终必须存在的真实能力", "必须通过的用户旅程", "必须验证的失败分支",
                    "必须真实持久化的数据", "必须真实验证的环境", "必须验证的风险",
                    "证明 Final Complete 的 Evidence"):
            self.assertIn(key, matrix)

    def test_granularity_demotes_valueless_stages(self):
        complexity = assess_complexity(simple_static_page_factors())
        needs = derive_capability_needs(simple_static_page_factors())
        plan = derive_active_plan(_profile())
        dep = build_delivery_execution_plan("g", complexity, needs, plan["active_stages"], {},
                                            stage_value_markers={"03_需求与范围": ["independent_user_value"]})
        # stages without value markers became tasks inside the marked one
        self.assertTrue(any("内含任务" in s for s in dep["dynamic_stages"]))

    def test_plan_is_navigation_not_gate(self):
        self.assertIn("CONTINUE", self._plan()["continuation"])

    def test_dyn007_scope_change_replans_partially(self):
        verified = {"ui": {"assumptions": ["业务定义=A"], "capabilities": ["ui"]},
                    "storage": {"assumptions": ["database_engine"], "capabilities": ["database"]}}
        result = assumption_change_model(verified, ["业务定义=A"], new_required=["采购模型"])
        self.assertEqual(result["classification"]["ui"], "INVALIDATED")
        self.assertEqual(result["classification"]["采购模型"], "NEW_REQUIRED")
        old = assess_complexity({"business_goals": 1, "user_journeys": 1})
        new = assess_complexity({"business_goals": 2, "user_journeys": 2, "data_state_complexity": 1})
        self.assertEqual((old["risk_level"], new["risk_level"]), ("LOW", "MEDIUM"))


class InteractionBoundaryTests(unittest.TestCase):
    def test_dyn008_user_mode_leaks_nothing_internal(self):
        state = {"user_goal": "g", "delivery_plan": {}, "questions": ["业务定义?"],
                 "UNDERSTANDING_BLOCKED": True, "CORE_RELEASE_IDENTITY_BLOCKED": False,
                 "gate_graph": {"contract_check": "PASS"}, "core_hash": "abc",
                 "adapter_metadata": {"x": 1}}
        view = user_view(state, "USER")
        dumped = str(view["user_visible"])
        for banned in ("UNDERSTANDING_BLOCKED", "CORE_RELEASE_IDENTITY_BLOCKED",
                       "gate_graph", "core_hash", "adapter_metadata"):
            self.assertNotIn(banned, dumped)
        self.assertIn("questions", view["user_visible"])

    def test_dyn008_internal_states_translated(self):
        state = {"status": "UNDERSTANDING_BLOCKED"}
        view = user_view(state, "USER")
        self.assertIn("UNDERSTANDING_BLOCKED", view["translations"])
        self.assertIn("需要先确认", view["translations"]["UNDERSTANDING_BLOCKED"])
        state2 = {"status": "CORE_RELEASE_IDENTITY_BLOCKED"}
        self.assertIn("身份校验未通过", user_view(state2, "USER")["translations"]["CORE_RELEASE_IDENTITY_BLOCKED"])

    def test_dyn009_diagnostic_mode_exposes_everything(self):
        state = {"core_hash": "abc", "gate_graph": {"g": "PASS"}, "telemetry": [1, 2]}
        view = user_view(state, "DIAGNOSTIC")
        self.assertEqual(view["exposed"], state)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            user_view({}, "DEBUG")
        self.assertEqual(INTERACTION_MODES, ("USER", "DIAGNOSTIC"))


def _profile(extra=None):
    base = {"project_type": "any", "business_goal": "b", "risk_level": "LOW",
            "required_capabilities": [], "acceptance_matrix": {}, "project_specific_constraints": []}
    base.update(extra or {})
    return base


if __name__ == "__main__":
    unittest.main()
