# ROUND1_FINDING_COVERAGE_MATRIX — Round 1 全部 7 项 Finding 覆盖矩阵

任务：TASK-20260830-V1.2-RELIABILITY ｜ 基线：v1.1.0（`4525ca7`）
来源：ComplexProjectLab Round 1 真实执行证据（Final Report / Telemetry Freeze Manifest / 独立验收）+ 用户总指令 FINDING-001..007
V1 合同缺口：FINDING-002/007 未进入评审（见 `V1_2_REQUIREMENT_GAP_AUDIT.md`），本矩阵在 V2 合同下补全。

| Finding | 现象 | 分类 | 处置 | v1.2 覆盖（机械） | 验证 |
| --- | --- | --- | --- | --- | --- |
| FINDING-001 CONTINUATION_PLANNING_FAILURE | 用户仅输入"继续"，子代理连续两次停止并重新等待新需求 | CORE_SKILL_DEFECT | ADOPT | `continuation_core.decide`：RESUME_REQUEST→五项核验→RESUME_VERIFICATION_PASS/FAIL；CONT/RESUME 场景 | test_5/6、test_resume_state_loss_is_blocked、RESUME-001/002 |
| FINDING-002 ILLEGAL_STAGE_WAIT | 阶段 PASS 后模型倾向"请告诉我是否继续" | CORE_SKILL_DEFECT | ADOPT | Stage PASS=Checkpoint≠Human Gate；`ILLEGAL_PASSIVE_STOP` 判定 + `unnecessary_human_wait_count` 指标；LEGAL_STOP_GATE 九字段 | CONT-001..004、test_passive_stop_is_rejected、test_1/2 |
| FINDING-003 TELEMETRY_INTEGRITY_FAIL | 项目自测 PASS 但核心验证拒绝（事件类型/correlation/hash-chain/anchor 非法） | CORE_SKILL_DEFECT | ADOPT | 唯一核心 Recorder（schema 校验/去重/hash-chain/anchor）；`check_telemetry_binding.py` 绑定验证 + 验收前强制执行；规格 `CORE_TELEMETRY_INTEGRITY_SPEC.md` | TELEMETRY-001/002/003、v1.1 遥测 14 项回归 |
| FINDING-004 ENVIRONMENT/PROJECT BLOCKER | PostgreSQL 未真实验收（Docker 未运行/adapter 未实现），Skill 未偷偷 fallback 冒充 PASS | ENVIRONMENT_BLOCKER + PROJECT_IMPLEMENTATION_GAP | REJECT_FROM_CORE | 三分类区分（SKILL_DEFECT ≠ PROJECT_GAP ≠ ENVIRONMENT_BLOCKER）；fail-fast 禁止 fallback→fake PASS（FAKE_PASS_BLOCKED 保留） | test_false_first_pass_is_rejected、negative fake_pass |
| FINDING-005 BENCHMARK_CONTROLLER_CONTAMINATION | Controller 提示过细污染行为实验 | BENCHMARK_DESIGN_DEFECT | ADOPT（基准协议层） | `BENCHMARK_PROTOCOL_V2`：PRIVATE_BENCHMARK_SPEC 与 PUBLIC_BUSINESS_EVENT 分离；`check_benchmark_contamination.py` 检测 `CONTROLLER_CONTAMINATED`；污染结果仅限工程验证 | BENCH-001、test_bench_001、business_voice 清洁测试 |
| FINDING-006 PLATFORM_COMPATIBILITY_GAPS | ZCode 显式调用成功；WorkBuddy/TRAE/Claude PARTIAL/BLOCKED | ADAPTER_BACKLOG | NEEDS_MORE_DATA | 禁止平台兼容问题引发 Core Fork（explicit_non_goals）；L1-L7 能力分级留待平台专属证据 | 合同边界 + validate-skill 无 fork 检查 |
| FINDING-007 MODEL_RESOURCE_EXHAUSTION | 模型额度接近耗尽导致施工断裂风险（本任务暂停-交接为再次实证） | CORE_SKILL_DEFECT | ADOPT | `EXECUTION_RESOURCE_GUARD`（GREEN/YELLOW/RED/UNKNOWN，不可见=NOT_AVAILABLE 禁估算，原子单元收口，UNVERIFIED_PARTIAL_WORK）+ `MODEL_HANDOFF_PROTOCOL`（包 schema+机械校验+verify_handoff+HANDOFF_VERIFICATION_PASS/FAIL） | RESOURCE-001..004、HANDOFF-001/002、新事件回归 |

**7/7 Finding 全部评审并有处置。** FINDING-002 于 V1 合同缺席、FINDING-007 于 V1 未实现，均已按 V2 合同补齐——缺口发现与修复链路见任务遥测 e06→e08 与 `V1_2_REQUIREMENT_GAP_AUDIT.md`（冻结证据，未改写）。
