#!/usr/bin/env python3
"""validate-skill.py — 结构/frontmatter/引用/版本/License 校验器（agentskills-standard 对齐）。

用法：
  python validate-skill.py --root <skill_dir>
  python validate-skill.py --help
退出码：0 = 全部通过（0 ERROR）；1 = 存在错误。
stdout 结构化（每行 JSON），方便 harness/CI 解析。
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata"}
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+)?(\+[0-9A-Za-z-]+)?$")
MODULES = [
    "00_总控", "01_项目理解", "02_当前状态审计", "03_需求与范围", "04_SDD规格",
    "05_TDD与测试策略", "06_架构设计", "07_RAG设计", "08_Agent设计",
    "09_MCP与工具权限网关", "10_企业治理与合规", "11_施工管理与增量实现",
    "12_失败处理与恢复", "13_浏览器真实验收", "14_多角色验收",
    "15_Evidence与防假验收", "16_部署", "17_License与合规", "18_升级与回滚",
    "19_最终交付与经验沉淀",
]


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None, "缺少 frontmatter（需以 --- 开头）"
    if text.count("---") < 2:
        return None, "frontmatter 格式不完整"
    _, fm, _remain = text.split("---", 2)
    data = {}
    for line in fm.strip().splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip()
    return (data, None) if data else (None, "frontmatter 为空")


def validate_skill(root: Path):
    errors = []
    warnings = []

    base = root if root.name == "SKILL.md" else root
    main_skill = base / "SKILL.md" if root.name != "SKILL.md" else base

    # 1) frontmatter 主 SKILL
    if not main_skill.exists():
        errors.append("缺少根 SKILL.md")
    else:
        data, err = parse_frontmatter(main_skill.read_text(encoding="utf-8"))
        if err:
            errors.append(f"{main_skill.name}: {err}")
        else:
            missing = REQUIRED_FRONTMATTER - set(data)
            if missing:
                errors.append(f"{main_skill.name}: 缺 frontmatter 字段 {sorted(missing)}")
            if data.get("version") and not SEMVER_RE.match(data["version"]):
                errors.append(f"{main_skill.name}: version 非 semver: {data.get('version')}")
            if len(data.get("description", "")) > 1024:
                errors.append(f"{main_skill.name}: description 超过 1024 字符")

    # 2) 每个模块必须有 SKILL.md + frontmatter + 版本
    for mod in MODULES:
        mdir = base / mod
        sk = mdir / "SKILL.md"
        if not mdir.exists():
            errors.append(f"{mod}: 目录不存在（骨架要求完整模块树）")
            continue
        if not sk.exists():
            errors.append(f"{mod}: 缺少 SKILL.md")
            continue
        data, err = parse_frontmatter(sk.read_text(encoding="utf-8"))
        if err:
            errors.append(f"{mod}/SKILL.md: {err}")
        elif data.get("version") and not SEMVER_RE.match(data["version"]):
            errors.append(f"{mod}/SKILL.md: version 非 semver")

    # 3) references/scripts 引用路径存在的文件（markdown 内相对链接抽查）
    ref_pattern = re.compile(r"\]\(([^)#]+\.(?:md|py|json))")
    for md in list(base.rglob("*.md")):
        rel = md.relative_to(base)
        for m in ref_pattern.finditer(md.read_text(encoding="utf-8")):
            link = m.group(1)
            if link.startswith(("http", "#", "mailto:")):
                continue
            target = (md.parent / link).resolve()
            if not target.exists():
                warnings.append(f"引用缺失: {rel}: {link}")

    # 4) schema 文件存在且合法 JSON
    schema_dir = base / "共享" / "schema"
    for sf in schema_dir.glob("*.json") if schema_dir.exists() else []:
        try:
            json.loads(sf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"schema 非合法 JSON: {sf.name}: {e}")

    # 输出
    result = {"errors": len(errors), "warnings": len(warnings), "error_list": errors, "warning_list": warnings}
    for e in errors:
        print(json.dumps({"level": "error", "msg": e}, ensure_ascii=False))
    for w in warnings:
        print(json.dumps({"level": "warning", "msg": w}, ensure_ascii=False))
    print(json.dumps({"summary": f"{len(errors)} errors, {len(warnings)} warnings"}, ensure_ascii=False))
    return 1 if errors else 0


def main():
    p = argparse.ArgumentParser(description="企业AI项目交付 Skill 结构校验器")
    p.add_argument("--root", required=True, help="Skill 目录或主 SKILL.md 的路径")
    args = p.parse_args()
    sys.exit(validate_skill(Path(args.root)))


if __name__ == "__main__":
    main()