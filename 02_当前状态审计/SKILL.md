---
name: enterprise-ai-project-delivery.02-state-audit
description: 模块02·当前状态审计。判存量真实情况：已有什么/完成到哪/哪些真哪些假/哪些不可改，禁止默认从零。Use when 需确认项目现状与不可修改边界。
version: 1.4.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 02_当前状态审计
  language: zh-CN
  gate: 需先通过 S0 施工前理解门禁
---

# 02 当前状态审计（存量真实情况）

## Overview
用只读手段审计项目现状，结论必须有 PROJECT_EVIDENCE，禁止默认从零。识别「哪些是真的 / 哪些是假实现 / 哪些不可修改」。

## When to Use
UNDERSTANDING 阶段，需要确定 current_state / completed_scope / forbidden_modify。

## Core Process
1. READ/SEARCH/INSPECT 只读审计现有代码/配置/Git/文档。
2. 判断已完成程度与证据真伪（如有实现是 stub/假实现，明确标记）。
3. 标出不可修改区（外部系统、生产环境、明确禁止项）。
4. 结论写回合同 current_state / completed_scope，provenance=PROJECT_EVIDENCE；状态只允许 NOT_FOUND、PRESENT_UNVERIFIED、VERIFIED_WORKING、VERIFIED_BROKEN、BLOCKED。
5. `scripts/audit_scan.py`（只读扫描辅助）。

## 反合理化 / Red Flags
- 默认用户从零开始 → 未审计，错误
- 把假实现当真实现 → 假状态
- 扫描进入未授权/生产系统 → 越界（硬边界）

## Verification
- 每个存量结论有真实证据（git_head/file_path/api_response）
- forbidden_modify 与用户/环境证据一致
- 未触碰生产系统
