"""Synthetic speech uses the same Core admission, authority and result as text."""

import base64
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from queue import Empty, Queue
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from oscar.desktop_voice import DesktopVoice, configured_voice, grant_continuous_voice
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
            muted=False,
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


class Wake:
    def detect(self, frame):
        return frame.samples[0] == 0.7

    def reset(self):
        pass


class Vad:
    def speech(self, frame):
        return frame.samples[0] > 0

    def reset(self):
        pass


class LiveFrames:
    def __init__(self):
        self.queue = Queue()
        self.closed = Event()

    def frames(self, stop):
        while not stop.event.is_set():
            try:
                yield self.queue.get(timeout=0.02)
            except Empty:
                continue

    def close(self):
        self.closed.set()

    def utterance(self, start=1):
        for value, offset in ((0.7, 0), (0.2, 0.1), (0, 0.8)):
            self.queue.put(
                AudioFrame((value,) * 512, start + offset, "synthetic", origin=Origin.SIMULATED)
            )


class ContinuousVoiceTests(unittest.TestCase):
    call = VoiceDialogueTests.call
    activate = VoiceDialogueTests.activate

    def setUp(self):
        test_desktop.DesktopTests.setUp(self)
        for kind, identifier in (("node", self.session.node_id), ("session", self.session.id)):
            row = self.h.store.get(kind, identifier)
            row["scopes"] = [*row["scopes"], "desktop:voice:continuous"]
            self.h.store.put(kind, identifier, row)

    def continuous(self, **kwargs):
        capture = LiveFrames()
        voice = DesktopVoice(
            self.core,
            capture,
            Recognizer("What is two plus three?"),
            wake=Wake(),
            vad=Vad(),
            muted=False,
            **kwargs,
        )
        self.core.voice = voice
        self.addCleanup(voice.close)
        return voice, capture

    def wait_for(self, predicate):
        until = monotonic() + 4
        while monotonic() < until:
            if predicate():
                return
            sleep(0.01)
        self.fail("voice condition did not become observable")

    def test_wake_routes_two_turns_through_existing_ask_without_retaining_audio(self):
        voice, capture = self.continuous()
        self.call("voice", {"operation": "listen"})
        self.assertEqual([], self.h.store.all("task"))
        capture.utterance()
        self.wait_for(
            lambda: len(self.h.store.all("task")) == 1
            and voice.thread is not None
            and not voice.thread.is_alive()
        )
        self.assertEqual("planned", voice.view["state"])
        capture.utterance(3)
        self.wait_for(lambda: len(self.h.store.all("task")) == 2)
        self.assertEqual([], self.h.store.all("action"))
        self.assertEqual([], self.h.store.all("voice_recording"))
        self.call("voice", {"operation": "cancel"})
        self.wait_for(lambda: not voice.listener_thread.is_alive())
        self.assertTrue(capture.closed.is_set())

    def test_muted_or_missing_separate_grant_cannot_open_input(self):
        voice, capture = self.continuous()
        voice.muted = True
        with self.assertRaises(PermissionError):
            voice.listen(self.session)
        voice.muted = False
        row = self.h.store.get("session", self.session.id)
        row["scopes"].remove("desktop:voice:continuous")
        self.h.store.put("session", self.session.id, row)
        with self.assertRaises(PermissionError):
            voice.listen(self.session)
        self.assertIsNone(voice.listener_thread)
        self.assertTrue(capture.queue.empty())

    def test_grant_revocation_stops_live_loop_and_cannot_issue_transcript(self):
        voice, capture = self.continuous()
        voice.listen(self.session)
        row = self.h.store.get("session", self.session.id)
        row["scopes"].remove("desktop:voice:continuous")
        self.h.store.put("session", self.session.id, row)
        capture.utterance()
        self.wait_for(lambda: not voice.listener_thread.is_alive())
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual("off", voice.view["voice_state"])

    def test_playback_and_uncertain_frames_cannot_wake_or_transcribe(self):
        class Reference:
            def clean(self, frame, speaking):
                from oscar.voice_runtime import AcousticDecision

                return AcousticDecision(frame, "uncertain", "synthetic")

        voice, capture = self.continuous(reference=Reference())
        voice.listen(self.session)
        capture.utterance()
        self.wait_for(lambda: capture.queue.empty())
        self.assertEqual([], self.h.store.all("task"))
        self.assertEqual("aware", voice.acoustic.state)

    def test_explicit_device_settings_persist_muted_without_ever_opening_audio(self):
        path = self.root / "voice.json"
        path.write_text(
            json.dumps(
                {"version": 1, "root": str(self.root), "input_device": 7, "output_device": None}
            )
        )
        with (
            patch("oscar.voice_adapters.FasterWhisper") as recognizer,
            patch("oscar.voice_adapters.SoundDeviceCapture") as capture,
            patch("oscar.voice_adapters.optional") as optional,
        ):
            inventory = [
                {
                    "name": "Synthetic microphone " + str(index),
                    "hostapi": 0,
                    "max_input_channels": 1,
                    "max_output_channels": 0,
                }
                for index in range(5)
            ]
            optional.return_value.query_devices.side_effect = lambda index=None: (
                inventory if index is None else inventory[index]
            )
            optional.return_value.query_hostapis.return_value = {"name": "Synthetic host"}
            recognizer.return_value.local = True
            capture.side_effect = lambda device: type(
                "Capture",
                (),
                {
                    "device": device,
                    "frames": lambda *_: self.fail("audio opened"),
                    "close": lambda *_: None,
                },
            )()
            voice = configured_voice(self.core, path)
            self.assertTrue(voice.muted)
            self.core.voice = voice
            with self.assertRaises(PermissionError):
                voice.start(self.session)
            voice.devices(self.session)
            inventory[4]["name"] = "Unexpected replacement"
            with self.assertRaises(VoiceError):
                voice.configure(self.session, muted=False, input_device=4, output_device=None)
            self.assertEqual(1, json.loads(path.read_text())["version"])
            inventory[4]["name"] = "Synthetic microphone 4"
            configured = self.call(
                "voice",
                {
                    "operation": "configure",
                    "muted": False,
                    "input_device": 4,
                    "output_device": None,
                },
            )
            self.assertFalse(configured["muted"])
            self.assertEqual(4, configured["input_device"])
            self.assertEqual(False, json.loads(path.read_text())["muted"])
            self.assertEqual(
                "Synthetic microphone 4", json.loads(path.read_text())["input_identity"]["name"]
            )
            restarted = configured_voice(self.core, path)
            self.assertFalse(restarted.muted)
            self.assertIsNone(restarted.listener_thread)
            self.call("voice", {"operation": "mute"})
            self.assertTrue(configured_voice(self.core, path).muted)
            self.assertIsNone(voice.listener_thread)

    def test_device_inventory_is_real_bounded_metadata_without_opening_streams(self):
        voice, _ = self.continuous()
        with patch("oscar.voice_adapters.optional") as optional:
            sd = optional.return_value
            inventory = [
                {
                    "name": "Synthetic input",
                    "hostapi": 0,
                    "max_input_channels": 1,
                    "max_output_channels": 0,
                },
                {
                    "name": "Synthetic output",
                    "hostapi": 0,
                    "max_input_channels": 0,
                    "max_output_channels": 2,
                },
            ]
            sd.query_devices.side_effect = (
                lambda index=None: inventory if index is None else inventory[index]
            )
            sd.query_hostapis.return_value = {"name": "Synthetic host"}
            result = voice.devices(self.session)
            self.assertEqual([0, 1], [d["id"] for d in result["devices"]])
            self.assertEqual([True, False], [d["input"] for d in result["devices"]])
            sd.InputStream.assert_not_called()
            sd.RawOutputStream.assert_not_called()

    def test_lost_control_connection_stops_capture_without_needing_a_remote_cancel(self):
        voice, capture = self.continuous()
        voice.listen(self.session)
        voice.listener_seen = monotonic() - 11
        capture.utterance()
        self.wait_for(lambda: not voice.listener_thread.is_alive())
        self.assertEqual([], self.h.store.all("task"))
        self.assertTrue(capture.closed.is_set())

    def test_revoked_continuous_grant_during_stt_cannot_issue_delayed_transcript(self):
        class HeldRecognizer(Recognizer):
            entered, release = Event(), Event()

            def transcribe(self, frames, final, stop):
                self.entered.set()
                self.release.wait(3)
                return super().transcribe(frames, final, stop)

        voice, capture = self.continuous()
        recognizer = HeldRecognizer("What is two plus three?")
        voice.recognizer = recognizer
        voice.listen(self.session)
        capture.utterance()
        self.assertTrue(recognizer.entered.wait(3))
        row = self.h.store.get("session", self.session.id)
        row["scopes"].remove("desktop:voice:continuous")
        self.h.store.put("session", self.session.id, row)
        recognizer.release.set()
        self.wait_for(lambda: not voice.thread.is_alive())
        self.assertEqual([], self.h.store.all("task"))

    def test_human_barge_in_interrupts_only_output_then_admits_next_wake_turn(self):
        class HumanReference:
            def clean(self, frame, speaking):
                from oscar.voice_runtime import AcousticDecision

                return AcousticDecision(frame, "human", "synthetic-human")

        class HeldPlayback(Playback):
            entered = Event()

            def play(self, chunk, stop):
                self.entered.set()
                stop.event.wait(3)
                stop.check()

        self.activate()
        speech, playback = Speech(), HeldPlayback()
        voice, capture = self.continuous(
            reference=HumanReference(),
            synthesis=SynthesisChain((speech,)),
            playback=playback,
            profile=VoiceProfile(provider="synthetic", fallback=()),
        )
        voice.listen(self.session)
        capture.utterance()
        self.assertTrue(playback.entered.wait(3))
        first = self.h.store.all("task")[0]["id"]
        for value, at in ((0.2, 3), (0.2, 3.1), (0.2, 3.2), (0.2, 3.3), (0, 4)):
            capture.queue.put(AudioFrame((value,) * 512, at, "synthetic", origin=Origin.SIMULATED))
        self.wait_for(lambda: len(self.h.store.all("task")) == 2)
        self.assertTrue(playback.cancelled)
        self.assertEqual("verified", self.h.store.task(first).state)
        self.wait_for(lambda: len(self.h.store.all("action")) == 2)
        self.assertEqual(2, len(self.h.store.all("task")))

    def test_selected_trusted_local_grant_never_elevates_other_sessions_or_opens_audio(self):
        row = self.h.store.get("session", self.session.id)
        row["scopes"].remove("desktop:voice:continuous")
        self.h.store.put("session", self.session.id, row)
        other = self.h.grid.pair(self.session.node_id, self.scopes)
        grant_continuous_voice(self.core, self.session.id)
        self.assertIn("desktop:voice:continuous", self.core.grants(self.session))
        self.assertNotIn("desktop:voice:continuous", self.core.grants(other))
        row["revoked"] = True
        self.h.store.put("session", self.session.id, row)
        with self.assertRaises(PermissionError):
            grant_continuous_voice(self.core, self.session.id)
        for invalid in ("", "*", True, "g" * 32):
            with self.assertRaises(ValueError):
                grant_continuous_voice(self.core, invalid)

    def test_pinned_microphone_and_output_fail_before_opening_changed_device(self):
        from oscar.voice_adapters import PlaybackReference, SoundDeviceCapture, SoundDevicePlayback
        from oscar.voice_contracts import StopToken

        identity = {
            "name": "Selected",
            "host_api": "Synthetic host",
            "input_channels": 1,
            "output_channels": 1,
        }
        capture = SoundDeviceCapture(2)
        capture.require_identity, capture.expected_identity = True, identity
        output = SoundDevicePlayback(2, PlaybackReference())
        output.require_identity, output.expected_identity = True, identity
        with patch("oscar.voice_adapters.optional") as optional:
            sd = optional.return_value
            sd.query_devices.return_value = {
                "name": "Different device",
                "hostapi": 0,
                "max_input_channels": 1,
                "max_output_channels": 1,
            }
            sd.query_hostapis.return_value = {"name": "Synthetic host"}
            with self.assertRaises(VoiceError):
                next(iter(capture.frames(StopToken())))
            with self.assertRaises(VoiceError):
                output.play(
                    AudioChunk(b"\0\0" * 512, 16000, "synthetic", "voice", "utterance"), StopToken()
                )
            sd.InputStream.assert_not_called()
            sd.RawOutputStream.assert_not_called()
            sd.query_devices.return_value["name"] = "Selected"
            capture.validate_device()
            sd.query_hostapis.return_value = {"name": "Different host"}
            with self.assertRaises(VoiceError):
                capture.validate_device()
            capture.expected_identity = None
            with self.assertRaises(VoiceError):
                capture.validate_device()
