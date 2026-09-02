"""Offline, deterministic demonstration of the trusted-delivery control path.

This is a demo harness, not product Runtime code.  It uses only the public
HarnessAdapterController boundary and emits an audit report for a presenter.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from harness_adapter_core import HarnessAdapterController, sign_trusted_event


SECRET = "demo-harness-secret"


def event(kind: str, ident: str, payload: dict | None = None) -> dict:
    return sign_trusted_event({"harness": "demo-harness", "session_id": "live-demo-session",
        "conversation_id": "live-demo-conversation", "event_id": ident, "event_type": kind,
        "timestamp": datetime.now(timezone.utc).isoformat(), "source": "DEMO_HARNESS",
        "payload": payload or {}}, transport_secret=SECRET)


def exact_pass(payload: bytes):
    return payload == b"PASS", {"expected": "PASS", "actual": payload.decode("utf-8", "replace")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Trusted Delivery offline demo")
    parser.add_argument("--run-dir", required=True, help="new or empty output directory")
    args = parser.parse_args()
    out = Path(args.run_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    state_path = out / "delivery-session.json"
    if state_path.exists():
        raise SystemExit("run_dir_already_contains_delivery_session")

    contract = [
        {"ac_id": "REPORT", "description": "approved report artifact", "verification_method": "file",
         "required_evidence": "controller verifier", "status": "OPEN", "source_revision": 1},
        {"ac_id": "SUMMARY", "description": "approved summary artifact", "verification_method": "file",
         "required_evidence": "controller verifier", "status": "OPEN", "source_revision": 1},
    ]
    bridge = HarnessAdapterController(harness="demo-harness", state_path=state_path,
                                      transport_secret=SECRET)
    state = bridge.start_session(event("UserPromptSubmit", "start"),
        original_user_request="交付报告和汇总；失败时不得假装完成", acceptance_contract=contract,
        auto_approve=True)
    work_id = state["runtime"]["plan"]["stages"][0]["name"]
    report, summary = out / "report.txt", out / "summary.txt"
    report.write_bytes(b"PASS"); summary.write_bytes(b"BROKEN")
    registry = {"exact-pass": exact_pass}

    bridge.verify_registered_artifact(event("ARTIFACT_VERIFICATION_REQUEST", "report-v1"),
        expected_contract_revision=1, work_id=work_id, path=report, ac_ids=["REPORT"],
        verifier_id="exact-pass", verifier_registry=registry)
    state = bridge.verify_registered_artifact(event("ARTIFACT_VERIFICATION_REQUEST", "summary-v1"),
        expected_contract_revision=1, work_id=work_id, path=summary, ac_ids=["SUMMARY"],
        verifier_id="exact-pass", verifier_registry=registry)
    failed_evidence = state["events"][-1]["evidence_id"]
    state = bridge.record_controller_failure(event("FAILURE_EVENT", "summary-failure"),
        expected_contract_revision=1, work_id=work_id, root_cause="summary artifact failed verifier",
        evidence_ids=[failed_evidence])
    failure_id = state["runtime"]["failures"][-1]["failure_id"]
    blocked = bridge.before_completion(event("Stop", "blocked-completion"))

    # The demo simulates a signed Harness assertion.  A production Harness must bind this
    # event to its real enterprise Owner identity before calling the same controller boundary.
    bridge.accept_owner_external_condition(event("OWNER_CONDITION", "owner-authorized",
        {"authority": "TRUSTED_TEST_OWNER_AUTHORITY"}), expected_contract_revision=1,
        condition_ref="demo-owner-authorized-repair")
    summary.write_bytes(b"PASS")
    state = bridge.verify_registered_artifact(event("ARTIFACT_VERIFICATION_REQUEST", "summary-v2"),
        expected_contract_revision=1, work_id=work_id, path=summary, ac_ids=["SUMMARY"],
        verifier_id="exact-pass", verifier_registry=registry)
    recovery_evidence = state["events"][-1]["evidence_id"]
    state = bridge.record_controller_recovery(event("RECOVERY_EVENT", "summary-recovery"),
        expected_contract_revision=1, failure_id=failure_id, action="Owner-authorized repair",
        recovery_evidence_ids=[recovery_evidence], blocker_evidence_ids=[recovery_evidence],
        regression_evidence_ids=[recovery_evidence])
    bridge.record_final_verification(event("ArtifactVerified", "final-bundle"), work_id=work_id,
        bundle={"demo": "trusted-delivery", "report": "PASS", "summary": "PASS"})
    completed = bridge.before_completion(event("Stop", "verified-completion"))
    result = {
        "DEMO_STATUS": "PASS" if not blocked["allow_completion"] and completed["allow_completion"] else "FAIL",
        "FAILED_ARTIFACT_BLOCKED_COMPLETION": not blocked["allow_completion"],
        "OWNER_AUTHORIZED_RECOVERY_REVALIDATED": state["runtime"]["failures"][-1]["status"],
        "FINAL_COMPLETION_ALLOWED": completed["allow_completion"],
        "STATE_FILE": str(state_path),
        "PRESENTER_MESSAGE": "AI 的完成主张在失败时被拦截；修复和重新验证后才被放行。",
    }
    (out / "demo_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
