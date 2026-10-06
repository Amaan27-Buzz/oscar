# Slice 08 local Voice quality pass

Status: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**, 2026-10-06.
Integration requires green exact-head CI; this is never physical PASS.
Physical acceptance: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
Naturalness: `REFERENCE / OWNER_NATURALNESS_ACCEPTANCE_NOT_RUN`.

## Research and local candidate scope

Primary sources retrieved 2026-10-06; upstream claims are REPORTED, not this laptop's measurements.

| Candidate | Evidence and practical boundary |
| --- | --- |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Existing CTranslate2 adapter reused; base.en, small.en CPU/int8 and RTX 5060/FP16; turbo comparison executed |
| [Distil large-v3.5](https://huggingface.co/distil-whisper/distil-large-v3.5) | Current English distilled candidate, CT2 comparison executed; English scope differs from multilingual turbo |
| [Whisper large-v3/turbo](https://huggingface.co/openai/whisper-large-v3-turbo) | Turbo is the practical lower-decoder-cost large-v3 comparison on an 8 GB shared GPU; full large-v3 not yet benchmarked |
| [Parakeet TDT v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) | Current multilingual candidate; CC-BY-4.0 attribution; ONNX/sherpa path avoids making NeMo mandatory; CPU int8 benchmark executed |
| [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) | 0.6B/1.7B and streaming candidate discovered; separate Transformers/vLLM stack, not measured here |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Native quantized alternative with mobile paths; runtime not measured here; public JFK fixture reused |
| [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) | Apache-2.0 82M neural model; local ONNX execution and original reference blend, no celebrity cloning |
| [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) | Optional MIT wrapper; Apache model/export and GPL phonemizer/eSpeak terms remain separate and require redistribution review; CPU binding works on Windows |
| [Piper](https://github.com/OHF-Voice/piper1-gpl) | Small local fallback; GPL runtime and individual voice MODEL_CARD terms must be retained/reviewed before distribution; local comparison executed |
| [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | Apache-2.0; 0.6B/1.7B, instruction control on the larger variants and VoiceDesign; upstream streaming claims do not prove this machine's latency; not locally executed |
| [Chatterbox](https://github.com/resemble-ai/chatterbox) | MIT, Turbo/Nano/multilingual paths, reference conditioning and watermarking; upstream Debian/Python reference differs from this Windows environment; not locally executed |
| [F5-TTS](https://github.com/SWivid/F5-TTS) | Flow matching/reference conditioning; MIT code but pretrained model CC-BY-NC terms are a distribution concern; not locally executed |

No unmeasured candidate is declared slower, less natural or universally inferior.
This is a practical measured selection, not an exhaustive leaderboard or microphone trial.

## Reproduction and evidence

`scripts/benchmark_voice.py fixtures` generates four original neutral sentences
using the explicit emergency Windows adapter without playback. STT also uses
public JFK audio from whisper.cpp; hashes/transcripts are in the local manifest.
The suite is small (one recorded speaker plus one synthetic source), not proof of
broad accents/noise/dictation quality. Punctuation/case normalization is explicit;
numeric rendering differences are counted rather than silently forgiven.

Run each candidate in a fresh process, three passes over fixed audio. Report
model load and first inference separately from warm median; rolling half-clip
partials are provisional, not native streaming. Sample process RSS/CPU and whole
GPU memory/utilization; shared GPU samples include other processes and cannot
establish exact transient kernel peak. Downloads/cache/builds are outside timed
inference; model assets are local and HF_HUB_OFFLINE is set for execution.

Cancellation rejects pre-cancelled work and discards in-flight STT output after
kernel/segment return. It does not forcibly preempt CUDA kernels. TTS cancellation
is checked before sentence generation and every 100 ms PCM delivery chunk; stop
latency during an already-running inference can exceed chunk-boundary latency.
Existing playback cancellation and generation fencing remain authoritative.

Weights, transfer fragments, WAVs and raw per-candidate reports stay in ignored
`.oscar/voice/quality`. Only nonprivate summary evidence and hashes belong in Git.
No microphone/playback, room AEC, owner Voice Match, Android or naturalness PASS.

## Original Voice Identity and Elocution

Read-only Elocution (owner-private `amaansyed27/Elocution`) contained architecture
and evaluation plans, not model/performance results. Reuse its separation of
identity, delivery and downstream DSP, and its insistence on human listening.
Do not build its speculative performance-planner schema in Slice 08.

`oscar_voice_profile()` preserves OSCAR identity/version and portable speaking
parameters with per-provider bindings. The Kokoro reference combines 65% bm_george
and 35% bm_lewis at rate 0.95. It is a stock-voice blend for original OSCAR text,
not a bespoke trained voice or an exact celebrity impersonation. Its final sound
is an owner listening decision. Piper/System.Speech bindings preserve the logical
identity but do not promise identical timbre. No unsupported emotional controls
are fabricated; current Kokoro control is voice blend, rate and sentence pacing.

## Cross-platform implications

Contracts for wake/VAD, transcript/finality, identity, PCM output, cancellation,
self-output, Match/Map, policy, Persona, arbitration and task handoff remain shared.
ONNX and native whisper/sherpa permit future Android/Linux/macOS bindings without
Python becoming a mobile requirement. Android on-device phonemization/runtime,
latency, memory and model-license packaging require separate validation.

Use lightweight local wake/VAD on Sunday; select available local/on-device STT/TTS
or authenticated LAN/Desktop inference as a capability. Desktop loss becomes
explicit degraded/unavailable state, with platform speech only as a declared
fallback. Home Node serving is an architectural path, not deployed here. Cloud
escalation needs an audio-capable provider adapter plus separate policy/grants.
Voice Identity never becomes a Windows System.Speech registry voice name.

Capture/playback, audio sessions/focus, permissions, AEC, Bluetooth routing,
background lifecycle and acceleration stay platform adapters. Windows evidence
never implies Sunday acceptance. Preserve the [consolidated owner run](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Operating Logs, specialist training and home-server migration stay
[post-alpha](POST-ALPHA-EVOLUTION.md), unimplemented.

## Measured selection

[Nonprivate reference record](evidence/voice-quality-reference-2026-10-06.json)
contains model/source hashes, fixtures, cold/warm and resource observations,
failed attempts and limitations. Model weights and WAVs are not in Git.

Preferred STT: **Whisper large-v3-turbo, faster-whisper/CTranslate2, CUDA FP16,
beam 5**. It fits this 8 GB RTX 5060 while retaining multilingual/long-form
coverage. Distil v3.5 is slightly faster but English-only; Parakeet v3 is an
excellent measured CPU candidate. This tiny suite ties base, Distil and turbo on
strict normalized WER, so it does not establish universal quality superiority.
Use **base.en CPU/int8** as the small established fallback; unavailable audio
returns blocked/text interaction, not fabricated recognition. Turbo int8/FP16 is
a measured lower-VRAM optional configuration, not silently selected over quality.

| STT binding | Load / first inference ms | Warm final / provisional ms | Fixture WER | Sampled GPU MiB / process RAM MB | Model assets MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| base.en CPU int8 | 534 / 498 | 569 / 516 | 2.56% | 0 / 320 | 148 |
| base.en CUDA FP16 | 2918 / 1139 | 141 / 101 | 2.56% | 328 / 745 | 148 |
| small.en CPU int8 | 1067 / 1344 | 1722 / 1599 | 6.41% | 0 / 563 | 486 |
| small.en CUDA FP16 | 1610 / 449 | 224 / 147 | 6.41% | 744 / 717 | 486 |
| Distil v3.5 CUDA FP16 | 4320 / 845 | 504 / 472 | 2.56% | 2216 / 1623 | 1516 |
| turbo CUDA FP16 | 1770 / 750 | 529 / 489 | 2.56% | 2344 / 1741 | 1622 |
| turbo CUDA int8/FP16 | 2968 / 1377 | 495 / 449 | 2.56% | 1320 / 1968 | 1622 |
| Parakeet v3 sherpa CPU int8 | 1824 / 223 | 233 / 132 | 3.85% | 0 / 958 | 671 |

Preferred neural TTS: **Kokoro 82M v1.0 full-precision ONNX CPU**, original
65/35 stock blend, rate 0.95. It gives a practical British-leaning original
reference path with portable ONNX assets and declared controls. Owner listening
must decide whether delivery/naturalness/consistency is good enough. **Piper alba**
is the lighter/faster neural fallback; its model card declares a CC-BY-4.0 dataset.
**System.Speech is only the Windows emergency fallback**, selected explicitly.
No external model/provider change changes OSCAR's logical identity/version.

| TTS binding | Load / cold first audio ms | Warm first audio ms | Warm RTF | Process RAM MB | Model MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kokoro full precision CPU, rate 0.95 | 1001 / 421 | 908 | 0.387 | 644 | 326 |
| Kokoro int8 CPU, rate 1.0 | 920 / 842 | 1873 | 0.828 | 409 | 92 |
| Piper alba CPU, rate 0.95 | 1259 / 68 | 86 | 0.041 | 323 | 63 |
| System.Speech, rate 0.95 | <1 / 334 | 320 | 0.049 | 32 | OS-installed |

Full precision beat Kokoro int8 for latency on this machine. A four-thread ONNX
session avoids excessive CPU use; it did not by itself improve int8 latency.
Kokoro CUDA was attempted and failed at missing `cudnn_graph64_9.dll`; no GPU TTS
success is claimed. The owner harness stays on the measured CPU neural path.
CPU percent can exceed 100% because it counts multiple cores. Whole GPU resource
samples can include unrelated processes (one CPU TTS run observed 92 MiB).

Roundtrip assessment on original generated samples: Kokoro 3.57%, Piper 8.93%,
System.Speech 3.57% strict normalized WER. These errors mix ASR and TTS and are
not human pronunciation ratings. Synthetic speaker cosine means were 0.523,
0.475 and 0.847 respectively. They expose uncertainty; they do not verify
perceptual consistency, naturalness or biometric identity. No embeddings were
retained. Owner review remains mandatory.

## Streaming and interruption changes

Kokoro yields sentence-generated audio in 100 ms PCM chunks. Playback now keeps
one native stream per utterance instead of reopening it per chunk, drains completed
output, aborts cancellation and fences older utterance cleanup from newer playback.
Piper checks cancellation before advancing its native generator. Existing own-output
reference subtraction, conservative uncertainty, human residual barge-in, tail guard,
Voice Match/Map self-output exclusion and generation fencing remain intact.
Software/mocked cancellation proof is not room AEC or physical barge-in acceptance.

## Reproduce prepared references

```powershell
.tmp/voice-env/Scripts/python.exe -m pip install '.[voice,voice-kokoro,voice-piper,voice-benchmark]'
.tmp/voice-env/Scripts/python.exe -m scripts.voice_setup --quality
# Supply a standard compatible CUDA 12 / cuDNN runtime for GPU STT; CPU fallback needs neither.
.tmp/voice-env/Scripts/python.exe -m scripts.benchmark_voice fixtures --public-jfk .oscar/voice/quality/fixtures/jfk.wav
.tmp/voice-env/Scripts/python.exe -m scripts.benchmark_voice stt --model .oscar/voice/quality/turbo --device cuda --compute float16
.tmp/voice-env/Scripts/python.exe -m scripts.benchmark_voice tts --provider kokoro --model .oscar/voice/quality/kokoro-fp32.onnx --voices .oscar/voice/quality/voices-hf.bin --voice oscar-reference --compute float32
.tmp/voice-env/Scripts/python.exe -m scripts.benchmark_voice assess --model .oscar/voice/quality/turbo --device cuda --compute float16
```

The public fixture is acquired explicitly from whisper.cpp, verified by SHA-256;
no benchmark implicitly downloads or opens a device. `assess` requires prepared
Kokoro/Piper/System.Speech sample runs. Python-only packages are desktop adapters,
not an Android requirement. Android-native binding, native phonemization and
actual device latency remain separate software/device work.

Optional G2P/phonemizer/eSpeak components have their own GPL terms; an Apache
model or MIT wrapper is not a blanket license for a bundled distribution. Review
all runtime/voice terms before shipping combined binaries. This is local reference
execution, not a distribution-license clearance.

## Integrated cold-start boundary

An unprimed integrated reference observed about 10.5 seconds preparing/synthesizing
its first response. The owner harness now prepares and silently primes synthesis
before starting capture. Generated startup PCM is discarded and never played.
The subsequent reference measured **3373 ms startup preparation**, **457 ms final
STT** and **609 ms first result audio**. These are separate costs on a synthetic
arithmetic task, not a controlled universal cold-start improvement or microphone
latency claim. Startup time remains visible; no instant-readiness claim is made.
