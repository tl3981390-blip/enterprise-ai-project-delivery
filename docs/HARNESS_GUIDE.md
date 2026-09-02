# Harness Guide

## v3 Stable mandatory boundary

Harness must assert `user_origin_ref` from the actual conversation user for approval and human/enterprise edits, and bind approval intent to the current plan revision and session scope. It must not synthesize approval from arbitrary prose. Harness may persist the six-field adaptive strategy in its own project-isolated store, but must not serialize author paths or treat missing state as an error. Core remains self-contained and storage-neutral.

When validating an installed copy, invoke `docs/validate_installed_copy.py` first and use its cache-safe environment for every additional Python/pytest probe (`PYTHONDONTWRITEBYTECODE=1`, pytest cache provider disabled). Never run ordinary pytest first inside the installed Skill: that changes the artifact under test and invalidates the zero-pollution assertion.

Harness operations `get_adaptive_strategy`, `get_strategy_guidance` and `update_adaptive_strategy` route through Delivery Runtime. Strategy values are safe Catalog IDs, loaded before the relevant decision, and must produce the documented behavior difference without weakening gates. The update operation accepts only current PASS `evidence_ids`; Harness must never call Adaptive Core with a caller-made Evidence object.

For every file, command, test, API, browser, database or capability result, the Harness/Tool Adapter first captures the real artifact and registers a `HARNESS_EXECUTION` receipt. `record_evidence` receives only its one-time `receipt_id` and optional acceptance/dependency/business metadata. The Host Model cannot submit a bare Evidence dict or override producer, source, status, candidate/work/execution identity or hash. Capability receipts must bind the Runtime-created `invocation_id`; reused, mismatched, stale or hash-inconsistent receipts fail closed. Human plan/change/correction/pause/resume/cancel operations must attach the real conversation authority reference with distinct USER or ENTERPRISE origin. Observed project/system changes require current PASS Evidence and never update the user-confirmed baseline.

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

## Controller-bound user controls

Installing the Skill makes its self-contained Delivery Core available; it does **not** by itself make a Harness intercept every conversation action. A Harness that needs enforced user-control transitions must bind its real conversation UI to `CodexAppServerAdapter.on_user_control(...)` (or the equivalent shared `HarnessAdapterController` operation).

The outer Harness is responsible for authenticating the actual conversation user and classifying only an explicit control as one of `USER_PAUSE`, `USER_RESUME`, `USER_CANCEL`, or `USER_CORRECTION`. It then signs that event with the harness transport secret, session and current contract revision. The adapter never infers a control transition from Host Model prose, punctuation, a tool result, or a normal question. Replay, another session, or an old contract revision fail closed.

This is deliberately a two-part boundary:

- The Harness owns real-user identity and the UI event.
- The shared controller owns persistent state, Runtime authority calls, evidence gates and completion exposure.

For a production enterprise integration, bind the Harness assertion to the enterprise identity provider and retain its audit reference. The deterministic demo uses a local, controlled Owner simulation solely to show the gate/recovery sequence; it is not a production identity integration. See `demo/DEMO_RUNBOOK.md` for the offline presentation rehearsal.
