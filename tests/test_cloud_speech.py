import json
import unittest
from unittest.mock import MagicMock

from oscar.cloud_speech import GroqRecognizer
from oscar.voice_contracts import AudioFrame, Origin, StopToken, VoiceCancelled, VoiceError


class CloudSpeechTests(unittest.TestCase):
    def test_preparation_opens_no_stream_and_defaults_to_muted(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from oscar.cloud_speech import mount_cloud_voice

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("oscar.voice_adapters.optional") as optional,
        ):
            core = MagicMock()
            mount_cloud_voice(core, self.h, Path(temporary))
            optional.return_value.InputStream.assert_not_called()
            optional.return_value.RawOutputStream.assert_not_called()
            self.assertTrue(core.voice.muted)
            self.assertFalse(core.voice.recognizer.local)
            self.assertIsNone(core.voice.wake_factory)

    def setUp(self):
        from oscar.credentials import Slot

        self.h = MagicMock()
        self.h.pool.slots = {"groq-test": Slot("groq-test", "groq", True)}
        self.h.pool.secret_for_adapter.return_value = "synthetic-transport-only"
        self.h.pool.reserve.return_value = True
        self.recognizer = GroqRecognizer(self.h)
        self.recognizer.opener = MagicMock()
        self.recognizer.opener.open.return_value.__enter__.return_value.headers = {}
        self.h.grid.clock.return_value = 1000
        self.frames = (AudioFrame((0.1,) * 512, 1, "fixture", origin=Origin.SIMULATED),)

    def test_free_plan_and_cancellation_fail_before_transport(self):
        self.h.router._confirmed_free_plan.return_value = False
        with self.assertRaises(VoiceError):
            self.recognizer.transcribe(self.frames, True, StopToken())
        self.recognizer.opener.open.assert_not_called()
        stop = StopToken()
        stop.cancel()
        with self.assertRaises(VoiceCancelled):
            self.recognizer.transcribe(self.frames, True, stop)
        self.recognizer.opener.open.assert_not_called()

    def test_bounded_memory_upload_uses_vault_and_releases_capacity(self):
        response = self.recognizer.opener.open.return_value.__enter__.return_value
        response.read.return_value = json.dumps({"text": "synthetic phrase"}).encode()
        result = self.recognizer.transcribe(self.frames, True, StopToken())
        self.assertEqual("synthetic phrase", result.text)
        request = self.recognizer.opener.open.call_args.args[0]
        self.assertEqual("Bearer synthetic-transport-only", request.get_header("Authorization"))
        self.assertIn(b"RIFF", request.data)
        self.h.pool.release.assert_called_once_with("groq-test")

    def test_cancelled_network_reply_cannot_reach_core(self):
        stop = StopToken()
        response = self.recognizer.opener.open.return_value.__enter__.return_value

        def reply(_):
            stop.cancel()
            return b'{"text":"late phrase"}'

        response.read.side_effect = reply
        with self.assertRaises(VoiceCancelled):
            self.recognizer.transcribe(self.frames, True, stop)
        self.h.pool.release.assert_called_once()

    def test_oversized_or_playback_input_never_uploads(self):
        for frames in (
            (AudioFrame((0.1,), 0, "fixture", origin=Origin.PLAYBACK),),
            (AudioFrame((0.1,) * 16000, 0, "fixture"),) * 16,
        ):
            with self.assertRaises(VoiceError):
                self.recognizer.transcribe(frames, True, StopToken())
        self.recognizer.opener.open.assert_not_called()

    def test_cloud_recognition_requires_live_surface_consent_even_with_a_key(self):
        from oscar.desktop_voice import DesktopVoice

        core = MagicMock()
        session = MagicMock()
        core.store.get.return_value = {"enabled": False}
        recognizer = MagicMock(local=False)
        voice = DesktopVoice(core, MagicMock(), recognizer)
        with self.assertRaises(PermissionError):
            voice.authorize_recognition(session)
        recognizer.ready.assert_not_called()
        core.store.get.return_value = {"enabled": True}
        voice.authorize_recognition(session)
        recognizer.ready.assert_called_once()
