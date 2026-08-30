#!/usr/bin/env python3
"""Reject project telemetry that is not bound to this canonical recorder and integrity verifier."""
import argparse, hashlib, json, sys
from pathlib import Path
from telemetry_core import verify_chain


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--core-root", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = args.core_root.resolve()
    recorder = root / "共享" / "scripts" / "record_delivery_event.py"
    verifier = root / "共享" / "scripts" / "calculate_delivery_metrics.py"
    errors = []
    if manifest.get("skill_id") != "enterprise-ai-project-delivery": errors.append("skill_id_invalid")
    if manifest.get("recorder_sha256") != sha256(recorder): errors.append("recorder_hash_mismatch")
    if manifest.get("verifier_sha256") != sha256(verifier): errors.append("verifier_hash_mismatch")
    log = Path(manifest.get("log", "")); anchor = Path(manifest.get("anchor", ""))
    if not log.is_file() or not anchor.is_file(): errors.append("telemetry_artifact_missing")
    else:
        _events, integrity = verify_chain(log, anchor)
        errors.extend(f"integrity:{item}" for item in integrity)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
