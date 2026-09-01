---
name: enterprise-ai-project-delivery
description: 通过自然语言接手并可靠交付复杂项目：理解真实目标和现状，使用或生成可由人类修改的动态计划，组合成熟能力，执行、恢复并用真实证据验收。适用于新建、续建、按既有计划推进或条件变化中的软件、AI、数据、自动化及其他多步骤项目；不因“企业/个人/AI/Web”等标签套模板。
license: MIT
metadata:
  skill_id: enterprise-ai-project-delivery
  version: 1.10.0
  language: zh-CN
---

# Reliable project delivery

产品定位：`AI DELIVERY CONTROLLER`。`understanding_core` 负责多轮目标理解、事实来源、
信息缺口与 Understanding Gate；动态计划的唯一编排真源是
`delivery_planning_core.compose_stages`；`delivery_runtime` 连接计划、能力调用、恢复和验收。

让用户只需要描述想完成什么。内部治理默认静默；对用户优先展示必要问题、项目理解、可编辑计划、执行结果、真实阻塞和最终证据，不展示状态码、Gate 名称或治理协议，除非用户要求诊断细节。
用户点名本 Skill 时记为 `EXPLICIT_INVOCATION` 并接受真实项目交付请求；项目标签不是拒绝或加重流程的理由。

## 先理解，再行动

在产生不可逆或写入性影响前，读取项目规则、当前状态、已有计划、证据和约束。只追问会实质改变方案且无法从现状查明的问题；其余不确定项明确记录并继续安全的只读工作。识别用户真正目标、成功标准、非目标、权限边界、已完成状态和验证方法。

Harness 必须把自然语言入口接到 `understanding_core.begin_understanding`，将每轮用户回答通过
`apply_answer` 写回事实事件；AI 推断只可 `PROPOSED`，不能静默成为事实。每轮最多展示四个当前最高价值问题，
但只要回答暴露新的 consequential unknown 就继续澄清。只有 `gate_pass=true` 后，才可通过
`delivery_runtime.start_from_understanding` 进入 Planning；不得直接构造一个看似完整的 facts 对象绕过理解。

不要把关键词当作流程选择器。复杂度只决定检查深度（内部记为 `DELIVERY_INTENSITY`），不是项目分类器，也不是三套固定流程模板；所需工作来自这个项目的真实问题、依赖、风险和交付物。

## 计划由人类拥有

`AI GENERATES, HUMAN OWNS.`

- 有用户或企业计划：保持其结构、顺序和命名，以它为计划主体；只把可靠性义务映射为适当的 Task、Check 或 Gate，并把风险作为建议说明。
- 无计划：从已发现的真实工作单元生成计划。阶段数没有预设；简单项目可以很短，复杂项目按自然边界拆分。
- 用户可用自然语言增删、移动、合并、拆分、替换或锁定任何部分。把该表达转成内部语义编辑后执行，不要求用户提供 ID、JSON 或状态码，也不得偷偷恢复 AI 原计划。
- 条件变化时，找出依赖该条件的工作和证据，调用成熟 Planner 重新生成受影响 Work Unit 的完整内容；没有新规划片段时保持规划中而不是只加“已重规划”标签。保留未受影响内容与仍有效 Evidence；人类拥有的受影响内容保持原文并请求人类复核。

需要确定性会话状态时，使用 `共享/scripts/delivery_runtime.py` 作为唯一编排入口；不要另建平行计划模型。
Capability 只能作为已发现 Work Unit 的施工或验证资源，绝不能创建 Work Unit 或决定其升级为 Stage。

## 组合成熟能力

`COMPOSE FIRST, EXTEND SECOND, REIMPLEMENT LAST.`

先查看当前 Harness 原生能力和已安装 Skills，再按需查看 `共享/references/上游吸收索引.md`。Specification、Clarification、Planning、Tasks、TDD、Testing、Review、Browser、Git、Deployment、Documentation、Handoff 等由成熟能力完成；本 Skill 只增加证据、权限、范围、恢复、连续性和防假完成控制。若必须本地实现，记录已搜索来源、兼容性理由和回归比较。集成后的真实能力不得低于上游基线。

当前 Harness 或企业目录可见的部门 Skill 可以作为项目资源，但不可凭名称直接信任。把项目/Planner 识别出的任意能力需求传给统一 Runtime，只从身份、兼容性、验证状态和权限允许的候选中选择；需要跨部门授权时先请求人类授权。看不见的 Skill 不能凭空发现，未提供企业 Skill Registry 时不得宣称已扫描全公司能力。Capability 只支持已有 Work Unit，不能产生项目结构。

选择能力后，Harness 使用 `request_capability_invocation` 取得绑定 Work Unit 的调用信封，实际执行后必须用
`record_capability_result` 回写输出和真实 Evidence。未授权、未兼容或仍需验证的候选不能生成可执行调用；
失败结果自动进入同一 Delivery Session 的 Failure/Recovery，不能以“已选中 Skill”冒充跨 Skill 协作完成。

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
