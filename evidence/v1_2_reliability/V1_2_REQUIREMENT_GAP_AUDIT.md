# V1_2_REQUIREMENT_GAP_AUDIT — 候选实现 vs 原始施工总指令

审计时间：2026-08-30T20:45:00+08:00
审计者：接管模型（MODEL_HANDOFF_READY 之后的 successor）
审计对象：`v1.2.0-dev` 未提交候选（HEAD `4525ca742a62a950eebade22c97440d6a2c6e181`，分支 `v1.2.0-dev`）
对照基准：用户原始《enterprise-ai-project-delivery v1.2.0 Long-Running Project Reliability Hardening 正式施工总指令》（用户于接管会话中全文提供）
辅助基准：`V1_2_CHANGE_CONTRACT.json`（理解门禁 PASS）、`plan.json`（对账 PASS）、`implementation_gate.json`、`tests/reliability/test_reliability_hardening.py`（23/23）

## 结论

**RH-7 / RELEASE_VERIFICATION 按总指令 §62 执行的当前判定为 FAIL。** 候选实现覆盖了连续施工/恢复/盲恢复/核心遥测绑定，但总指令中四项 Release Gate 必需能力没有任何机械实现，两项 Round 1 Finding 从未被评审。发布 v1.2.0 的条件当前不成立。

## 缺口明细

### GATE-1 EXECUTION_RESOURCE_GUARD：无实现（§26–§30，§62）

- 全库检索 `RESOURCE_GUARD|资源守卫|额度|RESOURCE_BUDGET|PROACTIVE_HANDOFF|UNVERIFIED_PARTIAL_WORK`：仅命中 evidence 文档，无协议文本、无脚本、无事件、无测试。
- §57 场景 `RESOURCE-001..004` 无对应测试。

### GATE-2 MODEL_HANDOFF（机械协议）：无实现（§31–§34，§62）

- 无 `MODEL_HANDOFF_PACKAGE_SCHEMA`（§65-7）；`共享/schema/` 仅有 `human_recovery_package.schema.json`。
- `continuation_core.LEGAL_HUMAN_GATES` 不含 `MODEL_HANDOFF_REQUIRED`；无交接包校验器、无 `HANDOFF_VERIFICATION_PASS/FAIL` 机械判定。
- 上一模型在暂停时实践了良好交接（生成了 `MODEL_HANDOFF_PACKAGE.md`），但这是模型行为，不是 Skill 的强制协议——总指令 FINDING-007 明确要求"必须新增 MODEL_HANDOFF_PROTOCOL"。
- §57 场景 `HANDOFF-001/002` 无对应测试。

### GATE-3 HANDOFF_VERIFICATION：无实现（§33–§34，§62）

- 接管核验（HEAD/worktree/contract/evidence 对账）由本模型人工完成；无脚本化 verifier，新模型无法机械执行 §33 的 8 项 Verify。

### GATE-4 BENCHMARK_CONTAMINATION_DETECTION：无实现（§53–§54，§62）

- 无 `BENCHMARK_PROTOCOL_V2`（§65-10）、无 `CONTROLLER_CONTAMINATED` 检测器、无 `BENCH-001` 测试。
- 注：`CANDIDATE_REVIEW.md` 将 BENCHMARK_CONTAMINATION 评审为 REJECT_FROM_CORE（不进入运行时行为），该处置针对的是"把基准卫生变成运行时门禁"，不豁免"建立基准协议本身"（§53 明确要求建立 PRIVATE_BENCHMARK_SPEC 与 PUBLIC_BUSINESS_EVENT 分离）。

### REVIEW-1 FINDING-002 ILLEGAL_STAGE_WAIT：未被评审

- `implementation_gate.json` 的 `round_1_findings_reviewed` 仅含 5 项（001/003/004/005/006 对应项），不含 FINDING-002。
- 实质覆盖：`ILLEGAL_PASSIVE_STOP` 判定与测试已实现（test_passive_stop_is_rejected 等），即缺陷已修但 Finding 未进入评审记录，矩阵不完整。

### REVIEW-2 FINDING-007 MODEL_RESOURCE_EXHAUSTION：未被评审且未实现

- 未出现在 `round_1_findings_reviewed`、`CANDIDATE_REVIEW.md`、合同 work_scope、成功标准中。
- 该 Finding 要求的 EXECUTION_RESOURCE_GUARD 与 MODEL_HANDOFF_PROTOCOL 均未实现（见 GATE-1/2/3）。
- 本任务自身的暂停-交接过程即为该 Finding 的再次实证。

### REC-GAP 回归缺口（§57）

- 缺 `REC-002`（安全回滚尝试+重验证）、`REC-003`（合法替代恢复路径）。
- `continuation_core.decide()` 对 `blocker.unrecoverable` 直接返回 RECOVERY_EXHAUSTED，跳过 §17–§18 的安全回滚评估与替代路径评估。

### DELIV-GAP §65 具名交付物缺口

| # | 交付物 | 现状 |
| --- | --- | --- |
| 2 | ROUND1_FINDING_COVERAGE_MATRIX | 缺（CANDIDATE_REVIEW 仅覆盖 5/7 findings） |
| 3 | RESCUE_EXPERIENCE_COVERAGE_MATRIX | 缺（内容散于 CANDIDATE_REVIEW，未成矩阵） |
| 4 | LONG_RUNNING_PROJECT_CONTINUITY_SPEC | 部分（持续施工与恢复协议.md 未含资源/交接生命周期） |
| 5 | RECOVERY_ESCALATION_SPEC | 部分（recovery ladder 一节，无安全回滚/替代路径全链） |
| 6 | HUMAN_RECOVERY_PACKAGE_SCHEMA | 有 |
| 7 | MODEL_HANDOFF_PACKAGE_SCHEMA | 缺 |
| 8 | EXECUTION_RESOURCE_GUARD_SPEC | 缺 |
| 9 | CORE_TELEMETRY_INTEGRITY_SPEC | 部分（check_telemetry_binding.py 行为未成规格文档） |
| 10 | BENCHMARK_PROTOCOL_V2 | 缺 |
| 11 | Negative Tests | 部分（23 项中缺 RESOURCE/HANDOFF/BENCH/REC-002/003） |
| 12 | Regression Suite | 部分（同上） |
| 13 | v1.1 Regression Report | 缺（结果在 implementation_gate 内一行，未成报告） |
| 14 | v1.2 Final Evidence | 待 RH-7 |
| 15 | v1.2 Release Report | 待 RH-7 |

### EVENT-GAP §50 新事件候选

已实现：ILLEGAL_PASSIVE_STOP、RECOVERY_EXHAUSTED、HUMAN_RECOVERY_REQUIRED、RESUME_REQUEST、RESUME_VERIFICATION_PASS/FAIL。
未实现：RESOURCE_BUDGET_WARNING、PROACTIVE_HANDOFF_STARTED、MODEL_HANDOFF_READY、MODEL_HANDOFF_COMPLETED、HANDOFF_VERIFICATION_FAIL、UNVERIFIED_PARTIAL_WORK。

### METRICS-GAP §51 新指标候选

已实现：unnecessary_human_wait_count。
未实现：model_handoff_count、successful_handoff_count、failed_handoff_count、resume_verification_fail_count（handoff_elapsed_time / handoff_rework_count 评估后可不采纳：需要 Provider 时间/返工语义，无真实来源时按 NOT_AVAILABLE 原则不估算）。

## 失败分类（Recovery ladder）

- 分类：`CONTRACT_FAILURE`（v1.2 变更合同不完整捕获总指令的显式 MUST，属前模型 AI_ERROR）
- 影响范围：RH-7 发布验证不能 PASS；不得发布 v1.2.0
- 冻结：本文件为失败证据，修复后不得改写本文件

## 恢复计划（bounded）

1. 追加 `V1_2_CHANGE_CONTRACT_V2.json` 补全范围（FINDING-002/007、GATE-1..4、REC-GAP、DELIV-GAP），原合同保留不改。
2. 追加 `plan_v2.json` 扩展 RH-8..RH-11；重跑理解门禁与计划对账。
3. 实现 EXECUTION_RESOURCE_GUARD、MODEL_HANDOFF_PROTOCOL、HANDOFF_VERIFICATION、BENCHMARK_PROTOCOL_V2、安全回滚/替代恢复判定、新事件与新指标。
4. 补齐 §65 具名交付物与 §57 缺失负向/回归测试。
5. 重跑全部回归（v1.2 扩展套件 + v1.1 14 项 + 结构校验 + 门禁 + 模拟）。
6. 重新执行 §62 Release Gate 全项判定，产出 Final Evidence 与 Release Report。
7. 预算：单轮实现；若实现引入不可收敛冲突，冻结后升级为 Human Recovery Package。
