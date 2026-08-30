# LONG_RUNNING_PROJECT_CONTINUITY_SPEC（长周期项目连续施工规格）

目标：用户在项目开始时完成目标沟通与必要授权后，AI 持续自主推进；普通阶段边界、普通错误、可恢复异常不得反复索要"继续"。机械核心：`共享/scripts/continuation_core.py`（CLI：`check_continuation.py`）。

## 1. 生命周期

```text
UNDERSTANDING → … → EXECUTING → VERIFYING → STAGE_PASS → AUTO_ADVANCE → NEXT_STAGE → …
→ FINAL_VERIFICATION → FINAL_COMPLETE
```

Stage PASS 只是自动 Checkpoint，不是 Human Gate。

## 2. 五不变量

| 不变量 | 含义 | 机械判定 |
| --- | --- | --- |
| NO_STAGE_WAIT | 有下一合法动作且无人类门禁 → 必须继续 | `AUTONOMOUS_CONTINUATION`；被动停 → `ILLEGAL_PASSIVE_STOP` + `unnecessary_human_wait_count` |
| NO_DEAD_END_SUSPEND | 任何等待必须带完整人类恢复包 | `LEGAL_HUMAN_GATES` + `validate_human_package` |
| NO_BLIND_RESUME | "继续"只是 RESUME_REQUEST | `RESUME_VERIFICATION_PASS/FAIL`（candidate/governance/contract/runtime/evidence 五核验） |
| NO_RESOURCE_CLIFF | 资源不足先收口交接，禁止半阶段断裂 | 见 [`EXECUTION_RESOURCE_GUARD_SPEC.md`](EXECUTION_RESOURCE_GUARD_SPEC.md) |
| NO_FAKE_CONTINUITY | 新模型必须重验真实状态 | 见 [`MODEL_HANDOFF_PROTOCOL.md`](MODEL_HANDOFF_PROTOCOL.md) |

## 3. 合法等待（穷举）

`HUMAN_AUTHORIZATION_REQUIRED`、`HUMAN_BUSINESS_DECISION_REQUIRED`、`CONSTRAINT_CONFLICT_REQUIRES_HUMAN`、`RECOVERY_EXHAUSTED`、`EXTERNAL_HUMAN_ACTION_REQUIRED`、`USER_ONLY_ACCEPTANCE_REQUIRED`、`USER_REQUESTED_PAUSE`、`FINAL_COMPLETE`；模型资源交接暂停走 `MODEL_HANDOFF_REQUIRED`（等待继任模型，非用户）。其余一律 `ILLEGAL_PASSIVE_STOP`，系统不得结束任务。

## 4. Stage PASS 后的固定序列

```text
Freeze Stage Evidence → Update State → Update Telemetry → Calculate Next Legal Action
→ Resource Guard → AUTO_ADVANCE
```

## 5. LEGAL_STOP_GATE

准备 `WAIT_FOR_USER` 前必须存在：`stop_reason / human_gate_id / blocking_condition / why_ai_cannot_continue / required_user_action / resume_condition / verification_method / last_known_good / next_safe_action`。缺任一字段 → `PASSIVE_STOP_REJECTED`，自动计算下一合法动作并继续。

## 6. 回归

CONT-001..004、AUTH-001/002、RESOURCE-001..004、HANDOFF-001/002（`tests/reliability/`）。
