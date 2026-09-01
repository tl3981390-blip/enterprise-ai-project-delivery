# FINAL TARGET CLOSURE REPORT

Status: `HISTORICAL` — superseded by the v3.0.0 Stable closure process.

Date: 2026-09-01 (Asia/Shanghai)

Candidate: `v3.0.0-rc3` (product Core unchanged from rc1; release-validation tooling corrected)

Formal baseline audited: `v2.0.0` at `d85872172db77d93e8253515f74d6e0c4e8b929a`.
Development started from the clean `v2.0.1` worktree at
`bfa62f1f29dad189f7b586d4627e1b60cda2634a`; v2.0.1's installer-backup fix is not
misreported as native v2.0.0 behavior.

## Product understanding

The Skill's final job is to make project delivery trustworthy: the user describes the desired
result, sees the model's understanding in a plan, retains control, and no longer has to supervise
every stage or validate narrative completion. The difference from an ordinary Skill is lifecycle
control across understanding, requirement continuity, planning, capability scope, continuation,
change, recovery and final evidence. The Host Model still understands and performs work; the Harness
still supplies workspace, accounts, permissions, tools and isolation.

## Phase 1 — PASS

### Preserved from v2

- Provenance-bearing multi-turn understanding and an explicit gate before public planning.
- Dynamic work discovery from project facts instead of project-type templates.
- Human semantic plan edits and partial replanning that preserves unaffected work/evidence.
- Capability candidate filtering for identity, compatibility, validation and permission.
- Candidate-bound Evidence, bounded recovery, verified resume and anti-fake completion.
- Autonomous-continuation and existing-project reconstruction controls.

### Root-cause corrections

| Gap | Root cause | Systemic correction | Evidence |
| --- | --- | --- | --- |
| Punctuation could be mistaken for intent semantics | No explicit Host-Model interpretation contract | Added context/rationale-bound intent records with one-question ambiguity handling | `test_intent_contract_is_semantic_and_punctuation_neutral`; ambiguity negative test |
| Reliability and user authority were expressed as one priority order | Business authority and truth integrity were conflated | Split Authority Plane from Integrity Plane | authority-plane regression tests |
| Planning did not have an executable review boundary | Runtime started in a generically planned state | `PLAN_REVIEW_REQUIRED`, explicit approval and scoped display waiver; execution fails closed before approval | plan-review attack tests |
| Confirmed requirements/errors could survive only as model prose | No compact durable baseline or correction lifecycle | Added confirmed-requirement baseline and correction ledger; recurrence enters Recovery; resolution requires PASS Evidence | correction recurrence and fake-completion tests |
| Capability status was terminal but context remained | Invocation record had no full lifecycle/deactivation cleanup | Bound session/revision/work/version/input/permission; terminal state removes input and temporary scopes, retaining hash/result/evidence | capability lifecycle/leakage tests |
| Evolution could over-promote preference or skip human release | Old classifications and short state machine were too broad | Evidence/reproduction/isolation/adversarial/final-goal/human-approval lifecycle; AUTO_RELEASE rejection | evolution candidate tests |
| Installed copy carried development caches | Installer exclusion set omitted `.pytest_cache` | General development-state exclusion plus actual copy regression | installer exclusion test and clean installed-copy inspection |

The breaking review/lifecycle contract justifies a MAJOR candidate rather than silently calling this a
v2 patch. No formal tag was moved.

## Phase 2 — PASS

Attack families included sparse and ambiguous goals, no-punctuation questions, AI inference presented
as fact, existing-project reconstruction, unreviewed plan execution, unauthorized capability,
candidate/version binding, wrong-work/wrong-candidate/stale Evidence, first recovery failure,
recovery budget, repeated confirmed errors, AI plan mutation, partial replan, fake completion,
resume identity mismatch, context leakage and installed-copy contamination.

Two attacks initially succeeded:

1. A manual candidate copy included `.mimosa`; investigation proved the product installer already
   excluded it, so the invalid manual packaging path was discarded and the real installer used.
2. The real installer then exposed a genuine `.pytest_cache` exclusion defect. Phase 2 failed, Phase 1
   fixed the installer and added a regression. Full Phase 2 was rerun.

Final rerun evidence:

- Development full regression: `311 passed in 9.04s`.
- Development validator: `0 errors, 0 warnings`.
- Fresh self-contained install: `INSTALLED_SELF_CONTAINED`, `365 files`.
- Installed discovery: exactly `1 SKILL.md` and `20 MODULE.md`.
- Installed development-state scan: `0` directories named `.git`, `.mimosa`, `.pytest_cache` or
  `__pycache__` before validation/testing.
- Installed validator: `0 errors, 0 warnings`.
- Installed-copy full regression: `311 passed in 11.06s`.

## Phase 3 — PASS

| Final-goal question | Result | Evidence basis |
| --- | --- | --- |
| User can start by stating what they want | PASS | Natural-language public entry and sparse-goal tests |
| Model understands before construction | PASS | Understanding session required; raw-fact bypass rejected |
| User sees the model's understanding | PASS | Plan review required before execution |
| User can change requirements normally | PASS | Human edits refresh the approved baseline; partial replan preserves unaffected work |
| Skill constrains the model, not the user | PASS | Authority and Integrity are independent planes |
| Approval removes stage-by-stage pushing | PASS | Autonomous-continuation tests and legal-stop control |
| User need not research Skills | PASS | Fact-derived discovery/resolution and arbitrary Harness-visible capabilities |
| Capabilities are selected and controlled | PASS | validation/permission filtering and Work-scoped invocation envelope |
| Confirmed requirements are not silently forgotten | PASS | durable confirmed-requirement baseline |
| Confirmed systemic errors do not silently recur | PASS | recurrence fingerprint enters Recovery and blocks completion |
| Changes adjust the affected portion | PASS | regenerated affected work; preserved/invalidated/revalidation evidence classes |
| Failures recover actively | PASS | original blocker plus related regression required |
| Completion means the real goal is met | PASS | current candidate-bound Acceptance Evidence required |
| Experience is more reliable than bare-model prose | PASS | deterministic gates cover the listed bare-model failure classes |
| Product remains a lightweight Delivery Skill | PASS | one public Skill; Harness/platform features excluded; no database/platform added |

Final user question: **PASS for the validated candidate**. An ordinary user can entrust a project to
the model with materially less supervision because confirmed intent, plan, corrections, capability
scope, recovery and completion are enforced by durable state and current Evidence rather than model
memory alone.

## Release status — PASS

The exact `v3.0.0-rc3` candidate was subsequently committed, annotated-tagged, published as a GitHub
prerelease, downloaded again, installed from the downloaded ZIP, fully regressed, and exercised in a
fresh real Codex Harness journey. See
[`V3_RC_RELEASE_VALIDATION_REPORT.md`](V3_RC_RELEASE_VALIDATION_REPORT.md) for the immutable identity,
SHA chain, failed rc1/rc2 attempts, historical attacks and Stable recommendation. Historical tags
were not moved. Non-Codex Harness compatibility items remain `PENDING_EXTERNAL_VALIDATION`.
