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
