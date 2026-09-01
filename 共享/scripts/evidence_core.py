"""Canonical evidence identity rules used by orchestration, recovery and acceptance."""
from __future__ import annotations

import re
import hashlib
import json
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
RECEIPT_ORIGIN = "HARNESS_EXECUTION"
RECEIPT_REQUIRED = ("receipt_id", "origin", "harness", "session_id", "candidate_id",
                    "work_id", "tool_or_capability", "execution_id", "producer",
                    "source_ref", "observed_at", "status", "content_hash", "artifact_refs")

# This is intentionally adapter-owned process state, not a serializable Delivery Session field.
# The Host Model has no manifest operation for registering a receipt. A Harness/Tool Adapter
# registers a receipt only after it captured the real execution artifact.
_HARNESS_RECEIPTS: dict[tuple[str, str], dict] = {}


def register_harness_execution_receipt(receipt: dict) -> str:
    """Adapter-only ingress for a real Harness/Tool execution receipt.

    Delivery Runtime never accepts a caller-made Evidence object. The Harness Adapter captures
    the result artifact, validates its hash here and registers the opaque receipt id. Only that
    id may subsequently be consumed by `record_evidence` once.
    """
    errors = validate_harness_receipt(receipt)
    if errors:
        raise ValueError("invalid_harness_execution_receipt:" + ",".join(errors))
    receipt_id = receipt["receipt_id"]
    key = (receipt["session_id"], receipt_id)
    if key in _HARNESS_RECEIPTS:
        raise ValueError("duplicate_harness_receipt_id")
    _HARNESS_RECEIPTS[key] = {"receipt": deepcopy(receipt), "consumed_by": None}
    return receipt_id


def validate_harness_receipt(receipt: dict) -> list[str]:
    if not isinstance(receipt, dict):
        return ["receipt_must_be_object"]
    errors = [f"missing:{key}" for key in RECEIPT_REQUIRED if receipt.get(key) in (None, "")]
    if receipt.get("origin") != RECEIPT_ORIGIN:
        errors.append("receipt_origin_not_harness_execution")
    if receipt.get("status") not in EVIDENCE_STATUSES:
        errors.append("receipt_status_invalid")
    if not _SHA256.fullmatch(str(receipt.get("content_hash", "")).lower()):
        errors.append("receipt_content_hash_invalid")
    try:
        datetime.fromisoformat(str(receipt.get("observed_at", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("receipt_timestamp_invalid")
    if not isinstance(receipt.get("artifact_refs"), list) or not receipt.get("artifact_refs"):
        errors.append("receipt_artifacts_required")
    elif not _receipt_artifacts_match(receipt):
        errors.append("receipt_artifact_hash_mismatch")
    return errors


def _receipt_artifacts_match(receipt: dict) -> bool:
    """Recompute an adapter-captured artifact hash; never merely validate hash shape.

    FILE receipts reread the referenced file. Other adapters pass captured result bytes in a
    HARNESS_CAPTURE artifact; this is the same captured stdout/response/screenshot/query result
    that the Harness registered, not Host Model prose.
    """
    hashes: list[str] = []
    for artifact in receipt.get("artifact_refs", []):
        if not isinstance(artifact, dict):
            return False
        kind = artifact.get("kind")
        if kind == "FILE":
            path = artifact.get("path")
            if not isinstance(path, str):
                return False
            try:
                with open(path, "rb") as handle:
                    payload = handle.read()
            except OSError:
                return False
        elif kind == "HARNESS_CAPTURE":
            payload = artifact.get("captured_content")
            if isinstance(payload, str):
                payload = payload.encode("utf-8")
            if not isinstance(payload, bytes):
                return False
        else:
            return False
        digest = hashlib.sha256(payload).hexdigest()
        if artifact.get("content_hash") != digest:
            return False
        hashes.append(digest)
    # One artifact has its direct hash; multiple artifacts bind an ordered digest manifest.
    combined = hashes[0] if len(hashes) == 1 else hashlib.sha256(
        json.dumps(hashes, separators=(",", ":")).encode("utf-8")).hexdigest()
    return receipt.get("content_hash") == combined


def canonical_evidence_from_receipt(session: dict, *, receipt_id: str,
                                    evidence_metadata: dict | None = None) -> dict:
    """Resolve one adapter-owned receipt and construct immutable canonical Evidence."""
    entry = _HARNESS_RECEIPTS.get((session["session_id"], receipt_id))
    if entry is None:
        # A session/candidate mismatch must be reported as such, not disguised as a missing
        # receipt. Receipt ids are unique per Harness session; an ambiguous foreign id fails.
        foreign = [value for (stored_session, stored_id), value in _HARNESS_RECEIPTS.items()
                   if stored_id == receipt_id and stored_session != session["session_id"]]
        if len(foreign) == 1:
            entry = foreign[0]
    if entry is None:
        raise PermissionError("trusted_harness_receipt_not_found")
    if entry["consumed_by"] is not None:
        raise ValueError("trusted_harness_receipt_already_consumed")
    receipt = entry["receipt"]
    if receipt["session_id"] != session["session_id"]:
        raise PermissionError("receipt_session_mismatch")
    if receipt["candidate_id"] != session["candidate_id"]:
        raise PermissionError("receipt_candidate_mismatch")
    known_work = {item.get("name") for bucket in ("stages", "tasks", "checks")
                  for item in session.get("plan", {}).get(bucket, [])}
    if receipt["work_id"] not in known_work:
        raise PermissionError("receipt_work_mismatch")
    _validate_receipt_execution(session, receipt)
    metadata = deepcopy(evidence_metadata or {})
    forbidden = {"producer", "source_ref", "status", "content_hash", "candidate_id",
                 "work_id", "execution_id", "receipt_id", "evidence_id", "session_revision"}
    attempted = sorted(forbidden & set(metadata))
    if attempted:
        raise PermissionError("evidence_metadata_cannot_override_receipt:" + ",".join(attempted))
    allowed = {"type", "dependencies", "acceptance_items", "business_metadata"}
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        raise ValueError("evidence_metadata_unknown:" + ",".join(unknown))
    record = {"evidence_id": receipt["receipt_id"],
              "type": metadata.get("type", "COMMAND"),
              "producer": receipt["producer"], "source_ref": receipt["source_ref"],
              "candidate_id": receipt["candidate_id"], "work_id": receipt["work_id"],
              "observed_at": receipt["observed_at"], "content_hash": receipt["content_hash"],
              "status": receipt["status"], "session_revision": session["revision"],
              "dependencies": metadata.get("dependencies", []),
              "acceptance_items": metadata.get("acceptance_items", []),
              "receipt_id": receipt["receipt_id"], "execution_id": receipt["execution_id"],
              "tool_or_capability": receipt["tool_or_capability"],
              # Keep auditable references/hashes, never copy captured stdout/response bytes into
              # the portable delivery state.
              "artifact_refs": [{key: deepcopy(value) for key, value in artifact.items()
                                 if key != "captured_content"}
                                for artifact in receipt["artifact_refs"]]}
    if "invocation_id" in receipt:
        record["invocation_id"] = receipt["invocation_id"]
    if "business_metadata" in metadata:
        record["business_metadata"] = metadata["business_metadata"]
    return record


def consume_harness_receipt(session: dict, receipt_id: str, evidence_id: str) -> None:
    entry = _HARNESS_RECEIPTS.get((session["session_id"], receipt_id))
    if entry is None:
        raise PermissionError("trusted_harness_receipt_not_found")
    if entry["consumed_by"] is not None:
        raise ValueError("trusted_harness_receipt_already_consumed")
    entry["consumed_by"] = evidence_id


def _validate_receipt_execution(session: dict, receipt: dict) -> None:
    """Capability receipts must bind to a Runtime-created invocation; generic tool receipts
    remain supported through the Harness-owned execution receipt contract."""
    invocation_id = receipt.get("invocation_id")
    if invocation_id is None:
        if not isinstance(receipt.get("execution_id"), str) or not receipt["execution_id"]:
            raise PermissionError("receipt_execution_id_required")
        return
    invocation = next((item for item in session.get("capability_invocations", [])
                       if item.get("invocation_id") == invocation_id), None)
    if invocation is None or invocation.get("status") != "REQUESTED":
        raise PermissionError("receipt_invocation_not_requested_or_not_found")
    if receipt.get("execution_id") != invocation_id:
        raise PermissionError("receipt_execution_id_mismatch")
    if receipt.get("work_id") != invocation.get("work_id"):
        raise PermissionError("receipt_invocation_work_mismatch")
    if receipt.get("tool_or_capability") != invocation.get("capability"):
        raise PermissionError("receipt_invocation_capability_mismatch")


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
