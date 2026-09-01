---
name: enterprise-ai-project-delivery.04-sdd
description: 模块04·SDD规格。先规格后编码，产出全维度规格（机械可检查）。Use when 需把需求转成可施工、可检查的规格。
version: 2.0.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 04_SDD规格
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 04 SDD 规格（先规格后编码）

## Overview
在写任何业务代码前，产出完整、可机械检查的规格。规格缺项即 blocked。

## When to Use
需求与范围明确后，进入设计前，将范围固化为规格。

## Core Process
1. 读取需求规格（03）。
2. 产出全维度规格（功能/数据/接口/错误/边界/性能），模板见 [`references/SDD规格模板.md`](references/SDD规格模板.md)，并沿用共享 SDD 流程而非另造流程。
3. 每个规格项标记是否可机检；不可机检项列出判定方式。
4. 与合同对账（DRIFT），写规格动作须在 work_scope 内。

## 反合理化 / Red Flags
- 规格缺项 → blocked
- 规格只写需求不写可检查点 → 无效
- 规格内容超出合同范围 → DRIFT

## Verification
- `共享/scripts/validate_design.py --kind spec` 通过
- 无合同外能力
- check_plan_alignment 对该规格动作 PASS
