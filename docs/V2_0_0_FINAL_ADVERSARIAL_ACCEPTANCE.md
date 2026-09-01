# v2.0.0 Final Adversarial Acceptance

Date: 2026-09-01 (Asia/Shanghai)

## Product decision

v1.10.0 is rejected as a final product candidate. The audit proved that it installed 21
discoverable Skills and accepted caller-manufactured facts, Work Units, Evidence and recovery
claims. v2.0.0 is a required major release because both the discovery contract and public Runtime
API are intentionally incompatible with those unsafe v1.x surfaces.

The repaired product is one public Skill with twenty internal modules. Modules remain separately
maintainable on disk, but Codex must not show or invoke them as independent `/` entries.

## Root causes and systemic repairs

| Root cause | Systemic repair |
| --- | --- |
| Every internal module was named `SKILL.md` | Only root remains `SKILL.md`; 20 internal references are `MODULE.md`; validator and installed-copy tests enforce exactly 1 + 20 |
| Understanding authority existed only in prose | Public `start_delivery` requires a sufficient Understanding Session; private facts entry is test-only |
| One answer could mutate unrelated facts | `apply_answer` permits exactly the fact bound to the outstanding question ID |
| Work, candidate and Evidence identity were caller strings | One append-only ledger binds evidence ID, producer, hash, candidate, revision, Work Unit and acceptance item |
| Recovery and completion trusted narratives | All downstream APIs accept only current ledger IDs; original blocker and related regression must pass |
| Manifest lifecycle names had no executable binding | `operation_handlers` maps every operation to a callable handler and is mechanically validated |
| Resume/handoff claims were parallel documents | Suspend/resume now share the authoritative Delivery Session and verify runtime/checkpoint identity |
| Tests followed internal happy paths | Added public-boundary negatives, single-discovery tests, candidate install tests and replayed the successful v1.10 attacks |

## Evidence executed on the exact candidate

- Development full regression: `301 passed`.
- Development validator: `0 errors, 0 warnings`.
- Candidate standard installation: `INSTALLED_SELF_CONTAINED`, 364 files; prior v1.10.0
  installation retained as `enterprise-ai-project-delivery.backup-1788231070`.
- Installed-copy full regression: `301 passed`.
- Installed-copy validator: `0 errors, 0 warnings`.
- Installed discovery count: exactly `1 SKILL.md` and `20 MODULE.md`.
- A-01 through A-10 replay: every former exploit was mechanically rejected in both development
  and standard-installed copies. Machine results are stored under
  `D:/企业Skill实验室/05_测试与验收证据/v2.0.0_adversarial_acceptance/`.
- Clean Codex task `v2 稀疏目标黑盒验收`: no construction, no invented features, four
  consequential questions, explicit unknown boundary.
- Clean Codex task `v2 简单修改黑盒验收`: zero product questions, one text replacement only,
  real browser open/click, HTTP 200, zero console errors/warnings; the first unsupported browser
  wait and full-page screenshot paths were preserved and recovered with supported equivalents.
- Clean Codex task `v2 现有项目接手黑盒验收`: read-only reconstruction, no user re-interview for
  discoverable facts, correct VERIFIED/UNVERIFIED/FAILED/UNKNOWN separation and one legal next action.

## Final status matrix

| Capability | Status | Evidence / boundary |
| --- | --- | --- |
| SINGLE_SKILL_DISCOVERY | PASS | development and installed-copy count = 1 public Skill + 20 internal modules |
| NATURAL_LANGUAGE_ENTRY | PASS | manifest handler and clean Codex tasks |
| SPARSE_GOAL_UNDERSTANDING | PASS | clean household-menu task did not plan or invent scope |
| OVER_QUESTIONING_GUARD | PASS | bounded button change used zero product questions |
| UNDER_QUESTIONING_GUARD | PASS | sparse task asked four decision-changing questions |
| UNDERSTANDING_TO_FACT_BINDING | PASS | cross-question mutation attack rejected |
| FACT_TO_PLAN_BINDING | PASS | raw `facts=` public-entry attack rejected |
| HUMAN_PLAN_AUTHORITY | PASS | existing plan-governance regression suite |
| CAPABILITY_AUTHORIZATION | PASS | unauthorized capability regression |
| CAPABILITY_TO_EXECUTION_BINDING | PASS | invented Work Unit and narrative result attacks rejected |
| CONDITION_CHANGE_DETECTION | PASS | changed dependency invalidates old evidence |
| TRUE_PARTIAL_REPLAN | PASS | affected planner fragment required; flag-only replan rejected |
| FAILURE_EVIDENCE | PASS | failure requires current FAIL evidence on the real Work Unit |
| BOUNDED_RECOVERY | PASS | budget and human package regression |
| ORIGINAL_BLOCKER_REVALIDATION | PASS | blocker PASS plus related regression IDs required |
| DUPLICATE_CALLBACK_GUARD | PASS | terminal recovery callback replay rejected |
| RESUME | PASS | mismatched checkpoint identity rejected; matching identity revalidated |
| HANDOFF | PENDING_EXTERNAL_VALIDATION | no second live Harness/host available for a real cross-runtime move |
| EVIDENCE_INTEGRITY | PASS | wrong candidate, arbitrary string, duplicate, stale and invalidated evidence rejected |
| ANTI_FAKE_PASS | PASS | wrong-candidate and changed-requirement completion attacks blocked |
| REAL_BROWSER_ACCEPTANCE | PASS | clean bounded-change task opened and clicked the page and checked console/network |
| EXISTING_PROJECT_RESUME | PASS | clean read-only reconstruction task preserved current project authority |
| INSTALLATION | PASS | standard candidate install, self-check and installed regression |
| RELEASE_IDENTITY | PENDING_EXTERNAL_VALIDATION | becomes PASS only after tag, GitHub Release asset, digest and reinstallation are verified |
| ENTERPRISE_CONTROLLED_PILOT_READY | PENDING_EXTERNAL_VALIDATION | requires a real authorized department/Harness pilot |
| ENTERPRISE_WIDE_PRODUCTION_PLATFORM_READY | NOT_INCLUDED_BY_DESIGN | SSO/RBAC/company registry/execution bus/SLA are not bundled |

## Freeze decision

The reliability Core is functionally accepted for release. No additional speculative Core feature
is justified. Publication remains gated by exact tag/asset/digest/reinstallation verification; live
cross-Harness handoff and enterprise pilot remain explicitly external and cannot be relabeled PASS.
