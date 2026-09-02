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

    def _event(self, event_type: str, thread_id: str, event_id: str, payload: dict) -> dict:
        return sign_trusted_event({"harness": "codex-app-server", "session_id": thread_id,
            "conversation_id": thread_id, "event_id": str(event_id), "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(), "source": "CODEX_APP_SERVER",
            "payload": payload}, transport_secret=self.transport_secret)
