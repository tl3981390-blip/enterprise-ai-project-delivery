import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from codex_app_server_adapter import CodexAppServerAdapter
from harness_adapter_core import HarnessAdapterController


def test_cdx_adapter_turn_completed_is_not_delivery_complete(tmp_path):
    bridge = HarnessAdapterController(harness="codex-app-server", state_path=tmp_path / "s.json", transport_secret="s")
    adapter = CodexAppServerAdapter(bridge=bridge, transport_secret="s")
    contract = [{"ac_id": "A", "description": "artifact A", "verification_method": "file",
                 "required_evidence": "file", "status": "OPEN", "source_revision": 1}]
    adapter.start(app_thread_id="thread-1", event_id="message-1", original_user_request="deliver artifact A",
                  canonical_contract=contract, auto_approve=True)
    result = adapter.on_notification({"method": "turn/completed", "params": {"threadId": "thread-1", "turn": {"id": "turn-1"}}})
    assert result["allow_completion"] is False
    assert result["status"] == "NOT_COMPLETE"
