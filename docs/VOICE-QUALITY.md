# Slice 08 local Voice quality pass

Status: local reference candidate under validation, 2026-10-06.
Physical acceptance: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
Naturalness: `REFERENCE / OWNER_NATURALNESS_ACCEPTANCE_NOT_RUN`.

## Research and local candidate scope

Primary sources retrieved 2026-10-06; upstream claims are REPORTED, not this laptop's measurements.

| Candidate | Evidence and practical boundary |
| --- | --- |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Existing CTranslate2 adapter reused; base.en, small.en CPU/int8 and RTX 5060/FP16; turbo comparison pending |
| [Distil large-v3.5](https://huggingface.co/distil-whisper/distil-large-v3.5) | Current English distilled candidate, CT2 comparison pending; English scope differs from multilingual turbo |
| [Whisper large-v3/turbo](https://huggingface.co/openai/whisper-large-v3-turbo) | Turbo is the practical lower-decoder-cost large-v3 comparison on an 8 GB shared GPU; full large-v3 not yet benchmarked |
| [Parakeet TDT v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) | Current multilingual candidate; CC-BY-4.0 attribution; ONNX/sherpa path avoids making NeMo mandatory; assets pending |
| [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) | 0.6B/1.7B and streaming candidate discovered; separate Transformers/vLLM stack, not measured here |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Native quantized alternative with mobile paths; runtime not measured here; public JFK fixture reused |
| [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) | Apache-2.0 82M neural model; local ONNX execution and original reference blend, no celebrity cloning |
| [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) | Optional MIT runtime; model/export and phonemizer licenses remain separate; CPU binding works on Windows |
| [Piper](https://github.com/OHF-Voice/piper1-gpl) | Small local fallback; GPL runtime and individual voice MODEL_CARD terms must be retained/reviewed before distribution; comparison pending |
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

Read-only [Elocution](https://github.com/amaansyed27/Elocution) contained architecture
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
