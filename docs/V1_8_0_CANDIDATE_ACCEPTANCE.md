# v1.8.0 Candidate Acceptance

Date: 2026-08-31 (Asia/Shanghai)

## Outcome

Candidate is locally accepted for release. No known locally repairable defect remains.

## Product scenarios

| Scenario | Observable result |
| --- | --- |
| Simple enterprise-labelled work | Label does not activate governance or a heavy plan |
| Complex personal project | Real persistence, migration, recovery and platform facts retain depth |
| Existing enterprise plan | Enterprise stages remain the authoritative plan body |
| Human modifies AI plan | Semantic merge is applied with human provenance; AI plan is not restored |
| Conditions change | Only AI work declaring the changed dependency is recomputed |
| Mature upstream capability | Higher-maturity compatible Harness/upstream source beats weaker local code |
| New machine/Harness install | Self-contained temp install copied 348 files and passed installed-copy validation |
| Failure and recovery | Failure evidence is frozen; recovery remains blocked until original blocker PASS; pending external evidence blocks completion |

These scenarios execute through `tests/reliability/test_delivery_runtime.py`, not wording-only assertions.

## Mechanical acceptance

- Full regression: `python -m pytest -q` -> `277 passed in 46.81s`.
- Repository validator: `python 共享/scripts/validate-skill.py --root .` -> `0 errors, 0 warnings`.
- Skill Creator validator with UTF-8 mode -> `Skill is valid!`.
- Candidate temp install -> `INSTALLED_SELF_CONTAINED`; installed-copy validator -> `0 errors, 0 warnings`.
- Git whitespace check -> no errors.
- Historical `v1.7.1` remains at `b26bdc8983bf0d36cb147b6dd28ed0b8069429e1` before release.

## Honest external boundary

The following are `PENDING_EXTERNAL_VALIDATION` until the release exists and external
environments run them: GitHub Release asset digest resolution; clean-machine installs on
TRAE, WorkBuddy and Claude; live production-project execution. They do not conceal a local
candidate failure and must not be reported as PASS.
