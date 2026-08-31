# MID_PROJECT_ATTACHMENT_SPEC（项目中途接入规格）

机械核心：`product_completion_core.py`（ATTACHMENT_DISCOVERY_FIELDS×14 / ADOPTION_BOUNDARY_FIELDS×8 / classify_pre_attachment / lazy_verify_plan / attach_allowed）；测试：ATT-001..010。

1. 模式：`MID_PROJECT_SKILL_ATTACHMENT`——已有项目直接调用本 Skill；禁止重建项目、禁止 Day-1 重跑（§10/16：existing_project + reconstructed_task + adoption_boundary + continued_execution）。
2. **第一阶段只读**（ATTACHMENT_DISCOVERY）：READ/SEARCH/ANALYZE/安全只读测试；无采纳边界前 `can_write=False`（attach_allowed 机械强制）。
3. 状态重建 14 字段：current_goal/git_head/worktree/requirements/contracts/runtime/database/tests/evidence/failures/agent_claims/stage/partial_work/blockers。
4. 采纳边界 8 字段（SKILL_ADOPTION_BOUNDARY_SCHEMA.json）：attachment_id/timestamp/task_id/git_head_at_attachment/runtime_identity/project_snapshot/skill_version/harness——自边界起 Skill 承担治理责任。
5. 历史四分类不洗白：`VERIFIED / UNVERIFIED / FAILED / UNKNOWN_PRE_ATTACHMENT`——旧 Agent 叙述 ≠ PASS（classify_pre_attachment）。
6. 惰性历史验证：只验后续工作真正依赖项（lazy_verify_plan），无关历史保持 UNVERIFIED。
7. 价值报告分期：PRE_ATTACHMENT=PARTIALLY_OBSERVABLE（不做完整因果归因）；POST_ATTACHMENT=FULLY_GOVERNED。
