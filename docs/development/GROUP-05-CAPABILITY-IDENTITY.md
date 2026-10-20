# Group 5 C1/C2 — universal capability and identity foundation

Local engineering candidate, 2026-10-20. **SOFTWARE_VERIFIED_LOCAL for the
documented synthetic scope; overall owner/provider rollout PARTIAL.** This is
neither universal PC/phone acceptance nor deployment. Ask is the sole active
authority mode. Gate C/D remain PARTIAL and Gate E NOT PASSED.

## Source, branch and architecture

The clean starting checkout was `codex/group-04-d2-connected-grid` at
`bd0102a9e933017b62f4caf23cfc5f88e04404c7`. The new local branch is
`codex/group-05-universal-capabilities`, based on that exact unmerged D2 candidate.
No remote push, PR creation, merge or GitHub Actions was performed. Published
PR #9/main state was not refreshed in this run; older D2 receipts are historical,
not a current GitHub claim. The final handoff records local commit IDs.

One Harness still composes Runtime, Controller, Executive, Grid, Personal Policy,
canonical Store and Event Archive. Account records and installation metadata use
that Store; neither is another task engine or competing capability catalog.
Connector Fabric feeds executable capabilities into the existing Grid. Auth Broker
owns credentials and verified provider identities; labels never grant authority.
BrowserProfiles owns private profile paths rather than accepting a path from a
tool request. Android adapters remain behind explicit native grants.

The D2 transport changes add signed connection-management requests and a bounded
metadata projection. They reuse its current authenticated session, owner key,
proof/signature checks and native review. They do not replace enrollment, TLS,
outbound file dispatch or D2 recovery semantics. This is the reviewed reason for
the additive D2 edits. The canonical Orb and approved native screen structure are
preserved; account/tools controls extend Desktop Preferences progressively.

## Inventory before and after

| Area | Starting foundation | Current candidate | Acceptance limit |
| --- | --- | --- | --- |
| Identity | Core relationship and per-device identity | Stable OSCAR operational/audit identity, owner relationship, optional email, service/workload and delegated account classes | No external OSCAR mailbox/account created |
| Accounts | CredentialRef and isolated provider flows | Provider/tenant/subject registry, arbitrary aliases/groups, defaults, explicit selection, generation/expiry/scope/org restrictions | Verified synthetic identities; real providers not enrolled |
| Auth | Gate B GitHub device flow and native vault | Shared PKCE/state/nonce/OIDC checks, refresh, account/service/audience-bound refs, native deletion | Provider consent/listener UI and real tenant policies not commissioned |
| MCP | Injected session/manifest boundary | Official SDK stdio and Streamable HTTP, reviewed discovery/tools/resources/prompts, cancel/timeout/reconnect, lifecycle CLI | Trusted local code only; remote provider OAuth interoperability not accepted |
| Browser | Typed ephemeral Playwright plan | Separate persistent account profiles, tabs/forms/select/upload/scroll/ARIA/screenshot/download | No owner Chrome attachment, arbitrary JS, authenticated/blob download or cookie export |
| Windows | Scoped files/Git/PowerShell/UIA | Existing typed app/process/window/element checks exercised against a real disposable WPF form | Broad arbitrary-app/visual control remains PARTIAL |
| Android | Native owner control and permission boundaries | Exact native action gate, launch/link/share and explicit app accessibility adapter | Emulator-only adapter acceptance; no production remote execution Worker |
| Native management | Devices and connection setup | Live Desktop identity/accounts/plugin health; signed rename/default/disable/connect/enable/remove review | New provider/server enrollment uses trusted backend/CLI, not a general self-service marketplace |
| Orchestration | Runtime/Executive/durable tasks | Existing runtime routes reviewed account-bound connectors and preserves evidence | No configured real model/provider or owner natural-language end-to-end acceptance |

See [Auth](GROUP-05-AUTH.md), [MCP](GROUP-05-MCP.md), and
[Android](GROUP-05-ANDROID.md) for detailed interfaces and source research.

## Identity, selection and authorization

Operational identity is an internal identity, not impersonation. OSCAR-owned and
owner-delegated credentials remain distinct. No label such as personal/work or an
email address acts as a security role. Same-provider, same-label accounts require
stable account identity or an eligible explicit default; material ambiguity denies.
Renaming never changes identity. Tenant/subject, credential ownership, audience,
scope, expiry, organization denial and generation are checked before dispatch
and independent connector readback. Scope withdrawal/disconnect fences old work.

Native management needs the existing owner-control grant, a short-lived exact
review and the enrolled owner signature. The reviewed state digest includes
current account/installation generation. Used challenges cannot replay or move
to another session. Provider tokens/profile locations are excluded from snapshots.
Local account disable and provider revocation are separate outcomes. MCP tool
annotations, prompt/resource text and model proposals cannot create permission.

Ask continues to apply to consequential actions. The Executor must recheck
target/session/account authority, rather than trusting model selection. Process
loss, missing grants and revoked/expired accounts withdraw executable eligibility.
Connector mutations are not retried automatically after ambiguous failure. Restart
loads installation metadata without autostarting tools or replaying writes.

## Browser decision and current official sources

Evaluated [Stealth Browser MCP](https://github.com/vibheksoni/stealth-browser-mcp)
(MIT), [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp)
(Apache-2.0), direct [Playwright Python](https://playwright.dev/python/docs/api/class-browsercontext)
and [Chromium CDP](https://chromedevtools.github.io/devtools-protocol/).
This is source review, not a performance/security benchmark or blanket endorsement.

| Criterion | Stealth Browser MCP | Playwright MCP | Chosen direct Playwright |
| --- | --- | --- | --- |
| Windows/runtime | Repository advertises Windows and Python/CDP | Official Node client/server; Windows browser support | Existing installed Python executor and real Windows Chromium acceptance |
| Sessions/profiles | Persistent CDP/browser functions advertised | Persistent/isolated context options documented | Stable account+generation profile key, private path, exclusive lock, new process per plan |
| Actions/observations | Broad CDP/script/browser surface | Accessibility-driven tools and screenshots | Fixed typed operations, DOM/ARIA observations and bounded artifacts |
| Upload/download | Broad browser/network functions | File/browser tool features documented | Scoped upload <=1 MB; anonymous anchor download <=1 MB, no auth export |
| Recovery | Requires independent acceptance | SDK/server lifecycle still needs OSCAR integration | Existing Worker cancel/timeout/process-tree handling; no write replay |
| Security integration | Would need review/restriction of script/cookie/network surface | Server origin options alone are not an OSCAR authorization boundary | Existing Grid/Personal Policy, exact origins checked for subresources/redirects, service workers blocked |
| Maintenance/resources | Community project; current support/performance not independently measured | Official Microsoft maintenance; extra Node/MCP process | Existing Playwright dependency, one temporary Chromium context; latency/RSS not benchmarked |
| Decision | Evaluated, not installed or vendored | Viable optional future adapter, not added | Smallest working extension of accepted executor |

No anti-bot evasion, hidden data extraction or credential copying was added.
The [official ARIA snapshot](https://playwright.dev/python/docs/aria-snapshots)
and [download](https://playwright.dev/python/docs/downloads) contracts informed
typed operations; browser-session cookies stay inside Chromium. A profile is not
an encrypted vault: on Windows its operator-controlled private directory ACL is
part of the deployment boundary. Browser profiles are disjoint from artifacts;
rename leaves sessions intact, while generation changes select a new profile.
Old profile bytes are not claimed erased on disconnect. POSIX symlink/private
mode checks are implemented but not exercised on a Linux host in this run.

MCP optional dependency is **2.3.0**, current stable protocol **2026-07-28**;
the actual negotiated fixture version is recorded. OAuth research uses
[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700),
[PKCE RFC 7636](https://www.rfc-editor.org/rfc/rfc7636), official provider/OIDC
documentation linked in the Auth report. Windows uses
[UI Automation security](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-security-overview)
and normal desktop rights; elevation/UAC, secure desktop, password fields and
uncooperative applications are not bypassed.

Actual local Python is **3.14.2**, Playwright **1.59.0**, Chromium package
**1217**, cryptography **46.0.3**. The existing manifest's optional browser/crypto
pins are newer; this run does not claim those different package builds were
tested. Rust default 1.97.1 could not build the existing minimum-1.99 dependencies;
the already installed **1.99.0** toolchain is used without lowering requirements.
Exact Desktop/Android dependency versions remain in their existing lock/build files.

## Observable acceptance and evidence limits

- Real OAuth HTTP fixtures issue signed OIDC identities; two account credentials
  execute independently after a fresh Python process restart using synthetic
  Windows Credential Manager entries. Only those run-created entries are deleted.
- MCP tests launch independent SDK server processes and a modern local HTTP
  server, invoke tools, access reviewed resources/prompts, verify independent file
  effects, reject schema drift and handle cancellation, timeout and process loss.
  A tool receipt remains REPORTED until the actual objective is checked.
- The existing Harness mounts Fabric executors on a separately enrolled Grid
  node with an explicit persisted permission ceiling. One linked synthetic
  research/workspace workflow selects two stable account IDs, reads an actual
  MCP knowledge tool, stops the write before RPC pending exact Executive Ask approval,
  writes via the second MCP process, independently verifies file bytes, and
  archives a native file artifact as a dependent step of the same reviewed
  Executive goal through the same Runtime. Canonical tasks,
  actions and evidence retain their identities. Wrong-account selection and a
  changed confirmation digest deny; disconnect withdraws capabilities and an
  explicit reconnect restores eligible tools. This is deterministic Core
  execution, not a live owner natural-language/model-provider session.
- Browser tests launch actual Chromium subprocesses, submit forms, select/upload,
  use tabs, inspect DOM/ARIA, save PNG/download bytes and reopen each of two
  account profiles. Alpha/beta HttpOnly sessions remain separate across launches.
  Revoked account binding denies access; fixture processes close after the run.
- Windows acceptance creates one disposable WPF application, observes its scoped
  UIA tree, checks process executable/window/PID binding, enters text with expected
  value fencing, invokes Submit and separately reads file bytes and updated UI.
  UIA Invoke is asynchronous: Runtime correctly retains PARTIALLY_VERIFIED when
  no application-specific completion verifier is configured. The external test
  waits for independently observed completion; it does not promote the Runtime
  receipt to VERIFIED. Changed PID is rejected, and only the fixture is closed.
- Android evidence uses a named disposable emulator and synthetic packages.
  Accessibility action service remains disabled unless explicitly enabled;
  adapter/JVM tests are not owner permission, physical or OEM acceptance.
- Native React projections/commands and Rust signed-review code have local tests;
  there is no new claim of owner visual approval or installed native GUI acceptance.

Initial failures are retained as failures: an early full Python run, while MCP
SDK/source integration was still changing, ran 799 tests with four MCP connection
errors and nine skips. Windows fixture iterations exposed missing classic
WinForms UIA patterns and asynchronous invocation before file readiness; the
fixture now uses WPF and independent readiness observation without weakening
production validation. Android monitor failures and their correction are recorded
in its report. Final receipts below supersede test counts, not failure history.
A later 25-test Fabric run had one MCP connection timeout while Gradle, Chromium
and native regression builds competed for host resources. Its failed receipt is
retained. A second focused run exposed the same fragile test setup: its two-second
configuration also constrained cold SDK initialization. The timeout test now uses
the existing default 15-second startup/RPC budget and a 30-second tool delay,
still requiring an actual `mcp_timeout`, successful subsequent lookup, cancellation
and reconnect. Production defaults and validation are unchanged. The 829-test
concurrent full run also failed Chromium launch preflight (one failure, 11 skips);
the subsequent quiet browser/Windows run passed all six checks. Neither failed
run is counted as a passing regression.
A subsequent 831-test run had one Windows fixture readback failure and nine
expected skips: the text field contained unexpected extra characters. UIA uses
ValuePattern, not keyboard injection; the source of the characters was not
conclusively established. The synthetic form previously opened as an active
dialog. Its corrected harness opens without activation/taskbar presence, rejects
keyboard focus and asserts initial focus/value before UIA writes. Both UIA task
receipts remain PARTIALLY_VERIFIED, with separate exact text/file/label checks.
The six browser/Windows checks then passed. This test-isolation correction is
not a claim that general owner-app interference or lifecycle causes are solved.

## Reproducible local verification

From the repository root, with the optional MCP/browser dependencies available:

```powershell
python -m unittest tests.test_accounts tests.test_auth_broker tests.test_connections -v
python -m unittest tests.test_mcp_client -v
python -m unittest tests.test_browser_profiles tests.test_windows_app_workflow -v
python -m unittest discover -s tests -t . -q
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
npm --prefix desktop test
npm --prefix desktop run build
cargo +1.99.0 test --manifest-path desktop/src-tauri/Cargo.toml
cargo +1.99.0 fmt --manifest-path desktop/src-tauri/Cargo.toml --check
cargo +1.99.0 clippy --manifest-path desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
python -m scripts.check_repository
```

Android exact-serial commands and API/platform assertions are in its report.
Never replace them with unspecified-device ADB or owner-phone testing.
The trusted MCP CLI preview/digest registration procedure is in the MCP report.
Do not enroll real accounts without separate commissioning authorization.

## Security review and unresolved limits

No confirmed unresolved critical/high defect was accepted within the tested
trusted-fixture boundary. This is an engineering self-review, not an independent
penetration-test or certification. Test negatives cover account confusion,
audience/scope/expiry, challenge replay/state drift/session substitution, schema
drift, path escapes, unsafe URL destinations, cancellation and generation fences.
Review also corrected a connect/removal race: a failed MCP connection cannot
restore a removed/replaced installation, and final registration rechecks the
current configuration and account inside the Store transaction. Signed management
commits its local authority fence before native-vault or MCP cleanup outside the
database lock. Native metadata projections omit credentials, executable paths
and full schemas, fit a fixed response budget and explicitly report truncation.
MCP instances now carry their reviewed stable account ID/generation into canonical
connector audit records. Their trusted transport still owns private session
authorization; a server response cannot choose or replace that identity.

The following remain real acceptance gaps:

| Severity / classification | Limit | Required next evidence |
| --- | --- | --- |
| High if exposed to hostile local plugins; outside current trusted-code boundary | Stdio servers execute with user OS rights; SDK framing is not a hostile-code memory sandbox | Hardened process isolation/resource admission before untrusted plugin installation |
| High if advertised as remotely executable; currently explicitly unavailable | Android native adapters lack production Core authorization/dispatch/result/readback transport | Existing Grid Worker integration and signed effect verification before capability advertisement |
| Medium / usability | Self-service new provider consent and new plugin registration UI are not complete; trusted setup/CLI is used | Configured provider/app registration and reviewed native enrollment flow |
| Medium / evidence | Broad Windows apps, arbitrary screenshots/visual targeting and natural-language live model workflows are not accepted | Application-specific real owner tasks and reliable outcome observers |
| Medium / deployment | Browser profile ACLs, Linux writable vault and public MCP OAuth are uncommissioned | Exact-host isolation, refresh/revocation and restore review |
| Low / hygiene | Existing HTTP-error tests emit ResourceWarning cleanup messages | Close test HTTPError handles without hiding denied-response evidence |

Provider remote revocation, organization policy and consent behavior remain
UNKNOWN until authoritative provider readback. Removed metadata/tokens are not
claimed securely erased from WAL/backups. No raw private content or credentials
are included in tracked fixtures, snapshots or this report.

## C3 handoff — genuine signed delegation

Do not activate Secure/Full Access by hiding Ask. C3 must implement an owner-signed
standing-delegation contract that pins relationship/operational identity, owner
key, account IDs/generations, node/session, capability/schema revision, data/resource
scope, allowed effects, risk ceiling, expiry and policy revision. Include a
monotonic **authority epoch** and independent revocation generation, with explicit
issuer and provenance. Unsigned model/Worker proposals never create authority.

Core commits revocation before cleanup and distributes epochs to each executing
node. Targets independently verify signature, current epoch, expiry, capability,
account and OS/provider permissions at dispatch and meaningful action boundaries.
Offline nodes fail closed after bounded authority freshness; reconnect cannot
restore old grants. Cancel leases and stale confirmations on revocation/rotation.
Record in-flight effects as uncertain until readback; do not replay mutations.
Test partition, delayed/reordered grants, clock skew, stale restore, concurrent
revocation, scope withdrawal, task cancellation and compromised remote requests.

Full Access means no OSCAR per-action prompt within valid delegated authority;
external mandatory approvals, OS restrictions, provenance, retention/perception
separation and deterministic physical safety remain. Independent adversarial
verification and owner activation/recovery UI are acceptance gates. Current
account/task/native generation checks are hooks, not a standing grant or C3 PASS.

## C4 handoff — portable voice, awareness and Workers

Voice Input, OSCAR Voice Identity, Voice Match and Voice Map remain separate.
Portable adapters must use the same task/context/relationship and model/capability
routing, preserve TTS exclusion and human barge-in, and prove cancellation and
device/provider loss. No microphone was captured in this run. Real owner audio,
speaker ambiguity, wake/VAD/STT/TTS, AEC and OEM background behavior need separate
permission and measured evidence.

Sentry perception, durable retention and action authority require independent
grants and expiry. Chief of Staff must consume timestamped source-backed current
context, express uncertainty, respect attention and independently read back every
schedule/message mutation. Calendar/mail account selection must use stable Auth
Fabric identity rather than an alias. Native Android background/Accessibility and
distribution policy restrictions must be resolved before advertising autonomy.

Autonomous Workers remain existing Executive/Durable Runtime Workers. They use
C3 signed scopes/epochs, exact reviewed capabilities, budgets/deadlines, memory
preflight and canonical event provenance. Test restart/lease expiry, duplicate
dispatch, unavailable accounts/devices, cancellation, readback disagreement and
revocation across every executor. Do not introduce another scheduler or model-owned
memory truth. Oracle/owner commissioning and scoped operational-alpha acceptance
remain separate, later owner decisions.

## Final local receipts

| Check | Local result |
| --- | --- |
| Complete Python regression | **831 tests: 822 passed, 9 intentional skips, zero failures/errors**, 506.926 s; `.oscar/group05-brain-verified.log`, implementation head `49563989a02d688e764f63a25b0abfcf4c2375df` |
| Auth/account focused | 22 passed, no skips; expanded provider/vault regression 95 tests with 1 POSIX skip |
| MCP/native management/mount | 25 passed, no skips before the final provenance/workflow extension; final regression includes the extension |
| Real browser and Windows application | 6 passed, no skips; actual Chromium and owned WPF processes |
| Desktop React | 96 passed in 18 files; final TypeScript/Vite production build passed |
| Native Rust | 23 passed, no failed/ignored; rustfmt and Clippy with warnings denied passed on installed Rust 1.99.0 |
| Android JVM | 52 passed, zero skipped |
| Android build | lintDebug, assembleDebug, assembleDebugAndroidTest passed |
| Android instrumentation | 7 passed, zero failed/skipped; EMULATED_SYNTHETIC API 35, exact AVD and serial above |
| Python static checks | Ruff and format passed (218 Python files); mypy passed (87 source files) |
| Repository | Required files, local Markdown links, removed references and value-silent secret scan passed; staged whitespace check passed |
| CI / hosted / owner-provider / physical | NOT_RUN; no push, Actions, PR, merge or commissioning |

The nine intentional Python skips are:

- `CloudEnrollmentTests.test_symlink_and_replaced_parent_do_not_redirect_private_output`
  and `test_unwritable_or_shared_parent_rejected_before_authorization`: POSIX descriptor/directory checks on Windows.
- `CloudPlatformTests.test_private_modes_and_regular_files_required`: POSIX owner/mode checks on Windows.
- `LocalVoiceModelTests.test_real_embedding_self_output_denial`,
  `test_real_local_stt_and_cancellation`, `test_real_local_wake_vad_and_no_wake_silence`,
  `test_wasapi_shared_format_without_opening_audio`, and
  `test_windows_synthesis_interrupted_at_chunk_boundary`: optional local voice executors not requested.
- `NeuralReferenceTests.test_prepared_neural_response_and_cancel`: optional prepared neural executor not requested.

Raw receipts are ignored local files under `.oscar/group05-*` and
`.oscar/group05/`; all test content is synthetic. These counts overlap the full
suite and must not be added together as unique tests. Implementation commits:

- `f0bc8af6f24de5e59e9d88251e52171d65a0b062` — account/Auth Fabric, MCP lifecycle,
  browser profiles, canonical Runtime integration, native management backend and
  synthetic executable acceptance.
- `ca3baef53834416b1662248b107cd8c4a6033619` — existing Desktop Preferences and
  signed owner-management transport.
- `7bec2ca4102eddb7bf282e9fc44a6896f96b5d0d` — Android native admission/grants,
  disposable fixtures and exact-emulator acceptance harness.
- `49563989a02d688e764f63a25b0abfcf4c2375df` — synthetic Windows UIA fixture does not activate or accept keyboard
  focus; initial value/focus and reported-task state remain asserted.

The following documentation-only commit contains this ledger and canonical status
updates. Its exact SHA and the final clean-tree result are included in the final
handoff and ignored `.oscar/group05-final.json`, avoiding a self-referencing Git
hash in this document. This section makes no final-head CI claim.
