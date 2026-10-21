# Voice dialogue software integration — 2026-10-21

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
Without this option the native voice capability remains unavailable. Configuration
requires exactly these fields:

```json
{"version":1,"root":"D:/path/to/prepared/voice","input_device":7,"output_device":null}
```

`root` contains `models/whisper-base.en` and optional prepared `quality` Kokoro/Piper
assets, as described by the existing voice setup tooling. Audio device indices
must be selected from the intended machine's device inventory; the example index
is illustrative. A null output disables spoken responses. A numeric output
selects an explicit local playback device. Preparing the configuration opens no
audio stream; explicit VoiceStart starts bounded push-to-talk input. No downloads
or cloud fallback occur. The owner must separately authorize real audio capture
before exercising a physical device.

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
physical barge-in. Those physical and owner checks remain NOT_RUN. Continuous
native wake listening and persisted mute/device selection UI are not established
by this bounded push-to-talk integration. The arithmetic-only historical
`VoiceCore` remains a separate reference harness; product dialogue reuses Desktop.

The sanitized [software receipt](../evidence/software-completion/voice-2026-10-21.json)
records source hashes from the working tree, exact checks and the synthetic model
results. It is evidence for the recorded source contents before the integration
checkpoint, not a claim of remote CI or physical acceptance.
