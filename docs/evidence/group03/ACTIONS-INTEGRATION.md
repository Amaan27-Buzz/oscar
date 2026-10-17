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
