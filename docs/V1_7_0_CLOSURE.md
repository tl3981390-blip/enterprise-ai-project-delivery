# v1.7.0 Closure — Human Plan Authority + Upstream Capability First

日期：2026-08-31 ｜ tag：`v1.7.0 → ba7f8b292cef0d2a00c0956f17d84ea440969cec` ｜ Release asset SHA-256：`058181d050da8b149137341f516f3e217c4370d031214357fd94a64cad244a14`（远端回验一致）｜ 状态：**CLOSED**

## 本轮修什么

在 v1.6.1（真动态交付）基础上补两块缺失的可靠性核心机制：

1. **HUMAN_PLAN_AUTHORITY**：AI 生成的 Delivery Plan 是推荐，不是固定流程。权威层级固定为 `CORE_RELIABILITY_INVARIANTS > EXPLICIT_HUMAN_DECISIONS > ENTERPRISE_REQUIRED_WORKFLOW > PROJECT_SPECIFIC_CONSTRAINTS > AI_GENERATED_DELIVERY_PLAN`（AI 在最低层）。
2. **UPSTREAM_CAPABILITY_FIRST**：本 Skill 不重新发明成熟能力，而是组合/扩展/驾驭上游 Skill 生态；Reliability Core 加可靠性，不造成能力退化。

## 机制（plan_governance_core.py）

- **人类修改**：add/remove/merge/split/reorder/modify/replace_all 全部支持；删除 Stage 时其验收/证据/恢复义务被**重新安置**到幸存 Stage（组织自由，可靠性要求不消失）；PLAN_LOCK 元素不被自动改（显式冲突才解释）。
- **企业已有计划优先**：`apply_human_plan` 保留企业计划主体，只补缺失的可靠性控制（理解门禁/最终验收），绝不把企业流程改成 AI 计划。企业阶段 provenance=ENTERPRISE_REQUIRED。
- **Provenance**：每项计划标 AI_GENERATED/HUMAN_PROVIDED/HUMAN_MODIFIED/ENTERPRISE_REQUIRED/SYSTEM_RELIABILITY_REQUIRED；后续 Replan 不得把 HUMAN_MODIFIED 偷改回 AI 原计划。
- **局部重算**：`replan_respecting_locks` 只重算受影响的 AI 生成项，人类锁定/提供项原样保留；不重开整个项目。
- **上游能力**：`capability_provenance_record`（source/version/method/controls/validation）；`capability_regression_guard`（集成后能力维度 ≥ 上游，可靠性维度应提高，否则 FAIL）；`resolve_capability_need`（已知→用适配器；未知但需要→发现上游；都没有→如实报 CAPABILITY_NOT_AVAILABLE，绝不静默 capability=false）；`upstream_update_reabsorb`（上游升级后 diff/兼容检查/回归/采纳，不冻结首版）。

## 验证

- **PLAN-001..012** 全绿：删除/增加/重排/合并/拆分/企业计划基础/防偷改/锁定/局部失效/义务重安置/建议不越权/provenance。
- **UP-001..008** 全绿：组合优先/来源记录/无退化/退化检出/未知能力发现/不可得如实报/升级重吸收/包装不限制上游。
- **全量田归**：**247/247 PASS**，结构校验器 0 错误 0 警告。

## 身份

```text
v1.5.0 → 491f6c9f76c6c384fd18a21303aba56812eeadb1（历史不变）
v1.5.1 → ba7ca9e71d90c2a20eb994053a6d2bee21c36f2c（历史不变）
v1.6.0 → 55207d242aac741d82959de6fd778416c6d304d4（历史不变，含已记录缺陷）
v1.6.1 → 766680bb7b0719341381b0d5a35e998065bdf1fd（历史不变）
v1.7.0 → ba7f8b292cef0d2a00c0956f17d84ea440969cec（本轮）
zip    → enterprise-ai-project-delivery-v1.7.0.zip
SHA-256= 058181d050da8b149137341f516f3e217c4370d031214357fd94a64cad244a14（远端回验==本地）
GitHub Release v1.7.0 = 已建
```

## Core Freeze

本轮属合法重开（新增核心机制：计划权威与能力继承，均为可靠性交付层缺失）。完成后：

```text
CORE_FEATURE_FREEZE = ACTIVE
```

## 原则固定

```text
AI GENERATES, HUMAN OWNS.
AI ADVISES, HUMAN MAY OVERRIDE.
CORE PROTECTS RELIABILITY, NOT AI'S PREFERRED WORKFLOW.

DON'T REBUILD MATURE CAPABILITIES WORSE.
COMPOSE FIRST. EXTEND SECOND. REIMPLEMENT LAST.
RELIABILITY CORE ADDS RELIABILITY, NOT CAPABILITY REGRESSION.
```
