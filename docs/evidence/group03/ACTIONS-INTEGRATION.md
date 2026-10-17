# Group 3 Actions integration - 2026-10-17

Owner authorization enables repository Actions and permits PR #7 integration
only after genuine final-head green CI. No CI waiver is authorized. Gate C and
Gate D remain **PARTIAL** regardless of software integration.

## Repository settings and trigger

Fresh preflight matched local, remote and PR head
`16c659498c0f101bbaa6bccbf8e2cf3b59159a61`, with clean working tree and main
`257349f82a96293c3737d446dca18ce46f098b04`. No intervening commits, comments,
reviews, review threads or merge conflicts were present. Main had no protection,
required check contexts or rulesets; the owner's CI condition still applies.

Actions changed from `enabled: false` to `enabled: true`, `allowed_actions:
selected`. Readback confirmed the exact existing workflow action/ref allowlist:

- `actions/checkout@v4`
- `actions/setup-java@v4`
- `actions/setup-node@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
- `android-actions/setup-android@v3`
- `dtolnay/rust-toolchain@stable`
- `lycheeverse/lychee-action@v2`
- `reactivecircus/android-emulator-runner@v2`

No unrestricted GitHub-owned or verified-publisher category was enabled.
The referenced action manifests had no additional nested action dependencies.
Workflow token default remains `read`, approval of PR reviews remains disabled,
and the existing SHA-pinning setting remains unchanged. No organization, account,
billing-plan, budget, credential-scope or unrelated repository setting changed.

The authenticated API did not expose the account plan. Billing usage endpoints
returned HTTP 404 with a missing `user`-scope diagnostic. No credential permission
was requested. Self-hosted runner count was zero; subsequent actual hosted-runner
execution establishes current eligibility, not remaining quota or future capacity.

The eight registered workflows have PR triggers and no draft exclusion. With no
manual dispatch trigger, the same draft PR was briefly closed and reopened to
emit `pull_request: reopened`. Its head, branch, discussion and evidence were
preserved. GitHub created eight workflows for the exact reviewed SHA. Individual
job results and final integration/merge receipt are recorded in PR #7; a queued,
cancelled or skipped job is never recorded as a pass.

## First genuine CI findings

| Finding | Classification | Correction and proof |
|---|---|---|
| Brain Linux full suite lacked `cryptography`; Windows matrix sibling was cancelled by fail-fast | Workflow dependency configuration | Install the existing pinned `mobile` extra alongside `dev`, matching Desktop/Mobile workflows. No dependency version or test assertion changed. |
| Simulated-day integration expected 25 completed occurrences but observed 19 | Test-clock synchronization | Wait for every due hourly occurrence before advancing the artificial clock; retain all 25 executions, source-loss, freshness, idle, archive and verification assertions. The test previously allowed a live background task's lease to expire during an instantaneous artificial jump. |
| Historical PR/run links under the retired original repository returned 404 | Documentation provenance | Retain the original URLs verbatim as labeled historical identifiers; do not replace them with unrelated current run IDs or claim they are live evidence. |
| Local preview URL was checked without a local development server | Documentation example | Show the local address as a command/example and explicitly require starting its server. |
| Google Little Signals research URL had invalid TLS hostname | External reference | Use the authoritative `experiments.withgoogle.com/little-signals` page; HTTP 200 verified without disabling TLS validation. |
| Emulated Expression atlas capture timed out in AndroidX's two-second frame-commit wait | Instrumentation readiness / runner environment | Compile APKs before emulator startup, require the fixture window to have focus before capture, retain all rendering/contract assertions and upload instrumentation reports. Logs do not establish a production renderer defect; the actual rerun must verify the correction. |
| Desktop native build passed but the disposable WPF field did not emit `ContentRendered` within 60 seconds | Native fixture / hosted rendering environment | Select process-local software rendering for this fixture, retain its stderr and report non-secret session/render diagnostics. Keep `ContentRendered`, independent UIA readback and native signing requirements intact. A hosted rerun must establish whether this resolves readiness. |
| Second-round Linux Python 3.12 full regression passed (684 tests, 36 platform/optional skips), then repository validation rejected an owner-local Windows generation record | Documentation portability | Preserve the exact provenance path as an explicitly local identifier, not a portable repository hyperlink. Validate relative links against the case-sensitive tracked Git tree as well as the Windows filesystem. The repository checker and test assertions remain unchanged. |
| Second-round emulator exited before instrumentation: `Available: 6789.79 MB`, `need 7372.80 MB` for its default userdata partition | Hosted runner disk capacity | Bound the disposable AVD userdata partition to 2,048 MiB, sufficient for the application and isolated fixtures, rather than deleting host SDKs or buying a larger runner. Bound boot wait to 300 seconds; actual instrumentation must still run and pass. This failure did not test the atlas correction. |

Local verification of the initial corrections: three Group 3 composition/crash
tests passed; the simulated-day test also retained all 25 occurrences at four
interpreter thread-switch intervals. Ruff, formatting, strict mypy and
repository/secret checks passed.
The same Lychee v0.24.2 version as CI checked all affected documents: **76 links,
zero errors**. Its isolated Windows binary was checked against the release asset
SHA-256; no runtime dependency or host installation was introduced.
The instrumentation readiness correction also passed local Android JVM tests,
APK/AndroidTest assembly and lint; the application APK and canonical Orb hashes
remain identical. Actual emulator success still requires the hosted rerun.
The revised WPF fixture passed the actual local Tauri self-check, including CNG
signing, registered-application readback, cancellation, reconnect and native
restart with shared Core tasks. This is Windows reference evidence; hosted
readiness and owner/physical acceptance remain separate.
The second hosted Desktop workflow subsequently passed all stages, including 86
frontend and 16 Rust tests, Tauri CNG/signing/readback/restart and standalone
Windows UIA verification. Emulator boot failure remains distinct from test failure.

No production Core, native UI/artwork, authorization, replay/expiry checks,
verification or idempotency behavior changed in these corrections. Earlier
closure receipts and benchmarks remain historical, intact and applicable to
their recorded source. Expensive benchmarks are not rerun for test/workflow/docs
corrections. Any subsequent actual CI finding must be diagnosed independently.

## Acceptance boundary

Only terminal successful final-head workflows permit software integration.
Physical Edge, owner audio/voice/biometric/provider commissioning, real Android
foreground-service/OEM/accessibility, live environmental Sentry, sustained
real-world operation, widgets/native schedule authoring, genuine standing Full
Access and production deployment/release remain deferred or unavailable.
Emulated instrumentation and firmware cross-builds do not establish physical PASS.
Group 4 implementation and post-alpha optimization are outside this run.
