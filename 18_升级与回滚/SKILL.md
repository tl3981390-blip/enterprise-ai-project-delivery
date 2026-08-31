---
name: enterprise-ai-project-delivery.18-upgrade-rollback
description: 模块18·升级与回滚。semver/迁移/兼容/回滚演练。Use when 需版本演进或回退。
version: 1.6.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 18_升级与回滚
  language: zh-CN
  gate: 发布/回滚时
---

# 18 升级与回滚

## Overview
用 semver + staging/adopt 管理版本，预留 previous stable，回滚必须真实演练而非「写了脚本=能回滚」。

## When to Use
版本变更、发布、回滚。

## Core Process
1. semver 判定（`scripts/semver_check.py`），MINOR 不破坏契约，MAJOR 有迁移说明。
2. candidate → 独立 Gate → staging → adopt（备份旧版）。
3. 升级失败不破坏当前版本，可一键 Rollback。
4. 回滚演练真实执行并验证恢复（`references/升级回滚演练.md`）。

## 反合理化 / Red Flags
- 自改自宣布升级成功 → 无独立 Gate
- 「脚本存在=能回滚」→ 需真实演练
- 升级破坏兼容却无迁移 → MAJOR 违规

## Verification
- semver 合规；staging/adopt 设备；回滚演练真实恢复有证据
