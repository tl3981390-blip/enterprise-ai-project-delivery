#!/usr/bin/env python3
"""Validate licensed upstream adaptation references."""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = {
    "SDD流程与规格模板.md", "Plan模板.md", "Tasks与分级仪式.md",
    "需求表达与最少提问.md", "Signoff与生产检查清单.md", "Traceability与收敛.md",
}
COMMITS = {
    "51e52be6c3b26fed3ff5424c671f4a559519a759",
    "939b1e74a8b27f963153df5f420170571d0e28e6",
    "a75bd6aa457123cab22d6ce7edd220faafbc043c",
}

def validate(refs: Path) -> list[str]:
    errors = []
    for name in sorted(REQUIRED):
        path = refs / name
        if not path.exists():
            errors.append(f"missing:{name}")
            continue
        first = path.read_text(encoding="utf-8").splitlines()[0]
        if not (first.startswith("<!-- Source:") and "License: MIT" in first and "Adaptation:" in first):
            errors.append(f"invalid_header:{name}")
        if not any(commit in first for commit in COMMITS):
            errors.append(f"unlocked_source:{name}")
    index = refs / "上游吸收索引.md"
    if not index.exists():
        errors.append("missing:上游吸收索引.md")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--references", required=True, type=Path)
    args = parser.parse_args()
    errors = validate(args.references)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
