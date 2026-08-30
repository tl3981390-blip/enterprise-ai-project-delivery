---
name: enterprise-ai-project-delivery.12-failure-recovery
description: 模块12·失败处理与恢复。根因定位+证据保留+自动/人工修复边界+停止条件。Use when 施工/阶段发生失败。
version: 0.2.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 12_失败处理与恢复
  language: zh-CN
  gate: 任意态可进入（失败时）
---

# 12 失败处理与恢复

## Overview
失败时保留真实证据、定位根因、在停止条件内修复；不能靠改报告 PASS。

## When to Use
发现失败（测试失败/越权/漂移/证据缺失等）。

## Core Process
1. 定位根因并保留失败现场证据（evidence_captured 必填）。
2. 尝试自动修复（受 max_loop 约束）。
3. 停止条件：max_loop 达到 / 无法自动修 / 契约权限变更 → 交人工（BLOCKED）。
4. 修复后重跑，禁止标注未跑为 PASS。

## 反合理化 / Red Flags
- 失败→改报告 PASS → 假通过
- 无限重试 → 违反停止条件
- 掩盖根因 → 失败

## Verification
- 失败有 evidence_captured；阻塞消失才 PASS；停在 BLOCKED 时请求人工
