# BATCH_EVOLUTION_SPEC（批量进化协议）

机械核心：`efficiency_core.py::experience_fingerprint/capture_experience/should_deep_analyze/batch_evolution` + `skill_evolution_core.py`（v1.4 起支持 SIMPLIFY/MERGE/REMOVE/DEFER）；回归：EFF-008/009。

1. 便宜捕获：每个 Event 只做 fingerprint 入箱（failure_pattern/classification/root_cause_class/affected_capability 四键指纹），不即时深度分析。
2. 深度分析仅由触发器启动：STAGE_END / PROJECT_END / REPEATED_PATTERN（repeat_count≥2）/ HIGH_SEVERITY_FAILURE / EXPLICIT_REVIEW。
3. 相同 Pattern 去重：已有指纹只 bump repeat_count + evidence_refs + project_refs，不重建完整学习档案。
4. 批量：一次处理多个 Experience，共享 pattern_context 与 heldout_protocol 设置；每个 Patch 的 Evidence 链保持独立可追踪。
5. 减法进化：SIMPLIFY/MERGE/REMOVE/DEFER 与加法同受九字段声明 + 四硬证（Negative/Held-out/Rescue/Round1 回归）约束；高 Token 成本 + 低风险拦截的治理项进 OVER_GOVERNANCE_CANDIDATE，优先找减法。
