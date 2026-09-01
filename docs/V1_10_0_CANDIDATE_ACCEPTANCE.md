# v1.10.0 Candidate Acceptance — Goal-to-Execution Closure

## Scope and SemVer

This is a minor release because it adds backward-compatible Runtime contracts for multi-turn
understanding, capability invocation and bounded recovery. It also fixes installed-copy
regression and version-identity validation defects found by a full product-goal audit.

## Required evidence before release

1. `git diff --check`.
2. `python 共享/scripts/validate-skill.py --root .` reports zero errors and warnings.
3. Full development regression passes.
4. Sparse-goal multi-round, existing-project, authorization, invocation-result, failure,
   blocker-revalidation, regression and fake-PASS negative tests pass.
5. Candidate archive is installed into a clean directory without `.git` or private workspace
   dependencies; validator and full regression pass from that installed copy.
6. Historical tags remain unchanged.
7. Only after the above: create the new annotated tag and GitHub Release, download the formal
   asset again, verify GitHub digest, reinstall it and repeat validator/full regression.

Actual third-party Harness execution remains environment-specific external validation. Core
contracts may be PASS while a Harness adapter is still `PENDING_EXTERNAL_VALIDATION`.
