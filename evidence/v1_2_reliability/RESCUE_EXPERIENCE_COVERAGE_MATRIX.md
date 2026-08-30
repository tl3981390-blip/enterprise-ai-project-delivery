# RESCUE_EXPERIENCE_COVERAGE_MATRIX — Rescue 历史经验回灌矩阵

任务：TASK-20260830-V1.2-RELIABILITY
来源：RESCUE_HISTORICAL_FAILURE_INVENTORY_V1（RF-001..009）+ RESCUE_EXPERIENCE_PACK_V1（RE-001..007），只读证据，未重测真实 Rescue 项目。
回灌规则（总指令 §35）：Historical Failure → Evidence → Generalized Pattern → v1.1 Coverage → Round 1 复证 → Gate/Recovery/Negative Test/Regression。

| 经验 | 来源（置信度） | 泛化模式 | v1.1 覆盖 | v1.2 处置与机械落点 | 验证 |
| --- | --- | --- | --- | --- | --- |
| RE-001 UI 真实性必须失效惰性 | RF-001/002/003（混合置信） | 界面不可用 ≠ 通过；无 universal UI outage 规则可泛化 | 模块 13 浏览器验收 | NEEDS_MORE_DATA：保留角色工作流 E2E 强化，不加普适断电规则 | 模块 13（既有） |
| RE-002 锁定每次验收输入的身份 | RF-004 | 恢复/交接/回滚后必须重验 candidate 身份 | 无 | ADOPT：resume 五项核验 + `verify_handoff`（git_head/worktree/contract/evidence/runtime） | HANDOFF-001/002、test_rescue_* 系列 |
| RE-003 恢复夹具模拟丢失记录 | RF-005（混合） | 恢复阶梯需覆盖部分状态丢失 | 部分 | NEEDS_MORE_DATA：recovery ladder 已入 `RECOVERY_ESCALATION_SPEC`；栈专属拓扑矩阵待另一独立项目 | REC-001..003 |
| RE-004 未知身份 fail-closed | RF-006 | 人类授权/权限不能从对话声明推断 | 部分 | ADOPT：AUTH-001/002；`RESUME_VERIFICATION_FAIL` 保持暂停 | test_7/8、AUTH-001/002 |
| RE-005 审计检测器对抗变体 | RF-007 | 检测器语料需对抗样本 | 无 | NEEDS_MORE_DATA：detector 专属语库会超出本交付 Skill 范围（Change Admission Rule 拒绝） | — |
| RE-006 报告项目机器证据 | RF-008 | 报告权威=核心遥测，非项目自述 | 部分 | ADOPT：核心遥测单源 + `CORE_TELEMETRY_INTEGRITY_SPEC` 验收强制 | check_telemetry_binding、TELEMETRY-001..003 |
| RE-007 Evidence 预检 | RF-009（部分事件来源） | 最终验收前必须跑核心遥测绑定 | 无 | ADOPT：验收前置检查进入发布门禁（final gate checks 含 telemetry_binding） | 发布门禁 final_gate.json |

**7/7 Rescue 经验全部处置**：ADOPT 4 项已机械化，NEEDS_MORE_DATA 3 项均给出不采纳/缓释理由（非静默丢弃）。
