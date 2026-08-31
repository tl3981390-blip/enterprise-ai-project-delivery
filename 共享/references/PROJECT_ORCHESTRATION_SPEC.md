# PROJECT_ORCHESTRATION_SPEC（复杂项目可靠性分层编排规格）

生效：POST_v1.5.0 核心缺陷修复（泛化收口）｜ 机械核心：`共享/scripts/product_completion_core.py`（Part E）｜ 回归：`tests/reliability/test_generalization.py`

## 产品第一身份

本 Skill 是 **COMPLEX PROJECT RELIABILITY DELIVERY SYSTEM**：面向复杂软件、AI、Agent、自动化、数据系统、企业系统、桌面/Web 软件及长期工程等多阶段复杂项目，提供可靠理解、范围约束、执行治理、证据、恢复、继续、交接、验收与防假完成机制。

- 关键词：`COMPLEX PROJECT / RELIABILITY / DELIVERY`，不是 `ENTERPRISE AI ONLY`。
- 企业 AI 是本 Skill 的**主要价值域与经验来源**，不是**使用资格条件**。

## 分层模型（Layer 1–7）

```text
Layer 1  Reliability Core（跨项目不变量，任何项目不可关闭）
Layer 2  Capability / Stage Registry（条件能力：RAG/Agent/MCP/治理/浏览器/部署/License…）
Layer 3  Project Understanding / Classification（当前项目是什么、需要哪些能力）
Layer 4  Active Delivery Plan（按 Layer 3 动态生成，禁止从历史/企业模板复制）
Layer 5  Enterprise Profile（企业真实流程作为输入编译，非内置模板）
Layer 6  Project Profile（项目特定规则）
Layer 7  Task Contract（任务级约束）
```

### Layer 1 — CORE INVARIANTS（恒活，不可削弱）

`UNDERSTAND_BEFORE_EXECUTE / SCOPE_AUTHORITY / CONTRACT_INTEGRITY / NO_FAKE_PASS / EVIDENCE_INTEGRITY / TELEMETRY / FAILURE_CLASSIFICATION / BOUNDED_RECOVERY / RECOVERY_REVALIDATION / NO_BLIND_RESUME / NO_STAGE_WAIT / LEGAL_STOP_GATE / RESOURCE_GUARD / HANDOFF / INDEPENDENT_VERIFICATION / FINAL_ACCEPTANCE`（与 `NON_OVERRIDABLE_CORE_INVARIANTS` 机械联动；企业/项目 Profile 均不可覆盖）。

生命周期恒活阶段：`00,01,02,03,04,05,06,11,12,15,19`（`12` 事件驱动进入）+ `14`（独立验收不变量的载体，视角随干系人缩放，见下）。

### Layer 2 — CONDITIONAL CAPABILITIES（注册表）

`CAPABILITY_REGISTRY`：`rag / agent / tool_permissions / enterprise_governance / browser_acceptance / deployment / license_compliance / upgrade_rollback / database / workflow / multi_role_approval → {stages, gates}`。

这些是**能力**，不是所有项目必经流程。项目不声明 → `NOT_APPLICABLE(capability_not_in_scope)`，禁止伪造 PASS，也禁止强行执行（SSO/RAG/MCP/审批对无此需求的项目是模板泄漏）。

### Layer 3 — Project Understanding

理解合同回答：是什么/目标/复杂度/风险/环境/用户/真实依赖/需要与不需要的能力。分类字段必填（`PROJECT_CLASSIFICATION_FIELDS`）；能力声明**选填**（缺省=不在范围内）。**项目类型回答「怎么交付」，不回答「配不配用」**。

### Layer 4 — Active Delivery Plan（`derive_active_plan`）

输出：`ACTIVE_STAGES / NOT_APPLICABLE_STAGES(含理由) / ACTIVE_GATES / REQUIRED_EVIDENCE / HUMAN_GATES / FINAL_ACCEPTANCE`。结构顺序：理解项目 → 识别风险 → 识别能力 → 生成 Active Plan → Risk Router 路由执行期 Gate（`RISK_BASED_GATE_ROUTING_SPEC` 继续有效：路由的是执行期 Gate，Plan 决定阶段/能力面）。条件变化后 Plan **必须可重算**（见假设变化模型）。

### Layer 5 — Enterprise Profile（企业流程=输入）

`compile_enterprise_workflow`：企业提交自己的真实流程（阶段/角色/审批/入口出口条件/证据/人工门禁）→ 编译为 Profile `workflow` 条目 → 校验不削弱 Layer 1 → 交企业确认 → 启用。不同企业可编译完全不同的流程于同一 Core 之上（`ONE CORE + MULTIPLE ENTERPRISE WORKFLOWS`）。**禁止**把任何企业流程固化为 Core 默认流程。

### Layer 6/7 — Project Profile / Task Contract

项目特定与任务级约束；`merge_profiles` 优先级与 `PROFILE_CONSTRAINT_CONFLICT` 检出继续有效。

## 适用性与触发

```text
EXPLICIT_INVOCATION（用户点名使用本 Skill）
  → 只要确实是项目交付任务：默认接受，不因 非企业/非AI/无SSO/无MCP 拒绝
  → 按实际情况生成 Active Delivery Plan（低复杂度 → 轻量 Plan，走 Quick 强度）

AUTO_TRIGGER（自动触发启发式）
  → 偏向 复杂/长周期/多阶段/高风险/AI/企业软件/跨系统
  → 只是启发式，不得否决 EXPLICIT_INVOCATION
```

禁止因领域拒绝后自行造出 `FAMILY MODE / PERSONAL MODE / HOME MODE` 等第二套模式——统一走能力条件激活 + 交付强度分级（Quick/Feature/Project = DELIVERY_INTENSITY：调节文档粒度/Evidence 深度/验证深度，不编码流程模板，不作项目类型分类器）。

## 验收视角（模块 14 泛化）

`required_acceptance_perspectives`：企业默认四视角（product/engineering/security/end_user）；单人项目坍缩为 `owner_user` 等。**不变量**：每个必需视角需 `PASS + reviewer + evidence`；执行者自证不构成验收；`check_acceptance.py` 机械执行。

## 经验路由与进化准入

- 五路分类（`classify_experience_route`）：`GLOBAL_RELIABILITY / HARNESS_SPECIFIC / ENTERPRISE_SPECIFIC / PROJECT_SPECIFIC / ONE_OFF`。去向：Core 候选 / Adapter 层 / Enterprise Profile / Project Profile / 归档。
- `FREQUENCY != GENERALIZABILITY`：频率/重复计数永不促进 GLOBAL；GLOBAL 另需 `cross_project_validated + counterexample_checked`。
- Core 准入（`validate_core_evolution_admission`）：真实失效 + 现核心不足 + 可泛化 + 可复现 + 证据 + 跨项目验证 + 反例检查 + 无模板/企业/项目泄漏，十项全真。
- 减法进化（SIMPLIFY/MERGE/REMOVE/DEFER）与九字段声明继续有效。

## 假设变化模型（`assumption_change_model`）

条件变化 → 识别受影响假设 → `INVALIDATED`（直接依赖）/ `REQUIRES_REVALIDATION`（共享能力面）/ `STILL_VALID`（保留）/ `NEW_REQUIRED`（新增）→ 重跑受影响理解 → 重算 Active Plan → 继续。禁止硬套旧模板，也禁止全部从零重做。

## HISTORICAL_PROJECT_ABSTRACTION_RULE（历史项目抽象规则）

```text
真实复杂项目 → 真实失败/漂移/假完成/恢复问题 → 提取 Failure Pattern
→ 抽象 Reliability Pattern → 通用 Core Mechanism
```

禁止：复制历史项目流程 → 固定模板 → 要求未来项目照走。检测到以下元素被全局强制且无机械证据证明属 Layer 1 时，判 `HISTORICAL_PROJECT_TEMPLATE_LEAKAGE`：固定阶段名/顺序、固定角色、固定技术栈、固定审批结构、固定数据库、固定 RAG/Browser/Deployment/MCP。
