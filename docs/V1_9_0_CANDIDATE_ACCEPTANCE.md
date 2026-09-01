# v1.9.0 Candidate Acceptance

Date: 2026-09-01 (Asia/Shanghai)

## Scope and admission

This candidate addresses a real enterprise-composition gap found during CEO-readiness audit:
the unified runtime could select known capabilities supplied by a Harness, but arbitrary
department capabilities such as `legal_review` could not enter the same fact-derived resolution
path. Candidate admission is limited to capability composition and current-facing documentation;
it does not add a project template or allow a capability to create a Stage.

## Observable behavior

- A project or mature Planner may declare an arbitrary support capability.
- A Harness-visible or enterprise-catalogued Skill can satisfy that need.
- Explicitly unauthorized, incompatible, identity-unverified, license-incompatible or
  runtime-blocked candidates are excluded and their reasons are retained.
- A selected but incompletely proven candidate is marked `REQUIRES_VALIDATION` and cannot be
  treated as production-ready evidence.
- Capability resolution is recomputed when project facts or visible catalogs change.
- Capability identity never creates or promotes project work or a Stage.
- Absence of a company-wide Skill Registry is reported honestly; this repository does not claim
  to scan Skills that the current Harness cannot expose.

## Candidate evidence

- Focused capability/delivery/replan suite: `23 passed`.
- Full regression: `286 passed in 50.66s`.
- Repository validator: `0 errors, 0 warnings`.
- Skill Creator validator: `Skill is valid!`.
- Candidate self-contained install: copied `352` files; installed-copy validation
  `0 errors, 0 warnings`; installed focused behavior suite `23 passed`; tag correctly classified
  as pre-release before publication.
- Formal v1.8.1 asset was independently downloaded, matched GitHub SHA-256
  `84ac6ca7b5165927cdac0337f86297b2cb52f87cb7f2280603762461e105e616`, installed
  self-contained and validated with `0 errors, 0 warnings`.
- Current and full Git history secret-pattern scan: `0` matching files for common PAT, AWS key
  and private-key markers.

## Honest product boundary

`ENTERPRISE_CONTROLLED_PILOT_READY` may be claimed only for a bounded workflow with a business
owner, IT owner, permitted data, explicit acceptance and human authority. The following remain
`PENDING_EXTERNAL_VALIDATION` or not included:

- Claude/TRAE/WorkBuddy clean-machine execution beyond their published conformance status;
- company-wide Skill Registry, SSO/RBAC, centralized audit console and cross-department bus;
- customer production outcomes, SLA, legal review and security certification;
- unattended high-risk production decisions or writes.

The candidate is not an enterprise AI platform and must not be sold as one.
