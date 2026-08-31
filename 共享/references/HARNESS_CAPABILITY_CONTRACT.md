# HARNESS_CAPABILITY_CONTRACT（Harness 能力合同）

机械核心：`product_completion_core.py`（15 能力 × 状态词表 × L1-L10 连续阶梯）；测试：`test_product_completion.py::HarnessConformanceTests`。

## 15 项能力（每 Harness 只声明真实状态）

`skill_discovery / skill_explicit_invocation / automatic_activation / read_project_state / write_project_state / tool_execution / permission_boundary / subagent_support / resume_support / handoff_support / usage_visibility / telemetry_write / filesystem_scope / browser_support / human_gate_support`

状态词表（禁假兼容）：`VERIFIED`（真实测试证据）｜`NOT_AVAILABLE`（平台无此能力）｜`NOT_APPLICABLE_BRIDGED`（经兼容桥保持核心语义）｜`NOT_TESTED_HERE`（本机不可测）。

## 等级（连续阶梯，见 SKILL.md ≠ 支持该 Harness）

L1 DISCOVER → L2 INVOKE → L3 CONTRACT_AND_GATE → L4 TOOL_EXECUTION → L5 TELEMETRY → L6 RESUME → L7 HANDOFF → L8 MID_PROJECT_ATTACH → L9 CLOSED_LOOP_CONTROL → L10 FULL_CONFORMANCE。
每级能力要求见 `LEVEL_REQUIREMENTS`；阶梯从底向上连续，遇未验证能力封顶。

## One Core / Multiple Thin Adapters（§4/§8）

平台专属 path/manifest/调用语法/生命周期钩子/权限翻译/工具绑定 → **只进 Adapter**；复杂项目可靠性规则 → **只属 Core**。禁止任何平台 Fork Core。不可用能力显式降级（§9：无 subagent 不模拟、无 token 记 NOT_AVAILABLE、不能自动 Resume 声明对应 level），但须测试兼容桥能否保持核心语义。

## 统一 HARNESS_CONFORMANCE_SUITE（12 项）

①发现 ②显式调用 ③任务合同 ④写权限限制 ⑤Gate 执行 ⑥遥测记录 ⑦Suspend ⑧同 Task Resume ⑨Model/Agent Handoff ⑩项目中途 Attach ⑪遥测触发闭环 Action ⑫最终价值报告。执行证据见 `HARNESS_CONFORMANCE_MATRIX.md`。
