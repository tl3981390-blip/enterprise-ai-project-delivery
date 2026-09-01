# FINAL_PRODUCT_TARGET

Status: `CURRENT`

Stable v3 clarification: user-visible plans contain only real work; clear bounded goals may require zero questions; user intent authorization is Harness-origin and current-plan-bound. Runtime self optimization is Evidence-backed Adaptive Execution Strategy only and never modifies Core or publishes a version. Formal installation is self-contained and portable without author workspace or saved strategy state.

Implementation boundary for v3.0.1: Strategy is a closed safe catalog consumed through Delivery Runtime and may update only from current PASS Evidence IDs in the same canonical ledger. Every public transition of user-owned state uses one trusted origin validator. Formal assets fail closed unless installed identity proves the exact immutable tag and 40-character commit. This synchronizes implementation without changing the product goal above.

This is the repository's only current final product target. Release closures, historical evidence,
old SDD and architecture documents describe earlier states; they do not override this target.

## The result for the user

`enterprise-ai-project-delivery` is a lightweight Delivery Skill that helps an AI model reliably
finish the project the user actually wants. Its purpose is not to teach users project governance or
make them operate an internal workflow. Its promise is simpler:

> The user can trust the model with a project without becoming the model's full-time supervisor.

Before using it, models often forget requirements, repeat acknowledged errors, patch one symptom
without checking the shared root cause, silently change scope, invent features, stop for unnecessary
"continue" prompts, make the user choose tools, and claim completion before the real project works.
Long projects amplify drift and context loss.

After using it, the user talks normally and explains the result they want. The model:

1. understands the current goal before writing;
2. asks only questions whose answers would materially change the work;
3. shows its plan so the user can see what the model believes the project is;
4. lets the user freely question, reject, add, remove, reorder, pause or replace decisions;
5. treats the approved plan and confirmed requirements as a durable delivery baseline;
6. continues through legal next actions without asking the user to push every stage;
7. discovers and uses the minimum sufficient currently available Skills, tools, agents or MCP;
8. scopes each capability to the work that needs it and removes its temporary context afterward;
9. replans only affected work and evidence when conditions change;
10. captures failures, fixes root causes, revalidates the original blocker and related behavior;
11. records user corrections so the same confirmed delivery error is not silently repeated;
12. accepts completion only when current evidence proves the original goal and acceptance result.

The noticeable experience must be: the model is more stable, remembers confirmed requirements,
drifts less, acts more continuously, catches related defects, and is more trustworthy than the bare
model.

## User control and plan visibility

The Skill controls the model, not the user. The user always owns legitimate business decisions and
can change their mind. A previous plan never gives the Skill authority to reject a new authorized
request. Real legal, enterprise-policy, external-permission or other-data boundaries are reported as
their actual source.

The plan is not an approval bureaucracy. It is the visible representation of the model's current
understanding, allowing the user to catch missing, invented, drifted or badly ordered work before
construction. An explicit instruction to start immediately may approve the current visible scope
without repeated questioning; the internal plan and approval scope still exist.

Truth is independent of authority. A user may waive work, but the Skill records that result as waived
and unverified, never PASS.

## Product boundary

The Host Model understands language, reasons, generates solutions and performs work. Ordinary Skills
provide domain techniques. This Delivery Skill controls understanding-before-action, requirement and
plan continuity, user ownership, autonomous continuation, capability scope, change/recovery and
evidence-backed completion. The Harness provides workspace, files, models, tools, Skills, MCP,
accounts, permissions, isolation and infrastructure.

The Delivery Skill does not recreate the Harness, user/tenant management, enterprise RBAC, a database
platform, transaction bus, project-management platform or company-wide Skill registry. It is
persistence-backend neutral and uses the task/workspace/project isolation already provided.

Natural-language intent is interpreted semantically by the Host Model from conversation context,
never from punctuation alone. Consequential ambiguity asks one minimal clarification question.

## Improvement boundary

Real corrections, recovery failures, acceptance failures and attacks may produce an improvement
observation. Personal preference, project-specific behavior, an external capability defect, Harness
limitation or enterprise policy does not automatically become a global Core defect, no matter how
frequent it is. A Core candidate needs evidence, reproduction, a generalizable root cause,
counterexamples and regression testing in an isolated development copy.

The installed formal Skill never edits or releases itself while delivering a project. Candidate
analysis and testing may be automated; formal publication remains a separately verified release.

## Final acceptance question

The product passes only when real evidence supports a yes to this question:

> Can an ordinary user now trust a project to the model more than before, without acting as the
> model's supervisor?

Allowed final states are `PASS`, `FAIL`, `PENDING_EXTERNAL_VALIDATION` and
`NOT_INCLUDED_BY_DESIGN`.
