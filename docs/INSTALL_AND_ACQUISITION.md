# Installation & Acquisition Guide

Four ways to get `enterprise-ai-project-delivery` from GitHub — they are **not** interchangeable.

## A. GitHub Release ZIP — for USE / INSTALL ✅ recommended

Path: **Repository → Releases → v1.5.0 → Assets → `enterprise-ai-project-delivery-v1.5.0.zip`**

- This is the **formal release artifact**, built from the `v1.5.0` tag.
- Formal identity: `SHA-256 = 020a759ab78ba3678ff68dd10cd74a5ef54a51036162c6ef40c7f2e0521e4e8d`
- Verify after download (PowerShell: `Get-FileHash <zip> -Algorithm SHA256`, or `sha256sum <zip>`).
- Use it for: installation, harness import, version archiving, formal release verification.

## B. Code → Download ZIP — branch snapshot, NOT the release artifact

The green **Code → Download ZIP** button gives you a **snapshot of the current branch source**.

- It carries **no Git history** and is **not** the formal v1.5.0 release asset.
- `main` may already be newer than the `v1.5.0` tag (post-release documentation commits are normal).
- Its SHA-256 is **not expected** to equal the release SHA-256.
- Do not use it for long-term development — clone instead.

## C. HTTPS clone — for DEVELOPMENT / MAINTENANCE / MACHINE MIGRATION

GitHub page **Code → HTTPS** shows the **repository URL** (there is no "clone button" on the page itself). You copy the URL, then clone in a terminal:

```bash
git clone https://github.com/tl3981390-blip/enterprise-ai-project-delivery.git
cd enterprise-ai-project-delivery
git fetch --tags
git rev-parse v1.5.0^{commit}   # must print 491f6c9f76c6c384fd18a21303aba56812eeadb1
```

## D. SSH / GitHub CLI — for environments already set up

- **SSH**: for accounts with a registered SSH key (`git@github.com:tl3981390-blip/enterprise-ai-project-delivery.git`). Not required for normal users.
- **GitHub CLI**: `gh repo clone tl3981390-blip/enterprise-ai-project-delivery` — requires `gh auth status` to be authenticated.

## Private repository authentication (applies to A–D for non-members)

This repository is **PRIVATE**. Any new machine, harness, agent or AI coding environment needs legitimate GitHub credentials: Git Credential Manager, GitHub CLI login, an SSH key, or a harness-native GitHub connection. **Never send your GitHub password, PAT, 2FA code, OAuth secret or private key to an AI model** — credentials are stored only by GitHub / the credential manager / the OS.

ChatGPT / GitHub-App style connectors: repository existence ≠ connector permission. If a connector cannot read this repo, authorize it in the GitHub App / Connector **Repository Access** settings for `tl3981390-blip/enterprise-ai-project-delivery`. This is `CONNECTOR_ACCESS_CONFIGURATION`, not a repository failure — do not switch the repo to public or create duplicates.

## Harness installation flow

```text
GitHub → enterprise-ai-project-delivery → Harness Adapter → Core → Project
```

Switching harnesses means **changing the adapter, never the core**. Per-harness installation/validation/limits: [HARNESS_GUIDE.md](HARNESS_GUIDE.md) and `adapters/<platform>/INSTALLATION.md`. After install, self-check: `python 共享/scripts/validate-skill.py --root .`

## Using the skill

- **New project**: load the skill in your harness, then instruct e.g. *"Use enterprise-ai-project-delivery to govern this project."* The skill enters understanding → contract → gated execution → telemetry → recovery → acceptance.
- **Existing half-done project**: invoke the same way — the skill runs **mid-project attachment**: read-only discovery → state reconstruction → adoption boundary → historical claims classified (`VERIFIED / UNVERIFIED / FAILED / UNKNOWN_PRE_ATTACHMENT`, never auto-laundered) → dependency verification → continue the *same* project. See README "Mid-project attachment".
