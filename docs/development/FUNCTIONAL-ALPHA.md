# Functional alpha — active implementation

Development continues on the consolidated `main` checkout. This is an implementation
checkpoint, not full alpha acceptance or a release claim.

## Everyday Desktop — verified-free cloud inference

From the repository in PowerShell:

```powershell
python -m pip install -e ".[desktop]"
python -m scripts.build_desktop
python -m scripts.start_oscar
```

The owner initially requested cloud inference only, then explicitly authorized
installed local inference and full local compute. The everyday launcher supports
available local models alongside verified-free cloud routes; paid fallback remains
disabled. To check live cloud inference:

```powershell
python -m scripts.start_oscar --check --provider openrouter
```

Preferences → Intelligence offers automatic verified-free routing and available
cloud and installed local models. Selection is persisted. Optional `--provider` and `--model` pins
override it for a launch. Eligibility requires current live zero-price evidence;
cached free labels, subscriptions and unknown cloud pricing cannot qualify.
Explicitly permitted local inference is a separate routing class.
No provider quotas are invented or multiplied by the number of keys. Groq/Gemini
free plans require account-specific evidence; a general free-tier advertisement
does not prove that a particular key cannot incur charges.

The launcher starts the existing Core, Controller, Router, Event Archive, Memory
Fabric and Executive. State lives under `%LOCALAPPDATA%\DawnlightLabs\OSCAR`;
Workspace and Companion use authenticated loopback with an anonymous-pipe bootstrap.
No credential files are created. The owner's restored `.env.local` is read only
through a bounded compatibility loader into the existing opaque credential pool.
It remains unchanged, ignored and untracked. Only registered provider variables
are accepted; shell execution, interpolation and copying secrets into the process
environment are disabled. New provider setup uses the existing OS Vault paths.
A data-directory lock prevents concurrent Core writers.
Missing provider bindings are imported into Windows Credential Manager through
SetupRuntime. Existing or revoked bindings are never overwritten or reactivated.
This lets a packaged alpha use the same secure configuration without copying the
project credential file into its distribution.

Cloud inference transmits entered messages and relevant conversation context to
the selected provider. It does not grant microphone, screen or clipboard access.

Conversation retention is enabled for this local owner surface, as requested by the
functional-alpha mandate. Quit OSCAR through Preferences or the tray to stop the
Desktop and its launcher-owned Core. Closing Workspace alone leaves the tray active.
Keep the data directory to preserve history across source rebuilds and upgrades.

The everyday launcher also mounts the existing local Windows Worker into this Core.
Preferences → Advanced controls → Direct device operations exposes its supported
file, Git, installed-program version and typed PowerShell operations. Files are
scoped to OSCAR's data workspace. Each consequential action still goes through
signed Ask review; this does not activate owner Full Access. Installed application
launches require separately allowed app IDs. No microphone, clipboard, screenshot
or retained-screen grant is automatically enrolled.

## Evidence on 2026-11-05

The local-inference receipts below are historical. They are not the current launch
policy and do not authorize further local inference.

- Windows debug executable built; actual Workspace accessibility state showed Connected.
- Real local inference completed through the existing Router using `qwen3.5:0.8b`.
- `python -m scripts.alpha_conversation_acceptance` passed signed Desktop admission,
  real model response, local model selection persistence, and canonical conversation
  recovery after Core restart, using disposable synthetic history.
- Focused history, setup and launcher enrollment tests passed, including refusal to
  reactivate revoked enrollment and invalidation of the previous Desktop session.
- TypeScript checking, Workspace tests and native Rust checking passed.
- Full Python typecheck passed (108 modules); focused Desktop/history/setup/launcher
  regression batch passed. Android debug APK, unit tests and lint built successfully
  at `mobile/app/build/outputs/apk/debug/app-debug.apk`; emulator shared-Core
  acceptance has not yet run.
- The actual local Worker performed a signed, disposable file write and a typed
  PowerShell UTF-8 write with independent byte readback. Neither mutation ran
  before approval. This does not establish broad visual computer-use acceptance.

Full GUI message/selection acceptance remains unverified. This is a development
executable, not a self-contained installer. Broader native execution, Workers,
Android shared-state acceptance, voice, cinematic onboarding, Setup Studio and
packaging remain in progress. Existing reference launchers remain synthetic and
separate; their results do not commission real providers or physical devices.

## Cloud continuation — 2026-11-06

- Actual verified-free OpenRouter inference completed through OSCAR's Router.
- Signed Desktop cloud conversation, a model-backed follow-up, model selection,
  and recovery of four retained turns after Core restart passed with synthetic data.
- Existing configuration remained byte-for-byte unchanged after loading.
- Router tests cover rejection of unknown, paid, subscription and local funding;
  configuration tests cover no writes, no interpolation and no process-env mutation.
- Planning requests now use constrained output when an eligible route supports it;
  101 focused planning/catalog/verification regressions passed. This is not yet
  broad provider commissioning.
- `python -m scripts.alpha_planning_acceptance` passed real verified-free cloud
  two-step Worker planning, an actual result handoff, two signed Ask reviews and
  independent verification of both steps and the saved file. All data and owner
  signing identities were disposable synthetic fixtures.

During this development run, check Codex's five-hour allowance and issue a
consolidated owner progress report when it reaches 50% remaining. This is a
reporting checkpoint, not a change to alpha completion criteria.

## First run, additional free providers and packaging — active continuation

- The first-run introduction is integrated with Core preferences, current model
  selection and the actual Workspace request path. Skip/replay, resume, reduced
  motion and optional muted-by-default introduction audio are implemented. Name
  and tone affect conversational expression, never authority or verification.
- Core and UI tests cover preference persistence, real request handoff and offline
  skip. The native first frame was inspected; a layout collision was corrected.
  Later verification runs in the background at the owner's request. Full rendered
  flow, motion and owner approval remain unverified.
- The owner confirmed all configured keys use Free plans with billing disabled.
  Plan confirmations are tied to current Vault bindings, expire after 24 hours,
  and do not survive credential replacement or revocation. Preferences and first
  run expose explicit renewal. Official free pricing and live model availability
  remain separate requirements. Pricing evidence expiry can temporarily exclude
  a provider until refreshed; OpenRouter's live zero-price inventory remains a
  fallback, subject to its actual account limits.
- Gemini `gemini-3.5-flash-lite` and Groq `openai/gpt-oss-120b` completed real
  inference. Both also passed the signed two-step Worker/result-handoff check.
  Gemini's first planning attempt failed safely, then the repeat passed; broad
  planning reliability is not established. `gemini-3.8-flash` is listed by the
  current API but this account's generation check returned HTTP 403; it is not
  claimed operational.
- A roughly 61 MB Windows bundle from clean commit `aef309f` contains the frozen
  Core, Desktop and Companion. The actual frozen executable passed Gemini
  Flash-Lite inference outside the checkout using existing Windows Vault bindings.
  No configuration secrets or user databases are bundled. Full packaged GUI and
  owner acceptance remain outstanding. Packaging: `python -m scripts.package_alpha`.

No computer-use interactions are to be performed during the current background
continuation. No physical phone, real capture, paid inference or local reasoning
model is authorized by this continuation.

## Shared everyday Core — 2026-11-06

The everyday launcher now composes the existing CloudCore and authenticated v2
Grid listener with the same Harness, canonical databases and local Windows Vault.
The listener binds only to `127.0.0.1:8765`; this does not deploy a Cloud Core or
enable a production phone's HTTPS connection. Existing Desktop v1 admission remains.
Explicit local-state adoption validates both databases and the existing owner/Core
identity before adding deployment identity metadata. It never resets enrollment.

Desktop projects retained phone turns from the same Event Archive. Android Grid
history pairs retained Desktop requests and answers by task ID, including older
events whose independently generated turn IDs differed. Canonical events are not
rewritten. Forgotten source requests suppress dependent answer projection.

Background service mode is available with `python -m scripts.start_oscar --headless`.
For a supervising process, add `--stop-on-stdin-close` and provide an anonymous stdin
pipe; closing that pipe shuts down the owned listener, services and state lock.
The actual persistent Core passed loopback health and clean exit (code 0), without
opening Desktop. Real Gemini inference passed after adoption; comparisons confirmed
unchanged owner identity, Vault bindings, pre-existing archive events and ignored
`.env.local`. Focused Cloud/state/launcher tests (45) and Desktop/Grid history tests
(42) passed; full Python typechecking passed (110 modules including the launcher).
These changes still need a rebuilt bundle and integrated Android acceptance.

The installed API 35 system-image directory is empty; the API 36.1 Play Store image
is present. No AVD is configured. Earlier directory-only inspection did not establish
an installed API 35 image. No physical Android device has been accessed.

The requested quota report was delivered at the next observed checkpoint: 38%
five-hour allowance remaining (previous observation 60%). The exact 50% crossing
was not observed. This checkpoint does not imply alpha completion.

### Packaged background verification and emulator boundary

The shared-Core Windows bundle passed real Gemini Flash-Lite inference from outside
the checkout. Its frozen headless Core/Grid passed loopback health and closed its
owned services with exit code 0 on stdin-pipe closure. The runtime comes from
`7a26f5a`; a concurrent test-runner-only edit means this build's manifest honestly
records a dirty working tree. Full native UI/owner acceptance remains outstanding.

Created one disposable `oscar_functional_alpha_api36_1` AVD from the already
installed API 36.1 image, with no window, audio or cameras. It booted and accepted
both APKs, but instrumentation was aborted by Android's SurfaceFlinger graphics
crash (`GoldfishMapper`, `hasReadColorBufferDma`). Reusing the same AVD with
SwiftShader still produced that system crash. The owned emulator was stopped;
native Keystore/Grid runtime acceptance is BLOCKED for this image/emulator
combination, not passed. No physical serial was queried or operated.

The existing Grid acceptance runner now permits an exact `--avd` guard, checks
boot completion, and addresses only the explicit emulator serial. It no longer
enumerates unrelated ADB devices. No OSCAR permission or transport security was
weakened to accommodate this environment failure.

## Shared model preferences — active continuation

Android Preferences now includes Models. It reads the same Core selection and
eligible routes as Desktop, supports Automatic for free-only routing, preserves an
unavailable selection visibly, and refreshes authoritative state after a change.
Model selection is implemented once in `oscar/model_preferences.py` and reused by
both surface adapters; it never changes the executor's routing policy. The everyday
launcher's existing persistence restores the shared selection on restart.

Remote selection requires a current enrolled owner binding, `grid:approve` and
`models` scopes, and Personal Policy approval. Ordinary paired observers cannot
change it. Android clears model controls with private-state suppression, and
does not optimistically announce a mutation as confirmed. No provider secrets or
local-model fallback were added. The native page extends the existing Preferences
component system; rendered/device acceptance remains unverified.

Focused Desktop/Grid/launcher regressions passed (62 tests); the added owner,
policy-denial and unavailable-selection check also passed. Python typechecking
passed (111 modules). Android unit tests cover bounded/malformed model projections
and preservation of an unavailable choice. Android unit tests, debug APK,
instrumentation APK and lint passed after the final privacy guard. The debug APK
SHA-256 is `2c19226fb7a66e1962fda3bd220058e30d04802dd4214c046d2e8096b865dd04`.
The Windows ZIP was rebuilt from clean `614e47a` and its actual frozen executable
passed real Gemini Flash-Lite inference outside the checkout using Windows Vault.
No device acceptance is implied. At this checkpoint provider-key entry still used
the restored configuration and secure Vault bindings; the integration below adds
application entry without replacing existing credentials.

## Secure provider entry in the application — active continuation

First run and Preferences → Intelligence now offer Add provider key for an
unconfigured cloud credential slot. The password field sends through the existing
authenticated native/Core path into SetupRuntime and Windows Credential Manager.
No plaintext credential file, conversation event or raw-key database record is
created. Entry requires current owner control scope and Personal Policy approval.
Present credentials cannot be overwritten by this operation. No restored
configuration values were edited or existing real Vault bindings replaced during
development or testing.

The field clears before awaiting admission, on cancellation and on connection
changes. Saving is described as configuration, not verified inference; Gemini/Groq
free-plan confirmation remains separate. The existing Router policy continues to
exclude paid/local inference in the everyday profile. Remote devices select the
shared model; provider-key setup is performed on the Core host. The remote Desktop
adapter now forwards shared model snapshots and selection requests too.

Synthetic acceptance verified Vault admission, refusal to overwrite, owner-scope
denial and absence of the key from state/archive databases and public snapshots.
The focused Python batch passed 50 tests, UI/setup regressions passed 26 tests,
native Rust tests passed 42 with one existing fixture-only skip, and Python
typechecking passed (111 modules). The production frontend and debug native app
build passed. Full rendered key-entry/first-run flow and real owner key entry have
not been exercised, in accordance with background-only verification. The Windows
bundle was rebuilt from clean `e3f0da7`; its frozen executable passed Gemini
Flash-Lite inference outside the repository using the existing Vault. Package
checks confirmed the matching native binary and exclusion of configuration and
user databases. The restored `.env.local` remains present, ignored and untracked.

## Opt-in cloud voice — active continuation

The everyday Desktop prepares the existing voice runtime with Groq
`whisper-large-v3-turbo` transcription and optional installed Windows speech
output. No local reasoning/STT model is loaded or downloaded. Preferences → Voice
offers explicit cloud audio consent before microphone controls become available.
The owner then selects devices and unmutes separately; preparation and settings
never start capture. Continuous/wake listening remains unavailable in cloud mode.

Cloud turns are bounded to 15 seconds. WAV upload is constructed in memory;
requests use current Vault bindings and a fresh confirmed Groq Free-plan assertion,
the shared conservative credential-capacity pool, bounded responses/timeouts and
no redirects or automatic mutation retry. Billing/local fallback remains disabled.
Cancellation suppresses a late transcript. Withdrawing cloud-audio consent cancels
the turn and removes its microphone/cloud scopes without changing other grants.
No real owner microphone or audio consent was activated during development.

`python -m scripts.alpha_voice_acceptance` passed generated Windows speech → actual
Groq transcription → canonical Ask → synthetic signed review → independently
verified arithmetic result `15` and retained voice/text history. Generated PCM was
not played. The initial HTTP 403 was resolved by using OSCAR's standard User-Agent;
the next observed planned state correctly required Ask approval. Both boundaries
were preserved rather than bypassed. Two final generated-audio acceptances passed.

Focused voice/launcher regressions passed (44), additional cloud admission/consent
tests passed (7), UI voice tests passed (5), and native tests passed (42 with one
existing fixture-only skip). Typechecking and native build passed. Hardware audio,
speech quality, barge-in during actual playback and rendered control acceptance
remain NOT RUN. Installed Windows speech is a fallback voice binding, not owner
acceptance of OSCAR's final voice identity. The roughly 72 MB Windows bundle was
rebuilt from clean `90d6fd3`. PortAudio, NumPy audio support and the Windows speech
helper are present; no credential files or user databases are bundled. Its frozen
executable passed actual Gemini Flash-Lite inference outside the repository.
Packaged hardware voice acceptance remains NOT RUN.

Current provider contracts: [Groq transcription](https://console.groq.com/docs/speech-to-text)
and [Free-plan limits](https://console.groq.com/docs/rate-limits). Account confirmation,
provider availability and actual remaining quotas remain separate observations.

## Owner expanded authorization and rendered acceptance — 2026-11-06

The owner explicitly lifted prior execution restrictions and made local compute
available for the full product mandate. Local-model and GUI/device verification
may now proceed. This supersedes the earlier background-only/local-model
prohibitions in this dated record. Configuration preservation remains the working
practice; no cleanup, credential replacement or paid inference is needed here.
The packaged everyday profile still enforces verified-free cloud routing until
an explicit local-mode implementation is integrated and verified.

The actual frozen Windows app rendered all four introduction steps, saved/resumed
their progression, and submitted its first request into Workspace. Its native Ask
review was inspected and confirmed for the bounded explanatory prompt. The actual
model response rendered with the honest Partially verified / Not independently
checked status. This establishes packaged onboarding-to-response behavior, not
general native computer control, audio hardware quality or owner acceptance.

Broader background checks passed: 130 focused Python cases, 31 UI cases, full
Python typechecking and repository secret-safety checks. Three pre-existing Clippy
collapsible-if warnings were corrected without changing their predicates; Clippy
now passes with warnings denied. The package still records its exact `90d6fd3`
source; subsequent documentation/style changes are not mislabeled as that binary.
Installed Ollama inventory includes Qwen3.5 9B/4B/0.8B; availability is not model
quality or integrated local-mode acceptance. No new weights were downloaded.

## Installed local model selection — active continuation

Following the expanded authorization, everyday Core now allows installed local
models alongside verified-free cloud routes. The Router's zero-cost policy has an
explicit `allow_local` exception that defaults off for existing cloud-only callers.
It accepts only a genuinely local provider with LOCAL funding; subscription, paid
and unknown cloud funding do not qualify. Existing live Ollama metadata checks
continue to reject cloud-proxy model claims.

Desktop and Android shared model selectors identify this expanded policy. Selecting
an installed model uses LOCAL mode and persists the selection; Automatic resets
the pin and can choose eligible zero-cost routes. Switching lists include cloud
routes even after a local model is selected. Explicit local selection disables
optional Ollama thinking so short output budgets yield final answers. The first
short check exhausted its final-text budget; the corrected real Qwen3.5 4B
Router check passed with `python -m scripts.start_oscar --check --provider
ollama-local --model qwen3.5:4b`. No new model download or secret change occurred.

Focused routing/Grid/launcher regressions passed (98); model UI tests and
TypeScript checking passed. Android unit tests, debug/instrumentation APK builds
and lint passed; debug APK SHA-256:
`2eb516c88c3384ae73147f1c932893d9f8aadab384eb026fa28fac1204ce6454`.
Python typechecking and repository checks passed. Desktop debug build passed.
The Windows ZIP still predates this integration and must be refreshed.

The existing disposable API 36.1 AVD was retried with GPU emulation enabled,
supported software rendering, 3 GB RAM and four cores. The same SurfaceFlinger
buffer-mapping assertion persisted; the owned emulator was stopped. This concrete
configuration change did not establish Android runtime acceptance. Device/image
compatibility remains the next runtime investigation, not an application PASS.

### Android emulator blocker resolved; local package verified

The official SDK repository supplied Emulator 37.2.13 (replacing 36.5.11), but
the same assertion initially persisted. Inspecting the AVD registration exposed
`target=android-0`, generated by the older command-line tools for the dotted API
36.1 image. Correcting this disposable AVD's registration to `android-36.1` allowed
the same installed image and supported software renderer to run successfully.
No duplicate image or data wipe was used. Future AVD preparation must validate
the registered target against the image, not rely solely on boot completion.
The [upstream tooling report](https://github.com/actions/runner-images/issues/14484)
describes the matching failure signature; local instrumentation provides the
acceptance evidence here.

`python -m scripts.verify_android_grid --serial emulator-5582 --avd
oscar_functional_alpha_api36_1` completed all five actual native checks:
Keystore export/signing, connected Grid, process-restored connection/history,
connection-loss private-state withdrawal, and revoke/logout. The fixture used an
actual trusted-CA HTTPS Core and independent scoped Worker, including verified
filesystem readback. Independent Core inspection confirmed device revocation.
This resolves the emulator-environment blocker for that bounded Grid acceptance;
it does not establish the everyday Core's complete Android experience, all phone
capabilities, physical phone or owner biometrics. Logs are under ignored
`.oscar/d2-android` with credential fields redacted.

The Windows ZIP was refreshed from clean `23d84c6`. Its frozen executable passed
real local Qwen3.5 4B inference outside the repository. The restored configuration
remains present, ignored and untracked. Rendered local/cloud switching and broader
cross-device continuity remain additional acceptance work.

## Recent conversation context across Grid — active continuation

Remote model requests previously displayed canonical history without supplying it
to inference. Grid now binds at most 40 recent canonical event IDs to a model
request. The executor reads a bounded evidence excerpt immediately before
inference; source IDs, epistemic status and the data-not-authority boundary remain
visible in its prompt. Prior text is not copied into durable task/action records.
Context handoffs expire after 120 seconds and are cleared after execution.

Admission requires archive-read authority. Execution and each provider attempt
recheck that authority and source visibility; changed/forgotten context cannot be
uploaded from an earlier cached excerpt. Source and parent-event relationships
are checked, including remote answers whose source request was forgotten. This
does not replace Controller Memory Preflight or grant memory access implicitly.

`python -m scripts.alpha_grid_conversation_acceptance` passed real installed
Qwen3.5 4B inference through signed synthetic Grid admission: the follow-up recovered
a synthetic Desktop observation, used its codename, and retained its response in
canonical shared history. Database inspection confirmed that the prior observation
was not duplicated into task state. A differently worded initial prompt required
an ungranted capability and was denied; the successful bounded model-reasoning
check does not generalize to all contextual objectives. This script uses the
actual Core/Grid request protocol directly, not Android rendering or HTTPS.

All 74 affected Desktop/Grid/conversation-planning regressions passed. New checks
cover source-ID prompt composition, private routing, read-scope withdrawal and
forgetting after admission. Typechecking and lint passed. Native Android follow-up
acceptance and a rebuilt Windows package remain outstanding for this change.

### Actual Android composer follow-up acceptance

`python -m scripts.verify_android_grid --serial emulator-5582 --avd
oscar_functional_alpha_api36_1 --real-model` passed native
`GridConnectedTest.realModelFollowsDesktopContext`. It enrolled the disposable
Android app over actual trusted-CA HTTPS, loaded the canonical synthetic Desktop
observation, typed into `interactionInput`, pressed Send, and received a real
installed Qwen3.5 4B response using its Cedar Otter codename. The test verified
Partially verified status rather than fabricating independent verification of
model prose, encrypted history persistence, and continuity after activity
recreation. Independent Core snapshot readback also confirmed the answer.

This uses the production CoreSession/composer/transport/history paths with a
synthetic owner and isolated Core, not an injected transcript or canned model
response. It does not commission the owner's physical phone or establish every
native permission/OEM behavior. Both APK builds, unit tests and lint passed;
the application APK is unchanged by the test-only addition. The Windows package
was rebuilt from clean `645fc08`, includes the latest Core context handoff, and
passed real local Qwen3.5 4B inference outside the checkout. Package inspection
confirmed exclusion of configuration secrets and user databases. The restored
`.env.local` remains present, ignored and untracked.

## Device invitation from the actual application — active continuation

Desktop Devices now exposes Pair a phone using the existing signed connection
management review and native confirmation. The owner supplies the phone's public
registration and a new device identity, with separate default-off history and
phone-review authority choices. Phone review uses its separate device-lock-backed
owner public key. The Core issues the existing five-minute, device-key-bound Grid
invitation only after signature verification and current owner/policy checks.
No key, shell command, new credential file or replacement Core is introduced.

Pending unexpired invitations are projected from canonical enrollment state and
disappear after consumption/expiry. A valid device signature is still required
to enroll. Existing identities are refused here rather than silently recovered.
This operation does not grant Android actions, microphone/camera/notifications,
continuous perception, Secure or Full Access. Those remain separately scoped.

The form explicitly explains the connectivity boundary: the everyday launcher is
loopback-only, and physical phones still need a reachable trusted HTTPS Core.
Issuing an invitation does not provision hosting, expose a port or open a firewall.
Public registration/invitation exchange is currently manual; QR/discovery and
production Cloud provisioning are not claimed by this integration.

Synthetic acceptance passed signed issuance, exact requested scopes, device proof,
consumed-invitation disappearance and signed-review replay rejection. The broader
Core/connection/Grid/launcher batch passed 85 cases; 21 UI/Workspace cases and
typechecking passed. The actual source-built Devices screen and default-off form
were inspected; checkbox sizing was then corrected and native build passed.
No new real owner device was enrolled during the inspection. Final packaged
pairing and physical-phone onboarding acceptance remain outstanding.


## Bounded delayed requests and native review repair

Conversation recognizes explicit delays such as `In 90 seconds, 19 + 23`,
bounded to one second through seven days and one run. Desktop and remote Grid
compute absolute due time from the Core clock before exact signed review.
Malformed delays fail rather than silently becoming immediate work.

Live native acceptance exposed management reviews incorrectly requiring an
existing task. The native bridge now explicitly projects whether a task is
required. Expiry, signed material and current-policy checks remain enforced.
Actual Workspace submission and Windows confirmation created one scheduled
addition. Independent Core readback confirmed completed/run_index=1 and the
bound task verified. The launcher now includes executive:read for automation
readback, migrating only exact legacy scope sets. Narrowed or revoked
enrollments still refuse startup.

Checks passed: 135 assistance/Executive/cloud/Desktop/Grid Python cases,
20 launcher cases, 28 Activity/Workspace cases, 42 Rust tests (one optional
synthetic voice fixture ignored), UI/native builds, Ruff and mypy.

The preceding pairing package from clean 6fbd996 passed real local Qwen3.5 4B
inference outside the checkout; it predates this delay/review repair.
Physical-phone onboarding and production HTTPS hosting remain unverified.
The restored .env.local was not edited and remains ignored/untracked.
