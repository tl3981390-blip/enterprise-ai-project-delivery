# enterprise-ai-project-delivery

> **A reliability layer for complex project delivery.**
> It turns "the AI said it's done" into "completion that can be proven with real evidence" — and it governs the whole journey: UNDERSTAND → GOVERN → EXECUTE → OBSERVE → RECOVER → VERIFY → LEARN.
>
> 适用对象是**复杂项目**（企业/个人、AI/非 AI、Web/桌面/数据/自动化均可）：显式点名本 Skill 即默认接受，按项目实际生成 Active Delivery Plan。企业 AI 是主要价值域与经验来源，不是使用资格条件（Skill 名称沿用历史标识）。

**Current version: v1.5.0** (First Generation Product Core, `CORE_FEATURE_FREEZE = ACTIVE`; post-v1.5.0 generalization defect fix in progress — see `evidence/post_v1_5_generalization/`) · Release commit `491f6c9` · Repository: **private**, owner `tl3981390-blip`

## Get the skill — pick one path

**I just want to USE it** → GitHub **Releases → v1.5.0 → Assets → `enterprise-ai-project-delivery-v1.5.0.zip`** (the formal release artifact — verify `SHA-256 = 020a759ab78ba3678ff68dd10cd74a5ef54a51036162c6ef40c7f2e0521e4e8d`, then load into your harness). Note: the green **Code → Download ZIP** button is a *branch source snapshot*, not the release artifact — see [docs/INSTALL_AND_ACQUISITION.md](docs/INSTALL_AND_ACQUISITION.md).

**Have your AI harness install it for you (agent mode)** → give your harness this repository URL plus: *"Follow `docs/AGENT_INSTALL.md` in this repo."* The agent clones (needs GitHub auth — repo is private), verifies `v1.5.0 → 491f6c9`, runs `python docs/install.py --harness auto` (self-contained full-core install, no author-local paths), and reports. Contract: [docs/AGENT_INSTALL.md](docs/AGENT_INSTALL.md).

**I want to DEVELOP / MAINTAIN it** → GitHub **Code → HTTPS → copy the repository URL**, then `git clone <url>` in a terminal (requires GitHub authentication — the repository is private), then `git fetch --tags` and verify `v1.5.0 → 491f6c9`. Full migration guide: [docs/DEVELOPMENT_AND_MIGRATION.md](docs/DEVELOPMENT_AND_MIGRATION.md).

Guides: [Installation & Acquisition](docs/INSTALL_AND_ACQUISITION.md) · [Harness Guide](docs/HARNESS_GUIDE.md) · [Development & Migration](docs/DEVELOPMENT_AND_MIGRATION.md) · [Development History](docs/DEVELOPMENT_HISTORY.md)

## What problem it solves

When AI agents build complex projects, four failure classes dominate:

1. **Building before understanding** — the root cause of goal drift, overreach and fake acceptance.
2. **Stalling and fake completion** — agents stop at every stage waiting for "continue", or claim success that evidence contradicts.
3. **Broken continuity** — failures, resource exhaustion and model switches fragment the work; successors redo or misread state.
4. **Unverifiable claims** — local "close-enough" telemetry and narrative reports cannot survive independent verification.

## Architecture

```text
enterprise-ai-project-delivery CORE (reliability mechanisms, feature-frozen)
                │
        Harness Capability Contract (L1–L10)
                │
   ┌────────────┼────────────┐
Adapter (ZCode) Adapter (Claude) Adapter (TRAE/WorkBuddy …)
                │
     ENTERPRISE PROFILE + PROJECT PROFILE (customization without forks)
```

- **Core**: cross-company, cross-project, cross-harness reliability mechanisms only.
- **Thin adapters**: per-platform discovery/invocation/lifecycle/permission mappings — never a core fork.
- **Profiles**: enterprise policies (approval, model, data, evidence…) and project specifics layered under non-overridable core invariants.

## Installation

Requires a harness that can load skills and execute local deterministic tests (Python 3.10+).

```bash
# ZCode: copy or link the canonical core into your skills directory
#   ~/.zcode/skills/enterprise-ai-project-delivery/
# Claude Code: place the thin adapter under
#   ~/.claude/skills/enterprise-ai-project-delivery/
# Other harnesses: see adapters/<platform>/INSTALLATION.md
python 共享/scripts/validate-skill.py --root .   # structural self-check
```

## Basic usage

The skill gates every task before any byte is written: answer the pre-construction questions → Task Understanding Contract → understanding gate → plan–contract alignment → only then execution opens write permissions, with drift checks throughout.

**Who can use it（适用性）**：任何复杂项目——个人或企业、AI 或非 AI、桌面/Web/数据/自动化。`EXPLICIT_INVOCATION`（用户点名使用）默认接受，不因项目类型拒绝；能力模块（RAG/Agent/MCP 权限/企业治理/浏览器验收/部署等）按项目声明条件激活，未声明记 `NOT_APPLICABLE`。分层编排见 `共享/references/PROJECT_ORCHESTRATION_SPEC.md`。

## Start from Day 1

```text
NEW PROJECT → invoke the skill → understand → contract → governed execution
```

Stages pass automatically; the agent continues to the next legal action on its own. Ordinary failures are recovered in bounded loops with mechanical revalidation; only genuine human gates pause the work.

## Mid-project attachment

```text
EXISTING PROJECT → invoke the skill halfway
  → read-only reconstruction (no writes before the adoption boundary)
  → adoption boundary (git head, runtime, snapshot, skill version, harness)
  → historical state classified (VERIFIED / UNVERIFIED / FAILED / UNKNOWN)
  → continue the existing project — never a rebuilt one
```

> Pre-attachment AI claims are **not** automatically trusted as verified evidence. Only history that future work actually depends on is verified (lazy historical verification).

## Recovery / Resume / Handoff

- **Recovery ladder**: freeze evidence → classify → bounded auto-recovery (with revalidation + regression) → safe rollback → compliant alternative → complete human recovery package.
- **Resume**: "continue" is only a request; resumption re-verifies blocker, git, worktree, contract, evidence and runtime identity.
- **Resource guard & model handoff**: on resource risk the agent closes out atomic units, checkpoints, and emits a complete handoff package; the successor must mechanically verify real state before inheriting the same task.

## Telemetry closed loop

Telemetry is not just reporting — it is a control loop: `OBSERVE → DECIDE → ACT → VERIFY`.

| Signal | Automatic action (always mechanically re-verified) |
| --- | --- |
| Failure | freeze → classify → bounded recovery → original-blocker revalidation |
| Illegal passive stop | legal-stop check → auto-continue |
| Fake PASS attempt | acceptance re-entry for the missing item |
| Resource risk | checkpoint / handoff preparation |
| Context waste | delta-context enforcement |
| Cache invalidation | relevant-gate reverification |

The runtime closed loop never modifies the formal core — core evolution stays gated behind the candidate pipeline.

## Enterprise customization

`CORE + HARNESS ADAPTER + ENTERPRISE PROFILE + PROJECT PROFILE` — no company forks. See [`examples/`](examples/) for synthetic profiles.

Profiles **cannot override** `NON_OVERRIDABLE_CORE_INVARIANTS`: anti-fake-PASS, evidence integrity, authorization boundary, candidate identity, scope authority. A project profile can never relax an enterprise policy (same-key restrictive overrides are rejected as `PROFILE_CONSTRAINT_CONFLICT`).

## Harness compatibility

| Harness | Status |
| --- | --- |
| ZCode 3.10.1 | **VALIDATED L9** (discover/invoke/contract/tools/telemetry/resume/attach/closed-loop/profile) |
| Claude Code 2.1.235 | L1 VERIFIED / **BLOCKED_RUNTIME_AUTH** (execution blocked by invalid API key in the tested environment) |
| TRAE | PENDING_EXTERNAL_VALIDATION (adapter ready; not installed in test environment) |
| WorkBuddy / CodeBuddy | PENDING_EXTERNAL_VALIDATION (adapter ready; not installed) |

Capability differs per platform, so conformance levels differ (L1–L10). Where a harness lacks a capability, the adapter declares an explicit boundary and takes a legal degradation path — the skill never pretends a platform has functions it does not have.

## Reliability efficiency

Delta context + hash-based invalidation, verified-state cache, risk-based gate routing, evidence-by-reference, hot/cold handoff, batched evolution.

`ENGINEERING_OBSERVATIONAL_BENCHMARK` (same-scope controlled replays during development, platform-native agents, model identity not strictly controlled):

| | v1.3 | v1.4 | v1.5 |
| --- | ---: | ---: | ---: |
| Total tokens | 9,872,301 | 9,209,337 | 8,970,430 |
| Elapsed (s) | 2,735 | 1,991 | 1,389.4 |
| Acceptance | 14/14 | 14/14 | 14/14 |

In the controlled engineering replay used during development, v1.5 consumed fewer total tokens and elapsed time than v1.4 and v1.3 while preserving the acceptance target. No guaranteed or average reductions are claimed.

## Evidence & anti-fake-PASS

One canonical recorder (schema validation, hash chain, anchor) is the single source of truth for delivery telemetry; local substitutes are rejected at acceptance. Completion claims require mechanical evidence; failures are frozen, never rewritten. Internal validation evidence beyond this repository (project labs, benchmark workspaces) is retained privately.

## Core feature freeze

`CORE_FEATURE_FREEZE = ACTIVE`. v1.5.0 is the **First Generation Product Core**. Ordinary new needs go to harness adapters, enterprise/project profiles, or documentation — not the core. The core reopens only if **all** hold: real project failure + current core cannot handle + generalizable + reproducible + evidence-backed.

## Known limitations

- Claude Code execution is currently blocked by runtime authentication in the tested environment (L1 verified mechanically).
- TRAE and WorkBuddy/CodeBuddy are not yet externally validated.
- Exact cross-run model identity was not fully controlled; benchmark results are observational.
- `FULL_SECURITY_AUDIT = NOT_AVAILABLE` (a complete AST security audit has not been executable in the development environment; passing gates cover governance/regression/evidence integrity only).

## Security status

No secrets, credentials or runtime artifacts are tracked (scanned across the full git history). See Known Limitations for the honest security-audit status.

## Versioning

Semver. Formal releases: v1.0.0 → v1.5.0 (v1.5.0 = First Generation Product Core, feature-frozen). Release evidence lives in `evidence/release_vX.Y.Z/`.

## License

MIT — see [LICENSE](LICENSE). Upstream attributions in [NOTICE](NOTICE); source boundaries in `09_License与来源边界.md`.
