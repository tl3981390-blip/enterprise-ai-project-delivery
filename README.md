# 企业AI项目交付 Skill（enterprise-ai-project-delivery）

> **理解完成之前，禁止施工。**
> 让企业 AI 项目从「AI 说做完了」变成「真实可以证明已完成」。

## 它解决什么

企业内部开发 AI 产品（RAG / Agent / 应用）时，先证明 AI「真正理解了用户目标、当前状态、约束、成功标准」，再按门禁式流程交付，最终用真实 Evidence 证明已完成——而不是事后「我说错了/你说得对」的补救。

## 四大价值主张

1. 防止未理解就施工
2. 防止施工过程目标漂移
3. 防止越权和擅自扩展
4. 防止假验收 / 失败后只改报告不改事实

## 使用方式

- **入口**：`SKILL.md`（主 Skill，触发 + S0 理解门禁 + 编排）。
- **任何任务先进入 UNDERSTANDING**：回答施工前八问 → 生成任务理解合同 → 施工前理解门禁 → `READY_TO_PLAN` → 计划-合同对账 → `READY_TO_EXECUTE` 才开放写改。
- **全程 DRIFT_CHECK**：任何不在合同内的动作 → `CONSTRAINT_CONFLICT` → `BLOCKED`。
- **持续施工**：目标与计划已锁定后，阶段通过会自动选择下一合法动作；“继续”只在暂停状态触发重新核验，不是对 blocker 已解决或权限已授予的盲信。
- **执行资源守卫**：模型资源不足时按 GREEN/YELLOW/RED/UNKNOWN 收口——不开危险新 Stage、完成或中止原子单元、生成完整交接包，禁止估算不可见额度。
- **模型交接**：`MODEL_HANDOFF_PACKAGE` 29 字段合同 + 继任模型 `verify_handoff` 机械核验（HEAD/工作区/合同/Evidence/运行时），核验失败禁止继承。
- **唯一遥测入口**：项目遥测必须使用核心 Recorder + hash-chain + anchor；项目本地“看似 PASS”的替代实现不能通过最终验收。
- **基准卫生**：基准私有标记与施工可见文本分离，泄漏即标记 `CONTROLLER_CONTAMINATED`，污染结果不得用于行为效果证明。

## 目录结构（阶段 1 骨架）

```text
SKILL.md                主 Skill（触发 + S0 + 编排）
00_总控/                 S0：理解门禁 / 状态机 / 任务理解合同 / 计划-合同对账 / DRIFT_CHECK / 权限阶段控制
01_项目理解 … 19_最终交付_经验沉淀
共享/
  references/            DoD、公共检查清单
  scripts/               validate-skill / check_understanding_gate / check_plan_alignment / check_state_machine / collect_evidence
  schema/                任务理解合同 / input / output / evidence
tests/evals/             结构 / 触发 / 状态机 / 理解专项 Eval
LICENSE / NOTICE / CHANGELOG.md
```

## 快速校验

```bash
python 共享\scripts\validate-skill.py --root .
python 共享\scripts\check_understanding_gate.py --contract tests\evals\structural\sample_contract_valid.json
python 共享\scripts\check_state_machine.py --legal tests\evals\state_machine\legal_transitions.json --walk tests\evals\state_machine\walk_happy_path.json
```

## 状态机（12 状态）

`UNDERSTANDING → UNDERSTANDING_BLOCKED/UNDERSTANDING_COMPLETE → READY_TO_PLAN → PLANNING → PLAN_BLOCKED/PLAN_COMPLETE → READY_TO_EXECUTE → EXECUTING → EXECUTION_BLOCKED/VERIFYING → COMPLETED`

**禁止**从 UNDERSTANDING 直接跳 EXECUTING。

## 边界

- 不连接/不修改企业生产系统、不修改 Harness（另行授权）。
- 阶段 1 只建 Skill 自身工程骨架，不做正式业务项目。
- OpenAI `.system` 全程只读。（License 见 `NOTICE` / `09`）

## 版本
`1.4.0`（Reliability Efficiency；v1.3.0 及更早版本保持不可变）。

## 授权
MIT License（见 LICENSE）。上游来源声明见 NOTICE。
