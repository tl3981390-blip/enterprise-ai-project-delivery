---
name: enterprise-ai-project-delivery.11-construction
description: 模块11·施工管理与增量实现。增量实现+DoD，防一次性大段施工。Use when 进入 EXECUTING 后的实际施工编排。
version: 1.1.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 11_施工管理与增量实现
  language: zh-CN
  gate: 需 READY_TO_EXECUTE 后（开放写权限）
---

# 11 施工管理与增量实现

施工中由 AI 自身错误导致已执行工作重做时追加 AI_REWORK_EVENT；用户批准的范围变更只能记 USER_SCOPE_CHANGE，外部网络/服务故障不能记 AI 返工。Stage 开始、首次通过和重新打开分别追加 STAGE_STARTED、STAGE_PASSED、STAGE_REOPENED。

## Overview
在 READY_TO_EXECUTE 后按增量实现，每增量测试+提交，遵守 DoD。始终接受 DRIFT_CHECK。

## When to Use
进入 EXECUTING，开放 WRITE/EDIT/EXECUTE 后。

## Core Process
1. 拆可验收增量（按 `references/Definition-of-Done.md`）。
2. 每增量实现→测试→提交→证据，不一次性大段施工。
3. 任务采用共享分级仪式与单次可完成格式；Quick 也不得跳过权限和证据门禁。
4. 每动作过 DRIFT_CHECK（与合同对账）。
5. 越权动作 → EXECUTION_BLOCKED。

## 反合理化 / Red Flags
- 一次性大段写 → 违反增量
- 未测就宣称完成 → 假通过
- 顺手扩展 → DRIFT

## Verification
- 每增量真实测试通过 + Git 提交可核验
- DoD 全勾
- DRIFT_CHECK 无冲突
