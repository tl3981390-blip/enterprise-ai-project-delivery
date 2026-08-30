---
name: enterprise-ai-project-delivery
description: 企业AI项目交付Skill。用于从业务问题出发，以「先理解、后计划、再施工、终验证」的门禁式流程交付一套可信、可验证的企业 AI 内部产品。Use when 你需要在企业内部开发一个 AI 产品/RAG/Agent，且要求交付过程可被真实 Evidence 证明、防目标漂移、防越权、防假验收。最高原则：理解完成之前禁止施工。
license: MIT
metadata:
  skill_id: enterprise-ai-project-delivery
  version: 1.2.0-dev
  language: zh-CN
  author: 企业Skill实验室
  requires: harness, permission-gateway
  entrypoint: SKILL.md
---

# 企业AI项目交付 Skill（enterprise-ai-project-delivery）

把一个企业 AI 项目从「AI 说做完了」变成「真实可以证明已完成」，并且在任何一个字节被修改之前，先证明我们真正理解了用户要什么。

## 最高原则（优先级最高，一切服从）

> **理解完成之前，禁止施工。**

任何任务进入本 Skill 后，**禁止直接 WRITE/EDIT/DELETE/EXECUTE/DEPLOY/MIGRATE/INSTALL/ALTER**。必须首先进入 `UNDERSTANDING` 状态：回答施工前八问 → 生成《任务理解合同》→ 施工前理解门禁（`PRE_EXECUTION_UNDERSTANDING_GATE`）→ 进入 `READY_TO_PLAN`；再经 PLAN → 计划-合同对账（`PLAN_CONTRACT_ALIGNMENT_CHECK`）→ `READY_TO_EXECUTE` 后才按模块开放写权限。执行全程持续 `DRIFT_CHECK`。

违反上述任一环节 = `CONSTRAINT_CONFLICT` → `BLOCKED`，**禁止先施工再解释**。

## 四大价值主张

- 防止未理解就施工（目标漂移/越权/假验收的根因）
- 防止施工过程目标漂移（DRIFT_CHECK）
- 防止越权和擅自扩展（禁止“顺手优化”）
- 防止假验收 / 失败后只改报告不改事实

## 触发方式

本 Skill 面向「企业内部 AI 开发交付方/应用工程师」主动配合使用。用户提出一个**企业 AI 内部产品开发**类任务时命中（参见下节触发意图）。Skill 是方法论门禁层，不替代交付 Agent 的编码，而是约束其有序、可验证地交付。

## 交付分级与核心工作流

先按可逆性和风险选用 Quick（低风险、可快速回滚）、Feature（跨组件或需完整规格）或 Project（多阶段、部署或治理影响）级别；分级只调节文档粒度，不能降低理解、权限、Evidence 或安全门禁。成熟的 Specify → Clarify → Plan → Tasks → Analyze → Implement → Converge 流程采用上游适配资产，企业机械门禁仍由本 Skill 独立掌握。详见 [`共享/references/上游吸收索引.md`](共享/references/上游吸收索引.md)。

## 核心工作流程（S0 编排）

每个受管项目在 UNDERSTANDING 通过核心唯一 Recorder 初始化 PROJECT_RELIABILITY_TELEMETRY，使用同一 task_id 贯穿执行、暂停、交接和恢复。发生漂移、失败、返工、人工介入、Fake PASS、Regression 或 Gate Failure 时立即追加事件，禁止等到最终报告再凭记忆补写。阶段通过是 checkpoint，不是等待用户的理由；只要存在下一合法动作且没有合法人类门禁，必须持续施工。详细协议见 [`共享/references/项目可靠性遥测协议.md`](共享/references/项目可靠性遥测协议.md) 与 [`共享/references/持续施工与恢复协议.md`](共享/references/持续施工与恢复协议.md)。

```text
任务进入
  ↓
[0] UNDERSTANDING 施工前理解门禁（S0 最高门禁）
    施工前八问 → 任务理解合同 → PRE_EXECUTION_UNDERSTANDING_GATE
    → 合法跳转：UNDERSTANDING_COMPLETE → READY_TO_PLAN（否则 UNDERSTANDING_BLOCKED/BLOCKED）
  ↓
[R] 阶段模块编排（受合同约束）
    01 项目理解 → 02 当前状态审计 → 03 需求与范围 → 04 SDD规格 → 05 TDD策略
    → 06 架构设计 → [07 RAG | 08 Agent | 09 权限网关 | 10 治理]
    → 11 施工 ⇄ 12 失败处理 → 13 浏览器验收 → 14 多角色验收 → 15 Evidence
    → 16 部署 → 17 License → 18 升级回滚 → 19 收尾沉淀
  ↓
[P] PLAN_CONTRACT_ALIGNMENT_CHECK：每个施工动作都在进入前与合同对账
  ↓
[E] READY_TO_EXECUTE → EXECUTING（此处才开放 WRITE/EDIT/EXECUTE）
     全程 DRIFT_CHECK
  ↓
[V] VERIFYING → COMPLETED（真实 Evidence 证明完成）
```

详细状态机与每状态权限见 [`00_总控/references/状态与权限矩阵.md`](00_总控/references/状态与权限矩阵.md)。

## 状态机与权限阶段控制

状态机（12 状态，禁止从 UNDERSTANDING 直接跳 EXECUTING）：

```text
UNDERSTANDING → UNDERSTANDING_BLOCKED / UNDERSTANDING_COMPLETE
UNDERSTANDING_COMPLETE → READY_TO_PLAN
READY_TO_PLAN → PLANNING → PLAN_BLOCKED / PLAN_COMPLETE
PLAN_COMPLETE → READY_TO_EXECUTE
READY_TO_EXECUTE → EXECUTING → EXECUTION_BLOCKED / VERIFYING
VERIFYING → COMPLETED
```

权限：UNDERSTANDING 阶段仅 `READ/SEARCH/INSPECT/ANALYZE/COMPARE/SUMMARIZE/VALIDATE_EXISTING_STATE`；写改权限在 `READY_TO_EXECUTE` 后按模块开放。

## 各模块 Overview

| 模块 | 职责 |
| ---- | ---- |
| 00_总控 | 施工前理解门禁 / 状态机 / 任务理解合同 / 计划-合同对账 / DRIFT_CHECK / 权限阶段控制 / 门禁 / 输出合同 |
| 01_项目理解 | 用户真正目标 / 最终结果 / 业务价值 |
| 02_当前状态审计 | 已有什么 / 完成到哪 / 哪些真哪些假 / 哪些不可改 |
| 03_需求与范围 | 范围 / 非目标 / 禁止项 / 成功标准 / 关键约束 |
| 04_SDD规格 | 先规格后编码，全维度规格 |
| 05_TDD与测试策略 | 判断式测试策略 |
| 06_架构设计 | 架构 / 组件 / 接口 / 部署形态 |
| 07_RAG设计 | 知识源 / 索引 / 权限 / 引用 / 拒答（四防） |
| 08_Agent设计 | 角色职责分离（多 Agent 适度） |
| 09_MCP与工具权限网关 | READ/WRITE/DELETE/EXECUTE/ADMIN/EXTERNAL 权限矩阵 |
| 10_企业治理与合规 | 审计 / SSO / 数据不出域 / 变更管理 |
| 11_施工管理与增量实现 | 增量实现 + DoD |
| 12_失败处理与恢复 | 根因定位 + 证据保留 + 停止条件 |
| 13_浏览器真实验收 | 真实浏览器操作验证 Web 产品 |
| 14_多角色验收 | 需求/工程/安全/用户 四视角 |
| 15_Evidence与防假验收 | 统一证据合同，防假验收 |
| 16_部署 | Build→Deploy→回滚，非“本地能跑” |
| 17_License与合规 | 代码/依赖/模型/数据许可扫描 |
| 18_升级与回滚 | semver / 迁移 / 兼容 / 回滚演练 |
| 19_最终交付与经验沉淀 | 最终报告 + 经验入库 |

## 输出合同（结构化，可被 JSON Schema 校验）

每次阶段/门禁完成，输出规范化 JSON（含 `phase`、`status`、`gate_results`、`evidence`、`can_advance`、`requires_human`），见 [`共享/schema/output_schema.json`](共享/schema/output_schema.json)。证据类型白名单与「模型文字禁止」见 `06`。

## 反合理化 / Red Flags

- 找借口跳过 UNDERSTANDING/合同 → 违反最高原则，BLOCKED
- “顺手优化”“顺便改一下”“以后可能需要” → 视为目标外扩展，`DRIFT_DETECTED`
- “已经完成了请直接验收”而无理解合同与证据 → 拒绝，回到门禁
- 只改报告不改事实 → 假验收，禁止
- “本阶段完成，请告诉我是否继续”但计划仍有合法动作 → `ILLEGAL_PASSIVE_STOP`，必须继续
- 用户说“继续”就盲信权限、服务或 blocker 已恢复 → `RESUME_VERIFICATION_FAIL`，保持暂停并更新恢复包

## Verification（本 SKILL 自身）

- `共享/scripts/validate-skill.py`：结构/frontmatter/引用/版本/License 校验
- `共享/scripts/check_understanding_gate.py`：理解门禁结构与必填字段校验
- `共享/scripts/check_plan_alignment.py`：计划-合同冲突检查
- `共享/schema/*.json`：合同/输入/输出/Evidence 的 JSON Schema
- `tests/evals/state_machine/`：状态机合法跳转测试
- `tests/reliability/`：持续施工、人类恢复包、盲恢复与核心遥测绑定回归

## 硬边界

- 不连接/不修改企业生产系统；不修改 Harness（Harness 落地另行授权）
- 阶段 1（本骨架）只建立 Skill 自身工程骨架，不实现正式业务项目
- OpenAI `.system` 内容全程只读，禁止复制（License 边界见 `09` / NOTICE）
