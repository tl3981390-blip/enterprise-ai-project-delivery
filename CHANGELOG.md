# CHANGELOG

## 3.0.3 (2026-09-01)

- Repaired the public `SKILL.md` YAML frontmatter so Codex can discover the single root Skill through `/`.
- Made the validator reject body text inside public frontmatter and added a regression for that discovery failure.

## 3.0.2 (2026-09-01)

- Made all six Adaptive Strategy catalog fields change the corresponding decision before it is made: consequential-question selection, real-work plan ordering, eligible capability ordering, recovery sequence, dependency-legal work selection and structured Host interaction guidance.
- Replaced public caller-made Evidence ingress with one-time Harness Execution Receipts. Canonical Evidence now derives producer, source, status, candidate/work/execution identity and verified artifact hash from the receipt; metadata cannot override them.
- Added behavioral-differential and Evidence-ingress attack regressions, including real receipt → ledger → Strategy → completion flow.

## 3.0.1 (2026-09-01)

- Wired the six-field Adaptive Strategy catalog into Delivery Session, phase guidance and runtime update operations.
- Restricted Strategy learning to current PASS records resolved from the canonical Evidence Ledger.
- Unified trusted provenance for human plans, requirement changes, corrections, user pause/resume and cancellation.
- Added fail-closed formal-asset identity validation and end-to-end Release-like source-to-install tests.
- **FAILED POST-RELEASE VALIDATION — DO NOT USE.** Strategy fields did not yet change underlying decisions and raw caller Evidence remained accepted. Tag and Asset are immutable historical evidence; repair proceeds only in v3.0.2.

## 3.0.0 (2026-09-01)

- Closed the final product target: real-work-only plans, canonical goal binding and task-scaled understanding.
- Added fail-closed user-origin authorization for plan approval and plan edits.
- Separated optional Evidence-backed Runtime Adaptive Execution Strategy from Publisher Core Maintenance.
- Hardened self-contained Release Asset installation and new-directory portability.

## 2.0.1 (2026-09-01)

- Fixed installer rollback placement: upgrade backups now live outside the Harness `skills/`
  discovery root, so historical module files cannot reappear in Codex `/` menus.
- Added a two-install regression proving the scan root still contains only the active Skill.

## 2.0.0 Candidate (2026-09-01)

- Breaking discovery fix: the package now exposes exactly one public `SKILL.md`; the 20
  numbered implementation references are internal `MODULE.md` files and no longer pollute
  the Codex `/` Skill menu.
- Breaking runtime fix: the public Planning entry accepts only a mechanically sufficient
  Understanding Session. Raw caller-created `facts` can no longer bypass provenance and scope gates.
- Added a candidate-, revision-, Work-Unit- and acceptance-bound append-only Evidence Ledger;
  model prose, arbitrary strings, wrong-candidate, stale and invalidated evidence are rejected.
- Bound capability invocation, failure, recovery, suspend/resume and completion to the same
  authoritative Delivery Session and real manifest handlers.
- Added duplicate-callback, recovery-regression, condition-change, single-discovery and formal
  installed-copy regressions. This is a major version because packaging and runtime APIs break
  compatibility with callers that depended on the unsafe v1.x surfaces.

## 1.10.0 Candidate (2026-09-01)

- Added a Harness-neutral multi-turn Understanding Runtime with consequential questions,
  answer-to-fact binding, provenance history, conflict/supersede states and a mechanical
  sufficiency gate before Planning.
- Bound capability resolution to real Work Unit invocation requests, Harness results,
  failure transitions and Evidence.
- Added recovery budgets, required related-regression evidence and complete human recovery
  packages when automatic recovery stops.
- Made installed Release regression self-contained: public tests no longer depend on `.git`
  or the author's private workspace bootstrap.
- Added mechanical version alignment checks across `SKILL.md`, `harness_manifest.json` and
  `RELEASE_METADATA.json`.
- Added product-behaviour regressions for sparse goals, existing-project reconstruction,
  AI-inference guards, authorization, invocation binding and recovery.

## 1.9.1 Candidate (2026-09-01)

- Corrected the released installation contract: personal exploration may select Latest Stable,
  while enterprise trial/test/pre-production/production must pin a human-approved exact tag,
  verify the Release asset SHA-256 and never auto-upgrade.
- Added an auditable enterprise version-governance guide and synchronized public install,
  adapter, development-migration, CEO and Workspace recovery documentation.
- No delivery-runtime or planning behavior changed; all historical tags remain immutable.

## 1.9.0 Candidate (2026-09-01)

- Added arbitrary project-declared capability needs without allowing capabilities to create Stages.
- Added auditable selection of Harness-visible/enterprise Skills; explicitly unauthorized,
  incompatible, identity-unverified or runtime-blocked candidates cannot be selected.
- Recomputes capability resolution when project conditions or visible catalogs change.
- Replaced stale public/private and v1.5-only acquisition/migration instructions with current,
  version-resolving guidance and an honest company-wide Skill Registry boundary.

## 1.8.1 (2026-08-31)

- Real partial replanning replaces affected AI work with complete planner-generated fragments
  and reclassifies Evidence; missing planner output cannot fake PASS.
- Human-owned affected work remains unchanged and is marked for review/revalidation.
- Capability identity no longer creates or promotes Work Units; capabilities only support
  project work discovered by human/upstream plans or explicit project facts.

## 1.8.0 (2026-08-31)

- Replaced the governance-first entrypoint with a concise natural-language delivery contract.
- Added one runtime connecting dynamic planning, human edits, affected-only replanning,
  capability composition, failure freezing, recovery revalidation and evidence completion.
- Added realistic end-to-end reliability scenarios and stable UTF-8 installer output.
- Aligned candidate identity across entrypoint metadata, release metadata and harness manifest.

本文件记录企业AI项目交付 Skill 自身版本的变更。遵循 `18`/`08` 的 semver 与 staging/adopt 规则。

## 1.5.0 (2026-08-31)

**FIRST GENERATION PRODUCT CORE COMPLETE**——产品化四能力域 + 多 Harness 架构 + 效率成果保持；发布即 `CORE_FEATURE_FREEZE = ACTIVE`。

- MID_PROJECT_SKILL_ATTACHMENT：只读发现（14 字段）→采纳边界（8 字段 schema）→历史四分类不洗白→惰性依赖验证→继续原项目（禁新建）；价值报告 PRE/POST 分期。
- TELEMETRY_CLOSED_LOOP：OBSERVE→DECIDE→ACT→**VERIFY**→结果事件（假设成功被机械禁止）；8 类事件→策略；max_attempts+人环 HALT 不可绕；与 Skill Evolution 严格分离。
- ENTERPRISE_CUSTOMIZATION：CORE+ADAPTER+ENTERPRISE_PROFILE+PROJECT_PROFILE 四层；7 项不可覆盖核心不变量；合并优先级与冲突检出；Global/Company 学习线分离。
- MULTI_HARNESS_ARCHITECTURE：Harness 能力合同（15 能力×4 状态词表）、L1-L10 连续阶梯、薄适配包×4（零 Core 复制）、运行时能力探测与真实验收矩阵。
- **唯一冻结例外（CORE_DEFECT）**：EXP-018/LL-014——同键嵌套限制性政策值可被低层静默覆盖（Harness 验收实测发现）；修复=递归叶路径冲突检出，mechanically_reproduced=YES、negative_test_added=YES、full_regression=PASS(140/140)。
- 效率（ENGINEERING_OBSERVATIONAL_BENCHMARK，同口径回放）：v1.5 8,970,430 token/1389s，未反弹且低于 v1.4（-2.59%）与 v1.3（-9.14%）；时间 -30.2%/-49.2%；v1.4 六效率机制全保留。
- Harness 真实状态（§6 词表）：ZCode=VALIDATED L9；Claude Code=L1+BLOCKED_RUNTIME_AUTH(401 实证)；TRAE/WorkBuddy=PENDING_EXTERNAL_VALIDATION。
- 新增规格/schema：HARNESS_CAPABILITY_CONTRACT、MID_PROJECT_ATTACHMENT_SPEC+SKILL_ADOPTION_BOUNDARY_SCHEMA、TELEMETRY_CLOSED_LOOP_SPEC+TELEMETRY_CONTROL_POLICY、双 Profile schema、CUSTOMIZATION_ARCHITECTURE、CORE_BOUNDARY_POLICY、PRODUCT_CORE_MANIFEST_V1。

## 1.4.0 (2026-08-31)

**Reliability Efficiency / Token Optimization**——同口径隔离回放实测：Token -6.71%（9,872,301 → 9,209,337）、时间 -27.21%、验收 14/14 持平、可靠性九项不回归全 PASS。

- TOKEN_COST_PROFILER 先行：v1.3 成本画像与 OG-001..007 过度治理排名（先归因后优化）。
- DELTA_CONTEXT：CONTEXT_SNAPSHOT（12 字段）+ 增量读取 + hash 失效（full_context_reload_count=1 实证）。
- VERIFIED_STATE_CACHE：机械验证结论按输入哈希缓存，严格失效，禁 stale 复用。
- RISK_BASED_GATE_ROUTING：LOW/MEDIUM/HIGH/CRITICAL 四级 + Gate 依赖图 + NOT_APPLICABLE + 未知面 fail-closed；CRITICAL 全链不降级。
- EVIDENCE_REFERENCE：证据存一次正文，之后 REF+hash 引用（evidence_dedup_count=21 实证）。
- HOT/COLD_HANDOFF：热上下文 9 字段 + 冷索引（ID+path/hash），交接不再重讲项目故事。
- BATCH_EVOLUTION：指纹去重 + 触发式深度分析（STAGE_END/PROJECT_END/REPEATED_PATTERN≥2/HIGH_SEVERITY/EXPLICIT）+ 批量处理；进化引擎新增 SIMPLIFY/MERGE/REMOVE/DEFER 减法操作。
- LL-008 修复：计划对齐禁止词 ASCII 词边界匹配（EFF-010 三例历史误报放行 / EFF-011 真禁止词仍阻）。
- LL-011 路径约定采纳；LL-010 端口预检评估后不采纳。
- 效率指标：gate/cache/delta/dedup 计数器 + TOKEN_PER_*（不可归因处 NOT_AVAILABLE）。

## 1.3.0 (2026-08-30)

**Reliability Coverage Hardening**（需求覆盖完整性 / 运行时-适配器交付完整性 / 角色工作流 E2E 完整性）。

- PATCH-EV-001 Contract Scope Completeness：理解门禁强制 source_requirements → requirement_coverage 全量处置（ADOPT/REJECT/NEEDS_MORE_DATA/DEFERRED），堵住"合同静默漏 MUST"失效类（源：v1.2 任务真实缺口）。
- PATCH-EV-002 Declared Runtime Adapter Gate：`check_declared_adapter.py`——声明的生产运行时无启用适配器 → Release BLOCKED；静默回退 → FAIL；开发态 → PENDING 不误伤（源：Round 1 PostgreSQL 声明≠交付）。
- PATCH-EV-003 Role Workflow E2E Coverage Gate：`check_role_workflow_coverage.py`——由工作流状态机+角色矩阵推导必需转换，旅程清单缺覆盖即 FAIL（源：Round 1 与 Phase B 两项目独立复现的角色能力面遗漏）。
- 随附（候选上已验证的提案侧基础设施）：`skill_evolution_core.py` 与 `SKILL_EVOLUTION_ENGINE_SPEC.md`（Experience→Learning→Bounded Patch→Negative/Held-out/Regression，仅 AUTO_PROPOSE）。
- 验证链：负向 17 + Held-out 46/46（独立代理出题）+ Rescue 8/8 + Round1 14/14 + 全量 78/78。
- Phase C 基准（ENGINEERING_OBSERVATIONAL_BASELINE）：双臂验收 14/14；With-Skill 2735s / 9,872,301 token，No-Skill 1039.5s / 3,845,571 token——过程可证明性与旅程广度 vs 更高成本，详见 Release Report 与 KNOWN_OVERHEAD。

## 1.2.0 (2026-08-30)

- Reliability Hardening：新增 `NO_STAGE_WAIT`、`NO_DEAD_END_SUSPEND` 与 `NO_BLIND_RESUME` 的可执行协议。
- 新增确定性 Continuation Gate：拒绝存在下一合法动作时的 `ILLEGAL_PASSIVE_STOP`，并统计 `unnecessary_human_wait_count`。
- 新增有界 Recovery Ladder、Last Known Good、Safe Recovery Escalation、Human Recovery Package 与 Resume Verification 规则。
- Core Telemetry Binding：项目最终验收必须绑定唯一 Recorder/Verifier、hash-chain 和 anchor；Round 1 式无锚点或弱本地日志在核心验证时拒绝。
- 新增持续施工、恢复、人类接管和遥测完整性回归；v1.1.0 行为回归保持通过。
- （接管补全）`EXECUTION_RESOURCE_GUARD`：GREEN/YELLOW/RED/UNKNOWN 资源状态、不可见即 NOT_AVAILABLE 禁估算、原子单元收口与 `UNVERIFIED_PARTIAL_WORK`（`EXECUTION_RESOURCE_GUARD_SPEC`）。
- （接管补全）`MODEL_HANDOFF_PROTOCOL`：29 字段交接包 schema + 机械校验 + `verify_handoff` 交接验证（`HANDOFF_VERIFICATION_PASS/FAIL`）。
- （接管补全）`BENCHMARK_PROTOCOL_V2`：PRIVATE_BENCHMARK_SPEC 与 PUBLIC_BUSINESS_EVENT 分离 + `CONTROLLER_CONTAMINATED` 检测。
- （接管补全）恢复升级阶梯机械化：`SAFE_ROLLBACK_ATTEMPT` 与合同合规 `ALTERNATIVE_RECOVERY` 先于 `RECOVERY_EXHAUSTED`。
- （接管补全）遥测新增 6 类事件（RESOURCE_BUDGET_WARNING/PROACTIVE_HANDOFF_STARTED/MODEL_HANDOFF_READY/MODEL_HANDOFF_COMPLETED/HANDOFF_VERIFICATION_FAIL/UNVERIFIED_PARTIAL_WORK）与 4 项交接/恢复核验指标。
- （接管补全）Round 1 全 7 项 Finding 与 Rescue 7 项经验覆盖矩阵、连续性/升级/遥测/基准具名规格、v1.1 回归报告。

## 1.1.0 (2026-08-30)

- 发布 PROJECT_RELIABILITY_TELEMETRY：追加式哈希链事件、机械指标、Token 可用性诚实状态、连续性和可靠性报告。
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
