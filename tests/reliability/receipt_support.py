"""Harness-adapter simulation used by tests; Host-model code never calls this in production."""
from __future__ import annotations

import hashlib

from evidence_core import register_harness_execution_receipt


def record_test_receipt(session: dict, *, receipt_id: str, work_id: str, status: str = "PASS",
                        acceptance_items: list[str] | None = None,
                        invocation_id: str | None = None,
                        tool_or_capability: str = "pytest") -> tuple[str, dict]:
    payload = f"captured harness result:{receipt_id}:{status}".encode("utf-8")
    receipt = {
        "receipt_id": receipt_id,
        "origin": "HARNESS_EXECUTION",
        "harness": "pytest-adapter",
        "session_id": session["session_id"],
        "candidate_id": session["candidate_id"],
        "work_id": work_id,
        "tool_or_capability": tool_or_capability,
        "execution_id": invocation_id or f"tool-execution:{receipt_id}",
        "producer": "TEST_RUNNER",
        "source_ref": f"harness://pytest/{receipt_id}",
        "observed_at": "2026-09-01T00:00:00+00:00",
        "status": status,
        "content_hash": hashlib.sha256(payload).hexdigest(),
        "artifact_refs": [{"kind": "HARNESS_CAPTURE", "artifact_id": receipt_id,
                           "captured_content": payload,
                           "content_hash": hashlib.sha256(payload).hexdigest()}],
    }
    if invocation_id is not None:
        receipt["invocation_id"] = invocation_id
    return register_harness_execution_receipt(receipt), {
        "type": "TEST_RESULT", "dependencies": [],
        "acceptance_items": acceptance_items or [],
    }
