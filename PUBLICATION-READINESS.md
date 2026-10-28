# Publication readiness - 2026-10-28

**Publication clearance: BLOCKED pending rights/privacy review. Repository is
PUBLIC by owner choice; the owner subsequently authorized this branch push.**

No actual secret, live credential, private key, browser session or personal
conversation archive was confirmed by this audit. That is a scoped finding, not
proof that every historical screenshot, author identity or asset is publishable.
Do not change repository visibility, rewrite history or merge as part of closeout.

## Scope and reproducible evidence

Starting implementation HEAD: `aa3dc6051e80c8ac9a4919159d0cdcb7c6c91852`, branch
`codex/software-completion`. Fetched all advertised origin branch/tag refs, then
inventoried all local/fetched refs: **583 commits, 3,235 tree objects, 6,037 unique
blobs**, 291,497,463 object bytes examined. The working tree began clean with
3,218 tracked paths. All reachable blob/commit/tag bytes were inspected by the
independent value-silent pattern/metadata inventory, including deleted historical
content. It is not just a current-tree `.env` check.

Gitleaks **8.30.1**, official upstream Windows x64 release, archive SHA-256
`d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`,
verified against GitHub release asset metadata before execution:

```powershell
git fetch origin --prune
gitleaks git . --log-opts="--all --full-history" --redact=100 --report-format=json --report-path=LOCAL_IGNORED_REPORT.json --no-banner
```

Gitleaks scanned 565 patch-bearing commits / 15.56 MB, exited 1 and reported
**1,014 matches**. This is not a clean scanner exit. Triage resolved **1,009**
source/artifact SHA-256 entries (including filenames containing `sentry`) and
**five** multiline false positives: four pairs of blank `.env.example` variables
at historical commits `7e77baf`/`2542514`, and ordinary documentation prose at
`b700a6c` (`GROUP-05-CAPABILITY-IDENTITY.md:26-27`). No match was treated as safe
merely because it was called a fixture. Underlying historical lines were checked.
The independent inventory additionally checked private-key headers, provider-token
forms, JWT forms, credential assignments, home paths, email-shaped content,
private-material markers, binary formats and object sizes. Credential assignments
were confirmed synthetic test/reference inputs; provider-token-shaped matches
were task-attention filenames/test tags. No private-key/JWT match was found.

Raw redacted scanner reports, triage and metadata inventory remain ignored in
`.oscar/closeout/`. No scanner executable, archive, raw audit log or generated
runtime/test artifact is added by this closeout. This report and the requested
continuation/ledger documents are the committed audit output. The final staged
closeout diff (eight documentation files, approximately 783 KB) was additionally
scanned with Gitleaks `git --pre-commit --staged --redact=100`: exit 0, no leaks.
Repository link and value-silent secret checks also pass.

## Findings and required disposition

| ID / severity | Finding and evidence | Required owner action before public release |
| --- | --- | --- |
| PUB-001 HIGH, public blocker | No repository-wide license/explicit public distribution grant was found. OSCAR and Dawnlight Labs ownership/contributor rights have not been certified. | Confirm publication authority for all company/contributor material; choose and add the intended project license or explicit proprietary public-source terms. Do not infer ownership from Git authorship. |
| PUB-002 HIGH, public blocker | Large existing visual/design/evidence collections include generated originals, owner-selected references and motion captures. Provenance is described in `design/oscar-mobile-visual-exploration/README.md` and `assets/brand/README.md`, but it is not a complete redistribution-rights register. Third-party references in `docs/design/expression/RESEARCH.md` are links/principle studies, not proof that all historical media is cleared. | Review and approve assets, supplied reference material, prompts and every retained media collection. Confirm generator/reference rights and remove/replace restricted material through separately approved remediation if necessary. |
| PUB-003 MEDIUM, public blocker pending review | Current Manrope/Fraunces OFL and CommonMark notices exist in `mobile/font-licenses/` and `mobile/third-party-licenses/`. Reachable history additionally contains `assets/fonts/source_sans_3.ttf` and `source_serif_4.ttf`; no matching repository notice was found for those historical files. The Gradle wrapper JAR is the only executable-style binary found; it is a build prerequisite, not an application release. | Verify historical font/wrapper provenance and redistribution notices across all refs that will become public. A current-tree deletion does not remove the historical objects. Keep existing notices. |
| PUB-004 MEDIUM, privacy review required | Historical and current documentation contains owner home/workspace paths, local tool/generation paths, UUIDs and two distinct non-noreply author email identities in commit metadata. Examples: `docs/development/SOFTWARE-ANDROID-PLATFORM-CONSENT.md`, `docs/evidence/software-completion/browser-workflow-2026-10-23.json`, `docs/ui/mobile/completion/evidence/raw-archive.json`, `docs/design/CROSS-PLATFORM-STORAGE.md`. Local provenance records referenced by docs are not available on GitHub. | Decide which identifying details may be public. Review screenshots/video for incidental private content; approve any history cleanup separately. Do not publish owner-local archives to repair broken provenance links. |
| PUB-005 MEDIUM, supply-chain hardening | Nine current workflows declare `contents: read`; no `pull_request_target`, write-all token, referenced repository secrets or `id-token: write` found. External actions use moving version tags (including `@stable`); checkout retains its default credentials behavior. Repository settings allow an explicit action list, default read tokens, no PR-review approval, and no mandatory SHA pinning. | Pin reviewed action commit SHAs and consider `persist-credentials: false` before public contributions; review dependency/update policy. Do not weaken protected branches. |
| PUB-006 MEDIUM, automated coverage gap | GitHub reports secret scanning disabled (alerts API 404 with that reason). Repository Actions secret list is empty and there are no environments; secret values are never readable or audited here. No exhaustive dependency-vulnerability audit or SBOM/license certification was performed. | Enable appropriate secret scanning/push protection/private reporting and review dependency security/licenses. Re-run the local history audit after any remediation and before further publication. |
| PUB-007 INFO, confirmed false positives | All 1,014 Gitleaks findings were triaged as hashes, empty example assignments or prose. Independent credential-assignment findings are synthetic test/reference values. | Keep future scanners enabled. Do not add blanket path/rule ignores just to hide this report. |

## Binary, data and research assessment

All 6,037 unique reachable blobs were inventoried. Detected binary formats are
PNG/JPEG/icons, GIF/MP4 evidence, seven unique font blobs and one Gradle wrapper
JAR. Current tracked paths contain 2,171 detected binary files (duplicate blobs
can have multiple paths). The largest reachable blob is about 2.06 MB, a mobile
illustration. No committed database, account cookie/session export, model weights,
raw audio, APK/EXE/DLL release or dataset archive was identified by object/name/
format review. This is not a malware, steganography, forensic or complete OCR
review; selected native contact-sheet/desktop captures were visually inspected
and showed synthetic/reference UI. Existing media is preserved, not newly added.

Private/proprietary/unpublished keyword findings were reviewed as security policy,
ordinary product documentation or linked public animation/library research. No
specific unpublished third-party research payload was confirmed. **The owner
must still approve Dawnlight Labs material for public disclosure**; absence of a
keyword or scanner hit cannot establish contractual rights/confidentiality.

Excluded: unadvertised GitHub refs, reflog-only/unreachable objects, external
release/Actions artifacts, unavailable external provenance archives, service
secrets/host credentials, private local runtime state and semantic review of every
image/video. No LFS pointers or submodule payloads were identified in tracked
attributes/inventory. Public visibility may also expose issues/PRs/artifacts;
review those separately. No legal/commercial clearance is asserted.

## GitHub handling and final checks

Repository `Amaan27-Buzz/oscar` initially reported **private** through the
connected API, then **public**, independently confirmed with `gh api`. The owner
confirmed changing visibility and explicitly requested publication of this branch.
No visibility change was made by this closeout. Draft D2 [PR #9](https://github.com/Amaan27-Buzz/oscar/pull/9)
is open/unmerged at `bd0102a9e933017b62f4caf23cfc5f88e04404c7`; main is
`36c3883377cc0e29b25e095bf53caa6a09f902ae`. Both are preserved. The current
software branch retains D2 ancestry and previously had no remote branch.

The latest owner instruction authorizes a normal public push of
`codex/software-completion` after checks. This does not certify licensing, media
rights or privacy clearance: PUB-001 through PUB-006 remain open. No actual
credential or sensitive research exposure was confirmed. Existing
workflows filter pushes to main/work and pull requests, so this new branch push
without a new PR should not start Actions. Verify remote HEAD equality and exact
SHA Actions status afterwards. Do not create another PR, change PR #9, merge,
force-push, alter visibility or rewrite any history.

If later review identifies an actual secret or restricted research payload,
stop publication, revoke/rotate the credential where applicable and obtain
explicit approval for coordinated history remediation. No destructive surgery
was performed. See [session state](docs/development/OSCAR-SESSION-STATE.md) and
[continuation](docs/development/OSCAR-CONTINUATION.md) for source/test limitations.
