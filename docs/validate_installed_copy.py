#!/usr/bin/env python3
"""Validate an installed copy without creating Python bytecode or test caches."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
POLLUTION_NAMES = {".git", ".mimosa", ".pytest_cache", "__pycache__"}


def pollution(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*")
                  if path.is_dir() and path.name in POLLUTION_NAMES)


def validate(root: Path) -> dict:
    root = root.resolve()
    before = pollution(root)
    if before:
        return {"status": "INSTALL_COPY_POLLUTED_BEFORE_VALIDATION", "pollution": before}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_ADDOPTS="-p no:cacheprovider")
    validator = subprocess.run(
        [sys.executable, str(root / "共享" / "scripts" / "validate-skill.py"),
         "--root", str(root)], cwd=root, env=env, text=True)
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            str(root / "tests")], cwd=root, env=env, text=True)
    after = pollution(root)
    status = "PASS" if validator.returncode == tests.returncode == 0 and not after else "FAIL"
    return {"status": status, "validator_exit": validator.returncode,
            "tests_exit": tests.returncode, "pollution_after": after}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    result = validate(parser.parse_args().root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

