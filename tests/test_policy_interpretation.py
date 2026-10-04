import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from oscar.policy import PersonalPolicy
from oscar.policy_interpretation import OpenPolicyAuthoring
from oscar.storage import Store


class Interpreter:
    def __init__(self, rules=None, ambiguities=None):
        self.output = json.dumps({"rules": rules or [], "ambiguities": ambiguities or []})

    def interpret(self, text):
        return self.output


def rule(capability="machine.files.write", effect="ask", conditions=None, **extra):
    return {
        "capability": capability,
        "effect": effect,
        "conditions": conditions or {},
        "priority": 0,
        "preference": None,
        "expires_at": None,
        **extra,
    }


class InterpretationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "state.sqlite"
        self.store = Store(self.path)
        self.policy = PersonalPolicy(self.store)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def author(self, *rules, ambiguities=None):
        return OpenPolicyAuthoring(self.policy, Interpreter(list(rules), ambiguities))

    def test_candidate_is_inactive_exact_confirmation_then_later_behavior(self):
        author = self.author(rule())
        candidate = author.propose("Ask before modifying any file")
        self.assertEqual([], self.policy.rules())
        self.assertFalse(candidate["rules"][0]["user_authoritative"])
        self.assertIn("machine.files.write", candidate["interpretation"])
        with self.assertRaises(PermissionError):
            author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=False)
        author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        self.assertFalse(
            self.policy.evaluate(
                "machine.files.write", ("files:write",), frozenset({"files:write"})
            ).allowed
        )
        self.assertTrue(
            self.policy.evaluate(
                "machine.files.write", ("files:write",), frozenset({"files:write"}), confirmed=True
            ).allowed
        )
        self.store.close()
        self.store = Store(self.path)
        self.assertFalse(
            PersonalPolicy(self.store).evaluate("machine.files.write", (), frozenset()).allowed
        )

    def test_ambiguity_never_creates_rules(self):
        with self.assertRaisesRegex(ValueError, "clarification"):
            self.author(ambiguities=["Which tasks count as flexible?"]).propose("Move my stuff")
        self.assertEqual([], self.policy.rules())

    def test_conflicting_interpretations_block_atomically(self):
        author = self.author(rule(effect="allow"), rule(effect="deny"))
        candidate = author.propose("Allow and never allow the same file operation")
        with self.assertRaisesRegex(ValueError, "conflicting"):
            author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        self.assertEqual([], self.policy.rules())

    def test_tampered_or_wrong_digest_rejected(self):
        author = self.author(rule())
        candidate = author.propose("Ask before file mutation")
        with self.assertRaises(ValueError):
            author.confirm(candidate["id"], "different", owner_authorized=True)
        candidate["rules"][0]["effect"] = "allow"
        self.store.put("open_policy_candidate", candidate["id"], candidate)
        with self.assertRaises(ValueError):
            author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)

    def test_model_cannot_set_authority_or_unbounded_rule(self):
        for proposed in (
            rule(user_authoritative=True),
            rule(priority=100),
            rule(expires_at=float("inf")),
        ):
            with self.assertRaises(ValueError):
                self.author(proposed).propose("Owner rule")

    def test_allow_cannot_grant_permission_or_weaken_hard_safety(self):
        author = self.author(rule(effect="allow"))
        candidate = author.propose("Allow file changes within existing grants")
        author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        for flags in ({}, {"hard_allowed": False}, {"confirmation_required": True}):
            self.assertFalse(
                self.policy.evaluate(
                    "machine.files.write",
                    ("files:write",),
                    frozenset() if not flags else frozenset({"files:write"}),
                    **flags,
                ).allowed
            )

    def test_representative_scopes_and_conditions_expire(self):
        proposals = [
            rule("connectors:external-communication"),
            rule("memory.retain", "deny", {"source": "banking-notifications"}),
            rule("attention.interrupt", "ask", {"activity": "video", "urgency": "ordinary"}),
            rule("machine.files.delete"),
            rule("models.reason", "prefer", {"power": "battery"}, preference="local"),
            rule("calendar.move", "deny", {"block_type": "class"}),
        ]
        for proposed in proposals:
            author = self.author(proposed)
            candidate = author.propose("Synthetic owner policy scope")
            author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
            decision = self.policy.evaluate(
                proposed["capability"], (), frozenset(), context=proposed["conditions"]
            )
            self.assertEqual(proposed["effect"] == "prefer", decision.allowed)
        author = self.author(rule("temporary.rule", "deny", expires_at=time() + 0.01))
        candidate = author.propose("Temporary restriction")
        author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        self.assertTrue(
            self.policy.evaluate("temporary.rule", (), frozenset(), now=time() + 2).allowed
        )

    def test_flexible_blocks_have_enforced_numeric_limit(self):
        author = self.author(
            rule(
                "calendar.move",
                "allow",
                {"block_type": "flexible"},
                numeric_limits={"shift_minutes": 30},
            ),
            rule("calendar.move", "deny", {"block_type": "class"}),
        )
        candidate = author.propose("Move flexible blocks up to 30 minutes; never move classes")
        author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        for block, delta, expected in (
            ("flexible", "30", True),
            ("flexible", "-30", True),
            ("flexible", "31", False),
            ("flexible", "nan", False),
            ("class", "10", False),
        ):
            self.assertEqual(
                expected,
                self.policy.evaluate(
                    "calendar.move",
                    ("calendar:write",),
                    frozenset({"calendar:write"}),
                    {"block_type": block, "shift_minutes": delta},
                ).allowed,
            )
        self.assertFalse(
            self.policy.evaluate(
                "calendar.move", (), frozenset(), {"block_type": "flexible"}
            ).allowed
        )


if __name__ == "__main__":
    unittest.main()
