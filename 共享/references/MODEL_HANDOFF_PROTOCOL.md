# MODEL_HANDOFF_PROTOCOL（模型交接协议规格）

目标：落实 NO_FAKE_CONTINUITY——当前模型资源不足（或用户要求）时主动生成完整 `MODEL_HANDOFF_PACKAGE`；新模型不得盲信交接状态，必须先机械核验真实项目状态，才能恢复同一 task_id 继续。

## 1. 交接包（MODEL_HANDOFF_PACKAGE）

字段合同见 [`共享/schema/model_handoff_package.schema.json`](../schema/model_handoff_package.schema.json)；机械校验：`continuation_core.validate_model_handoff_package`（CLI：`check_continuation.py --mode decide`，输入 `{"model_handoff_request": true, "model_handoff_package": {...}}`）。缺字段 → `CONSTRAINT_CONFLICT`，不得以不完整包进入 `MODEL_HANDOFF_READY`。

## 2. HANDOFF_READY 条件

State 保存、Evidence 保存、Telemetry Anchor 保存、Git 状态记录、Partial Work 标记、Next Legal Action 明确——全部满足才允许 `MODEL_HANDOFF_READY`（遥测事件同名）。

## 3. 新模型接管（§33 八步）

```text
Load Handoff → verify_handoff(package, current_real_state) → RESUME_CURRENT_TASK
```

机械核验：`check_continuation.py --mode verify-handoff --input <package.json> --current <current.json>`。
`current.json` 至少含 `git_head / worktree_identity / contract_hash / evidence_anchor / runtime_identity / task_id`，由新模型从真实仓库与 Evidence 现场取得（不得从交接包抄）。

- 全部一致 → `HANDOFF_VERIFICATION_PASS` → 沿用原 task_id，先重跑原失败 Gate 与 Regression 再继续（NO_BLIND_RESUME）。
- 任一不一致 → `HANDOFF_VERIFICATION_FAIL`（遥测事件同名）→ 禁止继承，进入安全恢复；HEAD/Worktree/Evidence/Contract 任一不同均属失败。

## 4. 禁止

- 新模型"重新看看项目"、重建 task_id、重问目标、重跑已完成 Stage。
- 因存在交接包就直接相信旧状态（凭包续作 ≠ 状态属实）。
- 把 UNVERIFIED_PARTIAL_WORK 当 PASS 汇报。
- `MODEL_HANDOFF_REQUIRED` 不是人类门禁：等待对象是继任模型，不是用户；恢复走 verify-handoff 而非人类恢复包。

## 5. 事件

`PROACTIVE_HANDOFF_STARTED`、`MODEL_HANDOFF_READY`、`MODEL_HANDOFF_COMPLETED`（继任模型 HANDOFF_VERIFICATION_PASS 后记录）、`HANDOFF_VERIFICATION_FAIL`、`UNVERIFIED_PARTIAL_WORK`。
