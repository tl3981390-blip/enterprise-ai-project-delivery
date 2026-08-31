# Development & Migration Guide

GitHub is the single central source of version truth. Machines come and go through it — never through USB drives, chat-app folder transfers, or rebuilding history from a release ZIP.

## New-machine development migration (canonical flow)

```text
1. Install Git
2. Set up legitimate GitHub authentication (GCM / gh auth login / SSH key)
3. Copy the HTTPS repository URL (GitHub → Code → HTTPS)
4. git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
5. git fetch --tags
6. Verify repository identity: owner tl3981390-blip, repo enterprise-ai-project-delivery, origin URL, default branch = main
7. Verify formal tag:      git rev-parse v1.5.0^{commit}   → 491f6c9f76c6c384fd18a21303aba56812eeadb1
8. Verify release commit:  git show --stat v1.5.0          → "release: ... v1.5.0 ..."
9. Verify main:            git rev-parse origin/main       → matches GitHub branch view
10. Create your development branch (e.g. git checkout -b <work>-dev) — never commit directly to main
11. Only then start modifying
```

## Identity rules

**Commit hashes do not change when you change computers.** The same commit is `491f6c9` on every machine; Git commit identity is content-derived. A *new* hash appears only when a *new commit* is made (new content/metadata), not because of the machine.

**Tag immutability.** `v1.5.0 → 491f6c9` is frozen. Never move, rewrite, recreate or force-push historical release identity.

## ZIP SHA-256 vs Git hash — two different identities

- **Git commit hash** = identity of the source tree + history entry (stable across machines).
- **Release asset SHA-256** = identity of the published ZIP file. Formal v1.5.0: `020a759ab78ba3678ff68dd10cd74a5ef54a51036162c6ef40c7f2e0521e4e8d`.

**Re-zipping changes the hash.** Even with identical source content, timestamps, entry ordering, compression metadata and archive parameters can differ, so a freshly built ZIP generally will NOT match the release SHA-256. Therefore formal identity verification is always performed against the **original GitHub Release asset**, never against a self-made archive.

## Upgrading without breaking history

Future releases add new tags (`v1.5.1`, `v1.6.0`, …) and new release assets. Old tags and old release assets stay untouched. Consumers pin to the tag they validated; developers move forward on branches.

## AI-assisted migration (allowed pattern)

You may open a fresh AI coding harness on the new machine, hand the model the private repository HTTPS URL, and let it — under legitimate GitHub authentication — clone, verify tag/commit/main, create a development branch and continue maintenance. The AI must not and cannot bypass the GitHub authentication boundary; credentials stay in GCM/gh/SSH, never in the conversation.

## Connector note (ChatGPT / GitHub App)

Connector access to a **private** repository requires explicit authorization in the GitHub App / Connector Repository Access settings. If a connector cannot read the repo, authorize `tl3981390-blip/enterprise-ai-project-delivery` there — this is `CONNECTOR_ACCESS_CONFIGURATION`, not a repository failure. Do not make the repo public, create duplicate repos, or re-publish v1.5.0 to work around it.

## What may change after a release

Post-release documentation commits on `main` (like this guide) are legitimate: they sit *after* the frozen tag and never move it. Rule of thumb: documentation, adapters, profiles and examples evolve on main; the core is feature-frozen (reopen only for evidence-backed, reproducible, generalizable failures the core cannot handle).
