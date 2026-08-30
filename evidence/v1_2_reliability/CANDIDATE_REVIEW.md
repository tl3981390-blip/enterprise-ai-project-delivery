# v1.2 Reliability Hardening Candidate Review

## Round 1

| Finding | Classification | Disposition | Reason |
| --- | --- | --- | --- |
| CONTINUATION_PLANNING_FAILURE | CORE_SKILL_DEFECT | ADOPT | Reproduced twice with only “继续”; deterministic continuation gate and regressions added. |
| TELEMETRY_INTEGRITY_FAIL | CORE_SKILL_DEFECT | ADOPT | Core recorder binding and pre-acceptance integrity gate added. |
| POSTGRESQL_ENVIRONMENT_BLOCK | ENVIRONMENT_BLOCKER / PROJECT_DEFECT | REJECT_FROM_CORE | A Skill cannot supply a Docker daemon or project-specific adapter; retain fail-fast acceptance rule. |
| BENCHMARK_CONTAMINATION | BENCHMARK_DEFECT | REJECT_FROM_CORE | Evaluation hygiene issue; preserve as benchmark protocol evidence, not runtime Skill behavior. |
| PLATFORM_COMPATIBILITY_GAPS | ADAPTER_BACKLOG | NEEDS_MORE_DATA | ZCode explicit load proved; WorkBuddy/TRAE/Claude runtime results need platform-specific evidence. |

## Rescue candidates

| Candidate | Evidence | v1.2 disposition |
| --- | --- | --- |
| RE-001 UI truth must fail inert | RF-001/RF-002/RF-003, mixed confidence | NEEDS_MORE_DATA: remains product-surface specific; role workflow E2E is reinforced but no universal UI outage rule added. |
| RE-002 lock every acceptance input | RF-004 | ADOPT: candidate identity and contract/evidence identity are mandatory in resume verification. |
| RE-003 recovery fixtures model lost records | RF-005, mixed current artifacts | NEEDS_MORE_DATA: recovery ladder added; stack-specific topology matrix needs another independent project. |
| RE-004 unknown identity fail-closed | RF-006 | ADOPT: human authorization and permission resume cannot be inferred from conversational claims. |
| RE-005 audit detector adversarial variants | RF-007 | NEEDS_MORE_DATA: valuable but detector-specific corpus would over-expand this delivery Skill. |
| RE-006 reports project machine evidence | RF-008 | ADOPT: core telemetry metrics and integrity gate remain the report authority. |
| RE-007 evidence preflight | RF-009, partial event provenance | ADOPT: final acceptance must run canonical telemetry binding before claiming PASS. |
