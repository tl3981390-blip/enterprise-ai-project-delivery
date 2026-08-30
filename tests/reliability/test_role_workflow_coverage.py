#!/usr/bin/env python3
"""PATCH-EV-003 ROLE_WORKFLOW_E2E_COVERAGE_GATE regressions, derived from ERL Round 1 + Phase B real failures."""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))
from check_role_workflow_coverage import check


def erl_workflow():
    """Derived from Enterprise Review Lab's real workflow: the two transitions real journeys caught missing."""
    return {
        "roles": ["employee", "reviewer", "approver", "admin"],
        "transitions": [
            {"from": "SUBMITTED", "to": "PENDING_REVIEW", "roles": ["employee"], "required": True},
            {"from": "PENDING_REVIEW", "to": "CHANGES_REQUESTED", "roles": ["reviewer"], "required": True},
            {"from": "CHANGES_REQUESTED", "to": "PENDING_REVIEW", "roles": ["employee"], "required": True},
            {"from": "PENDING_REVIEW", "to": "APPROVED", "roles": ["reviewer", "approver"], "required": True},
            {"from": "PENDING_REVIEW", "to": "REJECTED", "roles": ["approver"], "required": True},
            {"from": "ANY", "to": "ADMIN_SURFACE", "roles": ["admin"], "required": True},
            {"from": "ANY", "to": "OUTSIDER_BLOCKED", "roles": ["outsider"], "required": False},
        ],
    }


def journey(jid, covers):
    return {"journey_id": jid, "covers": [{"from": f, "to": t, "role": r} for f, t, r in covers]}


class RoleWorkflowCoverageTests(unittest.TestCase):
    def test_full_coverage_passes(self):
        journeys = [
            journey("J1", [("SUBMITTED", "PENDING_REVIEW", "employee"), ("CHANGES_REQUESTED", "PENDING_REVIEW", "employee")]),
            journey("J2", [("PENDING_REVIEW", "CHANGES_REQUESTED", "reviewer"), ("PENDING_REVIEW", "APPROVED", "approver")]),
            journey("J3", [("PENDING_REVIEW", "APPROVED", "reviewer")]),
            journey("J4", [("PENDING_REVIEW", "REJECTED", "approver"), ("ANY", "ADMIN_SURFACE", "admin")]),
        ]
        result = check(erl_workflow(), journeys)
        self.assertEqual(result["status"], "PASS"); self.assertEqual(result["missing"], [])

    def test_phase_b_admin_surface_gap_is_caught(self):
        """UJ-02 recurrence: admin surface journey missing -> gate FAILs exactly that transition."""
        journeys = [
            journey("J1", [("SUBMITTED", "PENDING_REVIEW", "employee")]),
            journey("J2", [("PENDING_REVIEW", "CHANGES_REQUESTED", "reviewer"), ("PENDING_REVIEW", "APPROVED", "approver")]),
            journey("J2b", [("CHANGES_REQUESTED", "PENDING_REVIEW", "employee")]),
            journey("J5", [("PENDING_REVIEW", "REJECTED", "approver")]),
        ]
        result = check(erl_workflow(), journeys)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["missing"], [{"from": "ANY", "to": "ADMIN_SURFACE", "roles": ["admin"]}])

    def test_round1_cross_session_review_discovery_gap_is_caught(self):
        """Round 1 / UJ-01: employee-only smoke left every later transition uncovered."""
        result = check(erl_workflow(), [journey("smoke", [("SUBMITTED", "PENDING_REVIEW", "employee")])])
        self.assertEqual(result["status"], "FAIL")
        missing_pairs = {(m["from"], m["to"]) for m in result["missing"]}
        self.assertIn(("PENDING_REVIEW", "APPROVED"), missing_pairs)

    def test_wrong_role_does_not_cover(self):
        journeys = [journey("J", [("SUBMITTED", "PENDING_REVIEW", "employee"), ("PENDING_REVIEW", "CHANGES_REQUESTED", "employee")])]
        result = check(erl_workflow(), journeys)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(m["from"] == "PENDING_REVIEW" and m["to"] == "CHANGES_REQUESTED" for m in result["missing"]))

    def test_optional_transitions_not_enforced(self):
        journeys = [
            journey("J1", [("SUBMITTED", "PENDING_REVIEW", "employee"), ("CHANGES_REQUESTED", "PENDING_REVIEW", "employee")]),
            journey("J2", [("PENDING_REVIEW", "CHANGES_REQUESTED", "reviewer"), ("PENDING_REVIEW", "APPROVED", "approver")]),
            journey("J4", [("PENDING_REVIEW", "REJECTED", "approver"), ("ANY", "ADMIN_SURFACE", "admin")]),
        ]
        result = check(erl_workflow(), journeys)
        self.assertEqual(result["status"], "PASS")

    def test_empty_journeys_fail_with_all_missing(self):
        result = check(erl_workflow(), [])
        self.assertEqual(result["status"], "FAIL"); self.assertEqual(result["covered"], 0); self.assertEqual(result["required"], 6)

    def test_multi_role_transition_accepts_any_listed_role(self):
        """PENDING_REVIEW->APPROVED lists reviewer+approver; either role covering it counts (J3 uses reviewer)."""
        journeys = [
            journey("J1", [("SUBMITTED", "PENDING_REVIEW", "employee"), ("CHANGES_REQUESTED", "PENDING_REVIEW", "employee")]),
            journey("J2", [("PENDING_REVIEW", "CHANGES_REQUESTED", "reviewer")]),
            journey("J3", [("PENDING_REVIEW", "APPROVED", "reviewer")]),
            journey("J4", [("PENDING_REVIEW", "REJECTED", "approver"), ("ANY", "ADMIN_SURFACE", "admin")]),
        ]
        self.assertEqual(check(erl_workflow(), journeys)["status"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
