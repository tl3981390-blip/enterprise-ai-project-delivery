# v1.7.1 Closure — Single Orchestration Runtime + Real Partial Replan + Release Resolution

日期：2026-08-31 ｜ tag：`v1.7.1 → b26bdc8983bf0d36cb147b6dd28ed0b8069429e1` ｜ Release asset SHA-256：`ceaf97e805380e0ea46b908abe196f39f54fd0ff6dbc77d8c1f7f928d2ed278e`（远端回验一致）｜ 状态：**CLOSED**

## 本轮修什么（剩余根因一次性收口）

1. **MULTIPLE_ORCHESTRATION_SOURCES_OF_TRUTH 消除**：`derive_active_plan` 改为 DEPRECATED 兼容包装器，委托给 `delivery_planning_core.compose_stages`（唯一编排真源）；SKILL.md 与 PROJECT_ORCHESTRATION_SPEC 不再描述固定生命周期阶段；`00–19` 模块是能力库/工具包/参考，不是必经阶段序列。
2. **假动态消除**：`FACTOR_CAPABILITY_NEEDS` 删除；能力激活只认显式事实（`reason_capability_needs` 结构化 required_facts/supporting_facts/blocking_unknowns/decision/reason/evidence_source）；驱动事实 UNKNOWN 传播 unknown，谓词异常不静默 false；Work Unit 从真实项目问题作曲，不由能力清单一对一映射。
3. **假 Replan 消除**：`replan_respecting_locks` 真正消费 new_facts、保留原顺序、返回真实假设键（非阶段名）；`apply_plan_edit` 真正分类 verified_state（preserved/invalidated/requires_revalidation/new_required）；PLAN_LOCK 区分 actor（锁 AI 不锁授权人类）；义务语义化重安置（不“最后一阶段接锅”）。
4. **安装身份断链修复**：`_resolve_asset_sha256` 读 Release manifest 或运行时 GitHub Release digest（不再有 expected=None）；self-check 含 plan_governance_core/delivery_planning_core。
5. **迁移假绿修复**：`test_migration_v2.py` 真实 git fixture（clean/dirty/unpushed/local-only 真检测）、不依赖作者工作区、缺 fixture 即 FAIL。
6. **主仓 Public 安全**：Mimosa 深扫 0 findings + git 历史/当前树零密钥；description 更新为通用定位。

## 验证

- **ORCH/FACT/CAP/STAGE/HUMAN/UPSTREAM/INSTALL/MIGRATION 全矩阵**：23 项 systemic closure + 22 DYN2 + 14 INST + 10 MIG2 + 9 REL + 12 PLAN + 8 UP 全绿。
- **全量田归**：**270/270 PASS**，结构校验器 0 错误 0 警告。
- **真实入口重放**：fact model → capability reasoning → stage composition 走通（ORCH-007）。

## 身份

```text
v1.5.0 → 491f6c9f76c6c384fd18a21303aba56812eeadb1（历史不变）
v1.5.1 → ba7ca9e71d90c2a20eb994053a6d2bee21c36f2c（历史不变）
v1.6.0 → 55207d242aac741d82959de6fd778416c6d304d4（历史不变，含已记录缺陷）
v1.6.1 → 766680bb7b0719341381b0d5a35e998065bdf1fd（历史不变）
v1.7.0 → ba7f8b292cef0d2a00c0956f17d84ea440969cec（历史不变）
v1.7.1 → b26bdc8983bf0d36cb147b6dd28ed0b8069429e1（本轮）
zip    → enterprise-ai-project-delivery-v1.7.1.zip
SHA-256= ceaf97e805380e0ea46b908abe196f39f54fd0ff6dbc77d8c1f7f928d2ed278e（远端回验==本地）
GitHub Release v1.7.1 = 已建
```

## Core Freeze

```text
CORE_FEATURE_FREEZE = ACTIVE
```

## 剩余 Pending（如实）

- **WorkBuddy 真实复验**：本机无 CLI → PENDING_EXTERNAL_VALIDATION。
- **Clean Machine Replay（live）**：需真实新机器且网络可达 GitHub → PENDING_EXTERNAL_VALIDATION。
- **真实上游 Baseline Replay**：本轮建立了机制（capability_regression_guard 接受真实度量），真实跨上游 replay 需独立环境 → PENDING_EXTERNAL_VALIDATION。

## 最终原则

```text
AI GENERATES. HUMAN OWNS.
UPSTREAM PROVIDES MATURE CAPABILITY. RELIABILITY CORE MAKES IT SAFER.
PROJECT FACTS DEFINE THE WORK. CAPABILITIES SUPPORT THE WORK.
CAPABILITIES DO NOT DEFINE THE STAGES.
RELIABILITY INVARIANTS CONSTRAIN DELIVERY. THEY DO NOT DEFINE A FIXED WORKFLOW.
```
