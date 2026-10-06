"""Opt-in real local model execution on synthetic speech; never microphone acceptance."""

import io
import os
import unittest
import wave

from oscar.voice_adapters import WindowsSpeech, audio_settings, optional, read_wave
from oscar.voice_contracts import (
    AudioFrame,
    Origin,
    StopToken,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
)
from scripts.voice_owner import models


@unittest.skipUnless(
    os.environ.get("OSCAR_VOICE_MODELS") == "1" and os.name == "nt",
    "optional Windows/local-model reference executor not requested",
)
class LocalVoiceModelTests(unittest.TestCase):
    def test_wasapi_shared_format_without_opening_audio(self) -> None:
        sd = optional("sounddevice")
        checked = 0
        for index, device in enumerate(sd.query_devices()):
            settings = audio_settings(sd, index)
            if settings is None:
                continue
            if device["max_input_channels"]:
                sd.check_input_settings(
                    device=index,
                    channels=1,
                    dtype="float32",
                    samplerate=16000,
                    extra_settings=settings,
                )
                checked += 1
            if device["max_output_channels"]:
                sd.check_output_settings(
                    device=index,
                    channels=1,
                    dtype="int16",
                    samplerate=16000,
                    extra_settings=settings,
                )
                checked += 1
        if not checked:
            self.skipTest("no WASAPI endpoint available; no hardware format evidence")

    @classmethod
    def setUpClass(cls) -> None:
        cls.wake, cls.vad, cls.stt, cls.embedding = models()
        output = list(
            WindowsSpeech().synthesize(
                "Oscar. What is two plus three?",
                VoiceProfile(
                    preferred_voice="local-system",
                    provider="windows-system-speech",
                    model="installed-voice",
                ),
                "reference-model-test",
                StopToken(),
            )
        )
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b"".join(c.pcm for c in output))
        cls.frames = read_wave(buffer.getvalue())

    def test_real_local_wake_vad_and_no_wake_silence(self) -> None:
        self.wake.reset()
        self.vad.reset()
        self.assertTrue(any(self.wake.detect(f) for f in self.frames))
        self.assertTrue(any(self.vad.speech(f) for f in self.frames))
        self.wake.reset()
        self.vad.reset()
        silence = tuple(
            AudioFrame((0.0,) * 512, i * 0.032, "reference", origin=Origin.SIMULATED)
            for i in range(100)
        )
        self.assertFalse(any(self.wake.detect(f) for f in silence))
        self.assertFalse(any(self.vad.speech(f) for f in silence))

    def test_real_local_stt_and_cancellation(self) -> None:
        transcript = self.stt.transcribe(self.frames, True, StopToken())
        self.assertIn("2", transcript.text)
        self.assertIn("3", transcript.text)
        self.assertTrue(transcript.final)
        self.assertEqual(transcript.status, "REPORTED")
        token = StopToken()
        token.cancel()
        with self.assertRaises(VoiceCancelled):
            self.stt.transcribe(self.frames, True, token)

    def test_real_embedding_self_output_denial(self) -> None:
        vector = self.embedding.extract(self.frames, StopToken())
        self.assertEqual(len(vector), 512)
        with self.assertRaises(VoiceError):
            self.embedding.extract(
                tuple(
                    AudioFrame(f.samples, f.timestamp, f.node_id, origin=Origin.PLAYBACK)
                    for f in self.frames
                ),
                StopToken(),
            )

    def test_windows_synthesis_interrupted_at_chunk_boundary(self) -> None:
        token = StopToken()
        stream = iter(
            WindowsSpeech().synthesize(
                "A longer original sentence for cancellation of local synthesis output.",
                VoiceProfile(
                    preferred_voice="local-system",
                    provider="windows-system-speech",
                    model="installed-voice",
                ),
                "cancellation-test",
                token,
            )
        )
        first = next(stream)
        self.assertEqual(first.rate, 16000)
        token.cancel()
        with self.assertRaises(VoiceCancelled):
            next(stream)


@unittest.skipUnless(
    os.environ.get("OSCAR_VOICE_MODELS") == "1" and os.name == "nt",
    "optional prepared neural reference executor not requested",
)
class NeuralReferenceTests(unittest.TestCase):
    def test_prepared_neural_response_and_cancel(self) -> None:
        from pathlib import Path

        from oscar.voice_identity import oscar_voice_profile
        from scripts.voice_owner import synthesis_models

        if not Path(".oscar/voice/quality/kokoro-fp32.onnx").is_file():
            self.skipTest("prepared neural model absent")
        token = StopToken()
        stream = iter(
            synthesis_models().synthesize(
                "The task is waiting for your approval. It has not executed.",
                oscar_voice_profile(),
                "neural-reference",
                token,
            )
        )
        chunk = next(stream)
        self.assertEqual(chunk.provider, "kokoro")
        self.assertEqual(chunk.voice, "oscar-reference")
        self.assertEqual(chunk.utterance_id, "neural-reference")
        self.assertEqual(chunk.rate, 24000)
        self.assertLessEqual(len(chunk.pcm), 4800)
        token.cancel()
        with self.assertRaises(VoiceCancelled):
            next(stream)
