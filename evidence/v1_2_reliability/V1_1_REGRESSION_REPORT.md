# V1_1_REGRESSION_REPORT — v1.1 能力回归报告

任务：TASK-20260830-V1.2-RELIABILITY ｜ 基线：v1.1.0 tag（`4525ca742a62a950eebade22c97440d6a2c6e181`）｜ 回归执行：2026-08-30（接管模型两轮重跑：Resume 审计轮 + 缺口修复后全量轮）

## 结果总览

| 套件 | 项数 | 结果 |
| --- | --- | --- |
| tests/telemetry/test_telemetry.py（v1.1 遥测回归） | 14 | **PASS**（两轮均 OK） |
| tests/reliability/test_reliability_hardening.py（v1.2 核心，v1.1 能力不退化） | 23 | **PASS**（两轮均 OK） |
| 共享/scripts/validate-skill.py --root . | 结构 | **0 errors, 0 warnings** |
| check_understanding_gate / check_plan_alignment（V2） | 门禁 | **PASS / PASS** |
| check_state_machine happy/illegal | 状态机 | **PASS / 正确 FAIL** |
| tests/telemetry/run_positive_simulation.py | 正向模拟 | **PASS**（unnecessary_human_wait_count=0，Token=NOT_AVAILABLE，23 事件，源日志 SHA-256 `db75c512…8160`） |
| git diff --check | 工作区 | **PASS** |

## v1.1 能力逐项不退化确认

Understanding Gate、Task Understanding Contract、State Machine、Plan Alignment、Drift、Failure Recovery、Evidence、RAG 四防、Agent/MCP/Permission、Four-role acceptance、Telemetry（Recorder/Metrics/锚点）、Fake PASS 阻断、Harness mock、Rollback、Release Evidence —— 由 14 项遥测回归 + 23 项可靠性套件 + 结构校验 + 状态机/门禁脚本覆盖确认（同 v1.1 发布时的检查集，全部保持 PASS）。

## v1.2 新增（不破坏 v1.1 行为）

- `tests/reliability/test_resource_handoff_benchmark.py`：17 项（RESOURCE-001..004、HANDOFF-001/002、REC-002/003、BENCH-001、新事件枚举）——**PASS**（首轮 2 项失败为夹具空列表真值误判，修复 `validate_model_handoff_package` 缺失语义后全绿；失败-修复链见任务遥测）。
- 指标扩展为追加式（continuity 新增 4 计数），v1.1 断言文件为子集比较，原 14 项回归不受影响。
- 事件枚举扩展 6 类（资源/交接），旧事件校验规则未改动。

## 合并回归

**54/54 PASS**（23 + 17 + 14），两轮验证。
