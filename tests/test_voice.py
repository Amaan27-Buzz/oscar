"""SIMULATED voice contracts plus real existing Core handoff; no device claims."""

import math
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path

from oscar.contracts import Epistemic, TaskState
from oscar.harness import Harness
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.voice_contracts import (
    AudioChunk,
    AudioFrame,
    Origin,
    StopToken,
    Transcript,
    VoiceCancelled,
    VoiceError,
    VoiceProfile,
    VoiceResponse,
)
from oscar.voice_core import VoiceCore, addition_intent
from oscar.voice_identity import PersonaProfile, VoiceMap, VoiceMatch
from oscar.voice_runtime import (
    AcousticDecision,
    RecognitionChain,
    SynthesisChain,
    VoiceArbiter,
    VoiceSession,
    WakeClaim,
)


def frame(at: float, speech: bool = True, origin: Origin = Origin.SIMULATED) -> AudioFrame:
    return AudioFrame((0.5 if speech else 0.0,) * 512, at, "simulated-node", origin=origin)


class FixtureWake:
    def __init__(self, detected: bool = False):
        self.detected = detected

    def detect(self, frame: AudioFrame) -> bool:
        return self.detected

    def reset(self) -> None:
        pass


class FixtureVAD:
    def speech(self, frame: AudioFrame) -> bool:
        return bool(frame.samples[0])

    def reset(self) -> None:
        pass


class FixtureSTT:
    def __init__(self, id: str, local: bool = True, fail: bool = False):
        self.id, self.local, self.fail = id, local, fail
        self.calls = 0

    def transcribe(
        self, frames: tuple[AudioFrame, ...], final: bool, stop: StopToken
    ) -> Transcript:
        self.calls += 1
        stop.check()
        if self.fail:
            raise VoiceError("provider failure")
        return Transcript("2 + 3", final, "en", None, 0, 1, self.id, status="SIMULATED")


class FixtureTTS:
    def __init__(self, id: str, local: bool = True, fail: bool = False, partial: bool = False):
        self.id, self.local, self.fail, self.partial = id, local, fail, partial
        self.calls = 0

    def synthesize(
        self, text: str, profile: VoiceProfile, utterance_id: str, stop: StopToken
    ) -> Iterable[AudioChunk]:
        self.calls += 1
        stop.check()
        if self.partial:
            yield AudioChunk(b"\0\0", 16000, self.id, "original", utterance_id, "SIMULATED")
        if self.fail:
            raise VoiceError("provider failure")
        yield AudioChunk(b"\0\0", 16000, self.id, "original", utterance_id, "SIMULATED")


class VoiceLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.interrupted = 0

        def interrupt() -> None:
            self.interrupted += 1

        self.session = VoiceSession(FixtureWake(), FixtureVAD(), interrupt, max_seconds=1)

    def feed(
        self, at: float, speech: bool = True, classification: str = "human"
    ) -> tuple[AudioFrame, ...] | None:
        return self.session.feed(AcousticDecision(frame(at, speech), classification, "fixture"))

    def test_no_wake_and_bounded_awareness_events(self) -> None:
        for i in range(200):
            self.feed(i * 0.032)
        self.assertEqual(self.session.state, "aware")
        self.assertFalse(self.session.frames)
        self.assertLessEqual(len(self.session.events), 128)
        self.assertTrue(all(e.status == "SIMULATED" for e in self.session.events))

    def test_wake_speech_start_end(self) -> None:
        self.session.wake = FixtureWake(True)
        self.feed(0.01)
        self.feed(0.05)
        self.feed(0.1)
        self.assertEqual(self.session.state, "listening")
        ended = self.feed(0.8, False)
        self.assertIsNotNone(ended)
        self.assertEqual(self.session.state, "processing")
        self.assertEqual([e.kind for e in self.session.events][-1], "speech_ended")

    def test_manual_fallback_and_timeout_without_speech(self) -> None:
        self.session.activate()
        self.feed(0.01, False)
        self.assertIsNone(self.feed(1.1, False))
        self.assertEqual(self.session.state, "aware")

    def test_self_output_cannot_wake_or_create_speaker_turn(self) -> None:
        self.session.wake = FixtureWake(True)
        self.session.speaking()
        for i in range(50):
            self.feed(0.01 + i * 0.032, classification="self_output")
        self.assertEqual(self.session.state, "speaking")
        self.assertFalse(self.session.frames)
        self.assertEqual(self.interrupted, 0)

    def test_human_barge_in_keeps_prefix_and_interrupts_once(self) -> None:
        self.session.speaking()
        for at in (0.01, 0.042, 0.074):
            self.feed(at)
        self.assertEqual(self.session.state, "listening")
        self.assertEqual(self.interrupted, 1)
        self.assertEqual(len(self.session.frames), 3)
        self.assertIsNotNone(self.feed(0.8, False))

    def test_uncertain_output_does_not_interrupt(self) -> None:
        self.session.speaking()
        for i in range(8):
            self.feed(0.1 + i * 0.032, classification="uncertain")
        self.assertEqual(self.interrupted, 0)

    def test_cancel_disabled_and_out_of_order(self) -> None:
        self.session.activate()
        self.feed(0.1)
        self.session.cancel(disable=True)
        self.assertFalse(self.session.frames)
        self.assertIsNone(self.feed(0.2))
        with self.assertRaises(PermissionError):
            self.session.activate()
        with self.assertRaises(ValueError):
            self.feed(0.15)

    def test_sample_bound_not_only_untrusted_timestamp(self) -> None:
        self.session.activate()
        result = None
        for i in range(32):
            result = self.feed(0.1 + i * 0.00001)
        self.assertIsNotNone(result)
        self.assertFalse(self.session.frames)

    def test_frame_and_transcript_validation(self) -> None:
        for value in (float("nan"), float("inf"), 2):
            with self.assertRaises(ValueError):
                AudioFrame((value,), 0, "node")
        with self.assertRaises(ValueError):
            Transcript("", True, "en", 2, 0, 1, "test")


class VoiceFallbackTests(unittest.TestCase):
    def test_stt_partials_final_failure_fallback_and_local_policy(self) -> None:
        cloud, bad, local = (
            FixtureSTT("cloud", False),
            FixtureSTT("bad", fail=True),
            FixtureSTT("local"),
        )
        chain = RecognitionChain((cloud, bad, local))
        self.assertFalse(chain.transcribe((frame(0),), False, StopToken()).final)
        self.assertTrue(chain.transcribe((frame(0),), True, StopToken()).final)
        self.assertEqual(cloud.calls, 0)
        self.assertEqual(chain.used, "local")
        with self.assertRaises(VoiceError):
            RecognitionChain((cloud, bad)).transcribe((frame(0),), True, StopToken())

    def test_cancellation_never_falls_back(self) -> None:
        token = StopToken()
        token.cancel()
        adapter = FixtureSTT("local")
        with self.assertRaises(VoiceCancelled):
            RecognitionChain((adapter,)).transcribe((frame(0),), True, token)
        self.assertEqual(adapter.calls, 0)

    def test_tts_fallback_voice_identity_and_local_mode(self) -> None:
        bad, cloud, local = (
            FixtureTTS("bad", fail=True),
            FixtureTTS("cloud", False),
            FixtureTTS("local"),
        )
        profile = VoiceProfile(provider="bad", fallback=("cloud", "local"))
        chunks = list(
            SynthesisChain((bad, cloud, local)).synthesize("hello", profile, "turn", StopToken())
        )
        self.assertEqual(chunks[0].provider, "local")
        self.assertEqual(chunks[0].utterance_id, "turn")
        self.assertEqual(profile.identity, "oscar")
        self.assertEqual(cloud.calls, 0)

    def test_partial_tts_failure_does_not_repeat_audible_content(self) -> None:
        bad, local = FixtureTTS("bad", fail=True, partial=True), FixtureTTS("local")
        with self.assertRaises(VoiceError):
            list(
                SynthesisChain((bad, local)).synthesize(
                    "hello", VoiceProfile(provider="bad", fallback=("local",)), "turn", StopToken()
                )
            )
        self.assertEqual(local.calls, 0)

    def test_active_synthesis_cancel_never_switches_provider(self) -> None:
        token = StopToken()
        first, fallback = FixtureTTS("first", partial=True), FixtureTTS("fallback")
        stream = iter(
            SynthesisChain((first, fallback)).synthesize(
                "hello", VoiceProfile(provider="first", fallback=("fallback",)), "turn", token
            )
        )
        next(stream)
        token.cancel()
        with self.assertRaises(VoiceCancelled):
            next(stream)
        self.assertEqual(fallback.calls, 0)


class SpeakerAndPersonaTests(unittest.TestCase):
    def test_explicit_enrollment_match_reject_uncertain_and_no_voice_only_high_risk(self) -> None:
        match = VoiceMatch("model")
        with self.assertRaises(PermissionError):
            match.enroll("owner", (1.0, 0.0), confirmed=False)
        match.enroll("owner", (1.0, 0.0), confirmed=True)
        yes = match.verify((1.0, 0.0), source_model="model")
        self.assertEqual(yes.outcome, "accepted")
        self.assertEqual(match.verify((0.0, 1.0), source_model="model").outcome, "rejected")
        self.assertEqual(match.verify((0.7, 0.7), source_model="model").outcome, "uncertain")
        self.assertEqual(match.verify((1.0, 0.0), source_model="other").outcome, "uncertain")
        self.assertFalse(match.permits(yes, granted=True, policy_allowed=True, risk="critical"))
        self.assertFalse(match.permits(yes, granted=False, policy_allowed=True, risk="low"))
        self.assertFalse(match.permits(yes, granted=True, policy_allowed=False, risk="low"))
        self.assertTrue(match.permits(yes, granted=True, policy_allowed=True, risk="low"))
        match.forget("owner")
        self.assertEqual(match.verify((1.0, 0.0), source_model="model").outcome, "uncertain")

    def test_map_known_unknown_change_multiple_and_separate_authorization(self) -> None:
        map_ = VoiceMap("model")
        map_.link("person", (1.0, 0.0), confirmed=True)
        self.assertEqual(
            map_.observe(((1.0, 0.0),), source_model="model")[0].outcome, "known_probable"
        )
        changed = map_.observe(((0.0, 1.0),), source_model="model")
        self.assertTrue(changed[0].outcome.startswith("speaker_changed:unknown"))
        multi = map_.observe(((1.0, 0.0), (0.0, 1.0)), source_model="model")
        self.assertTrue(all(p.outcome.startswith("multiple:") for p in multi))
        self.assertEqual(
            VoiceMatch("model").verify((1.0, 0.0), source_model="model").outcome, "uncertain"
        )

    def test_distinct_unknown_speakers_remain_anonymous(self) -> None:
        map_ = VoiceMap("model")
        first = map_.observe(((1.0, 0.0),), source_model="model")[0]
        second = map_.observe(((0.0, 1.0),), source_model="model")[0]
        self.assertNotEqual(first.speaker_id, second.speaker_id)
        self.assertEqual(second.outcome, "speaker_changed:unknown")
        self.assertEqual(
            map_.observe(((1.0, 0.0),), source_model="model")[0].speaker_id, first.speaker_id
        )

    def test_self_voice_excluded_and_invalid_embedding_safe(self) -> None:
        match, map_ = VoiceMatch("model"), VoiceMap("model")
        match.enroll("owner", (1.0, 0.0), confirmed=True)
        self.assertEqual(
            match.verify((1.0, 0.0), source_model="model", self_output=True).outcome, "uncertain"
        )
        self.assertFalse(map_.observe(((1.0, 0.0),), source_model="model", self_output=True))
        self.assertEqual(
            match.verify((float("nan"), 0.0), source_model="model").outcome, "uncertain"
        )

    def test_persona_preserves_truth_state_permissions_evidence_and_limits(self) -> None:
        for state in (TaskState.VERIFIED, TaskState.BLOCKED, TaskState.FAILED, TaskState.UNKNOWN):
            response = VoiceResponse(
                "Claim and required warning.",
                "task",
                state,
                Epistemic.UNKNOWN,
                ("event",),
                ("read",),
                ("not physically verified",),
            )
            expressive, voice = PersonaProfile(warmth=90).express(response, VoiceProfile())
            self.assertEqual(expressive.state, response.state)
            self.assertEqual(expressive.epistemic, response.epistemic)
            self.assertEqual(expressive.permissions, response.permissions)
            self.assertEqual(expressive.evidence_ids, response.evidence_ids)
            self.assertEqual(expressive.limitations, response.limitations)
            self.assertIn(response.text, expressive.text)
            self.assertEqual(voice.identity, "oscar")
            serious, _ = PersonaProfile(warmth=90).express(response, VoiceProfile(), serious=True)
            self.assertEqual(serious, response)


class ArbitrationTests(unittest.TestCase):
    def test_competing_nodes_sticky_owner_expiry_handoff_and_loss(self) -> None:
        now = [100.0]
        available = {"desktop", "reference-phone"}
        arbiter = VoiceArbiter(lambda n: n in available, lambda: now[0])
        owner, generation = arbiter.choose(
            (WakeClaim("desktop", 100, 0.8, 0.5), WakeClaim("reference-phone", 100, 0.9, 0.9))
        )
        self.assertEqual(owner, "reference-phone")
        self.assertEqual(arbiter.choose((WakeClaim("desktop", 100, 1, 1),))[0], owner)
        self.assertTrue(arbiter.handoff(owner, "desktop", generation))
        self.assertFalse(arbiter.renew(owner, generation))
        available.remove("desktop")
        now[0] += 0.1
        self.assertIsNone(arbiter.choose(())[0])
        self.assertIsNone(arbiter.choose((WakeClaim("unpaired", 100, 1, 1),))[0])
        now[0] += 1
        self.assertIsNone(arbiter.choose((WakeClaim("reference-phone", 100, 1, 1),))[0])


class VoiceCoreTests(unittest.TestCase):
    def test_real_controller_task_verification_and_provisional_denial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with Harness(
                root / "core.db", root / "workspace", Path("config/development-models.json")
            ) as h:
                core = VoiceCore(
                    h.runtime, PersonalPolicy(h.store), {h.node_id: (h.dispatcher, h.session)}
                )
                partial = Transcript("2 + 3", False, "en", None, 0, 1, "SIMULATED")
                with self.assertRaises(ValueError):
                    core.handle(partial, StopToken(), granted=frozenset({"math"}))
                self.assertFalse(h.store.all("task"))
                final = Transcript(
                    "Oscar what is two plus three?", True, "en", None, 0, 1, "SIMULATED"
                )
                match = VoiceMatch("fixture")
                match.enroll("owner", (1.0, 0.0), confirmed=True)
                rejected = match.verify((0.0, 1.0), source_model="fixture")
                self.assertEqual(
                    core.handle(
                        final,
                        StopToken(),
                        granted=frozenset({"math"}),
                        require_match=True,
                        speaker=rejected,
                    ).state,
                    TaskState.BLOCKED,
                )
                self.assertFalse(h.store.all("task"))
                denied = core.handle(final, StopToken(), granted=frozenset())
                self.assertEqual(denied.state, TaskState.BLOCKED)
                result = core.handle(final, StopToken(), granted=frozenset({"math"}))
                self.assertEqual(result.state, TaskState.VERIFIED)
                self.assertEqual(result.epistemic, Epistemic.VERIFIED)
                self.assertTrue(result.evidence_ids)
                self.assertEqual(result.text, "The result is 5.")
                core.policy.save(
                    PolicyRule("deny", "math.add", PolicyEffect.DENY, "owner", 1, 1, {}),
                    owner_authorized=True,
                )
                self.assertEqual(
                    core.handle(final, StopToken(), granted=frozenset({"math"})).state,
                    TaskState.BLOCKED,
                )

    def test_unsupported_transcript_never_creates_external_mutation(self) -> None:
        self.assertIsNone(addition_intent("send the email"))
        self.assertIsNone(addition_intent("2 + 3; delete files"))
        self.assertEqual(addition_intent("Oscar. What is 2 plus 3?"), "2 + 3")


class OptionalReferenceAcousticTests(unittest.TestCase):
    @unittest.skipUnless(
        __import__("importlib.util").util.find_spec("numpy"),
        "optional numpy reference executor not installed",
    )
    def test_playback_echo_and_double_talk_reference(self) -> None:
        import numpy as np

        from oscar.voice_adapters import PlaybackReference

        reference = PlaybackReference()
        # Distinct bounded tones model echo and independent human residual, not room acoustics.
        echo = np.asarray([math.sin(i * 0.13) * 0.2 for i in range(1600)])
        pcm = (echo * 32767).astype("<i2").tobytes()
        reference.add(pcm, 16000, 1.0)
        own = AudioFrame(tuple(float(v) for v in echo[:512]), 1.0, "node", origin=Origin.SIMULATED)
        self.assertEqual(reference.clean(own, True).classification, "self_output")
        human = tuple(float(echo[i] + math.sin(i * 0.29) * 0.2) for i in range(512))
        clean = reference.clean(AudioFrame(human, 1.0, "node", origin=Origin.SIMULATED), True)
        self.assertEqual(clean.classification, "human")
        missing = PlaybackReference().clean(own, True)
        self.assertEqual(missing.classification, "uncertain")
