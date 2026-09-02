"""TRUST-RECEIPT and controller artifact-verification regression coverage."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "共享" / "scripts"))

from codex_persistent_controller import PersistentCodexController


def contract():
    return [
        {"ac_id": "AC-01", "description": "result.json exists", "verification_method": "file",
         "required_evidence": "artifact", "status": "OPEN", "source_revision": 1},
        {"ac_id": "AC-02", "description": "result.json approved count 3", "verification_method": "json",
         "required_evidence": "artifact", "status": "OPEN", "source_revision": 1},
    ]


def setup(tmp_path):
    controller = PersistentCodexController(tmp_path / "run", secret="test-secret")
    manifest = {"run_id": "fixture-run", "thread_id": "fixture-thread", "project_root": str(tmp_path)}
    controller.adapter.start(app_thread_id="fixture-thread", event_id="owner-message",
                             original_user_request="create result.json exists and result.json approved count 3",
                             canonical_contract=contract(), auto_approve=True)
    return controller, manifest


def completed_item(item_type, item_id):
    return {"method": "item/completed", "params": {"threadId": "fixture-thread",
            "item": {"id": item_id, "type": item_type, "text": "host-controlled text"}}}


def test_trust_receipt_001_to_006_only_execution_items_enter_ledger(tmp_path):
    controller, manifest = setup(tmp_path)
    for index, item_type in enumerate(("userMessage", "reasoning", "agentMessage"), start=1):
        controller.seq = index
        controller._derive(manifest, completed_item(item_type, f"untrusted-{index}"))
    assert controller.bridge.restore_state()["runtime"]["evidence_ledger"] == []
    for index, item_type in enumerate(("commandExecution", "fileChange"), start=4):
        controller.seq = index
        controller._derive(manifest, completed_item(item_type, f"trusted-{index}"))
    ledger = controller.bridge.restore_state()["runtime"]["evidence_ledger"]
    assert [record["tool_or_capability"] for record in ledger] == ["commandExecution", "fileChange"]
    normalized = [json.loads(line) for line in (controller.run_dir / "normalized_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [item["trust_classification"] for item in normalized] == ["USER_EVENT", "MODEL_GENERATED_EVENT", "MODEL_GENERATED_EVENT", "TRUSTED_EXECUTION_EVENT", "TRUSTED_EXECUTION_EVENT"]


def test_controller_artifact_fixture_blocks_then_recovers_same_delivery_session(tmp_path):
    controller, manifest = setup(tmp_path)
    result = tmp_path / "result.json"
    result.write_text('{"status":"approved"}', encoding="utf-8")
    controller._verify_final_artifacts(manifest, turn_id="turn-1")
    blocked = controller.bridge.before_completion(controller.adapter._event("TurnCompleted", "fixture-thread", "turn-1", {}))
    state_after_failure = controller.bridge.restore_state()
    assert blocked["allow_completion"] is False
    assert any(item["ac_id"] == "AC-02" and item["status"] == "OPEN" for item in blocked["open_blockers"])
    assert any(item["status"] == "FAIL" for item in state_after_failure["runtime"]["evidence_ledger"])
    session_id = state_after_failure["delivery_session_id"]

    result.write_text('{"status":"approved","count":3}', encoding="utf-8")
    controller._verify_final_artifacts(manifest, turn_id="turn-2")
    recovered = controller.bridge.before_completion(controller.adapter._event("TurnCompleted", "fixture-thread", "turn-2", {}))
    final_state = controller.bridge.restore_state()
    assert final_state["delivery_session_id"] == session_id
    assert recovered["allow_completion"] is True
    assert any(item["status"] == "CLOSED_REVALIDATED" for item in final_state["open_blockers"])
    assert any(item["status"] == "FAIL" for item in final_state["runtime"]["evidence_ledger"])
    bundle = json.loads((controller.run_dir / "final_verification_bundle.json").read_text(encoding="utf-8"))
    assert bundle["source"] == "CONTROLLER_VERIFIER"
    assert bundle["delivery_session_id"] == session_id
    assert set(bundle["acceptance_results"]) == {"AC-01", "AC-02"}
    assert bundle["required_evidence_refs"]
