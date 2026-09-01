# v1.10.0 Final Adversarial Acceptance

Date: 2026-09-01. Baseline: formal GitHub Release v1.10.0.

## Formal installation

Codex standard installation was explicitly upgraded from v1.9.1 to v1.10.0 using the formal
GitHub Release asset. SHA-256 matched
`38b7a4bb7938220e7106cbf59b4b5e039a0f2b925a87b1b20c877f1dbecf2777`; the install copied
355 files and validator returned zero errors and warnings. The previous v1.9.1 installation was
preserved outside the Codex Skill discovery root.

## Successful attacks

### A-01 Multiple Skill discovery pollution

The formal installation contains 21 recursively discoverable `SKILL.md` files: one public
entrypoint plus twenty internal numbered modules. Codex exposes them separately in `/` discovery.
This contradicts the one-Skill/one-entrypoint product contract.

### A-02 Real new-session sparse-goal failure

Fresh projectless Codex task input: `我想做一个家庭点菜单。`

Observed first response offered four predetermined product forms and asked for users, price,
images, allergy markers and history without linking each question to a consequential decision.
After the user explained the family decision problem, it silently invented mobile Web, household
joining, images, random choice, dish balancing, allergies, history and concurrency. After the user
said desktop use was enough, it began construction without confirming the bounded feature set.

This proves over-questioning, AI-inferred scope promotion and understanding-to-work drift. The
task later hit the account usage limit during final browser verification; no completion claim is
accepted from that interrupted task.

### A-03 Understanding gate bypass

Calling formal installed `start_delivery(facts={"goal": ...})` returned `PLANNED` with 33 facts
still UNKNOWN. The documented multi-turn gate is not the exclusive Runtime entry.

### A-04 Cross-question fact smuggling

One outstanding question ID accepted updates for all other unanswered facts and produced
`gate_pass=true`. Question-to-fact binding is not enforced.

### A-05 Invented Work Unit execution

An authorized resolved capability accepted `work_id="invented-work-unit"` although that Work Unit
did not exist in the active plan.

### A-06 Narrative Evidence accepted

`record_capability_result` accepted the string `我已经验证通过` as Evidence and marked the invented
Work Unit PASS. Recovery similarly accepted narrative strings for failure evidence, blocker PASS
and regression proof, then marked the failure `RECOVERED_REVALIDATED`.

### A-07 Wrong-candidate and stale completion

Evidence explicitly carrying `candidate="wrong-candidate"` completed the session. After an
acceptance requirement changed, static-inspection evidence marked with an old candidate also
completed the session. Completion does not validate canonical evidence identity, candidate,
freshness or invalidation status.

### A-08 Duplicate terminal recovery callback

A recovered failure accepted a second callback and changed back to `RECOVERY_UNVERIFIED` instead
of rejecting the duplicate terminal transition.

### A-09 Manifest/Runtime operation mismatch

The Harness manifest advertises `advance`, `suspend`, `resume` and `verify`; none is exported by
the named Runtime. Related helpers exist in a separate module but are not bound to Delivery
Session state.

### A-10 Test-suite number overstates evidence class

The 294-pass suite is predominantly direct internal-function UNIT/STRUCTURAL/SYNTHETIC coverage.
It is runnable from an installed copy, but installed location does not transform synthetic tests
into REAL_HARNESS or BLACK_BOX evidence. The real new-session test found defects the suite missed.

## Attacks that held

- Unauthorized capability candidates did not generate executable invocation envelopes.
- Capability candidates requiring validation were not marked READY.
- Repeated capability-result callbacks were rejected after a terminal result.
- Recovery Budget stopped after three failed attempts and produced a detailed human package.
- The simple bounded button task asked no irrelevant product questions and chose a one-line edit;
  final browser validation was interrupted by the external account usage limit, so only the
  questioning/scope behaviour is evidence.
- Historical Release tag identities remained unchanged during installation.

## Root cause analysis

1. **Discovery boundary absent**: internal module filenames satisfy the Harness's public Skill
   discovery convention.
2. **Authority boundary documentary, not mechanical**: the gated entry coexists with a public
   bypass that accepts caller-manufactured facts.
3. **Identity is represented by caller strings**: Work Units, Evidence, candidates and callbacks
   are not validated against canonical session entities.
4. **Evidence integrity is disconnected from orchestration**: append-only evidence utilities
   exist, while completion/recovery accept arbitrary non-empty lists.
5. **Lifecycle helpers are parallel islands**: resume/handoff/continuation are tested outside the
   authoritative Delivery Session.
6. **Tests follow implementation surfaces**: direct function assertions did not exercise Skill
   discovery, new-session prompting, actual Harness invocation or adversarial evidence identity.

## Pre-fix status

All statuses use the required vocabulary.

| Capability | Status |
| --- | --- |
| NATURAL_LANGUAGE_ENTRY | FAIL |
| SPARSE_GOAL_UNDERSTANDING | FAIL |
| UNDER_QUESTIONING_GUARD | FAIL |
| OVER_QUESTIONING_GUARD | FAIL |
| UNDERSTANDING_TO_FACT_BINDING | FAIL |
| FACT_TO_WORK_BINDING | FAIL |
| WORK_TO_PLAN_BINDING | FAIL |
| HUMAN_PLAN_AUTHORITY | PASS |
| CAPABILITY_NEED_DISCOVERY | PASS |
| CAPABILITY_RESOLUTION | PASS |
| CAPABILITY_AUTHORIZATION | PASS |
| CAPABILITY_TO_REAL_EXECUTION | FAIL |
| WORK_UNIT_RESULT_BINDING | FAIL |
| CONDITION_CHANGE | FAIL |
| TRUE_PARTIAL_REPLAN | PASS |
| CAPABILITY_RE_RESOLUTION | PASS |
| CONTINUOUS_EXECUTION | FAIL |
| FAILURE_CAPTURE | FAIL |
| RECOVERY_BUDGET | PASS |
| ORIGINAL_BLOCKER_REVALIDATION | FAIL |
| REGRESSION_REVALIDATION | FAIL |
| HUMAN_RECOVERY_PACKAGE | PASS |
| RESUME | FAIL |
| HANDOFF | PENDING_EXTERNAL_VALIDATION |
| EVIDENCE_INTEGRITY | FAIL |
| ANTI_FAKE_PASS | FAIL |
| FINAL_ACCEPTANCE | FAIL |
| SCOPE_CONTROL | FAIL |
| GENERALIZATION | FAIL |
| NO_TEMPLATE_CALCIFICATION | FAIL |
| FORMAL_INSTALLATION | PASS |
| NEW_SESSION_SKILL_BEHAVIOR | FAIL |
| RELEASE_IDENTITY | PASS |
| ENTERPRISE_CONTROLLED_PILOT_READY | FAIL |
| ENTERPRISE_WIDE_PRODUCTION_PLATFORM_READY | NOT_INCLUDED_BY_DESIGN |

`CORE_FROZEN = NO`. Systemic repair is required before repeating the complete attack set.
