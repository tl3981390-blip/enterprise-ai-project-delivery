---
name: enterprise-ai-project-delivery.s0-understanding-gate
description: 企业AI项目交付Skill · S0总控（施工前理解门禁）。任何任务进入后被要求先证明理解，再允许施工。Use when 一个企业AI交付任务刚开始、或任何阶段要推进到写改动作前。核心：施工前八问 → 任务理解合同 → 施工前理解门禁 → READY_TO_PLAN；执行全程 DRIFT_CHECK。
version: 1.3.0
license: MIT
compatibility: open
metadata:
  skill_id: enterprise-ai-project-delivery
  module: 00_总控
  language: zh-CN
  entrypoint: SKILL.md
  depends_on: 共享/references, 共享/scripts
---

# S0 总控 · 施工前理解门禁（PRE_EXECUTION_UNDERSTANDING_GATE）

## Project Reliability Telemetry

UNDERSTANDING 时通过核心 Recorder 初始化项目事件日志与 anchor；task_id 在 suspend/handoff/resume 后不得变化。DRIFT_CHECK 发现偏离时立即记录 DRIFT_DETECTED，真正重新对齐并有新 Evidence 后记录引用源事件的 DRIFT_CORRECTED。遥测只能观察本 Skill 管理的交付事件，禁止员工、桌面、键盘或后台浏览器监控。

本模块是整个 Skill 的最高门禁，位于一切业务模块之前。职责：状态机推进、任务理解合同生成与锁定、理解门禁判定、计划-合同对账、DRIFT_CHECK、权限阶段控制、停止条件与人工介入。

## 最高原则

> **理解完成之前，禁止施工。**

在任何 `WRITE/EDIT/DELETE/EXECUTE/DEPLOY/MIGRATE/INSTALL/ALTER` 之前，必须：
1. 回答施工前八问；
2. 生成并锁定《任务理解合同》；
3. 通过 `PRE_EXECUTION_UNDERSTANDING_GATE`；
4. 推出真实 `UNDERSTANDING_COMPLETE`，进入 `READY_TO_PLAN`。

## 施工前八问（必须全部回答，第 8 项须区分阻塞性/非阻塞性未知项）

1. 用户真正要解决什么问题？
2. 用户为什么要解决这个问题？（业务价值）
3. 用户最终想得到什么结果？（最终交付物）
4. 当前项目已经有什么？（当前状态）
5. 已经完成到什么程度？
6. 哪些内容禁止修改？（禁止项）
7. 成功到底如何判断？（成功标准/验收标准）
8. 还有哪些未知信息会实质改变施工方向？（区分阻塞性/非阻塞性未知项）

规则：阻塞性未知项（如“这是新项目还是正在生产的系统”）未解决 → `UNDERSTANDING_BLOCKED`，禁止进入施工。非阻塞性未知项（如“按钮颜色”）记录但不阻塞。

## Core Process（状态机推进）

```text
任务进入
  ↓
UNDERSTANDING（仅只读权限）
  回答八问 → 收集当前AI上下文/项目证据 → 判断缺失 → 询问必要信息
  ↓
生成 TASK UNDERSTANDING CONTRACT（见 references/任务理解合同模板.md）
  逐项标记来源（USER_EXPLICIT / USER_PREVIOUSLY_CONFIRMED / PROJECT_EVIDENCE / SYSTEM_OBSERVED / AI_INFERRED）
  ↓
PRE_EXECUTION_UNDERSTANDING_GATE 判定
  目标｜状态｜范围｜禁止项｜成功标准｜关键约束 六要素明确 + 无阻塞性未知项 + 无重大内部冲突
  → PASS: UNDERSTANDING_COMPLETE → READY_TO_PLAN
  → FAIL: UNDERSTANDING_BLOCKED / BLOCKED（人工介入）
  ↓
PLANNING → 计划-合同对账（check_plan_alignment）→ READY_TO_EXECUTE
  ↓
EXECUTING（开放写权限，全程 DRIFT_CHECK）
  ↓
VERIFYING → COMPLETED
```

**禁止**从 `UNDERSTANDING` 直接跳 `EXECUTING`。合法跳转全表见 [`references/状态与权限矩阵.md`](references/状态与权限矩阵.md)。

## 权限阶段控制

- UNDERSTANDING：仅 `READ/SEARCH/INSPECT/ANALYZE/COMPARE/SUMMARIZE/VALIDATE_EXISTING_STATE`
- READY_TO_EXECUTE 后：按模块开放 `WRITE/EDIT/EXECUTE`
- 非授权状态出现写改请求 → `permission_denied` + 写入 `drift_check_log`（`CONSTRAINT_CONFLICT`）

## 计划-合同对账（PLAN_CONTRACT_ALIGNMENT_CHECK）

生成施工计划后不得直接施工，逐项核对每个动作：
- 是否服务于目标？是否在本轮范围？是否违反禁止项？是否扩大权限？是否修改未授权区域？是否新增用户未要求的能力？

任一冲突 → `READY_TO_EXECUTE = false`，计划必须修正。脚本负责结构/字段检查，业务含义判定由 AI 负责（脚本不替代判断）。

## DRIFT_CHECK（施工过程目标漂移检查）

执行期每个新动作须与任务理解合同对账。不在目标范围 / 与禁止项冲突 / 需扩大权限 → `CONSTRAINT_CONFLICT` → `BLOCKED`。禁止“顺手优化”。

## 停止条件与人工介入

- 阶段边界是 checkpoint，不是 human gate。存在下一合法动作且无合法 human gate 时，必须 `AUTONOMOUS_CONTINUATION`，不得要求用户再次说“继续”。
- 等待只允许由合法 human gate 触发，且除 FINAL_COMPLETE 外必须生成完整 `HUMAN_RECOVERY_PACKAGE`。
- 用户的“继续/continue/resume/已处理”只产生 `RESUME_REQUEST`；必须完成 Current State Audit 后才可恢复，不能盲信文字。
- `max_loop` 是单一恢复路径的显式预算，不是放弃后直接等待的理由；预算耗尽转入安全回滚/替代恢复评估。

持续施工、恢复与人类接管的字段和顺序见 [`共享/references/持续施工与恢复协议.md`](../共享/references/持续施工与恢复协议.md)。

## 反合理化 / Red Flags

- 跳过合同直接开始“做”→ 违反最高原则
- 用 AI_INFERRED 冒充用户要求升级范围/权限 → 拒绝
- “以后可能需要”作为扩容理由 → DRIFT_DETECTED

## Verification

- `共享/scripts/check_understanding_gate.py` 校验合同必填字段与门禁结构
- `共享/scripts/check_plan_alignment.py` 校验计划与合同冲突
- `tests/evals/state_machine/` 校验状态机合法跳转
- 任何 Gate 结果为 FAIL/BLOCKED 必须有真实证据（`understanding_gate_result` / `constraint_conflicts`）
