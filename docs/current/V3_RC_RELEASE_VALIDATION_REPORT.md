# V3 RC RELEASE VALIDATION REPORT

Status: `HISTORICAL` — RC evidence only; it does not describe the Stable product contract.

Date: 2026-09-01 (Asia/Shanghai)

Final status language in this report is limited to `PASS`, `FAIL`,
`PENDING_EXTERNAL_VALIDATION`, and `NOT_INCLUDED_BY_DESIGN`.

## 1. Candidate identity — PASS

The originally presented candidate `v3.0.0-rc1` failed Release Validation before publication because
its in-asset GitHub release declaration remained pending and no reproducible release-asset builder
existed. Its annotated tag remains immutable and unpublished as a Release.

`v3.0.0-rc2` corrected identity/build tooling and was published, but independent Fresh Session
validation found that the recommended validator/pytest workflow created `__pycache__` in the installed
copy. Its tag and GitHub prerelease remain immutable historical failed attempts.

The validated candidate is therefore `v3.0.0-rc3`:

- Git commit: `75f2189a95730709c1de0985398166707d1d9b4b`
- Annotated tag: `v3.0.0-rc3`
- Tag object: `fa21d3e4c8e9c689ee19d54631e09da3b604c688`
- Tag target commit: `75f2189a95730709c1de0985398166707d1d9b4b`
- Tag tree: inherited from the exact frozen commit
- Branch at freeze: `main`
- Worktree after freeze: clean
- GitHub Release: `https://github.com/tl3981390-blip/enterprise-ai-project-delivery/releases/tag/v3.0.0-rc3`
- GitHub state: `draft=false`, `prerelease=true`

Historical identities were not moved:

- rc1 tag object: `7c4059945585b4385fefa3be8d02b485df482175`
- rc2 tag object: `299eceba30fa05ec98fd96e5c99b6a17a03b50d3`

## 2. Release asset — PASS

- Asset: `enterprise-ai-project-delivery-v3.0.0-rc3.zip`
- Size: `544880` bytes
- Source commit: `75f2189a95730709c1de0985398166707d1d9b4b`
- Source tag: `v3.0.0-rc3`
- Build SHA-256: `783cc2a15bcb9359fb8931e7880f0f8d802d0f5d978a07f4b0d592e1f4dd64e6`
- GitHub asset digest: `783cc2a15bcb9359fb8931e7880f0f8d802d0f5d978a07f4b0d592e1f4dd64e6`
- Post-release downloaded SHA-256:
  `783cc2a15bcb9359fb8931e7880f0f8d802d0f5d978a07f4b0d592e1f4dd64e6`
- `DOWNLOADED_SHA == RELEASED_SHA`: `PASS`

The asset was produced by `docs/build_release_asset.py` using `git archive` from the immutable tag,
not by zipping the working directory. Archive inspection found one public `SKILL.md`, twenty internal
`MODULE.md`, and zero `.git`, `.mimosa`, `.pytest_cache`, or `__pycache__` entries.

## 3. Clean install manifest — PASS

The GitHub-downloaded ZIP was extracted to a fresh directory and its own installer was run with
`--zip`, producing:

- ZIP formal-release match: `true`
- Installer status: `INSTALLED_SELF_CONTAINED`
- Installed product files: `368` copied plus `INSTALL_INFO.json` (`369` files total)
- Public `SKILL.md`: `1`
- Internal `MODULE.md`: `20`
- `.git`, `.mimosa`, `.pytest_cache`, `__pycache__`: `0` before validation
- Installed validator: `0 errors, 0 warnings`
- Installed full regression: `314 passed`
- Pollution after recommended validation: `0`

The same downloaded asset was installed into the Codex standard Skill path. The previous installed
copy was retained outside the discovery root at
`C:/Users/34718/.codex/skill-backups/enterprise-ai-project-delivery.backup-1788244299`.
Standard-path discovery remained `1 SKILL.md / 20 MODULE.md` with zero forbidden state directories.

## 4. Development regression — PASS

Frozen rc3 development evidence:

- Full suite: `314 passed`
- Validator: `0 errors, 0 warnings`
- Precommit self-contained install: `PASS`
- Installed validation after tests: `PASS`, pollution `0`

The count increased from rc1's 311 to rc2's 313 for prerelease version/build identity tests, then to
rc3's 314 for cache-safe installed-copy validation. No failing test was deleted to match an expected
count.

## 5. Fresh-session black-box — PASS

Three separate Codex tasks were used; the final task loaded the standard-path installed rc3 through
the real Codex Harness:

- Independent installed-copy audit task: `01a05ba3-be7f-7b82-96bd-2010273962a1`
- Real Harness task: `01a05bab-2eee-77a0-bfce-abe435cf85c4`
- Loaded Skill: `enterprise-ai-project-delivery 3.0.0-rc3`
- Loaded path: `C:/Users/34718/.codex/skills/enterprise-ai-project-delivery/SKILL.md`

| Case | Status | Fresh-Harness evidence |
| --- | --- | --- |
| A bounded simple task | PASS | Short visible plan; bounded file change completed continuously without invented scope |
| B ambiguous goal | PASS | Construction stopped for consequential clarification; after a real user reply, concise plan was approved, `todo.txt` was created and exact-content acceptance passed |
| C no-punctuation challenge | PASS | `你确定这个可以` remained a question/challenge, not approval |
| D user changes requirement | PASS | New authorized requirement took effect; affected work changed without restoring the old plan |
| E proactive capability | PASS | Minimum sufficient visible capability selected without asking the user to choose |
| F capability lifecycle | PASS | Temporary instruction/input/permission context ended before unrelated work |
| G recoverable failure | PASS | Original failure retained; root cause fixed; blocker and related regression rerun; execution continued |
| H repeated correction | PASS | Confirmed root-cause recurrence entered Recovery and required evidence, rather than another apology |
| I fake completion | PASS | Partial artifact and narrative claim could not satisfy unmet Acceptance |

Fresh-Harness artifact evidence:

- Acceptance report SHA-256: `a5e337490b0badeafc8a9bc292316d9333d8dce16ad479e1d1eece394db269f4`
- Case B `todo.txt` SHA-256: `d1e469396a13a9ec0216408dc7fd3010beca0de86ce163119adabb49ac94a422`
- Case B completion gate: `pass=true`, state `COMPLETED`
- Installed forbidden-directory count after the journey: `0`

## 6. Historical attacks — PASS

Replayed attacks covered:

- multiple public `SKILL.md` discovery pollution;
- public raw-facts injection around Understanding;
- forged, stale, wrong-work, and wrong-candidate Evidence;
- Question/Approval confusion;
- AI plan drift and fake partial replan;
- wrong or unauthorized Capability binding;
- installation backup pollution;
- `.mimosa`, `.pytest_cache`, `__pycache__`, and `.pyc` pollution;
- narrative or high-test-count fake completion.

All named attacks were blocked in the installed copy. The first independent task's A–I targeted
replay passed `9` selected cases and historical replay passed `17`; the rc3 independent task passed
`22` targeted cases plus `8` supplemental attacks before the real Harness journey.

## 7. Failed attempts and root-cause repairs

| Candidate | Status | Failure | Root-cause repair |
| --- | --- | --- | --- |
| rc1 | FAIL | Release declaration could not become an exact published identity; no reproducible formal asset entrypoint | Prerelease-aware version sync and immutable-tag `git archive` builder |
| rc2 | FAIL | Recommended post-install validation generated four `__pycache__` directories and 37 `.pyc` files | Cache-safe `validate_installed_copy.py`, no pytest cache provider, bytecode disabled, pre/post pollution gate |
| rc3 | PASS | Two Fresh Session commands initially used wrong test class names and one fixture caught the wrong exception type; each produced `no tests ran` or fixture failure, not a product PASS | Corrected the disposable acceptance fixture and reran the complete affected matrices; no product code change |

No rc tag or asset was overwritten after failure.

## 8. External pending items

- TRAE real Host behavior: `PENDING_EXTERNAL_VALIDATION`
- WorkBuddy/CodeBuddy enterprise Host behavior: `PENDING_EXTERNAL_VALIDATION`
- Claude Code execution in the previously tested invalid-auth environment:
  `PENDING_EXTERNAL_VALIDATION`
- Company-wide invisible Skill registry discovery: `NOT_INCLUDED_BY_DESIGN`
- Enterprise tenant/RBAC/database platform: `NOT_INCLUDED_BY_DESIGN`

These do not invalidate the verified Codex RC identity or tested Codex user journey, but they remain
explicit compatibility limitations and cannot be advertised as PASS.

## 9. Stable release recommendation — PASS

There is sufficient evidence to begin a separate immutable `v3.0.0` Stable release process from the
validated rc3 content. This is a recommendation that the frozen content qualifies; it is not a claim
that the Stable tag or Stable asset already exists.

Before declaring `v3.0.0 Stable` published, the Stable flow must still create its own exact commit/tag,
asset, SHA, GitHub publication, re-download identity check, clean installation, installed-copy
regression, and release closure. The pending non-Codex Harness items remain pending after Stable and
must not be silently promoted.

## Final three answers

1. Does GitHub `v3.0.0-rc1` have the final valid formal RC identity? `FAIL`. It was frozen but failed
   Release Validation and was superseded without moving its tag. GitHub `v3.0.0-rc3` is the valid,
   unambiguous formal RC: `PASS`.
2. Does the GitHub-downloaded formal installed copy still satisfy the Final Product Target? `PASS`
   for the verified Codex Harness and all locally executable Core commitments; named unavailable
   Harness compatibilities remain `PENDING_EXTERNAL_VALIDATION`.
3. Is there enough evidence to publish `v3.0.0 Stable`? `PASS` as a release recommendation. Stable
   itself is not yet published and must repeat the immutable release identity chain.
