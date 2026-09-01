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
OPERATIONAL_DOCS = (
    "README.md",
    "docs/AGENT_INSTALL.md",
    "docs/INSTALL_AND_ACQUISITION.md",
    "docs/ENTERPRISE_VERSION_GOVERNANCE.md",
)


def _tagged_text(tag: str, relative_path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{tag}:{relative_path}"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", check=True).stdout


def _validate_tagged_release_source(tag: str, meta: dict) -> None:
    tagged_meta = json.loads(_tagged_text(tag, "共享/schema/RELEASE_METADATA.json"))
    for field in ("version", "tag", "release_asset", "release_channel"):
        if tagged_meta.get(field) != meta.get(field):
            raise SystemExit(f"tagged_metadata_mismatch:{field}")
    for relative_path in OPERATIONAL_DOCS:
        text = _tagged_text(tag, relative_path)
        current_lines = [line for line in text.splitlines() if any(marker in line for marker in (
            "current Stable", "当前 Stable", "当前 Valid Stable", "当前公开 Valid Stable"))]
        if not current_lines or any(tag not in line for line in current_lines):
            raise SystemExit(f"tagged_operational_document_version_mismatch:{relative_path}")


def build(output_dir: Path) -> dict:
    meta = json.loads(META.read_text(encoding="utf-8"))
    tag = meta["tag"]
    tag_commit = subprocess.run(
        ["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ROOT,
        capture_output=True, text=True, check=True).stdout.strip()
    if len(tag_commit) != 40:
        raise SystemExit("release_tag_does_not_resolve_to_commit")
    _validate_tagged_release_source(tag, meta)
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
