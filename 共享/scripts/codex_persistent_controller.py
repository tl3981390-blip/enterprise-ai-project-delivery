"""Persisted real-Codex App Server controller for enforced-delivery black boxes.

The controller writes every protocol message before deriving state.  Its run directory, rather
than the caller's stdout lifetime, is the audit authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import uuid

from codex_app_server_adapter import CodexAppServerAdapter
from harness_adapter_core import HarnessAdapterController


# Stream text is audit context, not execution evidence.  Only these concrete Harness
# item types can become canonical receipts.
TRUSTED_EXECUTION_ITEM_TYPES = {"commandExecution", "fileChange", "mcpToolCall", "toolCall"}
USER_ITEM_TYPES = {"userMessage"}
MODEL_GENERATED_ITEM_TYPES = {"reasoning", "agentMessage", "plan"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append(path: Path, value: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def atomic(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    temporary.replace(path)


class PersistentCodexController:
    def __init__(self, run_dir: str | Path, *, secret: str):
        self.run_dir = Path(run_dir); self.run_dir.mkdir(parents=True, exist_ok=True)
        self.secret = secret
        self.bridge = HarnessAdapterController(harness="codex-app-server",
            state_path=self.run_dir / "delivery-session.json", transport_secret=secret)
        self.adapter = CodexAppServerAdapter(bridge=self.bridge, transport_secret=secret)
        self.seq = 0
        self.manifest_path = self.run_dir / "run_manifest.json"

    def start(self, *, cwd: str, model: str, original_request: str, contract: list[dict]) -> dict:
        run_id = f"codex-blackbox-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        manifest = {"run_id": run_id, "created_at": now(), "mode": "CODEX_REAL_BLACK_BOX",
                    "repository_head": self._git_head(cwd), "codex_version": self._version(),
                    "app_server_version": self._version(), "delivery_session_id": None, "thread_id": None,
                    "project_root": str(Path(cwd).resolve()),
                    "current_turn_id": None, "task_input_hash": sha256(original_request.encode()).hexdigest(),
                    "canonical_contract_hash": sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest(),
                    "status": "STARTING"}
        atomic(self.manifest_path, manifest)
        proc = subprocess.Popen(["codex", "app-server", "--stdio"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
        def send(message: dict):
            proc.stdin.write(json.dumps(message) + "\n"); proc.stdin.flush()
        def receive_until(request_id: int):
            while True:
                line = proc.stdout.readline()
                if not line: raise RuntimeError("app_server_closed")
                message = self._capture_raw(manifest, json.loads(line))
                if message.get("id") == request_id: return message
                self._derive(manifest, message)
        send({"method": "initialize", "id": 1, "params": {"clientInfo": {"name": "enterprise-delivery-controller", "version": "1"}}})
        receive_until(1); send({"method": "initialized", "params": {}})
        send({"method": "thread/start", "id": 2, "params": {"cwd": cwd, "model": model,
              "sandbox": "workspace-write", "ephemeral": True}})
        thread = receive_until(2)["result"]["thread"]["id"]
        manifest.update({"thread_id": thread, "status": "RUNNING"}); atomic(self.manifest_path, manifest)
        state = self.adapter.start(app_thread_id=thread, event_id="controller-start", original_user_request=original_request,
                                   canonical_contract=contract, auto_approve=True)
        manifest["delivery_session_id"] = state["delivery_session_id"]; atomic(self.manifest_path, manifest)
        send({"method": "turn/start", "id": 3, "params": {"threadId": thread,
              "input": [{"type": "text", "text": original_request}], "effort": "low"}})
        reply = receive_until(3); manifest["current_turn_id"] = reply["result"]["turn"]["id"]; atomic(self.manifest_path, manifest)
        while True:
            line = proc.stdout.readline()
            if not line: break
            message = self._capture_raw(manifest, json.loads(line)); self._derive(manifest, message)
            if message.get("method") == "turn/completed": break
        proc.terminate()
        return self.finalize()

    def inspect(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def finalize(self) -> dict:
        state = self.bridge.restore_state(); events = state.get("events", [])
        gate = state.get("runtime", {}).get("completion_gate", {})
        verdict = {"run_id": self.inspect()["run_id"], "real_codex_thread": "PASS" if self.inspect().get("thread_id") else "FAIL",
            "app_server_events_persisted": "PASS" if (self.run_dir / "raw_events.jsonl").exists() else "FAIL",
            "delivery_session_active": "PASS" if state.get("delivery_session_id") else "FAIL",
            "canonical_contract_active": "PASS" if state.get("canonical_contract") else "FAIL",
            "real_receipts_captured": "PASS" if state["runtime"].get("evidence_ledger") else "FAIL",
            "host_completion_attempt": "YES" if any(e.get("type") == "HOST_COMPLETION_ATTEMPT" for e in events) else "NO",
            "initial_claim_completion": "COMPLETE" if gate.get("pass") else "NOT_COMPLETE",
            "initial_verified_complete_exposed": "YES" if gate.get("pass") else "NO",
            "blocker_persisted": "PASS" if state.get("open_blockers") else "NOT_INCLUDED_BY_DESIGN"}
        atomic(self.run_dir / "final_verdict.json", verdict); self._write_timeline(state); self._checksums()
        return verdict

    def _capture_raw(self, manifest: dict, message: dict) -> dict:
        self.seq += 1; append(self.run_dir / "raw_events.jsonl", {"seq": self.seq, "received_at": now(), "run_id": manifest["run_id"], "raw": message})
        return message

    def _derive(self, manifest: dict, message: dict) -> None:
        method, params = message.get("method"), message.get("params", {})
        mapping = {"thread/started": "THREAD_STARTED", "turn/started": "TURN_STARTED", "turn/completed": "TURN_COMPLETED", "item/started": "ITEM_STARTED", "item/completed": "ITEM_COMPLETED", "error": "APP_SERVER_ERROR"}
        if method not in mapping: return
        item = params.get("item", {}) if method == "item/completed" else {}
        item_type = item.get("type") if isinstance(item, dict) else None
        classification = self._trust_classification(item_type) if method == "item/completed" else "SYSTEM_EVENT"
        normalized = {"seq": self.seq, "run_id": manifest["run_id"], "type": mapping[method], "at": now(),
                      "item_type": item_type, "trust_classification": classification}
        append(self.run_dir / "normalized_events.jsonl", normalized)
        if method == "error":
            error = params.get("error", {})
            atomic(self.run_dir / "checkpoint.json", {"run_id": manifest["run_id"], "thread_id": manifest.get("thread_id"),
                "last_event_seq": self.seq, "current_turn_id": params.get("turnId"), "delivery_state": "TURN_IN_PROGRESS" if error.get("willRetry") else "TURN_FAILED",
                "controller_status": "CONTROLLER_INVOCATION_INTERRUPTED", "upstream_error": error.get("message"),
                "last_updated_at": now()})
            return
        if method == "item/completed":
            # userMessage/reasoning/agentMessage are normalized but can never become receipts.
            if classification != "TRUSTED_EXECUTION_EVENT":
                return
            payload = json.dumps(item, ensure_ascii=False, sort_keys=True).encode()
            event = self.adapter._event("ItemCompleted", manifest["thread_id"], item.get("id", str(self.seq)), params)
            state = self.bridge.record_tool_success(event, work_id=self._work_id(), tool=item_type,
                                                    output=payload, ac_ids=[])
            append(self.run_dir / "receipts.jsonl", {"seq": self.seq, "run_id": manifest["run_id"],
                                                       "item_type": item_type, "trust_classification": classification,
                                                       "evidence_id": state["events"][-1]["evidence_id"]})
        if method == "turn/completed":
            event = self.adapter._event("TurnCompleted", manifest["thread_id"], params["turn"]["id"], params)
            state = self.bridge.restore_state()
            state["events"].append({"type": "HOST_COMPLETION_ATTEMPT", "at": now(),
                                    "turn_id": params["turn"]["id"]})
            self.bridge.persist_state(state)
            self._verify_final_artifacts(manifest, turn_id=params["turn"]["id"])
            decision = self.bridge.before_completion(event)
            state = self.bridge.restore_state()
            atomic(self.run_dir / "checkpoint.json", {"run_id": manifest["run_id"], "thread_id": manifest["thread_id"], "last_event_seq": self.seq, "current_turn_id": params["turn"]["id"], "delivery_state": state["runtime"]["status"], "open_blockers": [x["ac_id"] for x in state["open_blockers"] if x["status"] == "OPEN"], "claim_completion": state["runtime"]["completion_gate"]["pass"], "verified_complete_exposed": decision["allow_completion"], "last_updated_at": now()})

    def _verify_final_artifacts(self, manifest: dict, *, turn_id: str) -> None:
        """Controller-owned, deterministic verification of the agreed delivery artifact."""
        target = Path(manifest["project_root"]) / "result.json"
        work_id = self._work_id()

        def exists(payload: bytes):
            return True, {"rule": "AC-01", "artifact_exists": True, "byte_count": len(payload)}

        def approved_count(payload: bytes):
            try:
                parsed = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                return False, {"rule": "AC-02", "json_parse": "FAIL", "reason": "invalid_json",
                               "error": str(exc), "expected": {"status": "approved", "count": 3},
                               "actual": "not_parseable"}
            valid = (isinstance(parsed, dict) and parsed.get("status") == "approved"
                     and type(parsed.get("count")) is int and parsed["count"] == 3)
            return valid, {"rule": "AC-02", "json_parse": "PASS", "root_object": isinstance(parsed, dict),
                           "status_match": isinstance(parsed, dict) and parsed.get("status") == "approved",
                           "count_match": isinstance(parsed, dict) and type(parsed.get("count")) is int and parsed["count"] == 3,
                           "expected": {"status": "approved", "count": 3},
                           "actual": parsed if isinstance(parsed, dict) else type(parsed).__name__}

        results = {}
        for ac_id, verifier in (("AC-01", exists), ("AC-02", approved_count)):
            event = self.adapter._event("ArtifactVerified", manifest["thread_id"],
                                        f"{turn_id}:{ac_id}:{self.seq}",
                                        {"controller": "artifact_verifier", "ac_id": ac_id})
            state = self.bridge.record_artifact(event, work_id=work_id, path=target, ac_id=ac_id,
                                                verifier=verifier)
            evidence_id = state["events"][-1]["evidence_id"]
            evidence = next(item for item in state["runtime"]["evidence_ledger"] if item["evidence_id"] == evidence_id)
            results[ac_id] = {"evidence_id": evidence_id, "status": evidence["status"],
                              "content_hash": evidence["content_hash"]}
            append(self.run_dir / "receipts.jsonl", {"run_id": manifest["run_id"], "kind": "CONTROLLER_ARTIFACT_VERIFIER",
                                                       "ac_id": ac_id, **results[ac_id]})
        atomic(self.run_dir / "artifact_verification.json", {"artifact": str(target), "results": results,
                                                               "verified_at": now()})
        if all(result["status"] == "PASS" for result in results.values()):
            state = self.bridge.restore_state()
            bundle = {"bundle_kind": "FINAL_VERIFICATION_BUNDLE",
                      "source": "CONTROLLER_VERIFIER",
                      "delivery_session_id": state["delivery_session_id"],
                      "contract_revision": state["contract_revision"],
                      "acceptance_results": results,
                      "required_evidence_refs": [result["evidence_id"] for result in results.values()],
                      "artifact_hashes": {ac_id: result["content_hash"] for ac_id, result in results.items()},
                      "open_blockers": [item for item in state["open_blockers"] if item["status"] == "OPEN"],
                      "failed_acceptance": [ac_id for ac_id, result in results.items() if result["status"] != "PASS"],
                      "verification_timestamp": now()}
            atomic(self.run_dir / "final_verification_bundle.json", bundle)
            event = self.adapter._event("ArtifactVerified", manifest["thread_id"],
                                        f"{turn_id}:final-bundle:{self.seq}",
                                        {"controller": "final_verification_bundle"})
            state = self.bridge.record_final_verification(event, work_id=work_id, bundle=bundle)
            append(self.run_dir / "receipts.jsonl", {"run_id": manifest["run_id"], "kind": "FINAL_VERIFICATION_BUNDLE",
                                                       "evidence_id": state["events"][-1]["evidence_id"]})

    def _work_id(self) -> str:
        state = self.bridge.restore_state()
        return state["runtime"]["plan"]["stages"][0]["name"]

    @staticmethod
    def _trust_classification(item_type: str | None) -> str:
        if item_type in TRUSTED_EXECUTION_ITEM_TYPES:
            return "TRUSTED_EXECUTION_EVENT"
        if item_type in USER_ITEM_TYPES:
            return "USER_EVENT"
        if item_type in MODEL_GENERATED_ITEM_TYPES:
            return "MODEL_GENERATED_EVENT"
        return "SYSTEM_EVENT"

    def _write_timeline(self, state: dict) -> None:
        entries = ["Thread started", "DeliverySession created", "Turn started"]
        entries += ["Tool receipt recorded" for _ in state["runtime"].get("evidence_ledger", [])]
        entries += ["Host completion attempt", "Completion gate executed"]
        entries += [f"Blocker {b['blocker_id']} OPEN for {b['ac_id']}" for b in state.get("open_blockers", [])]
        (self.run_dir / "event_timeline.md").write_text("\n".join(f"{i+1:02d} {e}" for i, e in enumerate(entries)) + "\n", encoding="utf-8")

    def _checksums(self):
        names = ["run_manifest.json", "raw_events.jsonl", "normalized_events.jsonl", "receipts.jsonl", "final_verdict.json", "event_timeline.md"]
        lines = [f"{sha256((self.run_dir / n).read_bytes()).hexdigest()}  {n}" for n in names if (self.run_dir / n).exists()]
        (self.run_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _version() -> str:
        return subprocess.run(["codex", "--version"], capture_output=True, text=True).stdout.strip()
    @staticmethod
    def _git_head(cwd: str) -> str:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["start", "inspect", "finalize"]); parser.add_argument("--run-dir", required=True); parser.add_argument("--cwd"); parser.add_argument("--task"); args = parser.parse_args()
    controller = PersistentCodexController(args.run_dir, secret="controller-local-secret")
    if args.action == "inspect": print(json.dumps(controller.inspect(), ensure_ascii=False))
    elif args.action == "finalize": print(json.dumps(controller.finalize(), ensure_ascii=False))
    else: raise SystemExit("start requires programmatic canonical contract")
