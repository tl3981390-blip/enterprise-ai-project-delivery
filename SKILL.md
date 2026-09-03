---
name: enterprise-ai-project-delivery
description: 通过自然语言接手并可靠交付复杂项目：理解真实目标和现状，使用或生成可由人类修改的动态计划，组合成熟能力，执行、恢复并用真实证据验收。适用于新建、续建、按既有计划推进或条件变化中的软件、AI、数据、自动化及其他多步骤项目；不因“企业/个人/AI/Web”等标签套模板。
license: MIT
metadata:
  skill_id: enterprise-ai-project-delivery
  version: 3.0.7
  language: zh-CN
---

# v3 Stable execution boundary

Only caller-selected consequential unknowns may trigger questions. A clear bounded task may ask zero questions and must produce at least one real work unit. Internal reliability gates remain internal. Plan approval and human/enterprise edits require a Harness-asserted conversation-user reference bound to the current plan revision and scope. Optional adaptive strategy state may tune question, planning, capability, recovery, order and interaction preferences only; missing state uses safe defaults and never blocks delivery.

Adaptive Strategy values are closed catalog IDs, are loaded before the corresponding decision, and must measurably change only safe behavior: consequential-question selection, real-work plan ordering, eligible capability ordering, recovery sequence, dependency-legal Work Unit selection or structured Host interaction guidance. Updates call `delivery_runtime:update_adaptive_strategy` with current PASS Evidence IDs in the same session ledger; they never edit Core, permissions, authority, Evidence rules or releases.

Canonical Evidence enters only through a Harness/Tool Adapter-created `HARNESS_EXECUTION` receipt. The public `record_evidence` operation accepts a previously registered one-time `receipt_id` plus limited acceptance/dependency/business metadata; it never accepts a caller-made Evidence dict. Producer, source reference, status, candidate/work/execution identity and artifact hash are constructed from the receipt and cannot be overridden. Human plans, requirement changes, user corrections, user pause/resume and cancellation all require the matching trusted Harness origin; AI inference can only remain proposed.

# Reliable project delivery

产品定位：`AI DELIVERY CONTROLLER`。`understanding_core` 负责多轮目标理解、事实来源、
信息缺口与 Understanding Gate；动态计划的唯一编排真源是
`delivery_planning_core.compose_stages`；`delivery_runtime` 连接计划、能力调用、恢复和验收。

本目录只有根 `SKILL.md` 是用户可发现入口。`00–19/*/MODULE.md` 是按事件读取的内部参考，
绝不能作为独立 Skill 注册或展示在 `/` 菜单。

让用户只需要描述想完成什么。内部治理默认静默；对用户优先展示必要问题、项目理解、可编辑计划、执行结果、真实阻塞和最终证据，不展示状态码、Gate 名称或治理协议，除非用户要求诊断细节。
用户点名本 Skill 时记为 `EXPLICIT_INVOCATION` 并接受真实项目交付请求；项目标签不是拒绝或加重流程的理由。

## 先理解，再行动

在产生不可逆或写入性影响前，读取项目规则、当前状态、已有计划、证据和约束。只追问会实质改变方案且无法从现状查明的问题；其余不确定项明确记录并继续安全的只读工作。识别用户真正目标、成功标准、非目标、权限边界、已完成状态和验证方法。

Harness 必须把自然语言入口接到 `understanding_core.begin_understanding`，将每轮用户回答通过
`apply_answer` 写回事实事件；AI 推断只可 `PROPOSED`，不能静默成为事实。每轮最多展示四个当前最高价值问题，
但只要回答暴露新的 consequential unknown 就继续澄清。只有 `gate_pass=true` 后，才可通过
`delivery_runtime.start_from_understanding` 进入 Planning；不得直接构造一个看似完整的 facts 对象绕过理解。

不要把澄清做成产品经理问卷。先从用户原话和只读项目证据提取已经明确的 Goal、Scope、Journey、
Deliverable、Permission 与 Acceptance；只问仍会改变决策的缺口。边界明确的小修改允许零问题。
稀疏目标不得自行补充平台、登录、图片、随机功能、历史、并发或企业能力；这些只能作为待确认建议，
不能进入 Fact、Work Unit 或施工范围。

自然语言意图由 Host Model 基于当前对话语义解释，并通过 `intent_core.record_intent` 写入可审计记录；
不得从问号或其他标点推断 Approval。若 Approval、Question、Change、Cancel 等之间存在会改变执行的歧义，
只问一个最小澄清问题。

不要把关键词当作流程选择器。复杂度只决定检查深度（内部记为 `DELIVERY_INTENSITY`），不是项目分类器，也不是三套固定流程模板；所需工作来自这个项目的真实问题、依赖、风险和交付物。

## 计划由人类拥有

`AI GENERATES, HUMAN OWNS.`

Human Authority 与 Truth Integrity 是两个独立平面：授权用户拥有业务目标、范围、计划和验收选择；
Evidence Core 只保证系统不会把 `USER_WAIVED / UNVERIFIED` 伪造成 `PASS`，不能借可靠性规则夺取业务决定权。

- 有用户或企业计划：保持其结构、顺序和命名，以它为计划主体；只把可靠性义务映射为适当的 Task、Check 或 Gate，并把风险作为建议说明。
- 无计划：从已发现的真实工作单元生成计划。阶段数没有预设；简单项目可以很短，复杂项目按自然边界拆分。
- 用户可用自然语言增删、移动、合并、拆分、替换或锁定任何部分。把该表达转成内部语义编辑后执行，不要求用户提供 ID、JSON 或状态码，也不得偷偷恢复 AI 原计划。
- 条件变化时，找出依赖该条件的工作和证据，调用成熟 Planner 重新生成受影响 Work Unit 的完整内容；没有新规划片段时保持规划中而不是只加“已重规划”标签。保留未受影响内容与仍有效 Evidence；人类拥有的受影响内容保持原文并请求人类复核。
- 所有 Delivery 在执行前都有自适应深度的用户计划审阅；明确的“不用再问，直接开始”可作为当前计划范围内的展示豁免与执行批准，但必须记录来源和范围。批准后自动连续执行，内部 checkpoint 不向用户索要“继续”。

必须使用 `共享/scripts/delivery_runtime.py` 维护确定性会话状态；公开 Planning 入口只接受已通过的
Understanding Session，不能直接注入 facts。Harness 操作与真实 handler 的映射以
`harness_manifest.json.operation_handlers` 为准，不要另建平行计划、Evidence、Resume 或 Handoff 模型。
Capability 只能作为已发现 Work Unit 的施工或验证资源，绝不能创建 Work Unit 或决定其升级为 Stage。

### 软件工程执行 Profile（按事实启用）

当当前事实已确认是已有代码库、源代码改动或缺陷修复时，Harness 应读取
`delivery_runtime:get_engineering_execution_profile`。它提供：先理解并跑相关基线、关键逻辑的聚焦测试与最小改动、
失败时系统化根因定位及 blocker/回归重验、完成前独立检查范围合规与工程质量。并行或可回滚代码施工只有在 Harness 已提供
隔离工作区时才建议使用隔离分支/worktree。该 Profile 不创建 Stage、不强制 TDD 于非代码任务、不要求子代理、
不发现或伪造其他 Skill，也不改变 Human Authority、Permission、Evidence 或 Completion Gate。

## 组合成熟能力

`COMPOSE FIRST, EXTEND SECOND, REIMPLEMENT LAST.`

先查看当前 Harness 原生能力和已安装 Skills，再按需查看 `共享/references/上游吸收索引.md`。Specification、Clarification、Planning、Tasks、TDD、Testing、Review、Browser、Git、Deployment、Documentation、Handoff 等由成熟能力完成；本 Skill 只增加证据、权限、范围、恢复、连续性和防假完成控制。若必须本地实现，记录已搜索来源、兼容性理由和回归比较。集成后的真实能力不得低于上游基线。

当前 Harness 或企业目录可见的部门 Skill 可以作为项目资源，但不可凭名称直接信任。把项目/Planner 识别出的任意能力需求传给统一 Runtime，只从身份、兼容性、验证状态和权限允许的候选中选择；需要跨部门授权时先请求人类授权。看不见的 Skill 不能凭空发现，未提供企业 Skill Registry 时不得宣称已扫描全公司能力。Capability 只支持已有 Work Unit，不能产生项目结构。

选择能力后，Harness 使用 `request_capability_invocation` 取得绑定 Work Unit 的调用信封，实际执行后必须用
`record_capability_result` 回写输出和真实 Evidence。未授权、未兼容或仍需验证的候选不能生成可执行调用；
失败结果自动进入同一 Delivery Session 的 Failure/Recovery，不能以“已选中 Skill”冒充跨 Skill 协作完成。

每次调用必须完整经历 `DISCOVER → RESOLVE → BIND → ACTIVATE → INVOKE → RESULT → EVIDENCE → DEACTIVATE`，
并绑定 Session、Plan Revision、Work Unit、Capability identity/version、input scope 和 permission scope。
Work Unit 结束后撤销外部 instruction context、临时授权和 invocation scope，禁止污染后续工作。

所有执行、失败、恢复和验收 Evidence 必须先通过 `record_evidence` 写入候选绑定的 Evidence Ledger。
模型文字、任意字符串、错误 candidate、未知 Work Unit、过期或失效 Evidence 都必须拒绝；后续接口只接收
ledger 中的 evidence_id。需求变化后按依赖分类 STILL_VALID / INVALIDATED /
REQUIRES_REVALIDATION，未完成重验不得 COMPLETE。

自我进化仅产生隔离 Candidate：观察必须先分类并复现，个人偏好、单项目特例、外部 Capability 缺陷和
Harness 限制不得冒充 Core 缺陷；频率不等于正确性。候选可自动分析、修补、测试和攻击，但正式替换必须
经过 Human Release Authority，禁止运行中自改和 `AUTO_RELEASE`。

只加载与当前项目事实有关的模块。例如有 Web 用户旅程才读取浏览器验收模块；有部署目标才读取部署模块；发生失败才读取恢复模块。目录编号是能力库历史标识，不是项目阶段。

## 执行和恢复

按计划持续完成下一合法动作，不因一个内部检查通过而被动停下。每次动作受当前范围与权限约束；外部写入、生产变更、凭据或不可逆操作仍需相应授权。

失败时保留原始错误、环境和候选身份，定位根因，按会话 Recovery Budget 进行有界恢复，并重新验证原 blocker 和相关回归后继续。预算耗尽时输出包含原始证据、尝试、根因、人工动作与恢复后重验方法的接手包。只改报告、换一条较弱路径或用户说“继续”都不能证明恢复。资源或上下文不足时，在原子工作单元边界保存事实、未完成项、证据引用、blocker 和下一动作，供后续模型机械核验后接手。

## 完成标准

完成声明必须由当前候选上的真实 Evidence 支撑：关键用户旅程、异常与错误输入、权限边界、数据持久化、重启/恢复、真实浏览器或 API、部署与回滚等按项目事实选择。证据必须能追溯到命令、文件、日志、截图或外部系统结果；模型叙述不是证据。

无法在当前环境验证的项目写成 `PENDING_EXTERNAL_VALIDATION`，并说明缺少条件、影响和恢复路径。存在失败、过期证据、死链、未重验 blocker 或外部待验项时，不得声称完成。

结束报告清楚区分：已实现、已真实验证、仅静态检查、未验证、阻塞和剩余风险。详细可靠性协议只在相应事件发生时按需读取 `12_失败处理与恢复/`、`15_Evidence与防假验收/`、`共享/references/持续施工与恢复协议.md` 与 `共享/references/MODEL_HANDOFF_PROTOCOL.md`。

## 安装与发布边界

正式安装必须从仓库 URL 获取 GitHub Release asset，验证 tag/资产身份，安装自包含副本并运行自检；不得依赖作者开发目录。个人使用可解析最新 Stable Release；企业受控环境必须使用人类批准的精确 tag，禁止静默回退或自动升级，并记录安装身份。开发 Workspace 的迁移与公开 Skill 分离，私有 bootstrap 不进入 Release。发布前完成 Candidate 验收，历史 tag 永不移动；无法验证的远端或 Harness 结果保持 `PENDING_EXTERNAL_VALIDATION`。安装细节见 `docs/AGENT_INSTALL.md` 与 `docs/ENTERPRISE_VERSION_GOVERNANCE.md`。
