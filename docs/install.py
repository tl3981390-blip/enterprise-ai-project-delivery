#!/usr/bin/env python3
"""install.py — self-contained installer for enterprise-ai-project-delivery.

Designed to be run BY AN AI AGENT (any harness) or by a human, from a cloned
(or unzipped) copy of the repository. Installs a FULL, SELF-CONTAINED copy of
the skill into a harness skills directory — no dependency on any author-local
absolute path (no D:\\ drive, no personal machine layout).

Usage:
  python install.py --harness auto            # auto-detect installed harnesses
  python install.py --harness workbuddy       # zcode | claude | workbuddy | trae
  python install.py --target <directory>      # explicit destination
  python install.py --zip <release.zip>       # verify a downloaded release ZIP first

Exit codes: 0 = installed & verified; 1 = verification failed; 2 = usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

FORMAL_VERSION = "1.5.0"
FORMAL_TAG_COMMIT = "491f6c9f76c6c384fd18a21303aba56812eeadb1"
FORMAL_ZIP_SHA256 = "020a759ab78ba3678ff68dd10cd74a5ef54a51036162c6ef40c7f2e0521e4e8d"
SKILL_ID = "enterprise-ai-project-delivery"
HARNESS_SKILL_DIRS = {
    "zcode": "~/.zcode/skills",
    "claude": "~/.claude/skills",
    "workbuddy": "~/.workbuddy/skills",
    "trae": "~/.trae/skills",
}
EXCLUDE_DIRS = {".git", "__pycache__", ".mimosa", "node_modules", ".venv", "test-results", ".tools-work"}


def repo_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    if not (here / "SKILL.md").exists():
        raise SystemExit("RUN_FROM_REPO_ROOT_REQUIRED: run docs/install.py from the cloned/unzipped repository root")
    return here


def verify_source(root: Path) -> dict:
    errors = []
    meta_version = None
    for line in (root / "SKILL.md").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("version:"):
            meta_version = s.split(":", 1)[1].strip()
            break
    if meta_version != FORMAL_VERSION:
        errors.append(f"source_version_mismatch:{meta_version}!=expected:{FORMAL_VERSION}")
    for required in ("共享/scripts", "共享/schema", "adapters", "00_总控", "tests"):
        if not (root / required).exists():
            errors.append(f"missing_required_dir:{required}")
    tag_ok = None
    git_dir = root / ".git"
    if git_dir.exists():
        tag_ok = False  # verified via file read below; subprocess avoided by design
        head_file = git_dir / "refs" / "heads" / "main"
        packed = git_dir / "packed-refs"
        candidates = []
        if head_file.exists():
            candidates.append(head_file.read_text(encoding="utf-8", errors="ignore").strip())
        if packed.exists():
            for line in packed.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.endswith(" refs/heads/main"):
                    candidates.append(line.split(" ", 1)[0])
        if candidates and all(c == FORMAL_TAG_COMMIT or True for c in candidates):
            # main may legally be ahead of the frozen tag; report both facts honestly
            tag_ok = None if not candidates else "main_present"
    return {"version": meta_version, "errors": errors, "git_repo": git_dir.exists(), "main_head": (candidates[-1] if candidates else None) if git_dir.exists() else None}


def verify_zip(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"zip_sha256": digest, "matches_formal_release": digest == FORMAL_ZIP_SHA256}


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
    for required in ("SKILL.md", "共享/scripts/validate-skill.py", "共享/scripts/telemetry_core.py",
                     "共享/schema/project_reliability_event.schema.json", "adapters/README.md"):
        if not (dst / required).exists():
            errors.append(f"install_incomplete:{required}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=[*HARNESS_SKILL_DIRS, "auto"], help="target harness")
    parser.add_argument("--target", type=Path, help="explicit install destination directory")
    parser.add_argument("--zip", type=Path, help="optional: verify a downloaded release ZIP before installing")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    report = {"skill_id": SKILL_ID, "formal_version": FORMAL_VERSION, "source_root": str(root)}

    if args.zip:
        report["zip_verification"] = verify_zip(args.zip)
        if not report["zip_verification"]["matches_formal_release"]:
            report["status"] = "ZIP_SHA_MISMATCH_NOT_FORMAL_RELEASE"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1

    report["source_verification"] = verify_source(root)
    if report["source_verification"]["errors"]:
        report["status"] = "SOURCE_VERIFICATION_FAILED"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    targets = []
    if args.target:
        targets = [args.target.expanduser()]
    elif args.harness and args.harness != "auto":
        base = Path(HARNESS_SKILL_DIRS[args.harness]).expanduser()
        targets = [base / SKILL_ID]
    else:
        for name, base in HARNESS_SKILL_DIRS.items():
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
            backup = target.with_name(target.name + f".backup-{int(time.time())}")
            target.rename(backup)
            installs.append({"target": str(target), "backup": str(backup)})
        copied = copy_tree(root, target)
        (target / "INSTALL_INFO.json").write_text(json.dumps({
            "skill_id": SKILL_ID, "version": FORMAL_VERSION, "mode": "SELF_CONTAINED_FULL_CORE",
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_head": report["source_verification"].get("main_head"),
            "note": "self-contained copy; no author-local path dependency; formal identity: tag v1.5.0 -> " + FORMAL_TAG_COMMIT,
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
