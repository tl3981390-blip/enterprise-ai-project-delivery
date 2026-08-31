# CORE_BOUNDARY_POLICY — Core 与非 Core 正式边界

生效：随 v1.5.0 正式发布；POST_v1.5.0 泛化缺陷修订单见文末 ｜ 配套：`PRODUCT_CORE_MANIFEST_V1.json` ｜ 状态：`CORE_FEATURE_FREEZE = ACTIVE`（本次修订单经合法重开通道，见 `evidence/post_v1_5_generalization/`）

## Core（只存跨企业、跨项目、跨 Harness 的通用可靠性机制）

Task Understanding / Task Contract / Scope Governance / Autonomous Continuation / Legal Stop / Recovery / Human Recovery / Resume / Resource Guard / Model Handoff / Evidence / Telemetry / Telemetry Closed Loop / User Journey / Independent Acceptance / Runtime Integrity（含声明适配器与角色工作流覆盖门禁）/ Requirement Coverage / Experience Learning / Controlled Evolution / Reliability Efficiency / Mid-project Attachment / Enterprise Customization（不变量与合并优先级）/ Harness Capability Architecture / Value & Reliability Reporting。

**重开唯一通道**：REAL_PROJECT_FAILURE + CURRENT_CORE_CANNOT_HANDLE + GENERALIZABLE + REPRODUCIBLE + EVIDENCE_BACKED（五条同时满足，走 Evolution 候选流水线）。新想法/新平台/新企业/新项目/新客户要求一律不得直接改 Core。

## Harness Adapter（`adapters/<platform>/`）

只存：discovery / invocation / path / lifecycle / permission translation / tool translation / capability declaration（每平台薄包 5 件，零 Core 复制；平台等级提升属此层验证工作，非 Core 开发）。

## Enterprise Profile

只存：公司角色 / 公司审批 / 模型政策 / 数据政策 / Security / Evidence 政策 / Deployment / Human Gate 政策（13 字段 schema；`NON_OVERRIDABLE_CORE_INVARIANTS` 之上不可越 Core）。

## Project Profile

只存：当前项目 Goal / Runtime / Acceptance / Risk / RAG / Workflow / 项目特殊 Constraint（12 字段 schema）。

## 学习线分离（禁污染）

`GLOBAL_FAILURE_PATTERN → Core Evolution`；`COMPANY_SPECIFIC_PATTERN → Enterprise Profile Evolution`；`PROJECT_SPECIFIC_PATTERN → Project Profile / Project Experience`。

## Harness 声明词表（对外唯一合法）

`VALIDATED`（真实验收+明确版本）｜`PARTIALLY_VALIDATED`｜`BLOCKED_RUNTIME_AUTH`｜`PENDING_EXTERNAL_VALIDATION`｜`NOT_AVAILABLE`。禁用 `SUPPORTED` 除非范围已真实验证并明确版本。

## POST_v1.5.0 泛化修订单（2026-08-31）

1. **适用性**：Core 的适用对象是复杂项目（企业/个人、AI/非 AI 均可）。`EXPLICIT_INVOCATION` 不得因项目类型被拒；`AUTO_TRIGGER` 偏好复杂/高风险但不否决显式调用。分层编排正式规格见 `PROJECT_ORCHESTRATION_SPEC.md`。
2. **Project Profile**：分类字段必填，能力声明（runtime/database/rag/agent/workflow/deployment_target）选填，缺省=NOT_IN_SCOPE。
3. **验收**：独立验证是不变量；视角随干系人缩放（`required_acceptance_perspectives`），企业四视角为默认实例。
4. **企业定制**：企业真实流程经 `compile_enterprise_workflow` 作为输入编译进 Enterprise Profile，非内置模板。
5. **经验路由**：五路（GLOBAL_RELIABILITY / HARNESS_SPECIFIC / ENTERPRISE_SPECIFIC / PROJECT_SPECIFIC / ONE_OFF），`FREQUENCY != GENERALIZABILITY`；Core 准入十项全真（`validate_core_evolution_admission`）。
