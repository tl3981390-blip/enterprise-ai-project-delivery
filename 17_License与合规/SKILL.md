---
name: enterprise-ai-project-delivery.17-license
description: 模块17·License与合规。代码/依赖/模型/数据许可扫描。Use when 需核验交付许可合规。
version: 0.2.0-dev
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 17_License与合规
  language: zh-CN
  gate: Release 前
---

# 17 License 与合规

## Overview
定义交付物的合法使用边界，扫描代码/依赖/模型/数据许可，红色告警阻断发布。

## When to Use
施工中借用第三方代码，及 Release 前。

## Core Process
1. 复制/改写上游 → 头部来源+许可注释（`2026` 边界见 `09`）。
2. 扫描依赖 License（`scripts/scan_license.py`）与模型/数据许可。
3. 红色许可 / 无法证明合法 → 阻断 Release。
4. 更新 NOTICE / 来源清单。

## 反合理化 / Red Flags
- 使用红色许可依赖仍发布 → 阻断
- 数据/模型许可未核查 → 合规风险
- OpenAI .system 复制进产物 → 全程禁止

## Verification
- 许可扫描输出无红色；NOTICE/来源清单完整
