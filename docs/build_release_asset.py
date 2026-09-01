#!/usr/bin/env python3
"""Build the declared release ZIP reproducibly from an immutable Git tag."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
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
    install_info = {
        "skill_id": meta["skill_id"], "version": meta["version"],
        "mode": "SELF_CONTAINED_FULL_CORE",
        "canonical_identity": f"tag {tag} -> commit {tag_commit}",
        "metadata_source": "共享/schema/RELEASE_METADATA.json",
        "note": "release-built self-contained copy; no author-local path dependency",
    }
    # INSTALL_INFO is a resolved release fact and cannot live in the tagged source
    # without self-reference. Add it with a fixed timestamp for reproducible bytes.
    info = zipfile.ZipInfo("enterprise-ai-project-delivery/INSTALL_INFO.json",
                           date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with zipfile.ZipFile(asset, "a") as archive:
        archive.writestr(info, json.dumps(install_info, ensure_ascii=False,
                                          indent=2, sort_keys=True) + "\n")
    payload = asset.read_bytes()
    return {"asset": asset.name, "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "source_tag": tag, "source_commit": tag_commit}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    print(json.dumps(build(parser.parse_args().output_dir), ensure_ascii=False, indent=2))
