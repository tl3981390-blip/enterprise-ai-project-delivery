# DELTA_CONTEXT_SPEC（增量上下文协议）

机械核心：`efficiency_core.py::make_snapshot/decide_context_load/context_delta`；回归：EFF-001/003。

1. 首次进入任务：允许加载完整必要上下文（mode=FULL，仅此一次）。
2. 每个安全 Checkpoint 建立 `CONTEXT_SNAPSHOT`（12 字段：task_id/goal_hash/contract_hash/stage_id/git_head/worktree_hash/runtime_identity/last_gate/last_evidence_anchor/last_event_id/current_blocker/next_legal_action）。
3. 后续 Stage 默认只读：Snapshot + 变化项（Changed Files/Contract/New Events/Evidence/Blocker/Runtime/Next Action）。无变化内容禁止全文重读。
4. Hash-based Invalidation：goal/contract/worktree/runtime 四类 hash 不变 → 复用上下文状态（reason_code=ALL_RELEVANT_HASHES_UNCHANGED）；任一变化 → 只重载对应上下文（changed_contract/changed_files/changed_runtime…）。
5. 完整合同/Experience/历史仍为 canonical source——本协议是运行时读取优化，不是删除（§33 同则）。
