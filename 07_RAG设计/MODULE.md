---
name: enterprise-ai-project-delivery.07-rag
description: 模块07·RAG设计。知识源/索引/权限/引用/拒答四防（幻觉/越权/旧版/假引用）。Use when 交付涉及检索增强生成。
version: 3.0.8
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 07_RAG设计
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 07 RAG 设计（四防）

## Overview
RAG 方案须防幻觉、防越权、防旧版本、防假引用。数据源访问须在合同数据边界内。

## When to Use
交付物含知识检索/问答时。

## Core Process
1. 明确知识源、索引、权限、引用、拒答策略。
2. 用 [`references/RAG四防检查.md`](references/RAG四防检查.md) 逐项核验。
3. 引用可回溯（`共享/scripts/check_governance.py --kind rag` 防假引用、越权和旧版）。
4. 数据源须在合同 allowed 内；外部数据权限未批 → blocked。

## 反合理化 / Red Flags
- 引用无法回溯 → 假引用
- 让模型检索越权数据 → 越权
- 绕过知识库权限 → 越权

## Verification
- 四防用例通过；引用真实可回溯；无越权数据访问
