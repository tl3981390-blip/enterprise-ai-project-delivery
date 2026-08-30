# HOT_COLD_HANDOFF_SPEC（热/冷交接协议）

机械核心：`efficiency_core.py::build_handoff_context`；回归：EFF-007。

1. HOT_CONTEXT（继任者立即必知，9 字段）：goal/task_id/current_stage/current_head/current_state/current_blocker/last_known_good/partial_work/next_legal_action。partial_work 空列表=显式"无部分工作"，仍属热项。
2. 历史（Failure/Recovery/Evidence/Reports/Full Telemetry/Old Stage/Experience Pack/Ledger）全部入 COLD_CONTEXT_INDEX：只给 ID+path/hash。
3. 继任者按需读取冷项；禁止交接包重讲整个项目故事。目标=最少上下文安全继续。
4. 身份核验不降级：hash 级 HEAD/worktree/contract/evidence/runtime 对账保持（v1.2 起的交接核验语义不变——省的是叙述，不是校验）。
