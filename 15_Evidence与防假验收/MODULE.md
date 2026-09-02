---
name: enterprise-ai-project-delivery.15-evidence
description: 模块15·Evidence与防假验收。统一证据合同，防假验收。Use when 需打包/核验阶段证据。
version: 3.0.6
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 15_Evidence与防假验收
  language: zh-CN
  gate: 阶段证据需落库
---

# 15 Evidence 与防假验收

遥测 Evidence 只能经 `共享/scripts/record_delivery_event.py` 写入，并由 `calculate_delivery_metrics.py` 与 `check_telemetry_binding.py` 验证 append-only JSONL、逐事件 SHA-256 链和独立 anchor。项目自己的“差不多”Writer/Verifier 不能成为接受依据。历史错误只能追加 CORRECTION_EVENT；删除、重排、覆盖、重复 event_id 或同类 correlation 重复均为 Integrity FAIL。模型总结和最终报告不能代替原始事件。

## Overview
按统一证据契约收集、打包、核验证据；模型文字禁止当证据。

## When to Use
每个阶段完成、进入下一阶段前，及最终交付时。

## Core Process
1. 本阶段产出证据归入 `evidence/<stage>/`（`scripts/collect_evidence.py` 打包 + manifest.sha256）。
2. 校验证据类型白名单（模型文字 ❌）及 checksum。
3. 校验理解证据（task_understanding_contract / understanding_gate_result / plan_alignment_result / drift_check_log / constraint_conflicts）。
4. 缺证据 → blocked；不冒充 PASS。
5. 最终验收前运行 `check_telemetry_binding.py`；Recorder/Verifier hash 不匹配、日志/anchor 缺失或核心完整性失败均禁止 Acceptance PASS。

## 反合理化 / Red Flags
- model_text 当证据 → 禁止
- 缺失关键证据仍 PASS → 假验收
- 篡改索引/哈希 → 防篡改拦截

## Verification
- 证据 schema 校验通过；`collect_evidence` 打包成功；清单可读回验证
