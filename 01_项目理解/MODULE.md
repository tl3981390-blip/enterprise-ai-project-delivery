---
name: enterprise-ai-project-delivery.01-understanding
description: 模块01·项目理解。回答用户真正要解决什么问题、为什么做、最终想得到什么结果与业务价值。Use when 需明确用户真实目标与最终交付物。最高原则：结论需标注来源，AI_INFERRED 不能冒充用户要求。
version: 3.0.7
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 01_项目理解
  language: zh-CN
  gate: 需先通过 S0 施工前理解门禁
---

# 01 项目理解（用户真正目标 / 最终结果 / 业务价值）

## Overview
澄清「为什么做 / 给谁用 / 价值」，输出可评审的目标声明。先于任何编码。

## When to Use
进入复杂项目交付任务的 UNDERSTANDING 阶段，尚未明确 user_real_goal / business_goal / final_deliverable 时。

## Core Process
1. 读入已锁定的任务理解合同（user_real_goal / business_goal / final_deliverable），按 [`references/最少提问法.md`](references/最少提问法.md) 只追问会改变方案的未知项。
2. 逐项核对来源（USER_EXPLICIT / USER_PREVIOUSLY_CONFIRMED / PROJECT_EVIDENCE / SYSTEM_OBSERVED / AI_INFERRED）。
3. 缺用户真实目标/最终结果/业务价值 → 标记缺失，返回 S0 理解门禁，禁止推进。
4. 产出 `references/最少提问法.md` 对应内容，更新合同 provenance。

## 反合理化 / Red Flags
- 把「给个大概目的」当完全理解 → 不足
- 用 AI_INFERRED 填充「用户真实目标」并冒充用户要求 → 拒绝
- 目标未定就跳到方案 → 违反最高原则

## Verification
- 合同三要素（user_real_goal/business_goal/final_deliverable）非空且来源非纯 AI_INFERRED
- `共享/scripts/check_understanding_gate.py` 结构校验通过
