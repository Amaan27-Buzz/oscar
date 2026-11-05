# Functional alpha — active implementation

Development continues on the consolidated `main` checkout. This is an implementation
checkpoint, not full alpha acceptance or a release claim.

## Everyday local Desktop

From the repository in PowerShell, with Ollama running:

```powershell
python -m scripts.build_desktop
python -m scripts.start_oscar
```

The default model is the installed `qwen3.5:9b`. For a lighter model:

```powershell
python -m scripts.start_oscar --model qwen3.5:0.8b
```

Preferences → Intelligence selects an available local completion model. Selection
is persisted; `--model` overrides it for a launch. Cloud-backed Ollama entries and
embedding-only models are excluded by the existing discovery checks. Paid provider
calls are disabled by the Router policy. Cloud provider setup remains separate work.

The launcher starts the existing Core, Controller, Router, Event Archive, Memory
Fabric and Executive. State lives under `%LOCALAPPDATA%\DawnlightLabs\OSCAR`;
Workspace and Companion use authenticated loopback with an anonymous-pipe bootstrap.
No credential files are created. The restored project `.env.local` is preserved,
ignored, untracked and is not read by this launcher. Secure provider onboarding uses
the existing OS Vault paths. A data-directory lock prevents concurrent Core writers.

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
