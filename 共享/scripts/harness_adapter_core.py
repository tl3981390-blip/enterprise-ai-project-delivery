"""Harness-neutral, persisted bridge into the Delivery Runtime.

This module deliberately contains no delivery policy.  A platform adapter verifies that an
incoming lifecycle event came through its own trusted transport, then calls this bridge.  The
bridge preserves the original request and canonical acceptance contract, turns real tool or
artifact observations into Harness receipts, and delegates completion to ``claim_completion``.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
from pathlib import Path
from uuid import uuid4

from delivery_runtime import (approve_plan, cancel_delivery, change_conditions, claim_completion,
                              record_evidence, record_failure, record_recovery,
                              record_user_correction as runtime_record_user_correction,
                              resolve_user_correction as runtime_resolve_user_correction,
                              resume, suspend)
from evidence_core import register_harness_execution_receipt
from understanding_core import begin_understanding
from delivery_runtime import start_from_understanding

EVENT_FIELDS = ("harness", "session_id", "conversation_id", "event_id", "event_type",
                "timestamp", "source", "payload")
OWNER_EVENT_TYPES = {"OWNER_DIRECTIVE", "OWNER_APPROVAL", "SCOPE_CHANGE",
                     "ACCEPTANCE_CHANGE", "RECOVERY_INPUT"}
USER_CONTROL_EVENT_TYPES = {"USER_PAUSE", "USER_RESUME", "USER_CANCEL",
                            "USER_CORRECTION"}
WRITE_ACTIONS = {"WRITE", "EDIT", "DELETE", "EXECUTE"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_trusted_event(event: dict, *, transport_secret: str) -> dict:
    """Harness-side helper.  It is not a Host Model operation; the secret stays in adapter config."""
    unsigned = deepcopy(event)
    unsigned.pop("transport_signature", None)
    unsigned["transport_signature"] = hmac.new(transport_secret.encode("utf-8"),
                                                 _canonical(unsigned), sha256).hexdigest()
    return unsigned


def verify_trusted_event(event: dict, *, harness: str, transport_secret: str) -> dict:
    if not isinstance(event, dict) or any(key not in event for key in EVENT_FIELDS):
        raise PermissionError("trusted_harness_event_fields_required")
    if any(not isinstance(event[key], str) or not event[key].strip()
           for key in EVENT_FIELDS if key != "payload"):
        raise PermissionError("trusted_harness_event_identity_invalid")
    if event["harness"] != harness:
        raise PermissionError("trusted_harness_event_harness_mismatch")
    provided = event.get("transport_signature")
    if not isinstance(provided, str):
        raise PermissionError("trusted_harness_event_signature_required")
    unsigned = deepcopy(event)
    unsigned.pop("transport_signature", None)
    expected = hmac.new(transport_secret.encode("utf-8"), _canonical(unsigned), sha256).hexdigest()
    if not hmac.compare_digest(provided, expected):
        raise PermissionError("trusted_harness_event_signature_invalid")
    return deepcopy(event)


class HarnessAdapterController:
    """A thin, persistence-backend-neutral controller around the existing Runtime."""

    def __init__(self, *, harness: str, state_path: str | Path, transport_secret: str):
        self.harness = harness
        self.state_path = Path(state_path)
        self.transport_secret = transport_secret

    def start_session(self, event: dict, *, original_user_request: str,
                      acceptance_contract: list[dict], auto_approve: bool = False) -> dict:
        event = self._event(event, {"SessionStart", "UserPromptSubmit"})
        if not isinstance(original_user_request, str) or not original_user_request.strip():
            raise ValueError("original_user_request_required")
        contract = self._validate_contract(acceptance_contract)
        understanding = begin_understanding(
            raw_goal=original_user_request,
            observed_facts={"acceptance_requirements": [item["description"] for item in contract]})
        runtime = start_from_understanding(understanding=understanding)
        if auto_approve:
            ref = self._owner_ref(event)
            runtime = approve_plan(runtime, intent_record={
                "intent": "DIRECTIVE", "consequential_ambiguity": False,
                "context_refs": [f"plan_revision:{runtime['revision']}",
                                 f"plan_scope:{runtime['session_id']}"]}, user_origin_ref=ref)
        state = {"adapter_schema_version": 1, "delivery_session_id": runtime["session_id"],
                 "harness_type": self.harness, "harness_session_id": event["session_id"],
                 "conversation_id": event["conversation_id"],
                 "original_user_request": original_user_request, "canonical_contract": contract,
                 "contract_revision": 1, "owner_decisions": [], "recovery_history": [],
                 "completion_status": "NOT_VERIFIED", "acceptance_bindings": {},
                 "open_blockers": [],
                 "runtime": runtime, "events": [self._event_record(event)]}
        self._bind_contract_items(state)
        return self.persist_state(state)

    def resume_session(self, event: dict) -> dict:
        event = self._event(event, {"SessionStart", "ThreadResume", "PostCompact"})
        state = self.restore_state()
        if state["harness_type"] != self.harness or state["harness_session_id"] != event["session_id"]:
            raise PermissionError("adapter_session_identity_mismatch")
        state["events"].append(self._event_record(event))
        return self.persist_state(state)

    def revise_contract(self, event: dict, *, replacement: list[dict], reason: str) -> dict:
        event = self._event(event, {"ACCEPTANCE_CHANGE"})
        state = self.restore_state()
        previous = deepcopy(state["canonical_contract"])
        state["canonical_contract"] = self._validate_contract(replacement)
        state["contract_revision"] += 1
        state["owner_decisions"].append({"event_id": event["event_id"], "reason": reason,
                                          "old_revision": state["contract_revision"] - 1,
                                          "new_revision": state["contract_revision"], "at": _now()})
        state["contract_history"] = state.get("contract_history", []) + [previous]
        self._bind_contract_items(state)
        return self.persist_state(state)

    def before_tool(self, event: dict, *, action: str) -> dict:
        event = self._event(event, {"PreToolUse"})
        state = self.restore_state()
        if action in WRITE_ACTIONS and state["runtime"]["status"] != "EXECUTING":
            return {"allow": False, "reason": "delivery_not_executing"}
        if state.get("completion_status") == "REQUIRES_HUMAN":
            return {"allow": False, "reason": "owner_decision_required"}
        return {"allow": True, "reason": None}

    def record_tool_success(self, event: dict, *, work_id: str, tool: str, output: bytes,
                            ac_ids: list[str] | None = None) -> dict:
        return self._record_observation(event, event_types={"PostToolUse", "ItemCompleted"},
                                        work_id=work_id, tool=tool, output=output, status="PASS", ac_ids=ac_ids)

    def record_tool_failure(self, event: dict, *, work_id: str, tool: str, output: bytes,
                            root_cause: str, ac_ids: list[str] | None = None) -> dict:
        state = self._record_observation(event, event_types={"PostToolUseFailure", "ItemFailed"},
                                         work_id=work_id, tool=tool, output=output, status="FAIL", ac_ids=ac_ids)
        evidence_id = state["events"][-1]["evidence_id"]
        runtime = record_failure(state["runtime"], work_id=work_id, evidence_ids=[evidence_id],
                                 root_cause=root_cause)
        state["runtime"] = runtime
        state["recovery_history"].append({"failure_evidence_id": evidence_id, "root_cause": root_cause,
                                            "at": _now()})
        state["completion_status"] = "BLOCKED"
        return self.persist_state(state)

    def record_artifact(self, event: dict, *, work_id: str, path: str | Path,
                        ac_id: str, verifier) -> dict:
        event = self._event(event, {"ArtifactVerified"})
        target = Path(path)
        if target.is_file():
            payload = target.read_bytes()
            passed, detail = verifier(payload)
        else:
            # A missing artifact is still a mechanical observation.  Recording a FAIL receipt
            # makes the resulting blocker auditable instead of turning it into a controller crash.
            payload = b""
            passed, detail = False, {"reason": "artifact_missing"}
        output = json.dumps({"path": str(path), "passed": bool(passed), "detail": detail},
                            sort_keys=True).encode("utf-8")
        return self._record_observation(event, event_types={"ArtifactVerified"}, work_id=work_id,
                                        tool="artifact_verifier", output=output,
                                        status="PASS" if passed else "FAIL", ac_ids=[ac_id],
                                        business_metadata={"verification_source": "CONTROLLER_ARTIFACT_VERIFIER",
                                                           "artifact_path": str(path),
                                                           "artifact_hash": sha256(payload).hexdigest(),
                                                           "verification_result": deepcopy(detail)})

    def record_final_verification(self, event: dict, *, work_id: str, bundle: dict) -> dict:
        """Bind Controller-produced final verification evidence, never Host prose, to Runtime finals."""
        event = self._event(event, {"ArtifactVerified"})
        state = self.restore_state()
        final_items = []
        for key, value in state["runtime"]["acceptance"].items():
            # The surrounding localized label is Core-owned; its stable semantic marker is
            # deliberately ASCII so a controller never depends on console locale encoding.
            if "Final Complete" not in key or "Evidence" not in key:
                continue
            final_items.extend(f"{key}:{item}" for item in value) if isinstance(value, list) else final_items.append(key)
        if not final_items:
            raise ValueError("runtime_final_verification_items_missing")
        required_contract_items = set(state["contract_runtime_items"].values())
        if not required_contract_items.issubset(state["acceptance_bindings"]):
            raise ValueError("canonical_artifacts_not_yet_verified")
        output = json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return self._record_observation(event, event_types={"ArtifactVerified"}, work_id=work_id,
                                        tool="controller_final_verification_bundle", output=output,
                                        status="PASS", ac_ids=None,
                                        runtime_acceptance_items=final_items,
                                        business_metadata={"verification_source": "CONTROLLER_ARTIFACT_VERIFIER",
                                                           "bundle_kind": "FINAL_VERIFICATION_BUNDLE"})

    def before_completion(self, event: dict) -> dict:
        event = self._event(event, {"Stop", "TurnCompleted", "TaskCompleted"})
        state = self.restore_state()
        runtime = claim_completion(state["runtime"], state["acceptance_bindings"])
        state["runtime"] = runtime
        passed = runtime["completion_gate"]["pass"]
        self._reconcile_completion_blockers(state, runtime["completion_gate"])
        state["completion_status"] = "VERIFIED_DELIVERY_COMPLETE" if passed else "NOT_COMPLETE"
        state["events"].append({**self._event_record(event), "type": "COMPLETION_INTERCEPTED",
                                "gate": deepcopy(runtime["completion_gate"])})
        self.persist_state(state)
        return {"allow_completion": passed, "status": state["completion_status"],
                "blocker": None if passed else deepcopy(runtime["completion_gate"]),
                "open_blockers": deepcopy(state["open_blockers"])}

    def pause_for_owner(self, event: dict, *, reason: str) -> dict:
        event = self._event(event, {"OwnerBoundary"})
        state = self.restore_state()
        state["completion_status"] = "REQUIRES_HUMAN"
        state["owner_decisions"].append({"event_id": event["event_id"], "reason": reason,
                                          "status": "OPEN", "at": _now()})
        return self.persist_state(state)

    def resume_from_owner(self, event: dict) -> dict:
        event = self._event(event, {"RECOVERY_INPUT", "OWNER_APPROVAL"})
        state = self.restore_state()
        state["completion_status"] = "NOT_VERIFIED"
        state["owner_decisions"].append({"event_id": event["event_id"], "status": "RESUMED", "at": _now()})
        return self.persist_state(state)

    def apply_user_pause(self, event: dict, *, expected_contract_revision: int, reason: str,
                         checkpoint_identity: dict, evidence_ids: list[str]) -> dict:
        """Persist a real user pause; a model cannot manufacture this control event."""
        event = self._integration_event(event, {"USER_PAUSE"}, expected_contract_revision)
        state = self.restore_state()
        state["runtime"] = suspend(state["runtime"], reason=reason,
            checkpoint_identity=checkpoint_identity, evidence_ids=evidence_ids,
            initiator="USER", authority_ref=self._owner_ref(event))
        state["events"].append({**self._event_record(event), "type": "USER_PAUSE_APPLIED"})
        return self.persist_state(state)

    def apply_user_resume(self, event: dict, *, expected_contract_revision: int,
                          suspension_id: str, current_identity: dict,
                          revalidation_evidence_ids: list[str]) -> dict:
        """Resume only the persisted user pause and only with fresh revalidation evidence."""
        event = self._integration_event(event, {"USER_RESUME"}, expected_contract_revision)
        state = self.restore_state()
        package = next((item for item in state["runtime"].get("suspensions", [])
                        if item.get("suspension_id") == suspension_id), None)
        if package is None:
            raise KeyError("user_suspension_not_found")
        state["runtime"] = resume(state["runtime"], package=package,
            current_identity=current_identity, revalidation_evidence_ids=revalidation_evidence_ids,
            user_origin_ref=self._owner_ref(event))
        state["events"].append({**self._event_record(event), "type": "USER_RESUME_APPLIED"})
        return self.persist_state(state)

    def apply_user_cancel(self, event: dict, *, expected_contract_revision: int) -> dict:
        """A trusted explicit user cancel is terminal; ambiguous model prose is not accepted."""
        event = self._integration_event(event, {"USER_CANCEL"}, expected_contract_revision)
        state = self.restore_state()
        state["runtime"] = cancel_delivery(state["runtime"], intent_record={
            "intent": "CANCEL", "consequential_ambiguity": False},
            user_origin_ref=self._owner_ref(event))
        state["events"].append({**self._event_record(event), "type": "USER_CANCEL_APPLIED"})
        return self.persist_state(state)

    def apply_user_correction(self, event: dict, *, expected_contract_revision: int,
                              description: str, violated_requirements: list[str],
                              root_cause_class: str, related_checks: list[str]) -> dict:
        """Turn an actual user correction into durable recovery work, never model self-report."""
        event = self._integration_event(event, {"USER_CORRECTION"}, expected_contract_revision)
        state = self.restore_state()
        state["runtime"] = runtime_record_user_correction(state["runtime"], description=description,
            violated_requirements=violated_requirements, root_cause_class=root_cause_class,
            related_checks=related_checks, user_origin_ref=self._owner_ref(event))
        state["events"].append({**self._event_record(event), "type": "USER_CORRECTION_APPLIED"})
        return self.persist_state(state)

    def resolve_user_correction(self, event: dict, *, expected_contract_revision: int,
                                correction_id: str, root_cause_fix: str,
                                evidence_ids: list[str]) -> dict:
        event = self._integration_event(event, {"RECOVERY_EVENT"}, expected_contract_revision)
        state = self.restore_state()
        state["runtime"] = runtime_resolve_user_correction(state["runtime"],
            correction_id=correction_id, root_cause_fix=root_cause_fix, evidence_ids=evidence_ids)
        state["events"].append({**self._event_record(event), "type": "USER_CORRECTION_RESOLVED"})
        return self.persist_state(state)

    def apply_contract_change(self, event: dict, *, expected_contract_revision: int,
                              changed_facts: dict, change_source: str, authority_ref: dict,
                              evidence_ids: list[str], replanned_work_units: dict | None = None) -> dict:
        """Trusted Harness-only binding for existing Runtime condition handling."""
        event = self._integration_event(event, {"CONTRACT_CHANGE"}, expected_contract_revision)
        state = self.restore_state()
        runtime = change_conditions(state["runtime"], changed_facts=changed_facts,
            change_source=change_source, authority_ref=authority_ref, evidence_ids=evidence_ids,
            replanned_work_units=replanned_work_units)
        state["runtime"] = runtime; state["contract_revision"] += 1
        state["events"].append({**self._event_record(event), "type": "INTEGRATION_CONTRACT_CHANGED"})
        return self.persist_state(state)

    def record_controller_recovery(self, event: dict, *, expected_contract_revision: int,
                                   failure_id: str, action: str, recovery_evidence_ids: list[str],
                                   blocker_evidence_ids: list[str], regression_evidence_ids: list[str]) -> dict:
        """Trusted Harness-only binding to the existing Runtime recovery state machine."""
        event = self._integration_event(event, {"RECOVERY_EVENT"}, expected_contract_revision)
        state = self.restore_state()
        state["runtime"] = record_recovery(state["runtime"], failure_id=failure_id, action=action,
            recovery_evidence_ids=recovery_evidence_ids, blocker_evidence_ids=blocker_evidence_ids,
            regression_evidence_ids=regression_evidence_ids)
        state["events"].append({**self._event_record(event), "type": "INTEGRATION_RECOVERY_RECORDED"})
        return self.persist_state(state)

    def record_controller_failure(self, event: dict, *, expected_contract_revision: int,
                                  work_id: str, root_cause: str, evidence_ids: list[str]) -> dict:
        """Trusted Harness-only failure binding; evidence must already be canonical."""
        event = self._integration_event(event, {"FAILURE_EVENT"}, expected_contract_revision)
        state = self.restore_state()
        state["runtime"] = record_failure(state["runtime"], work_id=work_id,
            root_cause=root_cause, evidence_ids=evidence_ids)
        state["events"].append({**self._event_record(event), "type": "INTEGRATION_FAILURE_RECORDED"})
        return self.persist_state(state)

    def verify_registered_artifact(self, event: dict, *, expected_contract_revision: int,
                                   work_id: str, path: str | Path, ac_ids: list[str], verifier_id: str,
                                   verifier_registry: dict) -> dict:
        """Run an allow-listed deterministic verifier; callers never submit PASS/FAIL."""
        event = self._integration_event(event, {"ARTIFACT_VERIFICATION_REQUEST"}, expected_contract_revision)
        verifier = verifier_registry.get(verifier_id)
        if not callable(verifier):
            raise PermissionError("registered_verifier_required")
        if not ac_ids or any(ac_id not in self.restore_state()["contract_runtime_items"] for ac_id in ac_ids):
            raise ValueError("artifact_acceptance_mapping_invalid")
        target = Path(path); payload = target.read_bytes() if target.is_file() else b""
        passed, detail = verifier(payload) if target.is_file() else (False, {"reason": "artifact_missing"})
        output = json.dumps({"path": str(path), "passed": bool(passed), "detail": detail}, sort_keys=True).encode("utf-8")
        return self._record_observation(event, event_types={"ARTIFACT_VERIFICATION_REQUEST"}, work_id=work_id,
            tool=f"registered_verifier:{verifier_id}", output=output, status="PASS" if passed else "FAIL", ac_ids=ac_ids,
            business_metadata={"verification_source": "CONTROLLER_VERIFIER", "verifier_id": verifier_id,
                               "artifact_path": str(path), "artifact_hash": sha256(payload).hexdigest(),
                               "verification_result": deepcopy(detail), "contract_revision": expected_contract_revision})

    def accept_owner_external_condition(self, event: dict, *, expected_contract_revision: int,
                                        condition_ref: str) -> dict:
        """Records a trusted owner condition; it never completes delivery or closes blockers."""
        event = self._integration_event(event, {"OWNER_CONDITION"}, expected_contract_revision)
        if event["payload"].get("authority") != "TRUSTED_TEST_OWNER_AUTHORITY":
            raise PermissionError("trusted_test_owner_authority_required")
        state = self.restore_state()
        state.setdefault("external_conditions", []).append({"condition_ref": condition_ref,
            "event_id": event["event_id"], "source": "TRUSTED_TEST_OWNER_AUTHORITY", "at": _now()})
        state["events"].append({**self._event_record(event), "type": "OWNER_EXTERNAL_CONDITION_ACCEPTED"})
        return self.persist_state(state)

    def _integration_event(self, event: dict, allowed: set[str], expected_revision: int) -> dict:
        event = self._event(event, allowed)
        state = self.restore_state()
        if (event["session_id"] != state["harness_session_id"] or
                event["conversation_id"] != state["conversation_id"]):
            raise PermissionError("harness_session_mismatch")
        if expected_revision != state["contract_revision"]:
            raise PermissionError("integration_contract_revision_stale")
        if any(item.get("event_id") == event["event_id"] for item in state["events"]):
            raise PermissionError("integration_event_replay")
        return event

    def persist_state(self, state: dict) -> dict:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)
        return deepcopy(state)

    def restore_state(self) -> dict:
        if not self.state_path.is_file():
            raise FileNotFoundError("delivery_session_not_found")
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _record_observation(self, event: dict, *, event_types: set[str], work_id: str,
                            tool: str, output: bytes, status: str, ac_ids: list[str] | None,
                            runtime_acceptance_items: list[str] | None = None,
                            business_metadata: dict | None = None) -> dict:
        event = self._event(event, event_types)
        state = self.restore_state()
        runtime = state["runtime"]
        digest = sha256(output).hexdigest()
        receipt_id = f"{self.harness}:{event['event_id']}:{uuid4()}"
        receipt = {"receipt_id": receipt_id, "origin": "HARNESS_EXECUTION", "harness": self.harness,
                   "session_id": runtime["session_id"], "candidate_id": runtime["candidate_id"],
                   "work_id": work_id, "tool_or_capability": tool, "execution_id": event["event_id"],
                   "producer": "HARNESS_RUNTIME", "source_ref": f"{self.harness}://{event['event_id']}",
                   "observed_at": event["timestamp"], "status": status, "content_hash": digest,
                   "artifact_refs": [{"kind": "HARNESS_CAPTURE", "captured_content": output,
                                       "content_hash": digest}]}
        register_harness_execution_receipt(receipt)
        labels = [state["contract_runtime_items"][ac_id] for ac_id in (ac_ids or [])]
        labels.extend(runtime_acceptance_items or [])
        runtime = record_evidence(runtime, receipt_id=receipt_id,
                                  evidence_metadata={"type": "TEST_RESULT", "acceptance_items": labels,
                                                     "business_metadata": deepcopy(business_metadata or {})})
        state["runtime"] = runtime
        for ac_id in ac_ids or []:
            state["acceptance_bindings"][state["contract_runtime_items"][ac_id]] = [receipt_id]
        for item in runtime_acceptance_items or []:
            state["acceptance_bindings"][item] = [receipt_id]
        state["events"].append({**self._event_record(event), "evidence_id": receipt_id, "status": status})
        return self.persist_state(state)

    def _bind_contract_items(self, state: dict) -> None:
        runtime_items = [item for item in state["runtime"]["acceptance"] if not isinstance(state["runtime"]["acceptance"][item], dict)]
        labels = []
        for key in runtime_items:
            value = state["runtime"]["acceptance"][key]
            labels.extend(f"{key}:{x}" for x in value) if isinstance(value, list) else labels.append(key)
        mapping = {}
        for ac in state["canonical_contract"]:
            match = next((label for label in labels if ac["description"] in label), None)
            if match is None:
                raise ValueError(f"canonical_contract_not_bound_to_runtime:{ac['ac_id']}")
            mapping[ac["ac_id"]] = match
        state["contract_runtime_items"] = mapping

    @staticmethod
    def _reconcile_completion_blockers(state: dict, gate: dict) -> None:
        """Persist a verifier-created blocker; model prose cannot create or close one."""
        reverse = {value: key for key, value in state["contract_runtime_items"].items()}
        unresolved = set(gate.get("missing", []) + gate.get("failed", []) +
                         gate.get("pending_external_validation", []))
        active_ids = set()
        for runtime_item in unresolved:
            ac_id = reverse.get(runtime_item)
            if ac_id is None:
                continue
            existing = next((item for item in state["open_blockers"]
                             if item["ac_id"] == ac_id and item["status"] == "OPEN"), None)
            if existing is None:
                evidence_id = next(iter(state["acceptance_bindings"].get(runtime_item, [])), None)
                evidence = next((item for item in state["runtime"].get("evidence_ledger", [])
                                 if item.get("evidence_id") == evidence_id), {})
                verification = evidence.get("business_metadata", {})
                existing = {"blocker_id": str(uuid4()), "ac_id": ac_id, "status": "OPEN",
                            "source": "MECHANICAL_VERIFICATION", "runtime_item": runtime_item,
                            "artifact_hash": verification.get("artifact_hash"),
                            "verification_result": verification.get("verification_result"),
                            "created_at": _now()}
                state["open_blockers"].append(existing)
            active_ids.add(existing["blocker_id"])
        for blocker in state["open_blockers"]:
            if blocker["status"] == "OPEN" and blocker["blocker_id"] not in active_ids:
                blocker["status"] = "CLOSED_REVALIDATED"
                blocker["closed_at"] = _now()

    @staticmethod
    def _validate_contract(contract: list[dict]) -> list[dict]:
        if not isinstance(contract, list) or not contract:
            raise ValueError("canonical_contract_required")
        required = {"ac_id", "description", "verification_method", "required_evidence", "status", "source_revision"}
        ids = set()
        cleaned = []
        for item in contract:
            if not isinstance(item, dict) or required - set(item) or item["status"] != "OPEN":
                raise ValueError("canonical_contract_item_invalid")
            if item["ac_id"] in ids:
                raise ValueError("canonical_contract_duplicate_ac_id")
            ids.add(item["ac_id"])
            cleaned.append(deepcopy(item))
        return cleaned

    def _event(self, event: dict, allowed: set[str]) -> dict:
        verified = verify_trusted_event(event, harness=self.harness, transport_secret=self.transport_secret)
        if verified["event_type"] not in allowed:
            raise PermissionError("trusted_harness_event_type_not_allowed")
        return verified

    def _owner_ref(self, event: dict) -> dict:
        if event["event_type"] not in OWNER_EVENT_TYPES | USER_CONTROL_EVENT_TYPES | {"UserPromptSubmit"}:
            raise PermissionError("trusted_owner_event_required")
        return {"origin": "USER", "harness": self.harness,
                "conversation_id": event["conversation_id"], "message_id": event["event_id"]}

    @staticmethod
    def _event_record(event: dict) -> dict:
        return {"event_id": event["event_id"], "event_type": event["event_type"],
                "timestamp": event["timestamp"], "source": event["source"]}
