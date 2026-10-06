# Slice 08 Voice Core

Owner closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
Software/reference validation is recorded for PR #14; integration requires green
exact-head CI. Gate C remains PARTIAL.
Reconciled baseline: `e8ac8f8bca1cb0cb7909523ac6af906ee289366f`.
See [quality pass](VOICE-QUALITY.md) and [consolidated acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 07 is COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION; physical Edge
remains DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED and mandatory before Unified Alpha.

Scope: replaceable microphone, local wake/VAD, STT, Core handoff, stable Voice
Identity/TTS, playback suppression/barge-in, separate Match/Map, simulated node
arbitration and Persona expression. No Sunday, Slice 10, persistent World Model,
Oracle deployment or Home Node. Voice acceptance is never inferred from fixtures.

## Research — official sources retrieved 2026-10-05

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx): selected optional local
  ONNX executor for configurable English keyword spotting, Silero VAD and speaker
  embeddings; avoids training a custom wake model or requiring an access key.
- [openWakeWord](https://github.com/dscripka/openWakeWord): strong replaceable
  alternative; custom OSCAR phrase requires its own trained model.
- [Porcupine](https://github.com/Picovoice/porcupine): on-device alternative;
  access-key/license boundary makes it unsuitable as a mandatory baseline.
- [Silero](https://github.com/snakers4/silero-vad): local VAD; no cloud wake/STT.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): selected local
  CPU/int8 Whisper adapter; bounded rolling-window partials are provisional,
  not native token streaming. [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
  remains a native alternative.
- [Parakeet v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3): candidate
  for later measured GPU/multilingual comparison, no mandatory NeMo dependency.
- [Piper](https://github.com/OHF-Voice/piper1-gpl): optional local streaming TTS;
  GPL/runtime and individual voice licenses must be reviewed for distribution.
  [Kokoro](https://github.com/hexgrad/kokoro) is an alternative quality candidate.
  Windows [System.Speech](https://learn.microsoft.com/en-us/dotnet/api/system.speech.synthesis.speechsynthesizer)
  supplies a zero-provider local fallback. No celebrity identity.
- [sounddevice](https://python-sounddevice.readthedocs.io/en/latest/api/streams.html)
  supplies optional PortAudio capture/playback, selecting Windows WASAPI explicitly.
  [WASAPI AEC](https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nn-audioclient-iacousticechocancellationcontrol)
  depends on endpoint/OS support; PortAudio alone does not prove AEC enabled.
- [SpeechBrain ECAPA](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb),
  sherpa WeSpeaker/CAM++ and [pyannote](https://github.com/pyannote/pyannote-audio)
  informed distinct verification vs perception boundaries. Learned similarity
  scores are not identity proof or calibrated biometric-security probabilities.

No paid-only provider is required. Model/provider absence stays BLOCKED.

## Runtime and boundaries

```text
explicit microphone grant → WASAPI/PortAudio mono 16k frames
→ local keyword spotting / Silero VAD / bounded pre-roll
→ activated STT only (provisional partials cannot execute)
→ final transcript → Controller / PersonalPolicy / existing Runtime
→ independent existing verification → immutable VoiceResponse
→ Persona expression → Voice Identity / synthesis fallback
→ cancellable speaker playback + own playback reference
```

Contracts live in `oscar/voice_contracts.py`; lifecycle/fallback/arbitration in
`voice_runtime.py`; optional model/audio adapters in `voice_adapters.py`.
`voice_core.py` composes existing Core contracts rather than a second task engine.
The owner harness is intentionally restricted to integer addition, with explicit
`math` grant. General conversational/action integration is not claimed.

Local wake is sherpa English GigaSpeech Zipformer int8 (configurable OSCAR BPE
keyword); VAD is Silero ONNX. The bilingual 2025 model is an alternative, not a
reason to replace the measured English baseline. STT is local faster-whisper
the quality-selected local binding with explicit base.en/CPU/int8 fallback; no
implicit download or cloud fallback at inference. Partial
transcripts use bounded rolling snapshots and are provisional. Interfaces permit
replacement; hosted STT through an audio-capable Router adapter is future optional
work because the current Router provider boundary is text-oriented.

VoiceProfile owns identity ID/version, preferred voice/provider/model, rate, style,
latency/quality mode, privacy, interruption and per-provider fallback bindings.
Fallback preserves this logical identity/configuration; identical timbre across
vendors is not promised. Kokoro full-precision ONNX is the current original reference neural binding;
Piper is the lighter neural fallback. System.Speech is an emergency Windows
binding and the synthetic fixture generator, not the intended OSCAR voice.
The neural owner harness composes these through the existing SynthesisChain.
Kokoro streams sentences as 100 ms PCM chunks; this is sentence-buffered synthesis,
not native token-to-audio streaming. Piper yields native sentence audio. The
emergency adapter prepares temporary PCM16 WAV, deletes it and yields chunks.
Native inference cannot be preempted mid-kernel; output is fenced/cancelled before
it becomes audible. See the [quality evidence](VOICE-QUALITY.md). Unsupported
prosody controls are not fabricated.

Fallback retries only before audible output; a partial failure never repeats the
utterance through another provider. Cancellation propagates at chunk/segment
boundaries and aborts playback. Native local STT inference cannot be forcibly
preempted mid-kernel; cancelled/obsolete generations cannot reach Core/output.

## Mandatory self-output / barge-in contract

TTS-origin frames never activate wake/STT/Match/Map. During output the front end
uses bounded timestamped playback PCM, a delay search and scalar echo subtraction.
Matched own output is suppressed. Independent residual speech for three frames
interrupts output and preserves the human prefix. Missing/ambiguous references
fail conservatively; manual activation remains available. The reference guard
continues across a short output tail. Audio queues and turns are bounded;
overflow/disconnect invalidates the turn rather than silently dropping context.

This reference suppressor is **not full calibrated room AEC**. Nonlinear echo,
reverberation, driver latency, quiet double-talk and endpoint processing can defeat
it. It may decline automatic barge-in when evidence is uncertain. WASAPI AEC
capability is researched, not enabled/verified by PortAudio alone. Full physical
self-wake suppression and human barge-in remain acceptance requirements; a physical
failure must be repaired before consolidated Gate C PASS; software closure cannot
be promoted to physical acceptance.

## Match, Map, arbitration and Persona

Match uses explicit confirmed enrollment and model-hash-bound CAM++ embeddings.
Similarity ≥0.8 is accepted evidence; <0.55 rejected; intermediate, ambiguous,
missing/invalid/model-mismatched evidence is uncertain. These are **uncalibrated
reference thresholds**, not identity certainty or biometric-security probabilities.
Replay/synthetic voice/spoofing is not prevented. Voice alone never authorizes
high-risk actions. Grants and PersonalPolicy are always independent. The harness
can require Match for the harmless task; it has no private/high-risk action route.

Map has separately confirmed known-person links and bounded transient anonymous
speaker clusters; it emits known-probable, unknown, changed and multiple source
segments with confidence/provenance. It has no authorization path. Multiple
segments may be supplied by an independent diarizer; real overlapping-speaker
diarization is not implemented/proven. Own TTS cannot enroll or update Map.
Biometric-like embeddings stay in ignored owner-only local enrollment, not Git or
OSCAR's Event Archive. Enrollment/linkage/retention grants remain separate.

The reference arbiter chooses one eligible fresh claim using priority, proximity,
quality, timestamp and stable node tie-break, then holds a renewable 10-second
conversation lease with generation fencing. Loss/expiry reselects; handoff must
come from the current generation. Grid authentication/availability must determine
eligibility upstream. It is one coordinator's reference contract, not distributed
consensus or phone/Edge-microphone acceptance.

Persona currently applies bounded acknowledgement and speaking style to an
immutable response while preserving its entire claim, epistemic/task state,
evidence, permission and limitations. Serious/failed/blocked contexts suppress
casual expression. Full natural-language Persona authoring/context learning is
future work; expression never changes PersonalPolicy or verification.

Sentry receives only bounded transient local speech/wake/change events. No Slice
11 persistent World Model, journal, ambient cloud STT or raw room retention is
implemented. Activated speech is transient; only the normalized harmless Core
task/result/evidence enters the normal local ledger.

## Reference evidence and performance

See [reference record](evidence/voice-reference-2026-10-05.json). On Intel Core
Ultra 7 255H, Windows/Python 3.12, actual local models processing System.Speech
**synthetic audio** produced OSCAR wake, speech detection, real STT and a VERIFIED
Core arithmetic result. Microphone and speaker playback were NOT RUN.

These are reference model execution timings, not real-device conversational latency:

| Stage | Reference measurement |
| --- | ---: |
| wake + VAD total inference over fixture | 57.57 ms |
| speech/wake location in synthetic clip | 0.224 s / 1.088 s |
| provisional partial STT | 398.50 ms |
| final STT | 382.59 ms |
| Core setup/handoff/verification | 259.38 ms |
| first generated TTS audio | 356.27 ms |
| speaker embedding | 29.66 ms |
| physical barge-in stop / microphone latency | UNKNOWN / NOT RUN |

No synthetic timing is presented as physical performance. Cold startup differs.
The deterministic suite covers wake/no-wake, VAD start/end/timeouts, provisional
STT/final execution, cancellation, feedback suppression/double-talk, Match
accepted/rejected/uncertain, Map identity/change/multiple, Persona integrity,
competing reference nodes, stale/lost claims, fallback and offline policy.
Opt-in tests exercise real local models and System.Speech on synthetic speech.

## Exact Windows owner acceptance

Prepared ignored local environment/models are at `.tmp/voice-env` and
`.oscar/voice/models`. For a fresh setup:

```powershell
py -3.12 -m venv .tmp/voice-env
.tmp/voice-env/Scripts/python.exe -m pip install '.[voice,voice-kokoro,voice-piper,voice-benchmark]'
.tmp/voice-env/Scripts/python.exe -m scripts.voice_setup --quality
.tmp/voice-env/Scripts/python.exe -m scripts.voice_owner preflight
```

Preflight enumerates devices, checks shared WASAPI 16k mono formats and loads models;
it never opens microphone/playback. The selected HyperX endpoints use a 48k
system mixer; explicit WASAPI shared-mode auto conversion supports our 16k frames.
Format support is verified without opening streams; this is not AEC evidence.
See [sounddevice shared conversion](https://python-sounddevice.readthedocs.io/en/latest/api/platform-specific-settings.html).
The observed HyperX WASAPI input/output IDs were **28 / 22** on this machine.
Run preflight again and replace IDs if inventory changed. Owner interaction starts here:

```powershell
.tmp/voice-env/Scripts/python.exe -m scripts.voice_owner enroll --input 28
# Type ENROLL; speak for five seconds. Type LINK only for separate Map linkage.
.tmp/voice-env/Scripts/python.exe -m scripts.voice_owner run --input 28 --output 22 --seconds 120 --allow-harmless-math --require-voice-match
```

1. Observe explicit real microphone use; say OSCAR, then “what is two plus three”.
2. Observe wake/speech, provisional transcription and independently verified task.
3. Hear OSCAR speak the result; Map is contextual and Match score remains evidence.
4. Enter **b** for a longer original barge-in test including OSCAR's own name.
5. Interrupt verbally while playback runs; observe output stop and new listening.
   Enter **p** for manual activation, **c** cancel or **q** close microphone/output.
6. Leave output uninterrupted and observe no self-wake/transcript/speaker feedback.
7. With Match required, try a non-enrolled/reference speaker; it must not execute
   the task. No private/high-risk routes are enabled even if similarity is high.
8. Run `reference` after enrollment to inspect the synthetic reference Match outcome
   without microphone/playback. This is a negative reference, not a spoof guarantee.
9. Record each step as VERIFIED / FAILED / UNKNOWN with observed endpoint/model,
   timestamps and measured physical onset/stop timings. Do not infer overall PASS.

```powershell
.tmp/voice-env/Scripts/python.exe -m scripts.voice_owner reference
.tmp/voice-env/Scripts/python.exe -m scripts.voice_owner forget
# Removes live enrollment file only; no secure-erasure/backups claim.
$env:OSCAR_VOICE_MODELS='1'
.tmp/voice-env/Scripts/python.exe -m unittest tests.test_voice tests.test_voice_models -v
Remove-Item Env:OSCAR_VOICE_MODELS
```

Raw microphone speech is never written by enrollment/run. Enrollment retains only
an explicitly approved local model-bound embedding; the owner applies the local
ACL before persistence. Stop for the owner; never fake microphone acceptance.

## Candidate verification

Local full regression: 483 tests PASS, six optional backend/model checks skipped
in the base environment. Prepared local model suite: 36 tests PASS, including
actual local wake/VAD/embedding, selected RTX STT, neural synthesis/cancellation
and WASAPI format query without opening streams. Streaming failure/cleanup,
utterance reuse, stale-generation finish and active cancellation are mocked
software evidence; room/device behavior is not inferred.

Ruff lint/format, strict mypy (56 Core modules plus setup/owner scripts), repository
contracts, local links, secret scan and diff checks PASS. Exact-head Windows/Linux,
Edge firmware and Voice CI gate integration on PR #14. The current model/resource
record is [quality reference evidence](evidence/voice-quality-reference-2026-10-06.json).
No microphone, playback or owner biometric/naturalness acceptance is inferred.
