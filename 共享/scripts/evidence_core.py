"""Canonical evidence identity rules used by orchestration, recovery and acceptance."""
from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime

EVIDENCE_TYPES = {
    "COMMAND", "FILE", "LOG", "SCREENSHOT", "API", "DATABASE", "BROWSER",
    "EXTERNAL_SYSTEM", "TEST_RESULT", "GIT", "RUNTIME_IDENTITY",
}
EVIDENCE_PRODUCERS = {
    "COMMAND_RUNNER", "FILESYSTEM", "LOG_COLLECTOR", "BROWSER_TOOL", "API_CLIENT",
    "DATABASE_CLIENT", "EXTERNAL_PROVIDER", "TEST_RUNNER", "GIT_CLIENT",
    "HARNESS_RUNTIME",
}
EVIDENCE_STATUSES = {"PASS", "FAIL", "PENDING_EXTERNAL_VALIDATION"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_evidence(record: dict, *, candidate_id: str, current_revision: int,
                      work_id: str | None = None) -> list[str]:
    if not isinstance(record, dict):
        return ["evidence_must_be_object"]
    errors = []
    required = ("evidence_id", "type", "producer", "source_ref", "candidate_id",
                "work_id", "observed_at", "content_hash", "status", "session_revision")
    errors.extend(f"missing:{key}" for key in required if record.get(key) in (None, ""))
    if record.get("type") not in EVIDENCE_TYPES:
        errors.append("evidence_type_invalid")
    if record.get("producer") not in EVIDENCE_PRODUCERS:
        errors.append("evidence_producer_invalid")
    if record.get("status") not in EVIDENCE_STATUSES:
        errors.append("evidence_status_invalid")
    if record.get("candidate_id") != candidate_id:
        errors.append("evidence_candidate_mismatch")
    if work_id is not None and record.get("work_id") != work_id:
        errors.append("evidence_work_mismatch")
    if not _SHA256.fullmatch(str(record.get("content_hash", "")).lower()):
        errors.append("evidence_content_hash_invalid")
    try:
        datetime.fromisoformat(str(record.get("observed_at", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("evidence_timestamp_invalid")
    if not isinstance(record.get("session_revision"), int):
        errors.append("evidence_revision_invalid")
    elif record["session_revision"] > current_revision:
        errors.append("evidence_from_future_revision")
    if not isinstance(record.get("dependencies", []), list):
        errors.append("evidence_dependencies_invalid")
    if not isinstance(record.get("acceptance_items", []), list):
        errors.append("evidence_acceptance_items_invalid")
    return errors


def append_evidence(session: dict, record: dict, *, work_id: str | None = None) -> dict:
    errors = validate_evidence(record, candidate_id=session["candidate_id"],
                               current_revision=session["revision"], work_id=work_id)
    if errors:
        raise ValueError("invalid_evidence:" + ",".join(errors))
    if any(item["evidence_id"] == record["evidence_id"] for item in session["evidence_ledger"]):
        raise ValueError("duplicate_evidence_id")
    stored = deepcopy(record)
    stored["valid_for_revision"] = session["revision"]
    stored["validation_status"] = "CURRENT"
    session["evidence_ledger"].append(stored)
    return stored


def evidence_by_id(session: dict, evidence_id: str) -> dict:
    record = next((item for item in session.get("evidence_ledger", [])
                   if item.get("evidence_id") == evidence_id), None)
    if record is None:
        raise KeyError(f"evidence_not_found:{evidence_id}")
    return record


def require_current_evidence(session: dict, evidence_ids: list[str], *, work_id: str | None = None,
                             status: str | None = None,
                             acceptance_item: str | None = None) -> list[dict]:
    if not evidence_ids or not all(isinstance(x, str) and x for x in evidence_ids):
        raise ValueError("evidence_ids_required")
    records = []
    for evidence_id in evidence_ids:
        record = evidence_by_id(session, evidence_id)
        if record.get("candidate_id") != session["candidate_id"]:
            raise ValueError("evidence_candidate_mismatch")
        if record.get("valid_for_revision") != session["revision"]:
            raise ValueError("evidence_stale_or_not_revalidated")
        if record.get("validation_status") in {"INVALIDATED", "REQUIRES_REVALIDATION"}:
            raise ValueError("evidence_invalidated")
        if work_id is not None and record.get("work_id") != work_id:
            raise ValueError("evidence_work_mismatch")
        if status is not None and record.get("status") != status:
            raise ValueError("evidence_status_mismatch")
        if acceptance_item is not None and acceptance_item not in record.get("acceptance_items", []):
            raise ValueError("evidence_not_bound_to_acceptance_item")
        records.append(record)
    return records


def reclassify_evidence(session: dict, *, changed_facts: set[str], next_revision: int) -> dict:
    classified = {"STILL_VALID": [], "INVALIDATED": [], "REQUIRES_REVALIDATION": []}
    for record in session.get("evidence_ledger", []):
        dependencies = set(record.get("dependencies", []))
        if dependencies & changed_facts:
            record["validation_status"] = "REQUIRES_REVALIDATION"
            classified["REQUIRES_REVALIDATION"].append(record["evidence_id"])
        elif record.get("status") == "PASS":
            record["validation_status"] = "STILL_VALID"
            record["valid_for_revision"] = next_revision
            classified["STILL_VALID"].append(record["evidence_id"])
        else:
            record["validation_status"] = "INVALIDATED"
            classified["INVALIDATED"].append(record["evidence_id"])
    return classified
