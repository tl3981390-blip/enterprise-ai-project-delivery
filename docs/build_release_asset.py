#!/usr/bin/env python3
"""Build the declared release ZIP reproducibly from an immutable Git tag."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "共享" / "schema" / "RELEASE_METADATA.json"


def build(output_dir: Path) -> dict:
    meta = json.loads(META.read_text(encoding="utf-8"))
    tag = meta["tag"]
    tag_commit = subprocess.run(
        ["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ROOT,
        capture_output=True, text=True, check=True).stdout.strip()
    if len(tag_commit) != 40:
        raise SystemExit("release_tag_does_not_resolve_to_commit")
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                      capture_output=True, text=True, check=True).stdout.strip():
        raise SystemExit("release_build_requires_clean_worktree")
    output_dir.mkdir(parents=True, exist_ok=True)
    asset = output_dir / meta["release_asset"]
    if asset.exists():
        raise SystemExit(f"release_asset_already_exists:{asset}")
    subprocess.run([
        "git", "archive", "--format=zip", "--prefix=enterprise-ai-project-delivery/",
        f"--output={asset}", tag], cwd=ROOT, check=True)
    payload = asset.read_bytes()
    return {"asset": asset.name, "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "source_tag": tag, "source_commit": tag_commit}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    print(json.dumps(build(parser.parse_args().output_dir), ensure_ascii=False, indent=2))

