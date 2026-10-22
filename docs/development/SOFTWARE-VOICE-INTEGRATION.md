# Voice dialogue software integration — 2026-10-22

`DesktopVoice` supports explicit Ask dialogue and Dictate through the existing
`Desktop.request` admission path. Final local transcripts share the Controller,
capability selection, Personal Policy, signed standing delegation, independent
task verification and Event Archive used by typed requests. Provisional speech
cannot issue tasks. Recognition never grants authority. Canonical conversation
retention still requires its separate grant; raw audio is not archived.

The Workspace microphone and Companion listening action select Ask. Text Tools
and legacy VoiceStart requests retain Dictate. Native voice lifecycle is separate
from the task state: cancelling speech does not cancel or reverse an issued task.
Delayed recognition and output are fenced by cancellation and turn generation.
Local response synthesis uses the existing SynthesisChain and stable Voice
Identity; an output failure preserves the actual task result. PCM reaching an
output sink is REPORTED, not proof the owner heard it.

## Local native configuration

The trusted local Core process accepts `serve --voice-config <absolute-json-path>`.
Without this option the native voice capability remains unavailable. The initial version-1 configuration
requires exactly these fields:

```json
{"version":1,"root":"D:/path/to/prepared/voice","input_device":7,"output_device":null}
```

`root` contains `models/whisper-base.en` and optional prepared `quality` Kokoro/Piper
assets, as described by the existing voice setup tooling. Audio device indices
must be selected from the intended machine's device inventory; the example index
is illustrative. A null output disables spoken responses. A numeric output
selects an explicit local playback device. Preparing configuration opens no audio
stream and defaults the microphone to muted. No downloads or cloud fallback occur.
The owner must separately authorize real audio capture before exercising a physical
device.

In native Preferences, **Check audio controls**, **Find audio devices**, select the
actual microphone and optional output, then explicitly save the mute choice.
Saving opens no audio stream. Version-3 settings atomically persist `muted`, the
selected numeric indices, and each selected device's name, host API and input/output
channel counts. Inventory changes between display and save are rejected. The native
capture adapter checks the saved identity before opening input, and playback checks
it before opening each output stream. Missing or changed identities fail closed and
require selection again; legacy version-1/2 files can prepare adapters but cannot
open an unpinned physical endpoint. Device names/host API cannot distinguish two
physical endpoints that the OS exposes with identical metadata.

A persisted unmuted choice never starts capture automatically after a Core restart.
**Mute microphone** cancels input, STT and output and persists mute even when device
inventory is unavailable. Ordinary explicit Ask/Dictate input remains bounded to
15 seconds. Audio configuration and an independent perception grant do not grant
consequential action authority.

## Explicit continuous local wake

Continuous wake additionally requires the exact enrolled session scope
`desktop:voice:continuous`, the existing `desktop:microphone` grant, current Personal
Policy, selected pinned devices, prepared local Sherpa wake/Silero VAD models, an
unmuted setting and a separate **Start local wake listening** action. Full Access
never supplies these perception grants. Trusted local operation can grant this
scope to one existing live Desktop microphone session:

```powershell
python -m oscar serve --voice-config D:/private/voice.json --continuous-voice EXACT_DESKTOP_SESSION_ID
```

The CLI does not enroll a device, extend session expiry, change action authority,
start capture or grant other sessions access. It validates the selected session and
Desktop node and audits the local grant. With no flag, enrolled scopes are unchanged.
The native panel reports missing models/grants honestly; remote Grid connections
without a local voice adapter retain unavailable controls.

`DesktopVoice` reuses `VoiceSession`, bounded pre-roll and activated STT, and final
transcripts enter the existing Desktop Ask path. It keeps capture local while a
separate bounded turn processes/speaks. Playback-reference suppression excludes
confident self-output and uncertain frames; classified human barge-in cancels only
STT/output. An issued task keeps its actual result. An overlapping utterance is
bounded and waits up to three seconds for the previous issued turn; if that turn
is still finishing, the owner is told to ask again rather than queue hidden work.
No ambient raw audio is stored, and wake recognition is not owner authentication.

Current grants/session authority are checked on every input frame and again after
STT before admitting a final transcript. The interaction lease renews every five
seconds. An authenticated foreground native inspect heartbeat is independently
required every ten seconds; loss stops input/output and requires explicit restart.
Native disconnect/logout/quit also sends a best-effort cancel. Revocation, mute,
endpoint loss and reordered devices do not silently restart listening.

## Reproducible synthetic acceptance

With the existing prepared local voice runtime and models:

```powershell
& .tmp/voice-env/Scripts/python.exe -m scripts.software_voice_reference
```

This exercises actual Windows speech fixture generation, Sherpa wake detection,
Silero VAD, CPU/int8 FasterWhisper, the canonical Desktop Core and Kokoro response
synthesis. Input and output remain in memory. Synthetic signed standing delegation
permits arithmetic and a spoken file-write request; actual task evidence and file
readback are inspected. Exact PCM reference suppression excludes OSCAR output,
while actual VAD on independently supplied synthetic human speech interrupts the
response without replaying the already verified task.

The script also runs the production Rust Bridge and CoreClient over real loopback
HTTP, with the same synthetic audio adapters. It verifies explicit Ask admission
after authority revocation, preserves the pending task on speech cancellation,
and verifies Dictate yields a preview without issuing another task. The bounded
synthetic bootstrap stays in a disposable directory, never in the evidence file.
Its Rust acceptance case is ignored in ordinary Cargo runs because it needs this
live local fixture; the script explicitly runs it and requires one passing test.

Receipts distinguish model/bridge software from native WebView rendering,
microphone, loudspeaker, real-time room echo cancellation, owner Voice Match and
physical barge-in. Those physical and owner checks remain NOT_RUN. The same script
now exercises the actual product continuous loop with real local wake/VAD/STT,
synthetic queued PCM, canonical verified arithmetic and listener cancellation.
Unit tests cover separate grants, delayed-STT revocation, foreground heartbeat
loss, persistent mute, inventory reordering and pin rejection before any native
stream opens. Native typed-command/projection tests and rendered Preferences tests
cover explicit device/settings/listen/mute controls. No actual microphone, speaker
or native WebView audio acceptance is inferred. The arithmetic-only historical
`VoiceCore` remains a separate reference harness; product dialogue reuses Desktop.

The sanitized [continuous software receipt](../evidence/software-completion/voice-continuous-2026-10-22.json)
records source hashes from the working tree, exact checks and the synthetic model
results. It is evidence for the recorded source contents before the integration
checkpoint, not a claim of remote CI or physical acceptance.
