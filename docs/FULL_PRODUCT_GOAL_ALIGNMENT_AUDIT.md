# FULL_PRODUCT_GOAL_ALIGNMENT_AUDIT

审计基线：GitHub 正式 Release `v1.9.1`，不是开发工作区 `main`。审计日期：2026-09-01。

## 产品目标判断

产品应是 Harness-neutral 的 AI Delivery Controller：从自然语言目标建立带来源的事实模型，发现真实工作，维护人类拥有的动态计划，组合已授权能力，持续执行，在变化和失败中保留证据并有界恢复，最后从原始目标独立验收。Core 不实现 ERP、SSO、部门业务系统或公司级 Skill Registry。

修复前结论：**NO**。v1.9.1 已有大量可靠性原语，但普通用户入口到真实完成仍存在关键断链，不能称为完整工作承担者。

## 基线安装证据

- GitHub Release：非 Draft、非 Prerelease，tag `v1.9.1`。
- Annotated tag object：`a4efadf924bf4c9d59805c1d785c8da63303def5`。
- Peeled release commit：`a76f732a0184da3914e67b3126eefe08e151e962`。
- Asset：`enterprise-ai-project-delivery-v1.9.1.zip`。
- 下载资产 SHA-256：`9a278de3c3a8ecaa508293b2c85b7c9d4057a0f15fbd220d06634562cecca19b`，与 GitHub Release digest 一致。
- 隔离安装：350 files，installer self-check PASS；`validate-skill.py` 报 `0 errors, 0 warnings`。
- Codex 标准目录安装成功；当前会话未热重载该 Skill，真实新会话自动发现仍为 `PENDING_EXTERNAL_VALIDATION`。
- 正式安装副本全回归：`279 passed, 8 failed`。失败来自 ZIP 无 `.git` 与资产外 `workspace-bootstrap` 依赖，证明自包含测试合同不成立。

## 根因问题图

### RC-01：Understanding 只有描述，没有会话状态机

问题：Runtime 接受调用方一次性提供的 `facts`，但没有 natural-language intake、consequential unknown、问题理由、回答写回、冲突、确认、supersede 或 sufficiency 计算。计划仍固定加入“施工前八问”。

违反目标：用户必须在 Runtime 外先成为产品经理；聊天问答无法机械证明改变 Fact Model、Complexity、Work Unit、Plan 或 Capability。

影响链：Natural Language Entry → Understanding → Fact Model → Planning 全部为 `NOT_BOUND_END_TO_END`。

最小正确修复：增加 Harness-neutral understanding session contract；问题由 decision impact 驱动；每次回答产生事实事件和来源历史；只有 gate 通过才能进入 planning。

### RC-02：Capability 选择未绑定执行

问题：`resolve_capability_need` 返回候选和 action，但 Runtime 没有 invocation request/result contract，没有 Work Unit 绑定、授权令牌、输出证据或失败转移。

违反目标：assert 选中了 Skill 不等于跨 Skill 协作。

影响链：Capability Resolution → Execution → Failure → Evidence 断开。

最小正确修复：定义由 Harness 执行的 invocation envelope；Core 验证 resolved/authorized/validated 状态，记录调用结果；失败自动冻结；成功结果进入候选绑定 Evidence。

### RC-03：Recovery 不受预算和回归约束

问题：Recovery 只检查非空 evidence 与 blocker status PASS；无最大尝试、回归要求、停止原因、Human handoff package。

违反目标：可能无限重试或用过窄的原 blocker 检查恢复。

最小正确修复：会话级 recovery policy、attempt budget、blocker + regression 双证据、人工接手包与明确 stop condition。

### RC-04：Release 自证合同不一致

问题：manifest 仍为 `1.8.1`；validator 未发现。正式 ZIP 的 8 个测试依赖 `.git` 或 Release 外 workspace-bootstrap。

违反目标：正式安装副本不能从自身真实回归，安装身份存在双真源。

最小正确修复：validator 机械比较 SKILL、manifest、release metadata；Release-mode 测试使用资产内 manifest/声明，不依赖开发仓或私有 bootstrap；开发迁移测试明确移出公开 Release 回归。

### RC-05：Fact lifecycle 与 acceptance 语义不足

问题：Fact state 只有 DECLARED/OBSERVED/INFERRED/UNKNOWN/NOT_APPLICABLE；不能表达 USER_CONFIRMED、PROJECT_EVIDENCE、CONFLICTED、SUPERSEDED。Acceptance 把复杂度说明对象也当作必须 Evidence 的验收项。

最小正确修复：扩展来源与生命周期，保留历史；验收矩阵区分 acceptance items 与 metadata。

## 修复前状态矩阵

| 能力 | 状态 | 证据/理由 |
| --- | --- | --- |
| NATURAL_LANGUAGE_ENTRY | PARTIAL | SKILL.md 描述入口；Runtime 无 intake binding |
| SPARSE_GOAL_UNDERSTANDING | FAIL | 无问题生成/多轮回答写回机制 |
| UNDER_QUESTIONING_GUARD | FAIL | 无 consequential-unknown 决策模型 |
| OVER_QUESTIONING_GUARD | FAIL | 固定“施工前八问”措辞 |
| UNDERSTANDING_TO_FACT_BINDING | FAIL | 无 answer event/update API |
| FACT_TO_PLAN_BINDING | PARTIAL | start_delivery 可从调用方预制 facts 生成计划 |
| DYNAMIC_WORK_DISCOVERY | PARTIAL | 支持 work_units/journeys/upstream plan；稀疏目标只能得到两个固定 Stage |
| COMPLEXITY_ADAPTATION | PARTIAL | 结构事实计分，但大量 UNKNOWN 不阻止 planning |
| HUMAN_PLAN_AUTHORITY | PASS | add/remove/merge/split/modify/reorder/replace/lock 权限测试存在 |
| CAPABILITY_NEED_DISCOVERY | PASS | 事实驱动且 capability 不制造 stage |
| CAPABILITY_RESOLUTION | PARTIAL | 候选筛选存在，未执行绑定 |
| CAPABILITY_AUTHORIZATION | PASS | permission false 被排除；未授权不选择 |
| CAPABILITY_TO_EXECUTION_BINDING | FAIL | 无 invocation lifecycle |
| CONTINUOUS_EXECUTION | PARTIAL | continuation 原语存在；未接真实 work executor |
| CONDITION_CHANGE_DETECTION | PASS | changed facts 驱动影响分类 |
| TRUE_PARTIAL_REPLAN | PASS | 缺 planner fragment 保持 PLANNING，不假标已重规划 |
| CAPABILITY_RE_RESOLUTION | PASS | 条件变化后重新解析 capability |
| FAILURE_EVIDENCE | PASS | 无 evidence 不能记录失败 |
| BOUNDED_RECOVERY | FAIL | 无 attempt budget/stop condition |
| ORIGINAL_BLOCKER_REVALIDATION | PARTIAL | blocker PASS 必需；缺 regression requirement |
| RESUME | PARTIAL | 原语/测试存在；未在当前 Codex 新会话真实验证 |
| HANDOFF | PARTIAL | 合同/测试存在；跨 Harness 外部验证不足 |
| EVIDENCE_INTEGRITY | PARTIAL | recorder/hash 原语存在；invocation result 未绑定 canonical evidence |
| TELEMETRY | PARTIAL | 能记录内部事件；入口/能力调用断链导致追踪不完整 |
| ANTI_FAKE_PASS | PARTIAL | 缺失/失败/pending/open failure 可阻止；candidate/evidence freshness 未贯穿入口 |
| FINAL_ACCEPTANCE | PARTIAL | fact-derived matrix；复杂度 metadata 被误作验收项 |
| SCOPE_CONTROL | PASS | 人类计划/约束与权限原语已覆盖 |
| HIGH_RISK_AUTHORITY | PARTIAL | 文档与候选权限筛选存在；无真实 Harness 写操作验证 |
| GENERALIZATION | PARTIAL | 结构事实优于关键词；稀疏输入仍无法形成事实 |
| NO_TEMPLATE_CALCIFICATION | PARTIAL | capability 不造 Stage；固定理解/最终验收 Stage 仍明显模板化 |
| INSTALLATION | FAIL | 文件安装 PASS，但安装副本全回归 8 FAIL |
| ENTERPRISE_VERSION_GOVERNANCE | PASS | exact tag + SHA + no auto-upgrade 已机械验证 |
| RELEASE_IDENTITY | FAIL | manifest 1.8.1 与 release 1.9.1 不一致，validator 漏检 |
| DOCUMENT_RUNTIME_ALIGNMENT | FAIL | README/SKILL 声明的自然语言闭环超过 Runtime 真实绑定 |
| REAL_INSTALLED_SKILL_BEHAVIOR | FAIL | 当前会话未加载；安装副本回归失败；无 NL E2E driver |
| ENTERPRISE_CONTROLLED_PILOT_READY | FAIL | 关键闭环断链 |
| ENTERPRISE_WIDE_PRODUCTION_PLATFORM_READY | NOT_INCLUDED_BY_DESIGN | 不包含 SSO/RBAC/公司级 Registry/执行总线/生产 SLA |

## 审计停止线

在 RC-01 至 RC-05 修复并从新候选资产干净安装回归前，不允许 COMPLETE、不允许以现有测试数发布、不允许宣称企业 Pilot Ready。
