# SYSTEMIC_ROOT_CAUSE_MAP — POST_v1.5.0 系统性泛化根因审计

审计日期：2026-08-31 ｜ 审计性质：只读全仓（步骤 1–9）｜ 基线：`v1.5.0 → 491f6c9`，HEAD=`3ab629c`（docs/examples/README-only delta），140/140 tests PASS，工作树干净。

## 0. 入口证据（冻结）

- 真实 Harness：WorkBuddy，用户显式请求「使用这个 Skill 做一个家庭点菜单项目」。
- Harness 结论：该 Skill =「企业 AI 内部产品开发」固定模板（固定阶段/SSO/企业权限/MCP 权限网关/多角色验收/数据治理/企业审批），家庭点菜单 ≠ 企业 AI 内部产品 → 判定不适用。
- 现象 A（分发文件在仓库根被判 Core 变化）：已由 `3ab629c` 修复，机械复核成立（tag 后增量仅 docs/examples/README），本轮不重复修改。

## 1. 问题链（SYMPTOM → DIRECT → DEEPER → AFFECTED → FIX → REGRESSION）

```text
WorkBuddy 拒绝个人项目显式调用
  ↓ 直接原因
触发面把「适用范围」写成「企业 AI 内部产品」领域条件：
  - 根 SKILL.md frontmatter description：Use when 你需要在企业内部开发一个 AI 产品/RAG/Agent
  - 安装面适配器（.zcode/skills/.../SKILL.md）description 同样写死「企业内部 AI、RAG 或 Agent 项目」
  - SKILL.md「触发方式」：面向「企业内部 AI 开发交付方」，且引用不存在的「下节触发意图」（悬空引用）
  - 触发例库 tests/evals/trigger/trigger_cases.md：正例全部企业内部 AI；负例只有琐碎问答；
    设计文档 07_测试与验收设计.md 承诺的 8–10 正/负例 + near-miss + train/val 从未交付
  ↓ 更深根因 RC-1
产品身份由「来源领域」而非「功能」定义：Skill 从真实企业 AI 交付方法论提炼而来
（03_我的项目能力提炼表.md：26 项能力全部企业 AI），来源领域泄漏进适用性条件、
模块命名（07_RAG设计/08_Agent设计/09_MCP…/10_企业治理…）、profile schema、
测试夹具与 Release 清单 —— 即 HISTORICAL_PROJECT_TEMPLATE_LEAKAGE
（泄漏层级：适用性/激活层，而非阶段顺序层）
  ↓ 关联子系统
触发层 + 分类层 + 阶段编排 + Profile schema + 验收脚本 + 测试体系 + 文档
  ↓ 修复
适用性与项目类型解耦（显式调用默认接受）；能力注册表 + 按项目生成 Active Delivery Plan；
触发例库补非企业/非 AI 边界例
  ↓ 回归
SYS-001/002/003/022/023/033/034/035
```

## 2. 根因清单（证据 → 结论）

### RC-1 APPLICABILITY_AS_DOMAIN_SCOPE（主根因）
「复杂项目可靠性交付」被写成「企业 AI 内部产品交付」。证据：SKILL.md:3 description、SKILL.md:35 触发方式、安装适配器 description、trigger_cases.md 例库、00_总控 SKILL.md:3（「企业AI交付任务刚开始」）、01_项目理解 When to Use（「企业 AI 交付任务」）。README 自称 "complex AI project delivery"、docs/INSTALL 完全任务无关、SKILL.md 却写「企业内部」——三层口径互相矛盾（文档-实现打架，§29）。

### RC-2 LAYER_FUSION（分类层与能力层融合）
`product_completion_core.py::PROJECT_PROFILE_FIELDS` 把分类字段（project_type/business_goal/risk_level/required_capabilities/acceptance_matrix/project_specific_constraints）与能力字段（runtime/database/rag/agent/workflow/deployment_target）合成一组必填；`PROJECT_PROFILE_SCHEMA.json` required 同样 12 项全必填；`test_missing_profile_fields_rejected` 把该假设锁死。后果：任何项目（含无 RAG/无 Agent 的个人项目）必须携带 AI/企业能力词汇才能通过分类 —— 能力在结构上是强制的，而非条件激活。

### RC-3 CAPABILITY_MODULES_AS_LIFECYCLE（能力模块被当生命周期强制）
- 根 SKILL.md 工作流把 13/14/16/17/18 无条件串进阶段链（仅 07–10 有选择括号）。
- `check_acceptance.py` 硬编码四角色（product/engineering/security/end_user）为全局强制，security 为企业角色；模块 14 「同一 Model 结论互相背书 → 无效」堵死了单人项目的合法坍缩路径。
- `19/Release检查清单.md` 要求「全部正式模块」「四角色」「真实企业哑案例」。
- `validate-skill.py` 把含企业 AI 命名的 20 模块树作为结构性强制（目录名本身是领域标签，但作为能力地址可保留——根因在激活语义不在命名）。
- Risk Router（`efficiency_core.route_gates`）机制本身真实有效（NOT_APPLICABLE + 依赖图 + CRITICAL 全链），但它只路由「执行期 Gate」，从不参与「计划期阶段/模块激活」；且测试里 available_gates 宇宙硬编码企业集合。Layer 4（Active Delivery Plan：ACTIVE_STAGES/NOT_APPLICABLE_STAGES/ACTIVE_GATES/REQUIRED_EVIDENCE/HUMAN_GATES/FINAL_ACCEPTANCE）作为产物不存在。

### RC-4 ENTERPRISE_CUSTOMIZATION_AS_PARAMETERIZATION（企业定制=内置模板改参数）
ENTERPRISE_PROFILE_FIELDS 是一张固定参数表（approval_policy/security_policy/audit_policy…），对应唯一隐式企业流水线；不存在「企业真实流程作为输入 → 编译为 Enterprise Profile/Workflow」的机制（§7 要求 Enterprise Workflow = 输入，不是 Core 默认流程）。CUS-001/002 仅参数化 approval_policy 取值。`05_Skill与Harness接口合同.md` 输入合同强制 org_policy_ref + user_identity（企业假设内建）。

### RC-5 EXPERIENCE_ROUTING_TWO_WAY_ONLY（经验路由二分且无频率护栏）
`classify_learning` 仅 GLOBAL/COMPANY 两线；CORE_BOUNDARY_POLICY 文本提到 PROJECT_SPECIFIC 线但代码未实现；无 HARNESS_SPECIFIC、无 ONE_OFF；GLOBAL 判定仅两个布尔（generalizable_across_organization），无 cross_project_validated / counterexample_checked 硬证；FREQUENCY≠GENERALIZABILITY 无机械护栏（§19/21）。减法进化（SIMPLIFY/MERGE/REMOVE/DEFER）已存在（合格，无需修）。

### RC-6 NO_ASSUMPTION_CHANGE_MODEL（早期假设锁死）
合同锁定后仅「重大变更须回本模块更新合同」；无 STILL_VALID/INVALIDATED/REQUIRES_REVALIDATION/NEW_REQUIRED 部分失效模型；无受影响假设→受影响验证态的依赖传播；VERIFIED_STATE_CACHE 按输入哈希严格失效（好基础）但无变更传播分类器。

### RC-7 DOC_IMPLEMENTATION_MISMATCH（文档口径分裂）
README（complex AI）≠ docs/INSTALL（任务无关）≠ SKILL.md/适配器（企业内部 AI）≠ 模块 00/01（企业 AI 交付）。另有 9 处模块 references 断链 + 1 处悬空章节引用 + `15_Evidence` 模块 references/scripts 空目录。

### RC-8 TEST_ASSUMPTION_LOCKIN（测试锁死错误设计）
- `test_critical_keeps_full_chain`：CRITICAL 必跑 rag/rbac/postgres 且 NOT_APPLICABLE 必空（企业 Gate 宇宙硬编码）。
- 夹具全域 census：唯一项目域夹具 = legal_rag（企业法务 RAG）+ EnterpriseReviewLab 审批流；examples 仅企业 profile；零非企业、零非 AI 夹具。
- `check_governance.py` 的 governance 检查强制 7 个企业治理字段（该检查本身属能力门禁，问题在于被当作全局验收链一部分）。

## 3. 判定（指令 §4 A–J 逐项）

- A. 「复杂项目=企业 AI」错同点：触发面 5 处 + profile schema + 四角色验收 + Release 清单 + 夹具全域。
- B. RELIABILITY INVARIANT（不得动）：理解先于施工、12 态状态机、合同+对账+DRIFT、NO_FAKE_PASS、Evidence 完整性（哈希链/Recorder 唯一）、遥测闭环、有界恢复+再验证、NO_STAGE_WAIT/LEGAL_STOP、资源守卫+模型交接、中途接入、merge 冲突检出、进化仅提案侧。PROJECT-SPECIFIC CAPABILITY（须条件化）：RAG、Agent、MCP 权限、企业治理/SSO、浏览器验收、多角色（企业四角色实例）、部署、License、升级回滚。
- C. 正确抽象的历史经验：NO_STAGE_WAIT/LEGAL_STOP（来自「等用户说继续」失败）、CONTRACT_SCOPE_COMPLETENESS（V1 合同漏 MUST）、ROLE_WORKFLOW_E2E_COVERAGE（角色面遗漏）、CRITICAL 全链不降级、治理成本观测。
- D. 泄漏：触发/适用性（RC-1）、能力必填字段（RC-2）、四角色全局强制（RC-3）、「全部正式模块/企业哑案例」（RC-3）。
- E. 19 阶段定性：CORE_LIFECYCLE = 00,01,02,03,04,05,06,11,12,15,19（11 个）；CONDITIONAL CAPABILITY = 07,08,09,10,13,16,17,18（8 个）+ 14（核心「独立验收」不变量 + 企业四角色为其实例化 → 恒活但视角随干系人坍缩）。属「文档表现错误 + 实现强制错误」并存，非历史流程顺序泄漏。
- F. Quick/Feature/Project 实测语义：交付强度（文档粒度/Evidence 深度），明确「不得降低理解、权限、Evidence、安全门禁」——不是三套固定流程模板，也不是项目分类器（合格；仅需在文档中显式声明 DELIVERY_INTENSITY 定位）。
- G. Router 真实性：执行期真实决策器；计划期缺位（见 RC-3）→ 修复 = 前置项目理解 → derive_active_plan，Router 继续管执行期 Gate。
- H. Enterprise Profile 现为「既定模板改参数」→ 须升级为「企业流程输入层」（RC-4）。
- I. Evolution 学习内容：现状二分路由 + 无频率护栏（RC-5）；抽象链（OBSERVED→CANDIDATE→VALIDATED）本身健全。
- J. 项目条件变化：无重理解机制（RC-6）。

## 4. Core Freeze 重开判定（指令 §42）

```text
REAL_HARNESS_FAILURE      = YES  （WorkBuddy 真实拒绝显式调用）
CURRENT_CORE_INSUFFICIENT = YES  （触发面+profile schema+验收脚本机械复现该拒绝）
GENERALIZABLE             = YES  （适用性解耦惠及所有非企业/非 AI 复杂项目）
REPRODUCIBLE              = YES  （description 文本与 validate_profile 规则确定性复现）
EVIDENCE_BACKED           = YES  （本文件 §1–§3 引用文件与行为）
→ CORE_FREEZE_REOPEN = LEGITIMATE（POST_V1.5_CORE_DEFECT_FIX）
```

## 5. 修复范围（根因最小化，非文件最小化）

Core：SKILL.md（根）、product_completion_core.py、PROJECT/ENTERPRISE_PROFILE_SCHEMA、check_acceptance.py、validate-skill.py、模块 00/01/13/14/16/19 语义、Release 清单、CORE_BOUNDARY_POLICY、新 PROJECT_ORCHESTRATION_SPEC、触发例库。
非 Core：examples（个人/桌面/双企业工作流）、tests（更新+新增 SYS 回归）、README/docs/CHANGELOG、9 处断链、安装面适配器。
不动：状态机/合同/遥测/恢复/交接/Evidence/上游吸收/演进提案侧流水线/减法 ops/Risk Router 执行期机制/历史 tag 与 evidence。
