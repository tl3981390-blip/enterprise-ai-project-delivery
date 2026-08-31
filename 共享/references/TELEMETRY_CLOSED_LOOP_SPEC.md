# TELEMETRY_CLOSED_LOOP_SPEC（遥测闭环规格）

机械核心：`product_completion_core.py`（TELEMETRY_CONTROL_POLICY / loop_decision / loop_result / LOOP_VERIFICATION）；测试：TCL-001..010。

1. 升级：OBSERVE → DECIDE → ACT → **VERIFY** → 结果事件。禁止"行动后假设成功"（loop_result 无机械复验即 LOOP_VERIFY_FAIL）。
2. **Runtime Closed Loop 与 Skill Evolution 严格分离**：闭环允许自动控制当前项目；Core 修改仍走 Candidate/Test/Release Gate（FORBIDDEN_LOOP_ACTIONS 含 MODIFY_SKILL_CORE）。
3. 事件→策略映射（TELEMETRY_CONTROL_POLICY.json 为机读版）：DRIFT→冻结/分类/范围恢复/合同重验；ILLEGAL_PASSIVE_STOP→合法停检查/自动继续；RESOURCE_WARNING→检查点/交接准备；FAKE_PASS→缺项验收重入；CACHE_INVALID→相关 Gate 重验；REPEATED_CONTEXT_LOAD→增量上下文强制；FAILURE→冻结/分类/有界恢复/原阻塞重验/回归后继续；GOVERNANCE_COST_ANOMALY→增量+重验。
4. Loop 安全：每策略 max_attempts（默认 3）、allowed/forbidden 动作、verification_method、failure_exit=HUMAN_ESCALATION（带完整包）、budget 耗尽即升级。
5. **Human Gate 不可绕过**：HUMAN_AUTHORIZATION/BUSINESS_DECISION/USER_ONLY/EXTERNAL_HUMAN/IRREVERSIBLE_PRODUCTION 事件 → HALT_AT_HUMAN_GATE（can_act=False）。
