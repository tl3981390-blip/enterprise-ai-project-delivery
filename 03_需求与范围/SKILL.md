---
name: enterprise-ai-project-delivery.03-requirements-scope
description: 模块03·需求与范围。明确范围/非目标/禁止项/成功标准/关键约束，清除不确定词。Use when 需界定需求边界与验收标准。
version: 1.6.1
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 03_需求与范围
  language: zh-CN
  gate: 需先通过 S0 施工前理解门禁
---

# 03 需求与范围（范围 / 非目标 / 禁止项 / 成功标准 / 关键约束）

## Overview
在目标清晰的前提下锁定范围边界，明确「做什么、明确不做什么、禁止改什么、如何算成功/验收」。

## When to Use
UNDERSTANDING→PLAN 阶段，需锁定 work_scope / explicit_non_goals / forbidden_modify / success_criteria / key_constraints。

## Core Process
1. 从合同读取目标与现状。
2. 按 [`references/需求与验收模板.md`](references/需求与验收模板.md) 用 MoSCoW、EARS 与 Given-When-Then 明确范围与非目标。
3. 明确禁止项（forbidden_modify / forbidden_tools / key_constraints）。
4. 定义可判定的成功标准与验收标准。
5. 清除模糊词（禁用词检查，`共享/scripts/check_requirements.py`）。
6. 写回合同，provenance 明确来源。

## 反合理化 / Red Flags
- 验收标准不可判定（「尽量」「优化」）→ 退回
- 范围模糊导致 DRIFT 空间大 → 留阻塞性未知
- 与禁止项冲突的需求 → 需澄清，禁止擅自折中

## Verification
- success_criteria / acceptance_criteria 可机械判定
- 无禁用词；禁止项明确
- check_requirements 通过
