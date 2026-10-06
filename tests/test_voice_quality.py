"""Portable neural adapter boundaries without models, downloads or audio devices."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from oscar.voice_adapters import (
    FasterWhisper,
    KokoroSpeech,
    PiperSpeech,
    PlaybackReference,
    SoundDevicePlayback,
)
from oscar.voice_contracts import AudioChunk, StopToken, VoiceCancelled, VoiceError, VoiceProfile
from oscar.voice_identity import oscar_voice_profile
from scripts.benchmark_voice import errors


class QualityTests(unittest.TestCase):
    def test_identity_bindings_do_not_change_identity(self) -> None:
        profile = oscar_voice_profile()
        self.assertEqual(profile.identity, "oscar")
        self.assertEqual(profile.provider, "kokoro")
        self.assertEqual(profile.fallback[-1], "windows-system-speech")
        self.assertEqual(len(profile.voice_bindings), 3)

    def test_word_error_distance(self) -> None:
        self.assertEqual(errors("One two three.", "one four three"), (1, 3))
        self.assertEqual(errors("one two", "one"), (1, 2))
        self.assertEqual(errors("one", "one two"), (1, 1))

    def test_no_implicit_assets_or_bad_gpu_config(self) -> None:
        with self.assertRaises(VoiceError):
            KokoroSpeech(Path("absent.onnx"), Path("absent.bin"))
        with self.assertRaises(ValueError):
            FasterWhisper(Path("absent"), device="made-up")

    def test_cancel_before_neural_call(self) -> None:
        engine = object.__new__(KokoroSpeech)
        token = StopToken()
        token.cancel()
        with self.assertRaises(VoiceCancelled):
            next(iter(engine.synthesize("Original text.", VoiceProfile(), "turn", token)))

    def test_piper_cancel_does_not_advance_native_generator(self) -> None:
        calls = []

        def generate(text: str, **kwargs: object):
            for index in range(2):
                calls.append(index)
                yield SimpleNamespace(audio_int16_bytes=b"\x00\x00", sample_rate=16000)

        engine = object.__new__(PiperSpeech)
        engine.voice = SimpleNamespace(synthesize=generate)
        token = StopToken()
        with patch(
            "oscar.voice_adapters.optional",
            return_value=SimpleNamespace(SynthesisConfig=lambda **kwargs: None),
        ):
            stream = iter(engine.synthesize("Text.", VoiceProfile(), "turn", token))
            next(stream)
            token.cancel()
            with self.assertRaises(VoiceCancelled):
                next(stream)
        self.assertEqual(calls, [0])

    def test_pcm_boundaries_and_cancel_no_next_sentence(self) -> None:
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional numeric runtime")

        class Model:
            calls = 0

            def create(self, text: str, **kwargs: object) -> tuple[object, int]:
                self.calls += 1
                return np.ones(24000, dtype="float32") * 0.1, 24000

        engine = object.__new__(KokoroSpeech)
        engine.engine = Model()
        token = StopToken()
        with patch("oscar.voice_adapters.optional", return_value=np):
            stream = iter(
                engine.synthesize(
                    "First sentence. Second sentence.",
                    VoiceProfile(preferred_voice="bm_george"),
                    "id",
                    token,
                )
            )
            chunk = next(stream)
            self.assertEqual(len(chunk.pcm), 4800)
            self.assertEqual(chunk.utterance_id, "id")
            token.cancel()
            with self.assertRaises(VoiceCancelled):
                next(stream)
        self.assertEqual(engine.engine.calls, 1)


class PlaybackStreamTests(unittest.TestCase):
    def test_utterance_reuse_finish_fencing_and_active_cancel(self) -> None:
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional numeric runtime")
        streams = []
        token = StopToken()

        class Stream:
            def __init__(self, **kwargs: object):
                self.closed = False
                self.aborted = False
                self.interrupt = False
                self.abort_error = False
                streams.append(self)

            def start(self) -> None:
                pass

            def stop(self) -> None:
                pass

            def write(self, pcm: bytes) -> bool:
                if self.interrupt:
                    token.cancel()
                return False

            def close(self) -> None:
                self.closed = True

            def abort(self) -> None:
                self.aborted = True
                if self.abort_error:
                    raise RuntimeError("synthetic device loss")

        sd = SimpleNamespace(RawOutputStream=Stream)
        playback = SoundDevicePlayback(0, PlaybackReference())
        chunk = AudioChunk(b"\x00\x00" * 1600, 16000, "neural", "voice", "first")
        with (
            patch(
                "oscar.voice_adapters.optional",
                side_effect=lambda name: np if name == "numpy" else sd,
            ),
            patch("oscar.voice_adapters.audio_settings", return_value=None),
        ):
            playback.play(chunk, token)
            playback.play(chunk, token)
            self.assertEqual(len(streams), 1)
            playback.play(AudioChunk(chunk.pcm, 16000, "neural", "voice", "second"), token)
            self.assertTrue(streams[0].closed)
            playback.finish("first")
            self.assertFalse(streams[1].closed)
            streams[1].interrupt = True
            with self.assertRaises(VoiceCancelled):
                playback.play(AudioChunk(chunk.pcm, 16000, "neural", "voice", "second"), token)
            self.assertTrue(streams[1].aborted)
            self.assertTrue(streams[1].closed)
            self.assertIsNone(playback.stream)

            token = StopToken()
            playback.play(chunk, token)
            streams[-1].abort_error = True
            streams[-1].interrupt = True
            with self.assertRaises(VoiceError):
                playback.play(chunk, token)
            self.assertTrue(streams[-1].closed)
            self.assertIsNone(playback.stream)
