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

The owner requested cloud inference only on 2026-11-06. Local models and paid
fallbacks are disabled in the everyday launcher. To check live inference:

```powershell
python -m scripts.start_oscar --check --provider openrouter
```

Preferences → Intelligence offers automatic verified-free routing and available
cloud models. Selection is persisted. Optional `--provider` and `--model` pins
override it for a launch. Eligibility requires current live zero-price evidence;
cached free labels, subscriptions, local models and unknown pricing cannot qualify.
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
No device acceptance is implied. Guided provider-key entry inside the app remains
missing; existing restored configuration and secure Vault bindings are supported.
