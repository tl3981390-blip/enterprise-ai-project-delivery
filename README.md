# enterprise-ai-project-delivery

> **A reliability layer for complex project delivery.**
> It turns "the AI said it's done" into "completion that can be proven with real evidence" — and it governs the whole journey: UNDERSTAND → GOVERN → EXECUTE → OBSERVE → RECOVER → VERIFY → LEARN.
>
> 适用对象是**复杂项目**（企业/个人、AI/非 AI、Web/桌面/数据/自动化均可）：显式点名本 Skill 即默认接受，按项目实际生成 Active Delivery Plan。企业 AI 是主要价值域与经验来源，不是使用资格条件（Skill 名称沿用历史标识）。

Current product truth: [`docs/current/FINAL_PRODUCT_TARGET.md`](docs/current/FINAL_PRODUCT_TARGET.md).

## v3 Stable product boundary

- User-visible plans contain only real project work. Understanding, evidence, recovery and completion gates are internal controls, not injected stages.
- Runtime Self Optimization means optional, Evidence-backed execution-strategy preferences. It never edits Core, source, version, commit, tag or Release.
- Publisher Core Maintenance is a separate repository workflow governed by tests, review and a formal Release.
- Normal users install the GitHub Release Asset. They never need the author's development workspace or adaptive-state files.
The current Stable is [`v3.0.3`](https://github.com/tl3981390-blip/enterprise-ai-project-delivery/releases/tag/v3.0.3),
frozen at commit `a4a4e6c64307dd10b8661e7272bd134df068a8ae`. Its formal Asset SHA-256 is
`2128d256d53a4f3e5498ecf4f5efde642f1bbe2d4c5247bbc6d11bb7b3e513c2`.
`v3.0.0`–`v3.0.2` are **FAILED POST-RELEASE VALIDATION — DO NOT USE** historical tags.

**Stable Release identity is verified at install time from GitHub and `共享/schema/RELEASE_METADATA.json`.** Personal users may resolve the latest Stable Release; enterprise-controlled environments install an approved exact tag and do not auto-upgrade. Natural language is the user interface; human plans are
authoritative; project facts determine the work; one runtime connects multi-turn understanding,
planning, capability invocation, partial replanning, bounded recovery and evidence-based
completion. Historical tags remain immutable.

## Get the skill — pick one path

**I just want to USE it personally** → resolve the repository's latest Stable GitHub Release,
download its versioned asset, verify its published digest, then install it. The green
**Code → Download ZIP** button is a branch snapshot, not a formal Release asset.

**Enterprise test or production** → give the Harness the approved exact tag, require asset-SHA verification, and prohibit automatic upgrades. See [Enterprise version governance](docs/ENTERPRISE_VERSION_GOVERNANCE.md).

**Have your AI harness install it for you (agent mode)** → give it the repository URL and
say: *"Install the latest Stable Release and follow `docs/AGENT_INSTALL.md`."* It resolves
the release, verifies identity, installs a self-contained copy and runs self-check.

**I want to DEVELOP / MAINTAIN it** → clone with legitimate authentication, fetch tags,
and keep the development workspace separate from installed Release copies.

Guides: [Installation & Acquisition](docs/INSTALL_AND_ACQUISITION.md) · [Harness Guide](docs/HARNESS_GUIDE.md) · [Development & Migration](docs/DEVELOPMENT_AND_MIGRATION.md) · [Development History](docs/DEVELOPMENT_HISTORY.md)

## What problem it solves

When AI agents build complex projects, four failure classes dominate:

1. **Building before understanding** — the root cause of goal drift, overreach and fake acceptance.
2. **Stalling and fake completion** — agents stop at every stage waiting for "continue", or claim success that evidence contradicts.
3. **Broken continuity** — failures, resource exhaustion and model switches fragment the work; successors redo or misread state.
4. **Unverifiable claims** — local "close-enough" telemetry and narrative reports cannot survive independent verification.

## Architecture

```text
enterprise-ai-project-delivery (one public SKILL.md)
                │
       20 internal MODULE.md references
                │
        Harness Capability Contract (L1–L10)
                │
   ┌────────────┼────────────┐
Adapter (ZCode) Adapter (Claude) Adapter (TRAE/WorkBuddy …)
                │
     ENTERPRISE PROFILE + PROJECT PROFILE (customization without forks)
```

- **Discovery boundary**: Codex sees one Skill in `/`; numbered modules are internal references,
  not separately installable or invocable Skills.
- **Core**: cross-company, cross-project, cross-harness reliability mechanisms only.
- **Thin adapters**: per-platform discovery/invocation/lifecycle/permission mappings — never a core fork.
- **Profiles**: enterprise policies (approval, model, data, evidence…) and project specifics layered under non-overridable core invariants.

## Installation

Requires a harness that can load skills and execute local deterministic tests (Python 3.10+).

For personal use, say: `Install the latest Stable Release and follow docs/AGENT_INSTALL.md.` For an enterprise-controlled environment, name the approved tag and follow [Enterprise version governance](docs/ENTERPRISE_VERSION_GOVERNANCE.md). The Harness must report a real limitation instead of claiming success when it cannot load Skills, access GitHub or write its Skill directory. See [Installation & Acquisition](docs/INSTALL_AND_ACQUISITION.md).

## Basic usage

The skill gates every task before any byte is written: gather decision-relevant facts from the
request and existing project evidence → ask only consequential unresolved questions (zero is valid
for a bounded task) → Task Understanding Contract → understanding gate → plan–contract alignment →
only then execution opens write permissions, with drift checks throughout.

Questions are generated from consequential information gaps, not a fixed questionnaire. Each
answer is recorded as a provenance-bearing fact event; model inference remains proposed until
confirmed. The Harness may ask up to four high-value questions in one round and continues only
when new answers expose further decision-changing gaps. Planning cannot start through the
multi-turn entry until the mechanical understanding gate passes.

When a Skill or Tool is selected, the Runtime issues a Work-Unit-bound invocation envelope.
The Harness performs the real call and returns output plus Evidence; failures enter the same
bounded recovery lifecycle. Capability selection alone is never reported as execution.

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

Harness-visible or enterprise-catalogued Skills can support project work when the host supplies their capability metadata. The runtime accepts arbitrary declared support needs, excludes candidates explicitly marked unauthorized, incompatible, identity-unverified or runtime-blocked, and records the selection. A capability never creates a Stage. This repository does **not** include a company-wide Skill Registry, SSO/RBAC or cross-department execution bus; those remain enterprise integration responsibilities.

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

## Core evolution boundary

Formal installed Core never self-modifies. Ordinary new needs go to Harness adapters,
enterprise/project profiles or documentation. A Core candidate is admitted only for a reproducible,
evidence-backed `CORE_RELIABILITY_DEFECT` or `GENERALIZABLE_IMPROVEMENT`, is changed in isolation,
passes targeted/adversarial/final-goal regression, and receives Human Release Authority.

## Known limitations

- Claude Code execution is currently blocked by runtime authentication in the tested environment (L1 verified mechanically).
- TRAE and WorkBuddy/CodeBuddy are not yet externally validated.
- Company-wide Skill discovery, SSO/RBAC and a cross-department execution bus are not bundled; only capabilities visible to and authorized in the current Harness/catalog can be selected.
- Exact cross-run model identity was not fully controlled; benchmark results are observational.
- `FULL_SECURITY_AUDIT = NOT_AVAILABLE` (a complete AST security audit has not been executable in the development environment; passing gates cover governance/regression/evidence integrity only).

## Security status

No secrets, credentials or runtime artifacts are tracked (scanned across the full git history). See Known Limitations for the honest security-audit status.

## Versioning

Semver. Historical tags remain immutable. Personal use may resolve the latest formal release from GitHub; enterprise-controlled environments pin an approved exact tag and upgrade only with explicit authorization. Release evidence and candidate acceptance records live under `evidence/` and `docs/`.

## License

MIT — see [LICENSE](LICENSE). Upstream attributions in [NOTICE](NOTICE); source boundaries in `09_License与来源边界.md`.
