"""Codex App Server lifecycle mapping for the shared Harness adapter.

The controller process owns the App Server transport.  This mapper intentionally does not parse
model prose: it accepts only App Server notifications and asks the shared bridge to decide whether
completion may be exposed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json

from harness_adapter_core import HarnessAdapterController, sign_trusted_event


class CodexAppServerAdapter:
    def __init__(self, *, bridge: HarnessAdapterController, transport_secret: str):
        if bridge.harness != "codex-app-server":
            raise ValueError("codex_adapter_requires_codex_harness")
        self.bridge, self.transport_secret = bridge, transport_secret

    def start(self, *, app_thread_id: str, event_id: str, original_user_request: str,
              canonical_contract: list[dict], auto_approve: bool = False) -> dict:
        return self.bridge.start_session(self._event("UserPromptSubmit", app_thread_id, event_id, {}),
            original_user_request=original_user_request, acceptance_contract=canonical_contract,
            auto_approve=auto_approve)

    def resume(self, *, app_thread_id: str, event_id: str) -> dict:
        return self.bridge.resume_session(self._event("ThreadResume", app_thread_id, event_id, {}))

    def on_notification(self, notification: dict) -> dict | None:
        method, params = notification.get("method"), notification.get("params", {})
        thread_id = params.get("threadId")
        if not isinstance(thread_id, str):
            return None
        event_id = params.get("turnId") or params.get("item", {}).get("id") or sha256(
            json.dumps(notification, sort_keys=True).encode()).hexdigest()
        if method == "turn/completed":
            return self.bridge.before_completion(self._event("TurnCompleted", thread_id, event_id, params))
        if method == "item/completed":
            item = params.get("item", {})
            # A completed item is captured as raw Harness evidence only when the controller has
            # already bound it to a Runtime Work Unit and explicit ACs.  Completion alone proves
            # no acceptance criterion.
            return {"captured": True, "item_type": item.get("type"), "requires_ac_binding": True}
        return None

    def on_user_control(self, *, app_thread_id: str, event_id: str, control: str,
                        expected_contract_revision: int, payload: dict) -> dict:
        """Apply an already-classified, real user control event.

        App Server model messages are deliberately not parsed here.  The outer Harness must
        classify and sign an explicit user action, so a Host cannot turn its own prose into a
        pause, cancel, correction, or resume.
        """
        if not isinstance(payload, dict):
            raise ValueError("user_control_payload_required")
        event = self._event(control, app_thread_id, event_id, payload)
        if control == "USER_CANCEL":
            return self.bridge.apply_user_cancel(event,
                expected_contract_revision=expected_contract_revision)
        if control == "USER_CORRECTION":
            return self.bridge.apply_user_correction(event,
                expected_contract_revision=expected_contract_revision,
                description=payload.get("description", ""),
                violated_requirements=payload.get("violated_requirements", []),
                root_cause_class=payload.get("root_cause_class", ""),
                related_checks=payload.get("related_checks", []))
        if control == "USER_PAUSE":
            return self.bridge.apply_user_pause(event,
                expected_contract_revision=expected_contract_revision,
                reason=payload.get("reason", ""),
                checkpoint_identity=payload.get("checkpoint_identity", {}),
                evidence_ids=payload.get("evidence_ids", []))
        if control == "USER_RESUME":
            return self.bridge.apply_user_resume(event,
                expected_contract_revision=expected_contract_revision,
                suspension_id=payload.get("suspension_id", ""),
                current_identity=payload.get("current_identity", {}),
                revalidation_evidence_ids=payload.get("revalidation_evidence_ids", []))
        raise ValueError("unsupported_user_control")

    def _event(self, event_type: str, thread_id: str, event_id: str, payload: dict) -> dict:
        return sign_trusted_event({"harness": "codex-app-server", "session_id": thread_id,
            "conversation_id": thread_id, "event_id": str(event_id), "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(), "source": "CODEX_APP_SERVER",
            "payload": payload}, transport_secret=self.transport_secret)
