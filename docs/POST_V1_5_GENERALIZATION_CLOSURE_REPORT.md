# SYSTEMIC_GENERALIZATION_CLOSURE_REPORT — POST_v1.5.0 泛化根因收口

日期：2026-08-31 ｜ 执行：SYSTEMIC_COMPLEX_PROJECT_RELIABILITY_ROOT_CAUSE_AUDIT（21 步全序）｜ 状态：**CLOSED**

## 1. 原始真实 Harness 症状

WorkBuddy（真实 Harness）读取正式 Skill/Adapter 后判定：该 Skill 为「企业 AI 内部产品」固定模板（固定阶段/SSO/企业权限/MCP 权限网关/多角色验收/数据治理/企业审批），进而以「家庭点菜单 ≠ 企业 AI 内部产品」拒绝用户显式调用。

## 2. 系统性根因（详见 `evidence/post_v1_5_generalization/SYSTEMIC_ROOT_CAUSE_MAP.md`，随 v1.5.1 发布）

| # | 根因 | 一句话证据 |
| --- | --- | --- |
| RC-1 | 适用性被写成领域条件 | 根 SKILL.md description「企业内部开发一个 AI 产品」+ 安装适配器同款 + 触发例库无非企业例 |
| RC-2 | 分类层与能力层融合 | PROJECT_PROFILE_FIELDS 12 项全必填（含 rag/agent/workflow） |
| RC-3 | 能力模块被当生命周期强制 | check_acceptance 四角色硬编码；Release 清单「全部正式模块/四角色/企业哑案例」 |
| RC-4 | 企业定制=内置模板改参数 | 无企业流程输入编译机制 |
| RC-5 | 经验路由二分、无频率护栏 | classify_learning 仅 GLOBAL/COMPANY 两线 |
| RC-6 | 无假设变化模型 | 合同锁定后无部分失效/重算机制 |
| RC-7 | 文档-实现口径分裂 | README(AI)/docs(任务无关)/SKILL.md(企业内部) 三层不一致 + 9 处断链 |
| RC-8 | 测试锁死错误设计 | 全域夹具=企业法务 RAG；CRITICAL 强制 rag/rbac/postgres |

发现的关联潜伏缺陷（同一根因族，已修）：悬空章节引用「触发意图」；9 处模块 references 断链；15_Evidence 空 references/scripts 目录（未动，无引用指向）；模块 00/01 When-to-Use 的企业预设。

## 3. 历史演化审计结论（v1.0→v1.5 + Rescue/ComplexProjectLab/EnterpriseReviewLab）

- 正确抽象（保留）：NO_STAGE_WAIT/LEGAL_STOP、CONTRACT_SCOPE_COMPLETENESS、ROLE_WORKFLOW_E2E_COVERAGE、CRITICAL 全链不降级、治理成本观测、减法进化 ops。
- 泄漏（已修）：来源领域（企业 AI）进入适用性/激活/schema/验收/清单——HISTORICAL_PROJECT_TEMPLATE_LEAKAGE 发生在**适用性层**而非阶段顺序层。
- 19 阶段定性：CORE_LIFECYCLE=00,01,02,03,04,05,06,11,12,15,19（+14 为独立验收不变量载体）；CONDITIONAL CAPABILITY=07,08,09,10,13,16,17,18。
- Quick/Feature/Project 实测=交付强度（DELIVERY_INTENSITY），非流程模板、非项目分类器（文档已显式声明）。
- Risk Router 为真实执行期决策器；计划期缺 Active Delivery Plan → 已补 `derive_active_plan`（理解→风险→能力→计划→路由，结构不再倒置）。

## 4. 修复（POST_V1.5_CORE_DEFECT_FIX）

Core（8 文件）：`SKILL.md`（根）、`共享/scripts/product_completion_core.py`（Part E：CAPABILITY_REGISTRY/derive_active_plan/compile_enterprise_workflow/classify_experience_route/validate_core_evolution_admission/assumption_change_model/required_acceptance_perspectives；分类-能力字段分离）、`共享/scripts/check_acceptance.py`（视角缩放）、`共享/scripts/validate-skill.py`（泛化护栏）、`共享/schema/PROJECT_PROFILE_SCHEMA.json`、`共享/schema/ENTERPRISE_PROFILE_SCHEMA.json`、`共享/references/PROJECT_ORCHESTRATION_SPEC.md`（新）、`共享/references/CORE_BOUNDARY_POLICY.md`（修订单）。
模块语义：00/01/11/13/16/18/19/05/06/08/10（条件激活/断链修复/Release 清单）+ 14 重写（独立验收不变量 + 视角缩放）。
非 Core：examples ×4（个人家庭菜单/桌面知识库/双企业工作流输入）、tests/evals/trigger/trigger_cases.md、README、05 接口合同修订单、CHANGELOG、9 处断链修复。

## 5. 测试

- 原有 140 项回归：**全 PASS，零修改**（放宽为向后兼容的直接证明）。
- 新增 `tests/reliability/test_generalization.py`：**32 项 SYS-001..035 机械回归**（含防复发护栏：validate-skill 检查 EXPLICIT_INVOCATION 语义 + 企业限定语回退检测）。
- 合计 **172/172 PASS**；`validate-skill.py` 0 错误 0 警告。

## 6. 重放（真实核心脚本驱动，ZCode 3.10.1 真实会话）

| 重放 | 结果 |
| --- | --- |
| R1 WorkBuddy 同场景：家庭点菜单显式调用 | **PASS**：EXPLICIT_INVOCATION 接受 → 理解门禁落入合法 `HUMAN_BUSINESS_DECISION_REQUIRED`（业务歧义=合法停止，非 Skill 拒绝）；过早声明 COMPLETE 被拒 |
| R2 非企业复杂桌面项目 | **PASS**：可靠性核心保留，enterprise/RAG/SSO/MCP 全 NOT_APPLICABLE，persistence/license/migration 能力激活 |
| R3 企业 A 流程（7 阶段） | **PASS**：WORKFLOW_COMPILED，source=ENTERPRISE_INPUT |
| R4 企业 B 流程（4 阶段，完全不同） | **PASS**：ONE CORE + MULTIPLE ENTERPRISE WORKFLOWS |
| R5 中途需求变化 | **PASS**：仅失效受影响态（INVALIDATED/REQUIRES_REVALIDATION/STILL_VALID/NEW_REQUIRED 四级正确），计划重算非从零 |
| R6 防模板钙化 | **PASS**：10 连企业 AI 项目后个人项目零能力泄漏；频率永不促 GLOBAL |
| R7 经验正确去向 | **PASS**：Harness→Adapter / 企业→Enterprise / 项目→Project / 通用→Core 候选，无串层 |
| 真实 WorkBuddy 复验 | **PENDING_EXTERNAL_VALIDATION**（本机无 WorkBuddy CLI；绝不伪造 PASS。复验合同：同一显式请求应到达业务澄清停止而非 Skill 拒绝） |

重放产物：`<historical-evidence-root>/post_v1_5_generalization/replay_report.json`。

## 7. 版本与身份

```text
v1.5.0 → 491f6c9f76c6c384fd18a21303aba56812eeadb1  （不变，历史未重写）
v1.5.1 → ba7ca9e71d90c2a20eb994053a6d2bee21c36f2c  （POST_v1.5.0 泛化缺陷修复）
zip    → enterprise-ai-project-delivery-v1.5.1.zip
SHA-256= 733c89b87d9e09c94406bcfbfb2fdd3f08061e4024bf3068e4b755f6b52f8715
GitHub push = PASS（main + 全部 tags；v1.5.0 tag 原样、v1.5.1 新增）
适配器完整性检查（机械执行）：tag 身份 PASS / core delta(过滤 docs|examples|README) 空 PASS / v1.5.0 历史身份 PASS / 工作树干净 PASS
```

版本决策依据（机械）：Core 语义缺陷修复 + 向后兼容（140 项旧测试零修改通过）→ semver PATCH → v1.5.1。不宣称 v1.5.0「本来就包含」该修复。

## 8. Core Freeze 决策

重开合法性：REAL_HARNESS_FAILURE=YES / CURRENT_CORE_INSUFFICIENT=YES / GENERALIZABLE=YES / REPRODUCIBLE=YES / EVIDENCE_BACKED=YES → `CORE_FREEZE_REOPEN = LEGITIMATE`（已记录）。修复+回归+重放+发布完成：

```text
CORE_FEATURE_FREEZE = ACTIVE   （重新生效）
PRODUCT_CORE = COMPLETE + v1.5.1 GENERALIZATION FIX
```

## 9. 安全扫描

Mimosa 深度扫描（fix 提交内容）：**0 findings**，sealed `sha256:0fb5935f…`；tag 后最终态复扫：**0 findings**，sealed `sha256:c6b973ee…`（两次一致）。提交/推送钩子的 python_ast_unavailable 兼容提示已通过上述密封扫描闭环。

## 10. 剩余限制（诚实声明）

1. WorkBuddy 真实复验未完成（本机无 CLI）→ `PENDING_EXTERNAL_VALIDATION`。
2. TRAE 仍 PENDING_EXTERNAL_VALIDATION（历史状态，与本轮无关）。
3. 15_Evidence 模块 references/scripts 为空目录（历史遗留，无引用指向，未在本轮根因链上，留待真实失效驱动）。
4. 仓库内开发史编号文档（01–10 号 md）为历史记录，仅 05 接口合同加了修订单，其余未逐字改写（历史文档不追溯重写）。
5. `FULL_SECURITY_AUDIT = NOT_AVAILABLE` 状态不变（静态扫描 ≠ 完整 AST 审计环境）。

## 11. 停止规则

本轮到此收口。下一阶段由**真实失效**（不同 Harness × 不同真实复杂项目 × 真实企业流程）而非作者想象驱动是否再次 Evolution；禁止想象性加功能。
