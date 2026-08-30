# EXECUTION_RESOURCE_GUARD_SPEC（执行资源守卫规格）

目标：落实 NO_RESOURCE_CLIFF——模型资源不足以安全完成下一工作单元时，禁止继续扩大施工，必须安全收口并交接，而不是让施工在半阶段断裂。

## 输入（仅限真实可见信号）

```text
visibility              ∈ {GREEN, YELLOW, RED, NOT_AVAILABLE}   # 平台/Provider 提供
provider_warning        # Provider 低额度预警（真实事件，非估算）
user_reported_exhaustion_risk  # 用户明确说没额度/快没额度/换模型
atomic_unit_in_progress # 当前处于必须安全收口的原子单元（迁移/批量变更/Git 操作/状态迁移）
atomic_unit_safe_to_complete   # 剩余资源能否安全完成当前原子单元
```

不可见即 `NOT_AVAILABLE`，禁止估算（不得输出"还剩 11%"之类）。资源状态抽象：`GREEN / YELLOW / RED / UNKNOWN`。

## 判定（机械，`共享/scripts/check_continuation.py --mode guard`）

```text
user_reported_exhaustion_risk=true                     → RED
visibility=RED                                          → RED
provider_warning 且 state ∈ {GREEN,UNKNOWN}             → YELLOW
visibility=NOT_AVAILABLE                                → UNKNOWN（不估算是 GREEN）
```

## 决策表

| 状态 | 原子单元 | 决策 | 必须事件 |
| --- | --- | --- | --- |
| GREEN/UNKNOWN | - | CONTINUE | - |
| YELLOW | - | PREPARE_CHECKPOINT：不开新的大型 Stage，准备 Checkpoint 与交接元数据 | RESOURCE_BUDGET_WARNING |
| RED | 无/未开始 | PROACTIVE_MODEL_HANDOFF | RESOURCE_BUDGET_WARNING, PROACTIVE_HANDOFF_STARTED, MODEL_HANDOFF_READY |
| RED | 进行中，可安全完成 | COMPLETE_ATOMIC_UNIT_THEN_HANDOFF：完成→必要验证→Checkpoint→交接 | 同上 + MODEL_HANDOFF_READY |
| RED | 进行中，无法安全完成 | STOP_NEW_WRITES：停止新写入，记录部分状态 | 同上 + UNVERIFIED_PARTIAL_WORK, MODEL_HANDOFF_READY |

部分工作（UNVERIFIED_PARTIAL_WORK）不得标记为 PASS；交接包中必须列入 `partial_unverified_work`。

## 指标

RESOURCE-001..004 为本规格的负向/回归场景；资源相关事件进入核心遥测（§50 事件）。指标 `model_handoff_count / successful_handoff_count / failed_handoff_count / resume_verification_fail_count` 由 `calculate_delivery_metrics.py` 机械计算；`handoff_elapsed_time / handoff_rework_count` 评估后暂不采纳（无真实 Provider 时间/返工来源，按 NOT_AVAILABLE 原则不估算）。
