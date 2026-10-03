"""Small owner-reviewed natural-language policy path; interpretation is not authority."""

import argparse
import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

from .contracts import new_id, record
from .policy import PersonalPolicy, PolicyEffect, PolicyRule
from .storage import Store


class PolicyAuthoring:
    def __init__(self, policy: PersonalPolicy):
        self.policy = policy

    def propose(self, text: str) -> dict[str, Any]:
        normalized = " ".join(text.lower().strip().rstrip(".! ").split())
        interpretations = {
            "never send messages without asking me": PolicyEffect.ASK,
            "always ask before sending messages": PolicyEffect.ASK,
            "never send messages": PolicyEffect.DENY,
            "you may send messages without asking me": PolicyEffect.ALLOW,
        }
        if normalized not in interpretations:
            raise ValueError("ambiguous or unsupported policy; clarify the exact send/ask rule")
        if self.policy.redact(text) != text:
            raise ValueError("credential material cannot enter policy candidates")
        effect = interpretations[normalized]
        rule = PolicyRule(
            new_id(),
            "connectors:external-communication",
            effect,
            "owner-reviewed natural-language interpretation",
            time(),
            time(),
            {},
        )
        interpretation = (
            f"For all Connector Fabric external communication (including mail/messages and "
            f"calendar invitations): {effect.value}. ASK requires confirmation for each action. "
            "This does not cover arbitrary terminal/agent sends or grant any permission."
        )
        candidate = {
            "id": rule.id,
            "text": text,
            "interpretation": interpretation,
            "rule": record(rule),
            "state": "candidate",
        }
        candidate["review_digest"] = hashlib.sha256(
            json.dumps(candidate, sort_keys=True).encode()
        ).hexdigest()
        self.policy.store.put("policy_candidate", rule.id, candidate)
        return candidate

    def confirm(self, candidate_id: str, review_digest: str, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("owner confirmation required")
        with self.policy.store.transaction():
            candidate = self.policy.store.get("policy_candidate", candidate_id)
            if candidate["state"] != "candidate" or review_digest != candidate["review_digest"]:
                raise ValueError("confirmation must name the exact pending interpretation")
            reviewed = {k: v for k, v in candidate.items() if k != "review_digest"}
            if (
                hashlib.sha256(json.dumps(reviewed, sort_keys=True).encode()).hexdigest()
                != review_digest
            ):
                raise ValueError("pending interpretation changed since review")
            data = candidate["rule"]
            rule = PolicyRule(**{**data, "effect": PolicyEffect(data["effect"])})
            # Do not silently replace existing contradictory owner policy.
            if any(
                existing.enabled
                and existing.capability == rule.capability
                and existing.conditions == rule.conditions
                and existing.priority == rule.priority
                and existing.effect != rule.effect
                and (existing.expires_at is None or existing.expires_at > time())
                for existing in self.policy.rules()
            ):
                raise ValueError("conflicting interpretation; explicitly resolve existing policy")
            self.policy.save(rule, owner_authorized=True)
            candidate["state"] = "activated"
            self.policy.store.put("policy_candidate", candidate_id, candidate)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()
    store = Store(args.state)
    try:
        author = PolicyAuthoring(PersonalPolicy(store))
        candidate = author.propose(args.text)
        print(candidate["interpretation"])
        print("Pending candidate: " + candidate["id"])
        if input("Owner: type CONFIRM to activate this interpretation: ") != "CONFIRM":
            print("Candidate remains inactive.")
            return 0
        author.confirm(candidate["id"], candidate["review_digest"], owner_authorized=True)
        print("Owner-confirmed rule activated; permissions are unchanged.")
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
