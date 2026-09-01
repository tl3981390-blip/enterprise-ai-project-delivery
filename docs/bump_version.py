#!/usr/bin/env python3
"""bump_version.py — canonical release-version bump (single source of truth).
Reads 共享/schema/RELEASE_METADATA.json, updates version/tag/asset fields, then syncs
root SKILL.md + all internal MODULE.md version fields so no file maintains its own copy.
Usage: python bump_version.py 1.6.0  (commit/sha256 stay PENDING until the tag exists)."""
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # docs/bump_version.py -> repo root
META = ROOT / "共享" / "schema" / "RELEASE_METADATA.json"
MANIFEST = ROOT / "harness_manifest.json"


def bump(new_version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+)?", new_version):
        raise SystemExit(f"invalid semver: {new_version}")
    meta = json.loads(META.read_text(encoding="utf-8"))
    old = meta["version"]
    meta["version"] = new_version
    meta["tag"] = f"v{new_version}"
    meta["release_asset"] = f"enterprise-ai-project-delivery-v{new_version}.zip"
    meta["github_release"] = f"v{new_version}"
    meta["release_channel"] = "candidate" if "-" in new_version else "stable"
    # Declaration model: never write a self-referential commit hash or a pre-computed
    # asset SHA into Git-tracked metadata. Both are resolved at install/release time.
    meta.pop("release_commit", None)
    meta.pop("asset_sha256", None)
    meta.pop("release_manifest", None)
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["version"] = new_version
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n",
                        encoding="utf-8")
    targets = [ROOT / "SKILL.md"] + [d / "MODULE.md" for d in ROOT.iterdir()
                                     if d.is_dir() and re.fullmatch(r"\d\d_.*", d.name) and (d / "MODULE.md").exists()]
    for p in targets:
        resolved = p.resolve()
        if ROOT not in resolved.parents and resolved != ROOT / "SKILL.md":
            raise SystemExit(f"path_traversal_blocked:{p} escapes repo root")
        text = resolved.read_text(encoding="utf-8")
        text, count = re.subn(r"(?m)^(\s*version:\s*)\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+)?\s*$",
                              rf"\g<1>{new_version}", text, count=1)
        if count != 1:
            raise SystemExit(f"version_field_not_found:{p}")
        resolved.write_text(text, encoding="utf-8", newline="")
    print(json.dumps({"bumped": f"{old} -> {new_version}",
                      "files_synced": len(targets) + 2}, ensure_ascii=False))


if __name__ == "__main__":
    bump(sys.argv[1] if len(sys.argv) > 1 else "")
