"""Portable neural adapter boundaries without models, downloads or audio devices."""

import unittest
from pathlib import Path
from unittest.mock import patch

from oscar.voice_adapters import FasterWhisper, KokoroSpeech
from oscar.voice_contracts import StopToken, VoiceCancelled, VoiceError, VoiceProfile
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
                engine.synthesize("First sentence. Second sentence.", VoiceProfile(), "id", token)
            )
            chunk = next(stream)
            self.assertEqual(len(chunk.pcm), 4800)
            self.assertEqual(chunk.utterance_id, "id")
            token.cancel()
            with self.assertRaises(VoiceCancelled):
                next(stream)
        self.assertEqual(engine.engine.calls, 1)
