# CHANGELOG

本文件记录企业AI项目交付 Skill 自身版本的变更。遵循 `18`/`08` 的 semver 与 staging/adopt 规则。

## 1.1.0-dev (2026-08-30)

- 开发 PROJECT_RELIABILITY_TELEMETRY：追加式哈希链事件、机械指标、Token 可用性诚实状态、连续性和可靠性报告。
- v1.0.0 Release、Tag 与已发布成品保持不变。

## 1.0.0 (2026-08-30)

**类型**：首个稳定版本（Stage 2A–10 全部门禁通过后签发）

**Release 能力**：上游许可内 SDD 适配、需求/规格/架构机械校验、RAG 四防、Agent 职责分离、MCP 默认拒绝、失败恢复、四角色与防假 Evidence、部署/许可/回滚、真实法务 RAG 案例、Skill 侧 Harness 合同。

**新增（设计补强）**：
- 最高原则「理解完成之前禁止施工」；`PRE_EXECUTION_UNDERSTANDING_GATE`（施工前理解门禁）。
- 12 状态状态机 + 权限阶段控制（UNDERSTANDING 只读，READY_TO_EXECUTE 后放开）。禁止 UNDERSTANDING→EXECUTING。
- 任务理解合同（Task Understanding Contract）+ 施工前八问 + 来源分级（USER_EXPLICIT/…/AI_INFERRED）。
- 计划-合同对账（PLAN_CONTRACT_ALIGNMENT_CHECK）+ DRIFT_CHECK（禁止顺手优化）。
- 理解类证据（task_understanding_contract / understanding_gate_result / plan_alignment_result / drift_check_log / constraint_conflicts）。
- 理解门禁专项 Eval A–E（07 2.5）。

**施工阶段 1（骨架）**：
- 建立主 SKILL + 20 模块目录（00_总控…19）+ 共享 references/scripts/schema + tests/evals。
- 共享 scripts：validate-skill / check_understanding_gate / check_plan_alignment / collect_evidence / check_state_machine。
- 共享 schema：task_understanding_contract / input / output / evidence。
- LICENSE / NOTICE / README；Git 初始化并首次提交。

**移除**：无。

**迁移**：无（首版）。

**安全**：默认拒绝权限；无生产系统访问；无任意写改在理解门禁前。

## Pre-1.0.0（设计阶段）
- 01–10 设计文档（架构/模块树/合同/测试/版本/License/施工计划）。
