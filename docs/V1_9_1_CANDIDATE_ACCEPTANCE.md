# v1.9.1 Candidate Acceptance — Enterprise Version Governance

## Scope

This is a documentation-and-install-contract patch. It does not change planning, runtime,
capability selection or delivery semantics.

## Acceptance criteria

| Criterion | Expected evidence |
| --- | --- |
| Personal default is clear | Install docs permit Latest Stable only when no exact version is supplied. |
| Enterprise pinning is clear | Public entrypoints require a human-approved exact tag, Release asset SHA-256 and no automatic upgrade. |
| Migration is not mistaken for production install | Workspace recovery docs state that a restored development directory is not a formal installation source. |
| Version identity remains traceable | Installer report requires skill id, version, exact tag, asset SHA-256, target path and self-check result. |
| No historical release is rewritten | Existing tags are inspected as immutable; this candidate receives a new patch tag only after validation. |

## Required verification before release

1. `git diff --check`
2. Documentation link and contradictory-wording scan
3. `python 共享/scripts/validate-skill.py --root .`
4. `python -m pytest -q`
5. Package and install the exact candidate tag from its GitHub Release asset, then rerun the installed validator and focused installation tests.

Anything not actually verified is `PENDING_EXTERNAL_VALIDATION`; it is not a PASS.
