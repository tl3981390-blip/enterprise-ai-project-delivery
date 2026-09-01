# DELIVERY_PLANNING_SPEC（通用动态交付规格）

生效：v1.6.0 ｜ 机械核心：`共享/scripts/delivery_planning_core.py` ｜ 回归：`tests/reliability/test_dynamic_delivery_v2.py`、`tests/reliability/test_replan_and_capability_decoupling.py`、`tests/reliability/test_delivery_runtime.py`

## 定位重申

`UNIVERSAL COMPLEX PROJECT RELIABILITY DELIVERY SKILL`：理解项目 → 识别真实结构/风险/依赖/约束 → 动态生成交付路径 → 执行 → Evidence → Recovery → Acceptance → Final Complete。它不是任何领域的模板系统。

## 1. 关键词只是上下文信号（KEYWORD_ROUTING_GUARD）

`企业 / AI / Agent / RAG / Web / Desktop / Personal / Family / 个人 / 家庭 / 内部` 等词只能是 `PROJECT_CONTEXT_SIGNAL`，用于措辞与领域理解，**不得**决定复杂度、阶段数、Delivery Intensity、是否 Quick、是否需要审批/SSO/MCP/RAG/多角色/企业治理。「企业内部改静态页」可以是 LOW；「个人跨平台桌面+同步+恢复+插件」可以是 HIGH。机械护栏：`keyword_signals_are_context_only()` 断言决策表键名零关键词泄漏（DYN-001）。

## 2. 复杂度来自真实结构（PROJECT_COMPLEXITY_ASSESSMENT）

`assess_complexity(factors)`：22 个结构因子（业务目标数/旅程/组件/依赖/外部系统/数据状态/失败分支/恢复/权限/安全/部署/并发/跨平台/迁移/不可逆/多角色/环境/验收难度/业务风险/存量兼容/范围变化/依赖深度），带权计分（单因子贡献封顶），输出 `COMPLEXITY_FACTORS / RISK_FACTORS / 依赖因子 / 验收因子` 与**具名 rationale**（每个等级必须能说明 WHY；未知因子 fail-closed 报错，不猜）。

## 3. 能力需求推导

`derive_capability_needs(factors, declared)`：能力 = 结构因子推导 ∪ 用户显式声明。相同结构的不同标签项目得到完全相同的能力集（DYN-004 同关键词不同复杂度 → 不同计划；同结构不同标签 → 相同计划）。

## 4. DELIVERY_EXECUTION_PLAN

`build_delivery_execution_plan(...)`：用户可见导航图。每阶段七要素：阶段名称/目标/主要工作/输出/进入条件/完成条件(含验收方式)/失败后的处理。固定的是 Goal/Output/Acceptance/Evidence 四件事，不是阶段数量与内容。颗粒度：Stage 必须携带 ≥1 价值标记（独立用户价值/架构边界/依赖边界/独立风险/状态边界/可独立验收产物），否则降级为上一 Stage 的内含任务（DYN-005）。Final Acceptance Matrix：最终必须存在的真实能力/必须通过的旅程/必须验证的失败分支/必须真实持久化的数据/必须真实验证的环境/必须验证的风险/证明 Final Complete 的 Evidence（DYN-006）。

## 5. 计划展示后默认自动继续

Delivery Plan 是导航图不是审批门：`SHOW_PLAN → 无真实阻塞 → CONTINUE`，保持 `NO_STAGE_WAIT`。合法 Human Gate 仅限：业务目标重大歧义、不可逆操作、权限授权、企业审批、用户专属验收、真实外部动作、重大架构方向决策。

## 6. USER_INTERACTION_BOUNDARY

`INTERACTION_MODE = USER`（默认）/ `DIAGNOSTIC`。USER 模式静默执行内部治理（Core Identity/Adapter 校验/合同内部态/Gate 评估/风险路由/能力注册/遥测与证据记账/恢复/Resume/Handoff），只暴露：必要问题、项目理解、Delivery Plan、重要计划变化、真正阻塞、重要失败、阶段关键成果、Final Acceptance。内部码（UNDERSTANDING_BLOCKED / CORE_RELEASE_IDENTITY_BLOCKED / NOT_APPLICABLE / Gate 图 / Core Hash / Adapter 元数据）必须经 `INTERNAL_STATE_TRANSLATIONS` 翻译为人类语言（DYN-008/009）。所有 Harness 遵守统一 WHAT_TO_EXPOSE，可保留各自语言风格。

## 7. Replan

范围/技术/部署/场景/优先级变化 → `assumption_change_model`（STILL_VALID/INVALIDATED/REQUIRES_REVALIDATION/NEW_REQUIRED）→ 重算复杂度与 Active Delivery Plan → 继续。禁止硬跑旧计划与全项目清零（DYN-007）。

## 8. 最少提问

只问会改变方案的问题；可自行推断项必须低风险/可逆/易改/不动核心架构/不引发大返工。未知项影响核心旅程/数据模型/架构/权限/部署/大量已有工作时必须询问。
