---
name: enterprise-ai-project-delivery.08-agent
description: 模块08·Agent设计。角色职责分离，多 Agent 适度，避免过度 Agent 化。Use when 交付涉及多角色/多agent协作。
version: 3.0.9
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 08_Agent设计
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 08 Agent 设计（角色职责分离）

## Overview
按逻辑角色分离职责，仅在需要时才用多 Agent，避免过度 Agent 化。

## When to Use
交付含 Agent/多角色协作设计时。

## Core Process
1. 明确角色与职责边界（`references/职责分离矩阵.md`）。
2. 一个角色尽量由一个 Skill/命令承载，必要时才拆 Agent。
3. 角色权限与合同 allowed_tools 一致，避免越权角色。
4. executor 不得批准自身高风险动作；critic 只能提出证据化问题，不能代替授权人签核或扩张权限。

## 反合理化 / Red Flags
- 为「显得先进」拆多 Agent → 过度
- 角色权限超出合同 → 越权
- 单一 Agent 又可研发又可验收 → 违反独立验收

## Verification
- 职责分离清单过；角色权限在合同内；无「自己验收自己」
