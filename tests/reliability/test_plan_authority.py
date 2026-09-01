#!/usr/bin/env python3
"""PLAN-001..012 — human plan authority regressions (v1.7.1, actor semantics)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from plan_governance_core import (  # noqa: E402
    AUTHORITY_ORDER, PlanAuthorityError, apply_human_plan, apply_plan_edit,
    check_plan_invariants, plan_authority_order, replan_respecting_locks,
)

HE = {"actor": "HUMAN_EXPLICIT"}
AI = {"actor": "AI_AUTOMATIC"}


def ai_plan():
    return {"stages": [
        {"name": "项目理解", "goal": "理解目标", "acceptance": "gate", "provenance": "AI_GENERATED",
         "assumptions": ["scope=A"], "capabilities": []},
        {"name": "数据层", "goal": "数据层", "acceptance": "db tests", "provenance": "AI_GENERATED",
         "assumptions": ["db=postgres"], "capabilities": ["database"]},
        {"name": "后端", "goal": "后端", "acceptance": "api tests", "provenance": "AI_GENERATED",
         "capabilities": []},
        {"name": "前端", "goal": "前端", "acceptance": "ui tests", "provenance": "AI_GENERATED",
         "capabilities": ["browser_acceptance"]},
        {"name": "最终验收", "goal": "独立验收", "acceptance": "matrix", "provenance": "AI_GENERATED",
         "capabilities": []},
    ]}


class HumanPlanAuthorityTests(unittest.TestCase):
    def test_authority_order(self):
        planes = plan_authority_order()
        self.assertEqual(planes["authority_plane"][0], "AUTHORIZED_HUMAN_DECISIONS")
        self.assertEqual(planes["authority_plane"][-1], "AI_GENERATED_DELIVERY_PLAN")
        self.assertIn("NO_FAKE_PASS", planes["integrity_plane"])

    def test_plan001_user_can_remove_stage(self):
        out = apply_plan_edit(ai_plan(), {"op": "remove", "stage_name": "前端", **HE})
        self.assertNotIn("前端", [s["name"] for s in out["stages"]])
        checks = [c for s in out["stages"] for c in s.get("checks", [])]
        checks += [s for s in out["stages"] if s.get("class") == "CHECK"]
        self.assertTrue(any("前端" in str(c) for c in checks))

    def test_plan002_user_can_add_stage(self):
        out = apply_plan_edit(ai_plan(), {"op": "add", "patch": {"name": "安全评审", "goal": "安全",
                                                                 "acceptance": "security checklist"}, **HE})
        self.assertIn("安全评审", [s["name"] for s in out["stages"]])
        self.assertEqual(out["stages"][-1]["provenance"], "HUMAN_PROVIDED")

    def test_plan003_user_can_reorder(self):
        out = apply_plan_edit(ai_plan(), {"op": "reorder",
                                          "new_order": ["项目理解", "前端", "后端", "数据层", "最终验收"], **HE})
        self.assertEqual([s["name"] for s in out["stages"]][:4], ["项目理解", "前端", "后端", "数据层"])

    def test_plan004_user_can_merge(self):
        out = apply_plan_edit(ai_plan(), {"op": "merge", "stage_name": "数据层", "merge_with": "后端",
                                          "target": "数据与后端", **HE})
        names = [s["name"] for s in out["stages"]]
        self.assertNotIn("数据层", names)
        self.assertNotIn("后端", names)
        merged = next(s for s in out["stages"] if s["name"] == "数据与后端")
        self.assertEqual(merged["provenance"], "HUMAN_MODIFIED")

    def test_plan005_user_can_split(self):
        out = apply_plan_edit(ai_plan(), {"op": "split", "stage_name": "数据层",
                                          "split_into": [{"name": "schema", "goal": "建模"},
                                                          {"name": "migration", "goal": "迁移"}], **HE})
        names = [s["name"] for s in out["stages"]]
        self.assertIn("schema", names)
        self.assertIn("migration", names)

    def test_plan010_remove_stage_rehomes_obligation(self):
        out = apply_plan_edit(ai_plan(), {"op": "remove", "stage_name": "数据层", **HE})
        self.assertTrue(out["reliability_check"]["pass"])
        checks = [c for s in out["stages"] for c in s.get("checks", [])]
        checks += [s for s in out["stages"] if s.get("class") == "CHECK"]
        self.assertTrue(checks)

    def test_plan011_ai_advises_never_overrides(self):
        plan = ai_plan()
        plan["stages"] = [s for s in plan["stages"] if s["name"] != "最终验收"]
        check = check_plan_invariants(plan)
        self.assertTrue(check["pass"])
        self.assertEqual(check["gaps"], [])

    def test_plan012_provenance_preserved(self):
        out = apply_plan_edit(ai_plan(), {"op": "modify", "stage_name": "后端",
                                          "patch": {"goal": "后端+缓存"}, **HE})
        backend = next(s for s in out["stages"] if s["name"] == "后端")
        self.assertEqual(backend["provenance"], "HUMAN_MODIFIED")
        self.assertEqual(backend["last_modified_by"], "HUMAN_EXPLICIT")
        self.assertTrue(backend["history"])


class HumanPlanAndEnterpriseTests(unittest.TestCase):
    def test_plan006_enterprise_existing_plan_is_base(self):
        human = {"source": "enterprise",
                 "stages": [{"name": "需求确认", "goal": "确认", "acceptance": "owner"},
                            {"name": "开发", "goal": "实现", "acceptance": "tests"},
                            {"name": "上线", "goal": "发布", "acceptance": "deploy record"}]}
        out = apply_human_plan(human)
        self.assertEqual(out["authority"], "HUMAN_PLAN_KEPT_AI_ADVISORY_ONLY")
        names = [s["name"] for s in out["stages"]]
        self.assertEqual(names, ["需求确认", "开发", "上线"])
        self.assertEqual(next(s for s in out["stages"] if s["name"] == "需求确认")["provenance"],
                         "ENTERPRISE_REQUIRED")

    def test_plan007_replan_never_stealth_restores_human_content(self):
        plan = apply_human_plan({"stages": [{"name": "需求确认", "goal": "确认", "acceptance": "owner"},
                                            {"name": "开发", "goal": "实现", "acceptance": "tests"}]})
        replanned = replan_respecting_locks(plan, changed_assumptions=["db=postgres"])
        self.assertTrue(replanned["human_locks_respected"])
        self.assertIn("需求确认", replanned["locked_preserved"])

    def test_plan008_lock_blocks_ai_not_owner(self):
        plan = ai_plan()
        plan["stages"][2]["locked"] = True
        with self.assertRaises(PlanAuthorityError):
            apply_plan_edit(plan, {"op": "modify", "stage_name": "后端", "patch": {"goal": "改"}, **AI})
        out = apply_plan_edit(plan, {"op": "modify", "stage_name": "后端", "patch": {"goal": "改"}, **HE})
        self.assertEqual(next(s for s in out["stages"] if s["name"] == "后端")["goal"], "改")

    def test_plan009_edit_reports_real_assumptions_not_stage_name(self):
        out = apply_plan_edit(ai_plan(), {"op": "modify", "stage_name": "数据层",
                                          "patch": {"goal": "数据层+分库"}, **HE})
        self.assertIn("db=postgres", out["affected_assumptions"])
        self.assertNotIn("数据层", out["affected_assumptions"])


if __name__ == "__main__":
    unittest.main()
