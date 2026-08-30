---
name: enterprise-ai-project-delivery.05-tdd-strategy
description: 模块05·TDD与测试策略。判断式测试策略，核心逻辑先测试。Use when 需设计测试策略并确保关键逻辑被测试覆盖。
version: 1.0.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 05_TDD与测试策略
  language: zh-CN
  gate: 需 READY_TO_PLAN 后
---

# 05 TDD 与测试策略

## Overview
决定哪些逻辑必须 TDD/关键测试，输出测试策略。核心逻辑不测试 = 不可验收。

## When to Use
规格与架构明确后，进入施工前的测试策略设计。

## Core Process
1. 依据规格/架构判断哪些逻辑需强测试（状态机、权限、数据、核心算法、错误路径）。
2. 输出测试策略 + 关键测试清单（模板 `references/TDD适用性判断.md`）。
3. 断言高空风险逻辑必须有真实测试（test_result 证据），否则 blocked。
4. 权限、状态机、数据变更、计费和安全决策一律视为核心逻辑，不得用“集成后再测”跳过。

## 反合理化 / Red Flags
- "这个简单不用测" → 拒绝
- 测试文件存在但未真实运行 → 假测试
- TDD 判断只凭感觉 → 需可判规则

## Verification
- 核心逻辑测试策略完整
- 关键测试在施工期真实通过（test_result 退出码 0）
