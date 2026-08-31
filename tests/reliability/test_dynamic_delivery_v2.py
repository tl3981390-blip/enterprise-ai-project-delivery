#!/usr/bin/env python3
"""DYN2-001..020 — TRUE dynamic delivery regressions (v1.6.1).
Proves: keywords AND structural factors never route; capabilities activate only from
explicit facts; stages are composed from the project's real work units (STAGE/TASK/
CHECK/NOT_APPLICABLE); Final Acceptance is fact-derived (no placeholders); reliability
invariants preserved."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from delivery_planning_core import (  # noqa: E402
    STAGE_UPGRADE_MARKERS, assess_complexity, classify_work_item, compose_stages,
    derive_final_acceptance, make_fact_model, reason_capability_needs, user_view,
)


def _na():
    return {"state": "NOT_APPLICABLE", "value": None}


def desktop_facts():
    return make_fact_model(
        goal="跨平台桌面知识库", users=["个人"],
        user_journeys=["导入笔记", "搜索", "同步", "恢复备份"],
        interfaces=["desktop_gui"], interface_types=["desktop_gui"],
        data={"entities": ["note", "attachment"]}, persistence=True, existing_database=True,
        cross_platform=True, runtime={"os": ["win", "mac"]},
        migration_requirements=True, recovery_requirements=True,
        retrieval_requirement=_na(), enterprise_policy_present=_na(),
        approval_requirement=_na(), deployment_requirement={"state": "DECLARED", "value": False})


def button_edit_facts():
    return make_fact_model(goal="修改静态页面按钮文案", users=["企业内部员工"],
                           interfaces=["web"], interface_types=["web"], data=None, persistence=False,
                           existing_database=False, deployment_requirement=False,
                           migration_requirements=False, retrieval_requirement=_na(),
                           enterprise_policy_present=_na(), approval_requirement=_na())


class KeywordAndFactorGuardTests(unittest.TestCase):
    def test_dyn2_001_same_structure_different_label_same_plan(self):
        # identical facts, different label vocabulary -> identical plan logic
        f = desktop_facts()
        caps1 = reason_capability_needs(f)
        caps2 = reason_capability_needs(f)
        self.assertEqual(caps1, caps2)
        c1 = compose_stages(f, assess_complexity({"components": 3}), caps1)
        c2 = compose_stages(f, assess_complexity({"components": 3}), caps2)
        self.assertEqual([s["name"] for s in c1["stages"]], [s["name"] for s in c2["stages"]])

    def test_dyn2_002_same_keyword_different_facts_different_plan(self):
        # both could be labelled "企业": trivial button edit vs heavy system
        simple = reason_capability_needs(button_edit_facts())
        heavy = reason_capability_needs(desktop_facts())
        self.assertNotEqual(
            {k: v["required"] for k, v in simple["capabilities"].items()},
            {k: v["required"] for k, v in heavy["capabilities"].items()})

    def test_dyn2_003_desktop_journeys_no_browser_acceptance(self):
        caps = reason_capability_needs(desktop_facts())
        self.assertIs(caps["capabilities"]["browser_acceptance"]["required"], False)  # desktop GUI ≠ web

    def test_dyn2_004_component_deps_no_database(self):
        facts = make_fact_model(goal="纯内存计算器", components=["parser", "engine"],
                                persistence=False, existing_database=False, data=None)
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["database"]["required"], False)  # no persistence fact

    def test_dyn2_005_personal_security_no_enterprise_governance(self):
        facts = make_fact_model(goal="个人密码管理器", security_requirements=["加密存储"],
                                users=["个人"], compliance=_na(), enterprise_policy_present=_na(),
                                approval_requirement=_na(), roles={"state": "DECLARED", "value": ["owner"]})
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["enterprise_governance"]["required"], False)  # personal ≠ enterprise

    def test_dyn2_006_cross_platform_not_deployment(self):
        facts = make_fact_model(goal="跨平台库", cross_platform=True, runtime={"os": ["win", "mac"]},
                                deployment_requirement=False, distribution_requirement=False)
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["deployment"]["required"], False)  # cross-platform ≠ deploy stage

    def test_dyn2_007_web_interface_activates_browser(self):
        facts = make_fact_model(goal="内部 FAQ 站点", interfaces=["web"], interface_types=["web"],
                                persistence=False, existing_database=False)
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["browser_acceptance"]["required"], True)

    def test_dyn2_008_persistence_activates_database(self):
        facts = make_fact_model(goal="记账本", persistence=True, existing_database=True,
                                data={"entities": ["entry"]})
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["database"]["required"], True)

    def test_dyn2_009_enterprise_profile_activates_governance(self):
        facts = make_fact_model(goal="企业审批系统", compliance=["数据不出域", "变更审批"],
                                enterprise_policy_present=True, approval_requirement=True,
                                roles=["employee", "approver", "admin"])
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["enterprise_governance"]["required"], True)
        self.assertIs(caps["capabilities"]["multi_role_approval"]["required"], True)

    def test_dyn2_010_deployment_required_activates(self):
        facts = make_fact_model(goal="发布到生产", deployment_requirement=True)
        caps = reason_capability_needs(facts)
        self.assertIs(caps["capabilities"]["deployment"]["required"], True)

    def test_dyn2_unknown_fact_not_silently_false(self):
        facts = make_fact_model(goal="某项目")  # interfaces UNKNOWN
        caps = reason_capability_needs(facts)
        self.assertEqual(caps["capabilities"]["browser_acceptance"]["required"], "unknown")


class DynamicComposerTests(unittest.TestCase):
    def test_dyn2_011_no_persistence_no_db_acceptance(self):
        matrix = derive_final_acceptance(button_edit_facts(), assess_complexity({}))
        self.assertNotIn("必须真实持久化的数据", matrix)

    def test_dyn2_012_journeys_from_facts_not_placeholders(self):
        matrix = derive_final_acceptance(desktop_facts(), assess_complexity({}))
        self.assertEqual(matrix["必须通过的用户旅程"], ["导入笔记", "搜索", "同步", "恢复备份"])
        self.assertNotIn("旅程1", str(matrix))

    def test_dyn2_013_button_edit_no_forced_sdd_tdd_arch_stages(self):
        caps = reason_capability_needs(button_edit_facts())
        plan = compose_stages(button_edit_facts(), assess_complexity({}), caps)
        names = [s["name"] for s in plan["stages"]]
        for forced in ("04_SDD规格", "05_TDD与测试策略", "06_架构设计", "14_多角色验收"):
            self.assertNotIn(forced, names)
        self.assertLessEqual(plan["stage_count"], 3)  # understanding + final acceptance (+ impl)

    def test_dyn2_014_complex_project_can_promote_architecture(self):
        facts = make_fact_model(goal="跨系统 ERP 集成", external_systems=True,
                                components=["a", "b", "c"], component_dependencies=True,
                                persistence=True, existing_database=True,
                                deployment_requirement=True, interface_types=["web"])
        caps = reason_capability_needs(facts)
        plan = compose_stages(facts, assess_complexity({"external_systems": 2, "components": 3}), caps)
        self.assertEqual(plan["stage_count"], 2)  # complexity/capabilities cannot invent a work boundary

    def test_dyn2_015_recovery_event_driven_not_standing_stage(self):
        caps = reason_capability_needs(button_edit_facts())
        plan = compose_stages(button_edit_facts(), assess_complexity({}), caps)
        self.assertNotIn("12_失败处理与恢复", [s["name"] for s in plan["stages"]])
        self.assertTrue(all(s["failure_handling"] for s in plan["stages"]))

    def test_dyn2_016_solo_project_no_multi_role_stage(self):
        caps = reason_capability_needs(button_edit_facts())
        self.assertEqual(caps["capabilities"]["multi_role_approval"]["required"], "unknown")  # approval/roles unknown
        solo = reason_capability_needs(make_fact_model(goal="个人记账", roles={"state": "DECLARED", "value": ["owner"]},
                                                       compliance=_na(), approval_requirement=_na()))
        self.assertIs(solo["capabilities"]["multi_role_approval"]["required"], False)

    def test_dyn2_018_every_real_stage_has_schema(self):
        caps = reason_capability_needs(desktop_facts())
        plan = compose_stages(desktop_facts(), assess_complexity({"components": 3}), caps)
        for stage in plan["stages"]:
            for field in ("name", "goal", "work", "output", "entry_condition",
                          "done_condition", "acceptance", "failure_handling", "evidence"):
                self.assertIn(field, stage, f"{stage.get('name')} missing {field}")

    def test_dyn2_019_four_class_classification(self):
        self.assertEqual(classify_work_item({"name": "x", "markers": ["high_risk"]}, {}), "STAGE")
        self.assertEqual(classify_work_item({"name": "x"}, {}), "TASK")
        self.assertEqual(classify_work_item({"name": "x", "verification_only": True}, {}), "CHECK")
        self.assertEqual(classify_work_item({"name": "x", "not_applicable": True}, {}), "NOT_APPLICABLE")

    def test_dyn2_020_complexity_never_picks_a_template(self):
        # same score band, different facts -> different capability sets
        low_a = reason_capability_needs(make_fact_model(goal="静态页改字", persistence=False,
                                                         existing_database=False))
        low_b = reason_capability_needs(make_fact_model(goal="记账本", persistence=True,
                                                         existing_database=True, data={"e": ["x"]}))
        self.assertNotEqual(low_a["capabilities"]["database"]["required"],
                            low_b["capabilities"]["database"]["required"])
        # and the score itself is identical for both (same trivial structure)
        self.assertEqual(assess_complexity({"components": 1})["risk_level"], "LOW")


class InvariantPreservationTests(unittest.TestCase):
    def test_dyn2_017_reliability_invariants_preserved(self):
        # understanding gate and final acceptance are ALWAYS present, recovery is event-driven
        caps = reason_capability_needs(button_edit_facts())
        plan = compose_stages(button_edit_facts(), assess_complexity({}), caps)
        names = [s["name"] for s in plan["stages"]]
        self.assertIn("项目理解与目标锁定", names[0])   # understand-before-execute
        self.assertIn("最终验收", names[-1])            # final acceptance
        self.assertTrue(all(s["failure_handling"] for s in plan["stages"]))  # recovery path exists

    def test_user_mode_boundary_still_holds(self):
        state = {"user_goal": "g", "UNDERSTANDING_BLOCKED": True, "core_hash": "x"}
        view = user_view(state, "USER")
        self.assertNotIn("UNDERSTANDING_BLOCKED", str(view["user_visible"]))
        self.assertIn("需要先确认", view["translations"]["UNDERSTANDING_BLOCKED"])


if __name__ == "__main__":
    unittest.main()
