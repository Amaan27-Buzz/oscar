# Slice 08 Voice Core

Status: IMPLEMENTING / OWNER_MICROPHONE_ACCEPTANCE_REQUIRED.
Accepted baseline: `9e443cac61281d7d890724b9ef593c0d58d145f3` (PR 13 merged).
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
