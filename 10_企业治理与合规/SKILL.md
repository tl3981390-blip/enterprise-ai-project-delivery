---
name: enterprise-ai-project-delivery.10-governance
description: 模块10·企业治理与合规。审计/SSO/数据不出域/变更管理。Use when 交付需符合企业治理与合规要求。
version: 0.2.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 10_企业治理与合规
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 10 企业治理与合规

## Overview
把企业治理（审计/SSO/数据不出域/变更管理/合规）纳入交付，治理项外链到企业政策。

## When to Use
交付涉及企业数据/身份/审批/合规时。

## Core Process
1. 读取企规（org_policy_ref / key_constraints）。
2. 按 `references/治理检查清单.md` 逐项核验（数据不出域、SSO、审计日志、变更审批）。
3. 与合同 key_constraints 对账；外部要求冲突 → blocked/人工。

## 反合理化 / Red Flags
- 为效率绕合规 → 拒绝
- 数据出域未批准 → 越界
- 通行证般跳过治理 → 违反企规

## Verification
- 治理清单通过；数据边界合规；变更走审批
