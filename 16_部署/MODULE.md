---
name: enterprise-ai-project-delivery.16-deploy
description: 模块16·部署。Build→Deploy→回滚，非「本地能跑」。Use when 交付需部署上线。
version: 3.0.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 16_部署
  language: zh-CN
  gate: 需验收通过、部署授权
---

# 16 部署

## Overview
部署不是「本地能跑」，须包含 Build/环境/迁移/回滚。生产部署需另行授权，演习先行。

## When to Use
施工与验收通过后，准备上线。**条件能力**：非部署型交付物（纯本地工具、纯 Skill 包、库等）记 `NOT_APPLICABLE` 及理由，并验证其对应的安装/发现/调用/卸载与恢复；禁止为走流程而虚构部署。

## Core Process
1. Build 产物 + 环境准备（`references/部署验收清单.md`）。
2. 部署到目标环境，验证可用性（非本地跑）。
3. 生产部署 → 需授权 + 演练；先 staging。
4. 失败 → 走回滚（见 18），不硬上生产。

## 反合理化 / Red Flags
- "本地能跑=可上线" → 拒绝
- 擅自连生产 → 越权
- 跳过回滚预案 → 风险高

## Verification
- 目标环境真实可访问 + 部署记录证据；生产变更走授权+演练
