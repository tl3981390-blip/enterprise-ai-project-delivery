# v1.8.1 Candidate Acceptance

Scope is limited to `REAL_PARTIAL_REPLAN` and `CAPABILITY_STAGE_DECOUPLING`.

## Scenario evidence

`tests/reliability/test_replan_and_capability_decoupling.py` covers:

- Same database capability: personal ledger Task versus production migration Stage.
- Same deployment capability: static publish Task versus multi-environment rollout Stage.
- PostgreSQL to SQLite: regenerated goal/work/output/dependencies/acceptance/evidence,
  unchanged UI, preserved Human content with review marker, classified Evidence and new acceptance.
- Missing planner fragment: `REPLAN_INPUT_REQUIRED`, never a false replanned flag.

## Mechanical result

- Focused behavioral regression: `99 passed`, followed by the missing-planner negative case.
- Full regression: `280 passed, 1 skipped`; the skip is the pre-existing GitHub-auth-dependent
  migration live test and is `PENDING_EXTERNAL_VALIDATION`, not PASS.
- Repository validator: `0 errors, 0 warnings`.
- Skill Creator validator: `Skill is valid!`.
- Git whitespace check: PASS.

External Harness executions and the skipped authentication-dependent live migration test remain
`PENDING_EXTERNAL_VALIDATION` unless run successfully.
