# Harness Guide

## v3 Stable mandatory boundary

Harness must assert `user_origin_ref` from the actual conversation user for approval and human/enterprise edits, and bind approval intent to the current plan revision and session scope. It must not synthesize approval from arbitrary prose. Harness may persist the six-field adaptive strategy in its own project-isolated store, but must not serialize author paths or treat missing state as an error. Core remains self-contained and storage-neutral.

When validating an installed copy, invoke `docs/validate_installed_copy.py` first and use its cache-safe environment for every additional Python/pytest probe (`PYTHONDONTWRITEBYTECODE=1`, pytest cache provider disabled). Never run ordinary pytest first inside the installed Skill: that changes the artifact under test and invalidates the zero-pollution assertion.

One core, thin adapters, honest levels. Switching harness = changing the adapter, never the core.

## Support matrix (real validation status only)

| Harness | Validation status | Level |
| --- | --- | --- |
| ZCode 3.10.1 | **REAL VALIDATED** — full chain exercised live (discover/invoke/contract/tools/telemetry/resume/attach/closed-loop/profile) | **L9** |
| Claude Code 2.1.235 | L1 verified mechanically; execution **BLOCKED_RUNTIME_AUTH** (invalid API key in the tested environment) | L1 |
| TRAE | Adapter ready, not installed in validation environment | PENDING_EXTERNAL_VALIDATION |
| WorkBuddy / CodeBuddy | Adapter ready, not installed | PENDING_EXTERNAL_VALIDATION |

Vocabulary: `VALIDATED / PARTIALLY_VALIDATED / BLOCKED_RUNTIME_AUTH / PENDING_EXTERNAL_VALIDATION / NOT_AVAILABLE`. "Adapter ready" ≠ "validated support"; we never claim "supports all major harnesses".

## Per-adapter quick reference

| Question | ZCode | Claude Code | TRAE | WorkBuddy/CodeBuddy |
| --- | --- | --- | --- | --- |
| Harness / version | ZCode 3.10.1 | Claude Code 2.1.235 | TRAE (n/a) | WorkBuddy / CodeBuddy (n/a) |
| Validation level | L9 | L1 (auth-blocked above) | L0 pending | L0 pending |
| How the skill is discovered | session Skill tool loads canonical core | `~/.claude/skills/<name>/` thin adapter dir | install then run capability probe | install then run capability probe |
| How the core is loaded | canonical repo via adapter | adapter manifest points to canonical core | same pattern | same pattern |
| Capability degradation rule | none needed | no subagent/browser execution until auth fixed; L2+ blocked honestly (never simulated) | declared via `CAPABILITIES.json` after probe | same |
| Telemetry support | core recorder, in-project (VALIDATED) | not yet validated | NOT_TESTED | NOT_TESTED |
| Resume support | VALIDATED (six-check) | not yet validated | NOT_TESTED | NOT_TESTED |
| Handoff support | VALIDATED | not yet validated | NOT_TESTED | NOT_TESTED |
| Mid-project attach | VALIDATED (no-laundering) | core-semantic ready, runtime pending | NOT_TESTED | NOT_TESTED |
| Known limitations | automatic_activation not yet demonstrated | invalid API key in test env (fix creds, rerun conformance suite — no core change needed) | not installed | not installed |

Adapter packages live in `adapters/<platform>/` (installation, invocation, lifecycle, permissions, capabilities). They contain **no core copy** — the core has a single canonical source. Where a harness lacks a capability, the adapter declares an explicit boundary and a legal degradation path; nothing is faked.
