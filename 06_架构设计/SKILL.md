---
name: enterprise-ai-project-delivery.06-architecture
description: 模块06·架构设计。架构/组件/接口/部署形态设计，架构评审通过后进入施工。Use when 需把规格落实为架构与模块边界。
version: 1.2.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 06_架构设计
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 06 架构设计

## Overview
在合同范围内设计架构/组件/接口/部署形态，评审通过方允许进入施工。

## When to Use
规格与测试策略就绪后，产出架构设计。

## Core Process
1. 按 [`references/架构决策模板.md`](references/架构决策模板.md) 设计组件与接口、数据流、部署形态、被否决备选与回滚。
2. 逐项与合同 work_scope / allowed_modify / forbidden_modify 对账。
3. 架构评审（`references/架构评审清单.md`），识别风险与不可行项。
4. 涉外部系统/权限 → 需要在合同允许范围，否则 blocked。

## 反合理化 / Red Flags
- 架构引入合同外系统/依赖 → DRIFT
- 需要越权连接 → blocked
- 架构评审草率 → 退回

## Verification
- 架构评审清单通过
- 架构在合同 allowed_modify 内
- 无越权/外部连接
