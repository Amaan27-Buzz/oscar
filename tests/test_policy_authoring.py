import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oscar.policy import PersonalPolicy
from oscar.policy_authoring import PolicyAuthoring
from oscar.storage import Store


class PolicyAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "policy.sqlite"
        self.store = Store(self.path)
        self.policy = PersonalPolicy(self.store)
        self.author = PolicyAuthoring(self.policy)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_show_confirm_restart_and_action_ask(self):
        candidate = self.author.propose("Never send messages without asking me.")
        self.assertIn("calendar invitations", candidate["interpretation"])
        self.assertEqual([], self.policy.rules())
        self.store.close()
        self.store = Store(self.path)
        self.policy = PersonalPolicy(self.store)
        self.author = PolicyAuthoring(self.policy)
        self.author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        self.store.close()
        self.store = Store(self.path)
        self.policy = PersonalPolicy(self.store)
        scope = "connectors:external-communication"
        self.assertFalse(self.policy.evaluate(scope, (scope,), frozenset({scope})).allowed)
        self.assertTrue(
            self.policy.evaluate(scope, (scope,), frozenset({scope}), confirmed=True).allowed
        )
        self.assertFalse(self.policy.evaluate(scope, (scope,), frozenset(), confirmed=True).allowed)

    def test_ambiguity_and_composite_interpretation_rejected(self):
        for text in (
            "send when appropriate",
            "never send messages except urgent ones",
            "never send messages; send without asking",
            "ask me sometimes",
        ):
            with self.assertRaises(ValueError):
                self.author.propose(text)
        self.assertEqual([], self.store.all("policy_candidate"))

    def test_owner_and_exact_interpretation_required(self):
        c = self.author.propose("Never send messages")
        with self.assertRaises(PermissionError):
            self.author.confirm(c["id"], c["review_digest"], owner_authorized=False)
        with self.assertRaises(ValueError):
            self.author.confirm(c["id"], "different-review", owner_authorized=True)
        self.assertEqual([], self.policy.rules())
        self.author.confirm(c["id"], c["review_digest"], owner_authorized=True)
        with self.assertRaises(ValueError):
            self.author.confirm(c["id"], c["review_digest"], owner_authorized=True)

    def test_conflicting_interpretations_do_not_silently_replace(self):
        c = self.author.propose("Never send messages")
        self.author.confirm(c["id"], c["review_digest"], owner_authorized=True)
        c = self.author.propose("You may send messages without asking me")
        with self.assertRaisesRegex(ValueError, "conflicting"):
            self.author.confirm(c["id"], c["review_digest"], owner_authorized=True)
        self.assertEqual("candidate", self.store.get("policy_candidate", c["id"])["state"])
        self.assertEqual(1, len(self.policy.rules()))
