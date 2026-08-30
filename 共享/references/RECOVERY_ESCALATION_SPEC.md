# RECOVERY_ESCALATION_SPEC（有界恢复与安全升级规格）

机械核心：`共享/scripts/continuation_core.py::decide`；流程见 [`持续施工与恢复协议.md`](持续施工与恢复协议.md)。

## 1. 普通失败生命周期

```text
FAIL → 冻结失败 Evidence → 分类 → 权限检查 → Recovery Plan → Recovery Attempt → Revalidation
```

分类至少区分：CODE / CONFIG / ENVIRONMENT / DEPENDENCY / DATA / PERMISSION / CONTRACT / GOVERNANCE / EXTERNAL_SERVICE / RUNTIME / EVIDENCE / RESOURCE / UNKNOWN。

## 2. Recovery Budget

每次自动恢复有明确预算（attempts / elapsed time / token / risk）。禁止无限修复循环；修复成功后禁止"问题已解决，请告诉我是否继续"——重验通过即自动继续。

## 3. 恢复成功条件

原 Blocking Condition 重新验证 PASS + Regression PASS，才允许 `AUTO_RECOVERY_SUCCESS`（遥测必须引用 failure_event_id、recovery_attempt_event_id 与 new_test_evidence）。

## 4. 升级阶梯（预算耗尽后禁止直接 SUSPENDED）

```text
RECOVERY_BUDGET_EXHAUSTED
  ↓ ① SAFE_ROLLBACK_ATTEMPT：安全、可逆、合同允许三者齐备才允许
  ↓ ② ALTERNATIVE_RECOVERY：不扩 Scope、不绕权限、不降 Acceptance、不绕 Human Gate
  ↓ ③ HUMAN_RECOVERY_PACKAGE + SUSPENDED_AWAITING_HUMAN
```

机械判定（`decide`）：

- `safe_rollback: {available, reversible, contract_allowed}` 全真 → `SAFE_ROLLBACK_ATTEMPT`，requires `candidate_identity + original_gate_revalidation + regression`；成功 → `SAFE_ROLLBACK_SUCCESS` 后寻找新合法路径。
- `alternative_recovery: {available, scope_unchanged, acceptance_unchanged, bypasses_permission=false, bypasses_human_gate=false}` → `ALTERNATIVE_RECOVERY`，验证通过后自动继续。
- 两者皆无 → `RECOVERY_EXHAUSTED`（遥测需 `human_recovery_package_ref`）。

## 5. 人类恢复包

字段合同：`共享/schema/human_recovery_package.schema.json` + `validate_human_package`。禁止"请处理后继续"。

## 6. 回归

CONT-003、REC-001/002/003、RESUME-001/002（`tests/reliability/`）。
