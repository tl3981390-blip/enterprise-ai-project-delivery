# v1.10.0 Release Closure

Date: 2026-09-01 (Asia/Shanghai)

## Formal identity

- Release: `https://github.com/tl3981390-blip/enterprise-ai-project-delivery/releases/tag/v1.10.0`
- Annotated tag object: `40f12cb8b29457bfe751ce06d4dc7ff2d47e6de3`
- Release commit: `f13ae703493c3082a6246af4bf2c1b5e063622ef`
- Asset: `enterprise-ai-project-delivery-v1.10.0.zip`
- GitHub asset SHA-256: `38b7a4bb7938220e7106cbf59b4b5e039a0f2b925a87b1b20c877f1dbecf2777`

## Verified evidence

- Development candidate validator: `0 errors, 0 warnings`.
- Development full regression: `294 passed`.
- Clean candidate self-contained install: PASS; clean installed-copy full regression: `294 passed`.
- Formal asset re-downloaded from GitHub; local SHA exactly equals GitHub Release digest.
- Formal ZIP verification: `matches_formal_release=true`.
- Formal asset installed into a new isolated directory: `INSTALLED_SELF_CONTAINED`, 355 files.
- Formal installed-copy validator: `0 errors, 0 warnings`.
- Formal installed-copy full regression: `294 passed`.
- Historical tag identities checked before and after release; no historical tag was moved.

## Product result

The Core now mechanically binds multi-turn understanding to facts and planning, and binds
capability selection to Harness invocation results, Work Units, failure state and Evidence.
Recovery is budgeted and requires original-blocker plus related-regression evidence. Installed
Release tests no longer rely on `.git` or the author's private bootstrap.

## Final status matrix

| Capability | Status | Evidence / boundary |
| --- | --- | --- |
| NATURAL_LANGUAGE_ENTRY | PASS | SKILL + manifest + understanding Runtime contract |
| SPARSE_GOAL_UNDERSTANDING | PASS | multi-round household-menu behaviour test |
| UNDER_QUESTIONING_GUARD | PASS | consequential decision impacts required for every question |
| OVER_QUESTIONING_GUARD | PASS | maximum four questions per round; additional rounds remain possible |
| UNDERSTANDING_TO_FACT_BINDING | PASS | answer event → provenance history → planning facts |
| FACT_TO_PLAN_BINDING | PASS | only `start_from_understanding` opens the multi-turn planning boundary |
| DYNAMIC_WORK_DISCOVERY | PASS | user journey becomes project work; capability does not create work |
| COMPLEXITY_ADAPTATION | PASS | structural facts drive depth; metadata is not acceptance work |
| HUMAN_PLAN_AUTHORITY | PASS | existing add/remove/merge/split/modify/reorder/replace/lock suite |
| CAPABILITY_NEED_DISCOVERY | PASS | fact/planner-declared arbitrary needs |
| CAPABILITY_RESOLUTION | PASS | identity/compatibility/license/permission/validation/maturity filtering |
| CAPABILITY_AUTHORIZATION | PASS | unauthorized candidate cannot generate invocation |
| CAPABILITY_TO_EXECUTION_BINDING | PASS | invocation envelope + Work Unit + output + Evidence + failure transition |
| CONTINUOUS_EXECUTION | PARTIAL | Core continuation policy verified; live Harness loop not rerun here |
| CONDITION_CHANGE_DETECTION | PASS | changed-fact impact classification suite |
| TRUE_PARTIAL_REPLAN | PASS | new planner fragment required; no flag-only replan |
| CAPABILITY_RE_RESOLUTION | PASS | change path recomputes capability resolution |
| FAILURE_EVIDENCE | PASS | failure/result evidence mandatory |
| BOUNDED_RECOVERY | PASS | three-attempt policy and human recovery package |
| ORIGINAL_BLOCKER_REVALIDATION | PASS | blocker PASS plus related regression Evidence required |
| RESUME | PARTIAL | deterministic Core suite PASS; current Codex new-session path not rerun |
| HANDOFF | PARTIAL | deterministic contract PASS; cross-Harness live handoff pending |
| EVIDENCE_INTEGRITY | PASS | canonical evidence path and invocation-bound evidence tests |
| TELEMETRY | PASS | understanding/invocation/failure/recovery events now share session |
| ANTI_FAKE_PASS | PASS | missing/failed/pending/open failure and metadata-negative tests |
| FINAL_ACCEPTANCE | PASS | fact-derived obligations; complexity metadata excluded from obligations |
| SCOPE_CONTROL | PASS | human constraints/plan authority preserved |
| HIGH_RISK_AUTHORITY | PASS | invocation readiness requires proven permission |
| GENERALIZATION | PASS | no project keyword templates in Core; household and enterprise cases |
| NO_TEMPLATE_CALCIFICATION | PASS | questions derive from decision gaps; work derives from facts/planner |
| INSTALLATION | PASS | formal asset clean install + full installed-copy regression |
| ENTERPRISE_VERSION_GOVERNANCE | PASS | exact tag + GitHub SHA + no auto-upgrade |
| RELEASE_IDENTITY | PASS | version surfaces mechanically aligned and formal identity verified |
| DOCUMENT_RUNTIME_ALIGNMENT | PASS | public entrypoints describe the new contracts and honest boundaries |
| REAL_INSTALLED_SKILL_BEHAVIOR | PENDING_EXTERNAL_VALIDATION | current Codex session did not hot-reload; new-session conversation required |
| ENTERPRISE_CONTROLLED_PILOT_READY | PENDING_EXTERNAL_VALIDATION | Core ready; one real department/Harness pilot still required |
| ENTERPRISE_WIDE_PRODUCTION_PLATFORM_READY | NOT_INCLUDED_BY_DESIGN | no bundled SSO/RBAC/company registry/execution bus/SLA |

## Stop-development decision

No further speculative Core expansion is justified by this audit. The next gate is a controlled
real Harness/department pilot. Any future Core change must be driven by reproducible pilot
failure, not by adding imagined enterprise systems.
