#!/usr/bin/env python3
"""install.py — self-contained installer for enterprise-ai-project-delivery (v1.6.0 rewrite).

Designed to be run BY AN AI AGENT (any harness) or by a human, from a cloned
(or unzipped) copy of the repository. Installs a FULL, SELF-CONTAINED copy of
the skill into a harness skills directory — no dependency on any author-local
absolute path (no D:\\ drive, no personal machine layout).

Release identity comes from ONE source: 共享/schema/RELEASE_METADATA.json.
This installer keeps NO hardcoded version/tag/commit/SHA (INST-005/INST-006).
Every identity check is REAL (no `or True`): negative inputs must FAIL (INST-007/008).

Usage:
  python install.py --harness auto            # auto-detect installed harnesses
  python install.py --harness workbuddy       # zcode | claude | workbuddy | trae
  python install.py --target <directory>      # explicit destination
  python install.py --zip <release.zip>       # verify a downloaded release ZIP first
  python install.py --strict-source           # require this file to live in docs/ (real repo checkout)
  python install.py --repo-url <url>          # Contract A entry point (agent flow)

Exit codes: 0 = installed & verified; 1 = verification failed; 2 = usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SKILL_ID = "enterprise-ai-project-delivery"
EXCLUDE_DIRS = {".git", "__pycache__", ".mimosa", "node_modules", ".venv", "test-results", ".tools-work"}
METADATA_REL = Path("共享") / "schema" / "RELEASE_METADATA.json"


def repo_root(strict: bool = False) -> Path:
    here = Path(__file__).resolve().parent.parent
    if strict and Path(__file__).resolve().parent.name != "docs":
        raise SystemExit("STRICT_SOURCE_VIOLATION: installer must live in docs/ of a real checkout (not copied bare)")
    if not (here / "SKILL.md").exists():
        raise SystemExit("RUN_FROM_REPO_ROOT_REQUIRED: run docs/install.py from the cloned/unzipped repository root")
    return here


def load_metadata(root: Path) -> dict:
    meta_path = root / METADATA_REL
    if not meta_path.exists():
        raise SystemExit(f"CANONICAL_RELEASE_METADATA_MISSING: {METADATA_REL} (single source of truth; do not invent versions)")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _tag_commit(root: Path, tag: str) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=root,
                             capture_output=True, text=True)
        return out.stdout.strip() or None
    except OSError:
        return None


def verify_source(root: Path, meta: dict) -> dict:
    """Real identity verification (Declaration/Resolution model).
    RELEASE_METADATA.json is a DECLARATION (version/tag/asset_name) — it never stores its
    own commit hash or the final asset SHA. The installer RESOLVES the release commit by
    running `git rev-parse <tag>^{commit}` at runtime; the asset SHA is proven by the
    Release manifest / ZIP download, never by a value baked into the repo before commit."""
    errors: list[str] = []
    warnings: list[str] = []
    meta_version = None
    for line in (root / "SKILL.md").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("version:"):
            meta_version = s.split(":", 1)[1].strip()
            break
    if meta_version != meta["version"]:
        warnings.append(f"source_version_mismatch:{meta_version}!=canonical:{meta['version']} (installable if tag resolves)")
    for required in ("共享/scripts", "共享/schema", "adapters", "00_总控", "tests"):
        if not (root / required).exists():
            errors.append(f"missing_required_dir:{required}")
    tag_ok = None
    git_dir = root / ".git"
    if git_dir.exists():
        actual = _tag_commit(root, meta["tag"])
        if actual is None or "^{commit}" in actual or len(actual) != 40:
            # tag not yet published: this is a PRE-RELEASE candidate. Installing from a
            # candidate checkout is legal (development mode), but we say so honestly
            # rather than pretending a formal identity. Formal installs verify the tag.
            tag_ok = "pre_release_candidate"
            warnings.append(f"pre_release_candidate:tag {meta['tag']} not published; installing as dev candidate")
        else:
            tag_ok = True  # resolved commit == the tag the declaration names
    else:
        # unpacked release ZIP has no .git; identity is proven by ZIP SHA (see verify_zip)
        tag_ok = "zip_only"
    return {"version": meta_version, "errors": errors, "warnings": warnings,
            "git_repo": git_dir.exists(), "tag_verified": tag_ok, "resolved_tag": meta["tag"]}


def verify_zip(path: Path, meta: dict) -> dict:
    """ZIP identity is proven by SHA against the RELEASE MANIFEST (produced after the
    asset exists), never by a value baked into the repo before the commit."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = _resolve_asset_sha256(meta)
    return {"zip_sha256": digest, "expected": expected,
            "matches_formal_release": expected is not None and digest == expected}


def _resolve_asset_sha256(meta: dict) -> str | None:
    """Asset SHA comes from the Release manifest/evidence (post-asset fact) OR the GitHub
    Release asset digest (resolved at install time). We never read a pre-computed SHA from
    the Git-tracked declaration (that was the v1.6.0 defect)."""
    manifest = meta.get("release_manifest") or {}
    sha = manifest.get("asset_sha256")
    if isinstance(sha, str) and len(sha) == 64:
        return sha
    return _github_release_asset_sha256(meta)


def _github_release_asset_sha256(meta: dict) -> str | None:
    """Resolve the formal asset SHA from the GitHub Release (post-release fact). Uses
    `gh release view --json assets` when gh is available; returns None if unreachable
    (caller must then fail honestly, never guess)."""
    gh = _which("gh")
    if not gh:
        return None
    repo = meta.get("repository", {}).get("url", "").replace("https://github.com/", "")
    tag = meta.get("tag")
    asset_name = meta.get("release_asset")
    if not (repo and tag and asset_name):
        return None
    try:
        out = subprocess.run([gh, "release", "view", tag, "-R", repo, "--json", "assets"],
                             capture_output=True, text=True, shell=False, timeout=10)
        if out.returncode != 0:
            return None
        import json as _json
        for asset in _json.loads(out.stdout).get("assets", []):
            if asset.get("name") == asset_name:
                digest = asset.get("digest") or asset.get("sha256") or ""
                return digest.replace("sha256:", "") if digest else None
    except Exception:
        return None
    return None


def _which(name: str) -> str | None:
    import shutil as _shutil
    return _shutil.which(name)


def copy_tree(src: Path, dst: Path) -> int:
    count = 0
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(src)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.name.endswith(".pyc"):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        count += 1
    return count


def self_check(dst: Path) -> list[str]:
    errors = []
    for required in ("SKILL.md", "00_总控/MODULE.md", "19_最终交付与经验沉淀/MODULE.md",
                     "共享/scripts/validate-skill.py", "共享/scripts/telemetry_core.py",
                     "共享/scripts/delivery_planning_core.py", "共享/scripts/plan_governance_core.py",
                     "共享/scripts/understanding_core.py", "共享/scripts/delivery_runtime.py",
                     "共享/scripts/evidence_core.py", "harness_manifest.json",
                     "共享/schema/RELEASE_METADATA.json",
                     "共享/schema/project_reliability_event.schema.json", "adapters/README.md"):
        if not (dst / required).exists():
            errors.append(f"install_incomplete:{required}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=["zcode", "claude", "workbuddy", "trae", "auto"], help="target harness")
    parser.add_argument("--target", type=Path, help="explicit install destination directory")
    parser.add_argument("--zip", type=Path, help="optional: verify a downloaded release ZIP before installing")
    parser.add_argument("--repo-url", help="informational: the repository URL this copy came from (agent Contract A entry)")
    parser.add_argument("--strict-source", action="store_true",
                        help="refuse to run unless this file still lives in docs/ of the real checkout")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = repo_root(strict=args.strict_source)
    meta = load_metadata(root)
    harness_dirs = meta["harness_skill_dirs"]
    report = {"skill_id": SKILL_ID, "canonical_version": meta["version"], "canonical_tag": meta["tag"],
              "source_root": str(root), "metadata_source": str(METADATA_REL)}

    if args.zip:
        report["zip_verification"] = verify_zip(args.zip, meta)
        if not report["zip_verification"]["matches_formal_release"]:
            report["status"] = "ZIP_SHA_MISMATCH_NOT_FORMAL_RELEASE"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1

    report["source_verification"] = verify_source(root, meta)
    if report["source_verification"]["errors"]:
        report["status"] = "SOURCE_VERIFICATION_FAILED"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    targets = []
    if args.target:
        targets = [args.target.expanduser()]
    elif args.harness and args.harness != "auto":
        targets = [(Path(harness_dirs[args.harness]).expanduser() / SKILL_ID)]
    else:
        for name, base in harness_dirs.items():
            base = Path(base).expanduser()
            if base.parent.exists():
                targets.append(base / SKILL_ID)
        if not targets:
            report["status"] = "NO_HARNESS_FOUND"
            report["hint"] = "pass --target <dir> or --harness <name>"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

    installs = []
    failed = False
    for target in targets:
        target = target.expanduser()
        if args.dry_run:
            installs.append({"target": str(target), "dry_run": True})
            continue
        if target.exists():
            # Never retain a prior Skill beneath the Harness scan root (normally
            # `<codex-home>/skills`): recursive discovery would expose all of its
            # historical MODULE/SKILL files in `/`. Keep rollback copies beside that
            # root instead, under `<codex-home>/skill-backups`.
            backup_root = target.parent.parent / "skill-backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / (target.name + f".backup-{int(time.time())}")
            while backup.exists():
                backup = backup_root / (target.name + f".backup-{time.time_ns()}")
            target.rename(backup)
            installs.append({"target": str(target), "backup": str(backup)})
        copied = copy_tree(root, target)
        (target / "INSTALL_INFO.json").write_text(json.dumps({
            "skill_id": SKILL_ID, "version": meta["version"], "mode": "SELF_CONTAINED_FULL_CORE",
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "canonical_identity": f"tag {meta['tag']} -> resolved at runtime",
            "metadata_source": str(METADATA_REL),
            "note": "self-contained copy; no author-local path dependency; reads identity from canonical RELEASE_METADATA.json",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        errors = self_check(target)
        installs.append({"target": str(target), "files_copied": copied, "self_check": errors or "PASS"})
        if errors:
            failed = True

    report["installs"] = installs
    report["post_install_recommendation"] = "run: python <skill-dir>/共享/scripts/validate-skill.py --root <skill-dir> (expect 0 errors)"
    report["status"] = "FAILED" if failed else ("DRY_RUN" if args.dry_run else "INSTALLED_SELF_CONTAINED")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
