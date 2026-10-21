"""Synthetic speech uses the same Core admission, authority and result as text."""

import base64
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from threading import Event
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from oscar.desktop_voice import DesktopVoice, configured_voice
from oscar.voice_contracts import (
    AudioChunk,
    AudioFrame,
    Origin,
    Transcript,
    VoiceError,
    VoiceProfile,
)
from oscar.voice_runtime import SynthesisChain

from . import test_desktop


class Capture:
    def frames(self, stop):
        yield AudioFrame((0.1,) * 512, 1, "synthetic", origin=Origin.SIMULATED)

    def close(self):
        pass


class LocalConfigurationTests(unittest.TestCase):
    def test_preparation_requires_explicit_devices_but_opens_no_audio_stream(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "voice.json"
            config = {"version": 1, "root": directory, "input_device": 7, "output_device": None}
            path.write_text(json.dumps(config), encoding="utf-8")
            with (
                patch("oscar.voice_adapters.FasterWhisper") as stt,
                patch("oscar.voice_adapters.SoundDeviceCapture") as capture,
                patch("oscar.voice_adapters.SoundDevicePlayback") as playback,
            ):
                stt.return_value.local = True
                voice = configured_voice(None, path)
                self.assertEqual("Dictate", voice.mode)
                capture.assert_called_once_with(7)
                capture.return_value.frames.assert_not_called()
                playback.assert_not_called()
                for invalid in (
                    {**config, "input_device": True},
                    {**config, "output_device": -1},
                    {**config, "cloud": True},
                    {**config, "root": ""},
                ):
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        configured_voice(None, path)
                self.assertEqual(1, stt.call_count)


class Recognizer:
    id, local = "synthetic", True

    def __init__(self, text):
        self.text = text

    def transcribe(self, frames, final, stop):
        return Transcript(self.text, final, "en", None, 0, 1, self.id)


class Speech:
    id, local = "synthetic", True

    def __init__(self):
        self.texts = []

    def synthesize(self, text, profile, utterance_id, stop):
        self.texts.append(text)
        yield AudioChunk(b"\0\0" * 512, 16000, self.id, "synthetic", utterance_id)


class Playback:
    def __init__(self):
        self.chunks, self.cancelled, self.finished = [], False, False

    def play(self, chunk, stop):
        stop.check()
        self.chunks.append(chunk)

    def finish(self, utterance):
        self.finished = True

    def cancel(self):
        self.cancelled = True


class VoiceDialogueTests(unittest.TestCase):
    setUp = test_desktop.DesktopTests.setUp
    call = test_desktop.DesktopTests.call

    def activate(self, capability="math.add"):
        review = self.call(
            "authority_challenge",
            {
                "mode": "full",
                "lifetime_seconds": 600,
                "capabilities": [
                    {
                        "node_id": self.h.node_id,
                        "session_id": self.h.session.id,
                        "capability_id": capability,
                    }
                ],
                "account_ids": [],
                "resolve_ask_rules": [],
            },
        )
        signature = self.key.sign(
            base64.b64decode(review["signing_payload"]),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        self.call(
            "authority_complete",
            {
                "challenge_id": review["challenge_id"],
                "signature": base64.b64encode(signature).decode(),
            },
        )

    def voice(self, text="What is two plus three?", *, playback=None, recognizer=None):
        speech = Speech()
        playback = playback or Playback()
        self.core.voice = DesktopVoice(
            self.core,
            Capture(),
            recognizer or Recognizer(text),
            mode="Ask",
            synthesis=SynthesisChain((speech,)),
            playback=playback,
            profile=VoiceProfile(provider="synthetic", fallback=()),
        )
        return self.core.voice, speech, playback

    def run_voice(self, voice):
        voice.start(self.session)
        voice.thread.join(5)
        self.assertFalse(voice.thread.is_alive())
        return voice.inspect(self.session)

    def test_ask_preserves_pending_native_approval_and_speaks_that_boundary(self):
        voice, speech, playback = self.voice()
        view = self.run_voice(voice)
        self.assertEqual("planned", view["state"])
        self.assertTrue(view["approval_required"])
        self.assertEqual([], self.h.store.all("action"))
        self.assertIn("needs owner approval", speech.texts[0])
        self.assertTrue(playback.finished)
        self.assertEqual("reported", view["voice_output"])

    def test_signed_delegation_executes_natural_file_request_and_independently_verifies(self):
        self.activate("files.write")
        voice, speech, playback = self.voice(
            "Oscar, please write spoken.txt with text voice verified"
        )
        view = self.run_voice(voice)
        self.assertEqual("verified", view["state"])
        self.assertFalse(view["approval_required"])
        self.assertEqual(b"voice verified", self.h.files.read("spoken.txt"))
        self.assertTrue(view["evidence"])
        self.assertEqual([], self.h.store.all("sunday_challenge"))
        self.assertEqual(1, len(playback.chunks))
        self.assertIn("verified", speech.texts[0])

    def test_output_failure_keeps_verified_task_and_never_claims_nothing_executed(self):
        class FailedPlayback(Playback):
            def play(self, chunk, stop):
                raise VoiceError("synthetic output disconnected")

        self.activate()
        voice, _, playback = self.voice(playback=FailedPlayback())
        view = self.run_voice(voice)
        self.assertEqual(
            ("verified", "5", "failed"),
            (
                view["state"],
                view["value"],
                view["voice_output"],
            ),
        )
        self.assertTrue(playback.cancelled)
        self.assertEqual("verified", self.h.store.task(view["task_id"]).state)

    def test_barge_in_cancels_output_without_reversing_or_replaying_issued_task(self):
        class HeldPlayback(Playback):
            entered = Event()

            def play(self, chunk, stop):
                self.entered.set()
                stop.event.wait(3)
                stop.check()

        self.activate()
        voice, _, playback = self.voice(playback=HeldPlayback())
        voice.start(self.session)
        self.assertTrue(playback.entered.wait(3))
        task_id = voice.view["task_id"]
        cancelled = voice.cancel(self.session)
        voice.thread.join(3)
        self.assertFalse(voice.thread.is_alive())
        self.assertEqual(("verified", task_id), (cancelled["state"], cancelled["task_id"]))
        self.assertEqual("cancelled", cancelled["voice_state"])
        self.assertEqual("verified", self.h.store.task(task_id).state)
        self.assertEqual(1, len(self.h.store.all("action")))
        self.assertTrue(playback.cancelled)

    def test_cancelled_delayed_stt_cannot_reach_core(self):
        class HeldRecognizer(Recognizer):
            entered, release = Event(), Event()

            def transcribe(self, frames, final, stop):
                self.entered.set()
                self.release.wait(3)
                return super().transcribe(frames, final, stop)

        recognizer = HeldRecognizer("Please write spoken.txt with text cancelled")
        self.activate("files.write")
        voice, speech, playback = self.voice(recognizer=recognizer)
        voice.start(self.session)
        self.assertTrue(recognizer.entered.wait(3))
        voice.cancel(self.session)
        recognizer.release.set()
        voice.thread.join(3)
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual([], speech.texts)
        self.assertEqual([], playback.chunks)

    def test_provisional_transcript_and_provider_network_fallback_are_rejected(self):
        recognizer = Recognizer("2 + 3")
        transcript = recognizer.transcribe((), True, None)
        from oscar.voice_contracts import StopToken

        with self.assertRaises(ValueError):
            self.core.transcript(
                self.session, replace(transcript, final=False), StopToken(), mode="Ask"
            )
        with self.assertRaises(PermissionError):
            DesktopVoice(self.core, Capture(), recognizer, profile=VoiceProfile(local_only=False))
        self.assertEqual([], self.h.store.all("action"))

    def test_own_playback_origin_cannot_reach_stt_or_create_a_task(self):
        class OwnOutput(Capture):
            def frames(self, stop):
                yield AudioFrame((0.1,) * 512, 1, "oscar", origin=Origin.PLAYBACK)

        voice, speech, playback = self.voice()
        voice.capture = OwnOutput()
        self.assertEqual("blocked", self.run_voice(voice)["state"])
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual([], speech.texts)
        self.assertEqual([], playback.chunks)

    def test_voice_uses_shared_continuous_conversation_and_retention_grant(self):
        from oscar.grid import Node, NodeRole

        scopes = (*self.scopes, "desktop:conversation:read", "desktop:conversation:retain")
        self.h.grid.register(Node("voice-owner", NodeRole.DESKTOP, scopes))
        self.session = self.h.grid.pair("voice-owner", scopes)
        self.core.register_owner_key(self.session, self.encoded, owner_authorized=True)
        self.activate()
        voice, _, _ = self.voice()
        view = self.run_voice(voice)
        turns = self.core.conversation(self.session)["turns"]
        self.assertEqual(["owner", "oscar"], [turn["role"] for turn in turns])
        self.assertTrue(all(turn["retained"] for turn in turns))
        self.assertTrue(all(turn["task_id"] == view["task_id"] for turn in turns))
        self.assertEqual("2 + 3", turns[0]["text"])
