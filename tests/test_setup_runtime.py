import json
import unittest

from oscar.credentials import CredentialPool
from oscar.models import ProviderSpec
from oscar.policy import PersonalPolicy, PolicyEffect, PolicyRule
from oscar.setup_runtime import SetupRuntime
from oscar.storage import StateConflict
from oscar.voice_contracts import StopToken, Transcript
from oscar.voice_core import VoiceCore
from tests.support import Rig
from tests.test_oauth_device import TestVault


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.r = Rig()
        self.addCleanup(self.r.close)
        provider = ProviderSpec(
            "fixture", "openai", "https://example.test", {"fixture-slot": "FIXTURE_KEY"}
        )
        self.pool = CredentialPool([provider], environ={"FIXTURE_KEY": "old-environment-secret"})
        self.vault = TestVault()
        self.setup = SetupRuntime(self.r.runtime, self.pool, self.vault)
        self.r.runtime.setup = self.setup

    def test_configuration_is_not_authority_and_resumes(self):
        with self.assertRaises(PermissionError):
            self.setup.configure("persona", {}, owner_authorized=False)
        self.setup.configure("persona", {"warmth": 80}, owner_authorized=True)
        self.setup.configure(
            "preferences", {"reduced_motion": True, "show_presence": False}, owner_authorized=True
        )
        self.setup.configure("voice", {"rate": 1.1}, owner_authorized=True)
        restarted = SetupRuntime(self.r.runtime, self.pool, self.vault)
        self.assertEqual(80, restarted.profile("persona")["warmth"])
        self.assertEqual(1.1, restarted.voice_profile().rate)
        self.assertFalse(restarted.snapshot()["voice"]["operational"])
        self.assertEqual("unavailable", restarted.snapshot()["policy"]["full_access"])
        self.assertEqual([], self.r.store.all("perception_source"))

    def test_native_binding_rechecks_deletion_and_never_uses_old_copy(self):
        self.setup.provider("fixture-slot", "synthetic-new-secret", owner_authorized=True)
        self.assertEqual("synthetic-new-secret", self.pool.secret_for_adapter("fixture-slot"))
        snapshot = self.setup.snapshot()
        self.assertTrue(snapshot["provider"]["credential_available"])
        self.assertFalse(snapshot["provider"]["operational"])
        self.assertNotIn("synthetic-new-secret", json.dumps(snapshot))
        self.assertNotIn("synthetic-new-secret", json.dumps(self.r.store.all("setup_provider")))
        reference = self.r.store.all("setup_provider")[0]["reference"]
        self.vault.delete(reference)
        self.assertEqual("", self.pool.secret_for_adapter("fixture-slot"))
        self.assertFalse(self.pool.eligible("fixture-slot"))
        self.assertEqual("<redacted>", self.pool.redact("synthetic-new-secret"))

    def test_interrupted_secret_write_is_recovered_without_replay(self):
        original = self.vault.put

        def crash(secret, **kwargs):
            original(secret, **kwargs)
            raise OSError("injected interrupted setup")

        self.vault.put = crash
        with self.assertRaises(OSError):
            self.setup.provider("fixture-slot", "synthetic-interrupted", owner_authorized=True)
        self.assertFalse(self.pool.eligible("fixture-slot"))
        restarted = SetupRuntime(self.r.runtime, self.pool, self.vault)
        self.assertEqual(1, restarted.recover())
        self.assertEqual({}, self.vault.values)
        self.assertEqual("revoked", self.r.store.all("setup_provider")[0]["state"])

    def test_revocation_during_vault_acquisition_fails_closed(self):
        self.setup.provider("fixture-slot", "synthetic-revoked", owner_authorized=True)
        original = self.vault.read

        def revoke(reference, **kwargs):
            value = original(reference, **kwargs)
            self.setup.revoke_provider("fixture-slot", owner_authorized=True)
            return value

        self.vault.read = revoke
        self.assertEqual("", self.pool.secret_for_adapter("fixture-slot"))
        self.assertEqual({}, self.vault.values)

    def test_replacement_requires_revocation_and_profiles_reject_authority(self):
        self.setup.provider("fixture-slot", "synthetic-one", owner_authorized=True)
        with self.assertRaises(StateConflict):
            self.setup.provider("fixture-slot", "synthetic-two", owner_authorized=True)
        self.setup.revoke_provider("fixture-slot", owner_authorized=True)
        self.setup.provider("fixture-slot", "synthetic-two", owner_authorized=True)
        for section, data in (
            ("preferences", {"full_access": True}),
            ("voice", {"rate": True}),
            ("persona", {"warmth": True}),
        ):
            with self.assertRaises(ValueError):
                self.setup.configure(section, data, owner_authorized=True)

    def test_persona_and_policy_use_the_existing_voice_core(self):
        self.setup.configure("persona", {"warmth": 80}, owner_authorized=True)
        voice = VoiceCore(self.r.runtime, PersonalPolicy(self.r.store), self.r.transports)
        turn = Transcript("two plus two", True, "en", 0.99, 0, 1, "synthetic-transcript")
        result = voice.handle(turn, StopToken(), granted=frozenset({"math"}))
        self.assertEqual("verified", result.state)
        self.assertTrue(result.text.startswith("All right. "))
        now = self.r.clock()
        self.setup.policy(
            PolicyRule("deny-math", "math.add", PolicyEffect.DENY, "owner-setup", now, now, {}),
            owner_authorized=True,
        )
        self.assertEqual(
            "blocked", voice.handle(turn, StopToken(), granted=frozenset({"math"})).state
        )

    def test_other_relationship_cannot_read_or_rebind_configured_credentials(self):
        self.setup.provider("fixture-slot", "synthetic-scoped", owner_authorized=True)
        self.r.runtime.relationship_id = "other"
        other = SetupRuntime(self.r.runtime, CredentialPool([], environ={}), self.vault)
        self.assertFalse(other.snapshot()["provider"]["configured"])
        with self.assertRaises(PermissionError):
            other.configure("persona", {}, owner_authorized=True)

    def test_stale_revoke_does_not_overwrite_reenrollment(self):
        self.setup.provider("fixture-slot", "synthetic-old", owner_authorized=True)
        original = self.vault.delete

        def replace(reference):
            self.vault.delete = original
            self.setup.revoke_provider("fixture-slot", owner_authorized=True)
            self.setup.provider("fixture-slot", "synthetic-current", owner_authorized=True)
            original(reference)

        self.vault.delete = replace
        self.setup.revoke_provider("fixture-slot", owner_authorized=True)
        self.assertEqual("synthetic-current", self.pool.secret_for_adapter("fixture-slot"))

    def test_cold_restart_and_rotating_stream_redaction(self):
        self.setup.provider("fixture-slot", "short-fixture", owner_authorized=True)
        provider = ProviderSpec(
            "fixture", "openai", "https://example.test", {"fixture-slot": "FIXTURE_KEY"}
        )
        pool = CredentialPool([provider], environ={})
        SetupRuntime(self.r.runtime, pool, self.vault)
        self.assertTrue(pool.slots["fixture-slot"].present)
        chunks = []
        stream = pool.safe_stream(chunks.append)
        self.setup.revoke_provider("fixture-slot", owner_authorized=True)
        rotated = "longer-fixture-" + "x" * 120
        self.setup.provider("fixture-slot", rotated, owner_authorized=True)
        pool.secret_for_adapter("fixture-slot")
        stream(rotated[:60])
        stream(rotated[60:])
        stream.finish()
        self.assertNotIn(rotated, "".join(chunks))
