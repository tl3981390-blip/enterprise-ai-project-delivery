#!/usr/bin/env python3
"""collect_evidence.py — 把阶段产物打包成 Evidence Bundle + manifest.sha256。

用法：
  python collect_evidence.py --stage <stage> --evidence-dir <dir> [--help]
产出：
  <stage>/index.json + 原始证据 + manifest.sha256
说明：append-only，不覆盖既有证据；入库前 redact 由上层处理（不在此打包）。
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(stage: str, evidence_dir: Path):
    stage_dir = evidence_dir / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    files = sorted([f for f in stage_dir.iterdir() if f.is_file() and f.name != "index.json"])
    # 去重 SKILL/模板等大文本比重过高时由上层控制；这里仅收集未受忽略文件
    index = {
        "stage": stage,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": [{"name": f.name, "sha256": sha256_hex(f)} for f in files],
        "append_only": True,
    }
    (stage_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_lines = [f"{e['sha256']}  {e['name']}" for e in index["files"]]
    (stage_dir / "manifest.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(description="阶段Evidence打包")
    p.add_argument("--stage", required=True)
    p.add_argument("--evidence-dir", required=True, type=Path)
    args = p.parse_args()
    sys.exit(collect(args.stage, args.evidence_dir))


if __name__ == "__main__":
    main()