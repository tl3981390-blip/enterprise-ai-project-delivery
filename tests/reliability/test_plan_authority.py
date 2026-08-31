#!/usr/bin/env python3
"""PLAN-001..012 — human plan authority regressions (v1.7.0)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from plan_governance_core import (  # noqa: E402
    AUTHORITY_ORDER, PlanAuthorityError, apply_human_plan, apply_plan_edit,
    check_plan_invariants, plan_authority_order, replan_respecting_locks,
)


def ai_plan():
    return {"stages": [
        {"name": "项目理解", "goal": "理解目标", "acceptance": "gate", "provenance": "AI_GENERATED",
         "assumptions": ["scope=A"]},
        {"name": "数据层", "goal": "数据层", "acceptance": "db tests", "provenance": "AI_GENERATED",
         "assumptions": ["db=postgres"]},
        {"name": "后端", "goal": "后端", "acceptance": "api tests", "provenance": "AI_GENERATED"},
        {"name": "前端", "goal": "前端", "acceptance": "ui tests", "provenance": "AI_GENERATED"},
        {"name": "最终验收", "goal": "独立验收", "acceptance": "matrix", "provenance": "AI_GENERATED"},
    ]}


class HumanPlanAuthorityTests(unittest.TestCase):
    def test_authority_order(self):
        self.assertEqual(plan_authority_order()[0], "CORE_RELIABILITY_INVARIANTS")
        self.assertEqual(plan_authority_order()[-1], "AI_GENERATED_DELIVERY_PLAN")

    def test_plan001_user_can_remove_stage(self):
        out = apply_plan_edit(ai_plan(), {"op": "remove", "stage_name": "前端"})
        names = [s["name"] for s in out["stages"]]
        self.assertNotIn("前端", names)
        # its acceptance obligation is re-homed, not lost
        last = out["stages"][-1]
        self.assertTrue(any(c.get("from_removed_stage") == "前端" for c in last.get("checks", [])))

    def test_plan002_user_can_add_stage(self):
        out = apply_plan_edit(ai_plan(), {"op": "add", "patch": {"name": "安全评审", "goal": "安全",
                                                                  "acceptance": "security checklist"}})
        self.assertIn("安全评审", [s["name"] for s in out["stages"]])
        self.assertEqual(out["stages"][-1]["provenance"], "HUMAN_PROVIDED")

    def test_plan003_user_can_reorder(self):
        out = apply_plan_edit(ai_plan(), {"op": "reorder",
                                          "new_order": ["项目理解", "前端", "后端", "数据层", "最终验收"]})
        self.assertEqual([s["name"] for s in out["stages"]][:4], ["项目理解", "前端", "后端", "数据层"])

    def test_plan004_user_can_merge(self):
        out = apply_plan_edit(ai_plan(), {"op": "merge", "stage_name": "数据层", "merge_with": "后端",
                                          "target": "数据与后端"})
        names = [s["name"] for s in out["stages"]]
        self.assertNotIn("数据层", names)
        self.assertNotIn("后端", names)
        self.assertIn("数据与后端", names)
        merged = next(s for s in out["stages"] if s["name"] == "数据与后端")
        self.assertEqual(merged["provenance"], "HUMAN_MODIFIED")

    def test_plan005_user_can_split(self):
        out = apply_plan_edit(ai_plan(), {"op": "split", "stage_name": "数据层",
                                          "split_into": [{"name": "schema", "goal": "建模"},
                                                          {"name": "migration", "goal": "迁移"}]})
        names = [s["name"] for s in out["stages"]]
        self.assertIn("schema", names)
        self.assertIn("migration", names)
        self.assertNotIn("数据层", names)

    def test_plan010_remove_required_stage_rehomes_reliability(self):
        # human deletes a stage; organization is free, but its reliability obligation survives
        out = apply_plan_edit(ai_plan(), {"op": "remove", "stage_name": "数据层"})
        self.assertTrue(out["reliability_check"]["pass"])  # organization is free
        last = out["stages"][-1]
        self.assertTrue(last.get("checks"))  # the removed stage's evidence/acceptance carried over

    def test_plan011_ai_advises_never_overrides(self):
        # removing the final acceptance stage leaves a gap; AI advises, does not block the edit
        plan = ai_plan()
        plan["stages"] = [s for s in plan["stages"] if s["name"] != "最终验收"]
        check = check_plan_invariants(plan)
        self.assertFalse(check["pass"])
        self.assertIn("missing_final_acceptance", check["gaps"][0])

    def test_plan012_provenance_preserved(self):
        out = apply_plan_edit(ai_plan(), {"op": "modify", "stage_name": "后端", "patch": {"goal": "后端+缓存"}})
        backend = next(s for s in out["stages"] if s["name"] == "后端")
        self.assertEqual(backend["provenance"], "HUMAN_MODIFIED")
        others = [s for s in out["stages"] if s["name"] != "后端"]
        self.assertTrue(all(s["provenance"] == "AI_GENERATED" for s in others))


class HumanPlanAndEnterpriseTests(unittest.TestCase):
    def test_plan006_enterprise_existing_plan_is_base(self):
        human = {"source": "enterprise",
                 "stages": [{"name": "需求确认", "goal": "确认", "acceptance": "owner"},
                            {"name": "开发", "goal": "实现", "acceptance": "tests"},
                            {"name": "上线", "goal": "发布", "acceptance": "deploy record"}]}
        out = apply_human_plan(human)
        self.assertEqual(out["authority"], "HUMAN_PLAN_KEPT_AI_ADVISORY_ONLY")
        # enterprise stages keep their order and content; AI only ADDS the missing controls
        names = [s["name"] for s in out["stages"]]
        self.assertEqual(names[0], "项目理解与目标锁定")   # inserted reliability control first
        self.assertEqual(names[1], "需求确认")             # enterprise plan preserved next
        self.assertEqual(names[2], "开发")
        self.assertEqual(names[3], "上线")
        self.assertEqual(names[4], "最终验收")
        ent = next(s for s in out["stages"] if s["name"] == "需求确认")
        self.assertEqual(ent["provenance"], "ENTERPRISE_REQUIRED")

    def test_plan007_replan_never_stealth_restores_human_content(self):
        plan = apply_human_plan({"stages": [{"name": "需求确认", "goal": "确认", "acceptance": "owner"},
                                            {"name": "开发", "goal": "实现", "acceptance": "tests"}]})
        replanned = replan_respecting_locks(plan, changed_assumptions=["db=postgres"])
        self.assertTrue(replanned["human_locks_respected"])
        self.assertIn("需求确认", replanned["locked_preserved"])  # human content never touched

    def test_plan008_locked_stage_not_auto_modified(self):
        plan = ai_plan()
        plan["stages"][2]["locked"] = True
        with self.assertRaises(PlanAuthorityError):
            apply_plan_edit(plan, {"op": "modify", "stage_name": "后端", "patch": {"goal": "改"}})

    def test_plan009_human_edit_only_invalidates_affected(self):
        out = apply_plan_edit(ai_plan(), {"op": "modify", "stage_name": "数据层",
                                          "patch": {"goal": "数据层+分库"}})
        self.assertEqual(out["affected_assumptions"], ["数据层"])  # only the edited stage


if __name__ == "__main__":
    unittest.main()
