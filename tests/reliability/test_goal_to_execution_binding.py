#!/usr/bin/env python3
"""Product-behaviour regressions for goal understanding and capability execution."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from delivery_runtime import (record_capability_result, record_evidence,
                              record_recovery, request_capability_invocation,
                              start_from_understanding)
from understanding_core import apply_answer, begin_understanding, propose_inference


def answer_all(session):
    values = {
        "users": ["我和家里人"],
        "user_journeys": ["添加候选菜并投票后确定今天吃什么"],
        "final_deliverable": "电脑上可使用的家庭点菜单",
        "acceptance_requirements": ["可添加删除菜、投票并确定结果"],
        "explicit_constraints": ["先只支持本机电脑"],
        "permissions": ["只允许本地项目写入"],
    }
    while not session["gate_pass"]:
        for question in list(session["questions"]):
            fact = question["fact"]
            session = apply_answer(session, question_id=question["question_id"],
                                   fact_updates={fact: values[fact]})
    return session


class SparseGoalUnderstandingTests(unittest.TestCase):
    def test_sparse_goal_requires_consequential_questions_and_binds_answers(self):
        session = begin_understanding(raw_goal="我想做一个家庭点菜单。")
        self.assertFalse(session["gate_pass"])
        self.assertLessEqual(len(session["questions"]), 4)
        self.assertTrue(all(q["decision_impacts"] and q["why"] for q in session["questions"]))
        session = answer_all(session)
        delivery = start_from_understanding(understanding=session)
        self.assertEqual(delivery["facts"]["users"]["provenance"], "USER_CONFIRMED")
        planned_work = [w for item in (delivery["plan"]["stages"] + delivery["plan"]["tasks"])
                        for w in item.get("work", [])]
        self.assertIn("添加候选菜并投票后确定今天吃什么", planned_work)

    def test_ai_inference_cannot_silently_pass(self):
        session = begin_understanding(raw_goal="我想做一个家庭点菜单。")
        session = propose_inference(session, fact="final_deliverable", value="手机 App",
                                    rationale="model guess")
        self.assertFalse(session["gate_pass"])
        self.assertEqual(session["facts"]["final_deliverable"]["state"], "PROPOSED")

    def test_existing_project_requires_project_reconstruction(self):
        session = begin_understanding(raw_goal="继续把这个项目做完。", mode="EXISTING_PROJECT")
        self.assertIn("existing_state", session["blocking_unknowns"])
        self.assertIn("existing_evidence", session["blocking_unknowns"])


class CapabilityExecutionBindingTests(unittest.TestCase):
    def _delivery(self):
        understanding = answer_all(begin_understanding(raw_goal="生成报价并完成必要审查。"))
        registry = {"legal_review": {"maturity": 9, "validation_status": "VALIDATED",
                    "source_identity_verified": True, "compatible": True,
                    "license_compatible": True, "permission_granted": True}}
        understanding["facts"]["required_capabilities"] = {
            "state": "ACTIVE", "value": ["legal_review"], "source": "USER_CONFIRMED",
            "evidence": "answer", "history": [{"event_id": "cap", "state": "ACTIVE"}]}
        understanding["facts"]["work_units"] = {
            "state": "ACTIVE", "value": [{
                "name": "quote-review", "goal": "审查报价条款", "class": "TASK",
                "work": ["核对合同和价格"], "capabilities": ["legal_review"],
                "acceptance": "审查工具结果可追溯",
            }], "source": "USER_CONFIRMED", "evidence": "answer",
            "history": [{"event_id": "work", "state": "ACTIVE"}]}
        return start_from_understanding(understanding=understanding, capability_registry=registry)

    def _evidence(self, delivery, evidence_id, *, status="PASS"):
        return record_evidence(delivery, evidence={
            "evidence_id": evidence_id, "type": "TEST_RESULT", "producer": "TEST_RUNNER",
            "source_ref": f"pytest://{evidence_id}", "candidate_id": delivery["candidate_id"],
            "work_id": "quote-review", "observed_at": "2026-09-01T00:00:00+00:00",
            "content_hash": (evidence_id.encode().hex() + "0" * 64)[:64],
            "status": status, "session_revision": delivery["revision"],
            "dependencies": [], "acceptance_items": [],
        })

    def test_resolution_is_bound_to_invocation_work_and_evidence(self):
        delivery = self._delivery()
        delivery = request_capability_invocation(delivery, work_id="quote-review",
                                                 capability="legal_review",
                                                 input_payload={"document": "quote-1"})
        iid = delivery["capability_invocations"][0]["invocation_id"]
        delivery = self._evidence(delivery, "tool-result")
        delivery = record_capability_result(delivery, invocation_id=iid, status="PASS",
                                            output={"approved": True},
                                            evidence_ids=["tool-result"])
        self.assertEqual(delivery["verified_state"]["quote-review"]["status"], "PASS")

    def test_unready_or_unauthorized_capability_cannot_invoke(self):
        understanding = answer_all(begin_understanding(raw_goal="生成报价并完成必要审查。"))
        understanding["facts"]["required_capabilities"] = {
            "state": "ACTIVE", "value": ["legal_review"], "source": "USER_CONFIRMED",
            "evidence": "answer", "history": [{"event_id": "cap", "state": "ACTIVE"}]}
        registry = {"legal_review": {"validation_status": "VALIDATED",
                    "source_identity_verified": True, "compatible": True,
                    "license_compatible": True, "permission_granted": False}}
        delivery = start_from_understanding(understanding=understanding,
                                            capability_registry=registry)
        work_id = next(item["name"] for bucket in ("stages", "tasks", "checks")
                       for item in delivery["plan"].get(bucket, []) if item.get("name"))
        with self.assertRaises(PermissionError):
            request_capability_invocation(delivery, work_id=work_id, capability="legal_review",
                                          input_payload={})

    def test_recovery_requires_regression_and_has_budget(self):
        delivery = self._delivery()
        delivery = request_capability_invocation(delivery, work_id="quote-review",
                                                 capability="legal_review", input_payload={})
        iid = delivery["capability_invocations"][0]["invocation_id"]
        delivery = self._evidence(delivery, "timeout", status="FAIL")
        delivery = record_capability_result(delivery, invocation_id=iid, status="FAIL",
                                            output=None, evidence_ids=["timeout"])
        fid = delivery["failures"][0]["failure_id"]
        delivery = self._evidence(delivery, "fixed")
        delivery = self._evidence(delivery, "blocker-pass")
        delivery = record_recovery(delivery, failure_id=fid, action="retry after fix",
                                   recovery_evidence_ids=["fixed"],
                                   blocker_evidence_ids=["blocker-pass"])
        self.assertEqual(delivery["status"], "RECOVERING")
        delivery = self._evidence(delivery, "regression")
        delivery = record_recovery(delivery, failure_id=fid, action="verify regression",
                                   recovery_evidence_ids=["fixed"],
                                   blocker_evidence_ids=["blocker-pass"],
                                   regression_evidence_ids=["regression"])
        self.assertEqual(delivery["status"], "EXECUTING")


if __name__ == "__main__":
    unittest.main()
