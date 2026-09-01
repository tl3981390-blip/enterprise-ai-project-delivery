---
name: enterprise-ai-project-delivery.12-failure-recovery
description: 模块12·失败处理与恢复。根因定位+证据保留+自动/人工修复边界+停止条件。Use when 施工/阶段发生失败。
version: 3.0.4
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 12_失败处理与恢复
  language: zh-CN
  gate: 任意态可进入（失败时）
---

# 12 失败处理与恢复

失败先追加 FAILURE_EVENT 或 GATE_FAILED，再追加 RECOVERY_ATTEMPT。只有引用失败、恢复尝试和新的通过测试 Evidence 时，才允许 AUTO_RECOVERY_SUCCESS；需要业务判断、新权限、外部动作或风险批准时记录 HUMAN_INTERVENTION_REQUIRED。

## Overview
失败时保留真实证据、定位根因、在停止条件内修复；不能靠改报告 PASS。

## When to Use
发现失败（测试失败/越权/漂移/证据缺失等）。

## Core Process
1. 冻结失败现场、分类（CODE/CONFIG/ENVIRONMENT/DATA/PERMISSION/CONTRACT/EXTERNAL_SERVICE/RUNTIME/EVIDENCE/UNKNOWN）并保存 Last Known Good。
2. 在明确 Recovery Budget 内自动修复，每次 `RECOVERY_ATTEMPT` 后重新验证。
3. 成功必须重跑原 Blocking Gate 与 Regression，才可记录 `AUTO_RECOVERY_SUCCESS` 并自动继续原计划。
4. 预算耗尽后评估 `SAFE_ROLLBACK_ATTEMPT` 与不扩 Scope 的替代恢复路径；不能恢复才记录 `RECOVERY_EXHAUSTED`。
5. 交人工时进入 `SUSPENDED_AWAITING_HUMAN`，同时生成完整 `HUMAN_RECOVERY_PACKAGE`；禁止只说“请处理后继续”。
6. 用户说继续时仅走 `RESUME_REQUEST → RESUME_VERIFICATION_PASS/FAIL`；PASS 后先复验旧失败和 Regression，再继续。

## 反合理化 / Red Flags
- 失败→改报告 PASS → 假通过
- 无限重试 → 违反停止条件
- 掩盖根因 → 失败

## Verification
- 失败有 evidence_captured；阻塞消失才 PASS；停在 BLOCKED 时请求人工
- `共享/scripts/check_continuation.py`：恢复/继续/资源/交接判定（含 SAFE_ROLLBACK_ATTEMPT、ALTERNATIVE_RECOVERY、verify-handoff）
- 规格：[RECOVERY_ESCALATION_SPEC](../共享/references/RECOVERY_ESCALATION_SPEC.md)、[EXECUTION_RESOURCE_GUARD_SPEC](../共享/references/EXECUTION_RESOURCE_GUARD_SPEC.md)、[MODEL_HANDOFF_PROTOCOL](../共享/references/MODEL_HANDOFF_PROTOCOL.md)
