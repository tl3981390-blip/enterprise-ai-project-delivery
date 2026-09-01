# TARGET_SOURCE_AUDIT

Baseline inspected: formal `v2.0.0` (`d85872172db77d93e8253515f74d6e0c4e8b929a`). Current
development start: `v2.0.1` (`bfa62f1f29dad189f7b586d4627e1b60cda2634a`).

| Source family | Classification | Decision |
| --- | --- | --- |
| `docs/current/FINAL_PRODUCT_TARGET.md` | CURRENT | The only current final product target. |
| Current root `SKILL.md` and runtime Core | PARTIALLY_CURRENT | Operational contract; must conform to the Current target. |
| `README.md`, architecture and Harness documents | PARTIALLY_CURRENT | Descriptive sources; conflicts are superseded by the Current target. |
| `共享/references/SKILL_EVOLUTION_ENGINE_SPEC.md` and batch evolution spec | PARTIALLY_CURRENT | Candidate-only boundary retained; old external-lab and lifecycle assumptions superseded. |
| `docs/V2_0_0_RELEASE_CLOSURE.md` | HISTORICAL | Evidence about immutable v2.0.0, not the current target. |
| Earlier release closures and evidence directories | HISTORICAL | Retained as attacks/evidence; never current requirements. |
| Old SDD, total-control and numbered module narratives | SUPERSEDED where conflicting | Internal references only; Current target controls. |

No second file may claim `Status: CURRENT` for the final product target. Historical files are retained
for traceability and attacks rather than rewritten.
