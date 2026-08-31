---
name: enterprise-ai-project-delivery.09-permission-gateway
description: 模块09·MCP与工具权限网关。READ/WRITE/DELETE/EXECUTE/ADMIN/EXTERNAL 权限矩阵。Use when 需定义工具/MCP权限边界。
version: 1.5.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 09_MCP与工具权限网关
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 09 MCP 与工具权限网关

## Overview
把工具/MCP 权限固化为矩阵，默认拒绝、显式允许。高风险操作需人工确认。

## When to Use
交付涉及工具/MCP/外部调用权限时。

## Core Process
1. 枚举所需工具/MCP，填 [`references/权限矩阵模板.md`](references/权限矩阵模板.md)，未列出的动作默认拒绝。
2. 与合同 allowed_tools / forbidden_tools 对账。
3. 高风险（EXECUTE/ADMIN/写生产/外发）必须具有逐动作批准与过期时间；生产访问仍受项目硬边界禁止。
4. 越权即拒绝（permission_denied + drift_check_log）。

## 反合理化 / Red Flags
- "给最大权限省事" → 拒绝
- AGENT 跳过权限直接调用 → 越权
- 生产/外部权限未批 → blocked

## Verification
- 权限矩阵过校验；拒绝用例通过；无越权调用
