#!/usr/bin/env python3
"""check_benchmark_contamination.py — BENCHMARK_PROTOCOL_V2 污染检测。

 PRIVATE_BENCHMARK_SPEC（含测试意图、事件名、门禁 id）与 PUBLIC_BUSINESS_EVENT（施工 Agent
 可见文本）必须分离。Controller 若把私有标记泄漏进可见文本，结果只能标记
 CONTROLLER_CONTAMINATED，不得用于行为效果证明。

用法：
  python check_benchmark_contamination.py --benchmark <spec.json> [--text <agent-visible.txt>]
  spec.json: {"private_markers": ["USER_SCOPE_CHANGE", ...], "public_text": "..."} 或用 --text 提供文件
输出：{"status":"PASS|CONTROLLER_CONTAMINATED","leaked_markers":[...]}
"""
import argparse, json, sys
from pathlib import Path


def check(spec: dict, text: str) -> dict:
    leaked = sorted({m for m in spec.get("private_markers", []) if m and m in text})
    return {"status": "CONTROLLER_CONTAMINATED" if leaked else "PASS", "leaked_markers": leaked}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, type=Path)
    parser.add_argument("--text", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.benchmark.read_text(encoding="utf-8"))
    text = args.text.read_text(encoding="utf-8") if args.text else spec.get("public_text", "")
    result = check(spec, text)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
