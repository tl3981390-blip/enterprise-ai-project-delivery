#!/usr/bin/env python3
"""ORCH + FACT + CAP + STAGE + HUMAN + INSTALL — final systemic regressions (v1.7.1)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from delivery_planning_core import (  # noqa: E402
    assess_complexity, complexity_from_facts, compose_stages, derive_final_acceptance,
    make_fact_model, reason_capability_needs,
)
from plan_governance_core import (  # noqa: E402
    PlanAuthorityError, apply_human_plan, apply_plan_edit, check_plan_invariants,
    replan_respecting_locks,
)
from product_completion_core import derive_active_plan  # noqa: E402


class OrchestrationTruthTests(unittest.TestCase):
    def test_orch001_root_skill_no_fixed_lifecycle(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("生命周期阶段恒活", text)
        self.assertNotIn("生命周期恒活", text)
        self.assertIn("唯一编排真源", text)
        self.assertIn("compose_stages", text)

    def test_orch002_spec_no_fixed_lifecycle(self):
        text = (ROOT / "共享" / "references" / "PROJECT_ORCHESTRATION_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("RELIABILITY_INVARIANT != STAGE", text)
        self.assertIn("不存在「生命周期恒活阶段」这种固定序列", text)

    def test_orch003_single_planner_source(self):
        plan = derive_active_plan({"business_goal": "g", "required_capabilities": []})
        self.assertIn("compose_stages", plan["planner"])

    def test_orch005_capability_not_stage(self):
        facts = make_fact_model(goal="记账本", persistence=True, existing_database=True,
                                data={"entities": ["entry"]}, interface_types=[])
        caps = reason_capability_needs(facts)
        plan = compose_stages(facts, assess_complexity({}), caps)
        self.assertNotIn("database", [s["name"] for s in plan["stages"]])

    def test_orch007_entrypoint_calls_dynamic_planner(self):
        facts = make_fact_model(goal="跨平台桌面知识库", user_journeys=["导入", "搜索"],
                                interface_types=["desktop_gui"], persistence=True, existing_database=True)
        caps = reason_capability_needs(facts)
        complexity = complexity_from_facts(facts)
        plan = compose_stages(facts, complexity, caps)
        names = [s["name"] for s in plan["stages"]]
        self.assertIn("项目理解与目标锁定", names[0])
        self.assertIn("最终验收", names[-1])


class FactModelIntegrityTests(unittest.TestCase):
    def test_fact001_unknown_field_not_silently_dropped(self):
        model = make_fact_model(goal="g", custom_business_rule="必须双人复核")
        self.assertIn("custom_business_rule", model)
        self.assertIn("custom_business_rule", model["_extended_facts"])

    def test_fact002_extra_fact_kept(self):
        model = make_fact_model(goal="g", project_specific_metric="99.9%")
        self.assertTrue(model["project_specific_metric"]["extended"])

    def test_fact003_malformed_fact_not_capability_false(self):
        model = make_fact_model(goal="g")
        caps = reason_capability_needs(model)
        self.assertEqual(caps["capabilities"]["browser_acceptance"]["required"], "unknown")

    def test_fact004_complexity_from_facts(self):
        facts = make_fact_model(goal="g", user_journeys=["a", "b"], persistence=True,
                                existing_database=True, data={"entities": ["x", "y", "z"]})
        c = complexity_from_facts(facts)
        self.assertIn(c["risk_level"], ("LOW", "MEDIUM", "HIGH", "CRITICAL"))
        self.assertTrue(c["rationale"])


class CapabilityFactTests(unittest.TestCase):
    def test_cap001_data_exists_not_database(self):
        facts = make_fact_model(goal="CSV 分析", data={"entities": ["rows"]},
                                persistence=False, existing_database=False)
        self.assertIs(reason_capability_needs(facts)["capabilities"]["database"]["required"], False)

    def test_cap002_knowledge_ui_not_rag(self):
        facts = make_fact_model(goal="知识库文件管理 UI", interface_types=["web"],
                                retrieval_requirement={"state": "NOT_APPLICABLE", "value": None})
        self.assertIs(reason_capability_needs(facts)["capabilities"]["rag"]["required"], False)

    def test_cap003_workflow_word_not_agent(self):
        facts = make_fact_model(goal="审批流", workflow="submit -> review",
                                agent_autonomy_requirement={"state": "NOT_APPLICABLE", "value": None},
                                tool_execution_requirement={"state": "NOT_APPLICABLE", "value": None})
        self.assertIs(reason_capability_needs(facts)["capabilities"]["agent"]["required"], False)

    def test_cap004_external_system_not_mcp_gateway(self):
        facts = make_fact_model(goal="对接支付", external_systems=["payment_gateway"],
                                external_tool_permission_requirement={"state": "NOT_APPLICABLE", "value": None},
                                permissions={"state": "NOT_APPLICABLE", "value": None})
        self.assertIs(reason_capability_needs(facts)["capabilities"]["tool_permissions"]["required"], False)

    def test_cap005_generic_security_not_enterprise_governance(self):
        facts = make_fact_model(goal="个人密码本", security_requirements=["加密"],
                                enterprise_policy_present={"state": "NOT_APPLICABLE", "value": None},
                                approval_requirement={"state": "NOT_APPLICABLE", "value": None})
        self.assertIs(reason_capability_needs(facts)["capabilities"]["enterprise_governance"]["required"], False)

    def test_cap007_unknown_propagates(self):
        facts = make_fact_model(goal="g")
        self.assertEqual(reason_capability_needs(facts)["capabilities"]["browser_acceptance"]["required"],
                         "unknown")


class DynamicStageTests(unittest.TestCase):
    def test_stage001_work_units_produce_project_specific_stages(self):
        facts = make_fact_model(goal="库存管理系统", user_journeys=["下单", "扣减", "对账"],
                                interface_types=["web"], persistence=True, existing_database=True,
                                data={"entities": ["inventory", "order"]})
        caps = reason_capability_needs(facts)
        plan = compose_stages(facts, assess_complexity({"components": 3}), caps)
        names = [s["name"] for s in plan["stages"]]
        self.assertIn("项目理解与目标锁定", names[0])
        self.assertIn("最终验收", names[-1])
        self.assertNotIn("数据持久化与一致性验证", names)
        self.assertIs(caps["capabilities"]["database"]["required"], True)

    def test_stage002_capability_does_not_auto_create_stage(self):
        facts = make_fact_model(goal="静态页改字", interface_types=["web"], persistence=False,
                                existing_database=False)
        caps = reason_capability_needs(facts)
        plan = compose_stages(facts, assess_complexity({}), caps)
        self.assertLessEqual(plan["stage_count"], 3)


class HumanPlanRuntimeTests(unittest.TestCase):
    def test_human003_new_facts_trigger_recomputation(self):
        plan = apply_human_plan({"stages": [{"name": "需求确认", "goal": "确认", "acceptance": "owner"}]})
        out = replan_respecting_locks(plan, changed_assumptions=[], new_facts={"persistence": True})
        self.assertIn("persistence", out["new_facts_consumed"])

    def test_human004_verified_state_classified(self):
        verified = {"db_schema": {"assumptions": ["persistence_model"], "capabilities": ["database"]},
                    "ui": {"assumptions": ["layout"], "capabilities": ["ui"]}}
        out = apply_plan_edit(apply_human_plan({"stages": [{"name": "需求确认", "goal": "c", "acceptance": "a"}]}),
                              {"op": "modify", "actor": "HUMAN_EXPLICIT", "stage_name": "需求确认",
                               "patch": {"goal": "确认+冻结"}}, verified_state=verified)
        cls = out["verified_state_classification"]
        self.assertIn("preserved", cls)
        self.assertIn("invalidated", cls)

    def test_human005_affected_assumptions_real(self):
        plan = apply_human_plan({"stages": [{"name": "数据层", "goal": "g", "acceptance": "a",
                                             "capabilities": ["database"]}]})
        out = apply_plan_edit(plan, {"op": "modify", "actor": "HUMAN_EXPLICIT", "stage_name": "数据层",
                                     "patch": {"goal": "g2"}})
        self.assertIn("database_type", out["affected_assumptions"])
        self.assertNotIn("数据层", out["affected_assumptions"])

    def test_human011_replace_all_keeps_invariants(self):
        plan = {"stages": [{"name": "项目理解", "goal": "理解", "acceptance": "gate"},
                            {"name": "实现", "goal": "实现", "acceptance": "tests"},
                            {"name": "最终验收", "goal": "验收", "acceptance": "matrix"}]}
        out = apply_plan_edit(plan, {"op": "replace_all", "actor": "HUMAN_EXPLICIT",
                                     "patch": {"stages": [{"name": "自定义流程", "goal": "g",
                                                            "acceptance": "验收"}]}})
        # human replaces organization freely; the reliability check ADVISES on the missing
        # independent-acceptance control (it does not silently pass, and does not block the edit)
        self.assertFalse(out["reliability_check"]["pass"])
        self.assertTrue(any("missing_understanding_entry" in g for g in out["reliability_check"]["gaps"]))


class InstallResolutionTests(unittest.TestCase):
    def test_inst002_formal_zip_resolves_from_release(self):
        text = (ROOT / "docs" / "install.py").read_text(encoding="utf-8")
        self.assertIn("_github_release_asset_sha256", text)
        self.assertIn("release_manifest", text)

    def test_inst008_plan_governance_in_self_check(self):
        text = (ROOT / "docs" / "install.py").read_text(encoding="utf-8")
        self.assertIn("plan_governance_core.py", text)
        self.assertIn("delivery_planning_core.py", text)


if __name__ == "__main__":
    unittest.main()
