#!/usr/bin/env python3
"""bump_version.py — canonical release-version bump (single source of truth).
Reads 共享/schema/RELEASE_METADATA.json, updates version/tag/asset fields, then syncs
root SKILL.md + all module SKILL.md version: fields so no file maintains its own copy.
Usage: python bump_version.py 1.6.0  (commit/sha256 stay PENDING until the tag exists)."""
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # docs/bump_version.py -> repo root
META = ROOT / "共享" / "schema" / "RELEASE_METADATA.json"


def bump(new_version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", new_version):
        raise SystemExit(f"invalid semver: {new_version}")
    meta = json.loads(META.read_text(encoding="utf-8"))
    old = meta["version"]
    meta["version"] = new_version
    meta["tag"] = f"v{new_version}"
    meta["release_asset"] = f"enterprise-ai-project-delivery-v{new_version}.zip"
    meta["asset_sha256"] = "PENDING_UNTIL_RELEASE"
    meta["github_release"] = f"v{new_version}"
    # release_commit is only known once the tag exists; keep the previous value so
    # a tag-mismatch is never silently accepted. The release pipeline updates it.
    meta.setdefault("release_commit", meta.get("release_commit"))
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    targets = [ROOT / "SKILL.md"] + [d / "SKILL.md" for d in ROOT.iterdir()
                                     if d.is_dir() and re.fullmatch(r"\d\d_.*", d.name) and (d / "SKILL.md").exists()]
    for p in targets:
        resolved = p.resolve()
        if ROOT not in resolved.parents and resolved != ROOT / "SKILL.md":
            raise SystemExit(f"path_traversal_blocked:{p} escapes repo root")
        text = resolved.read_text(encoding="utf-8")
        text = text.replace(f"version: {old}", f"version: {new_version}")
        resolved.write_text(text, encoding="utf-8", newline="")
    print(json.dumps({"bumped": f"{old} -> {new_version}", "files_synced": len(targets) + 1}, ensure_ascii=False))


if __name__ == "__main__":
    bump(sys.argv[1] if len(sys.argv) > 1 else "")
