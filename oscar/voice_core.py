"""Voice final-turn handoff uses the existing Controller, Runtime and verifier."""

import re
from collections.abc import Mapping

from .contracts import Epistemic, TaskState
from .grid import SessionHandle
from .jev import Intent
from .policy import PersonalPolicy
from .runtime import Runtime
from .transport import Transport
from .voice_contracts import StopToken, Transcript, VoiceResponse
from .voice_identity import SpeakerEvidence, VoiceMatch

NUMBERS = dict(
    zip(
        "zero one two three four five six seven eight nine ten eleven twelve "
        "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split(),
        range(21),
        strict=True,
    )
)


def addition_intent(text: str) -> str | None:
    clean = re.sub(r"[,.?!]", "", text.lower().strip())
    clean = re.sub(r"^(?:hey\s+)?oscar\s*", "", clean)
    clean = clean.removeprefix("what is ").replace(" plus ", " + ")
    terms = clean.split("+")
    if len(terms) != 2:
        return None
    parts = [str(NUMBERS.get(t.strip(), t.strip())) for t in terms]
    result = " + ".join(parts)
    return result if re.fullmatch(r"\d{1,12} \+ \d{1,12}", result) else None


class VoiceCore:
    def __init__(
        self,
        runtime: Runtime,
        policy: PersonalPolicy,
        transports: Mapping[str, tuple[Transport, SessionHandle]],
    ):
        self.runtime, self.policy, self.transports = runtime, policy, transports

    def handle(
        self,
        transcript: Transcript,
        stop: StopToken,
        *,
        granted: frozenset[str],
        require_match: bool = False,
        speaker: SpeakerEvidence | None = None,
    ) -> VoiceResponse:
        stop.check()
        if not transcript.final:
            raise ValueError("provisional STT cannot execute a task")
        intent = addition_intent(transcript.text)
        if intent is None:
            return VoiceResponse(
                "This acceptance session supports harmless integer addition only.",
                "",
                TaskState.BLOCKED,
                Epistemic.UNKNOWN,
                limitations=("bounded acceptance scope",),
            )
        permission = self.policy.evaluate("math.add", ("math",), granted)
        if not permission.allowed:
            return VoiceResponse(
                "That request is blocked by permission or Personal Policy.",
                "",
                TaskState.BLOCKED,
                Epistemic.UNKNOWN,
            )
        if require_match and (
            speaker is None
            or not VoiceMatch.permits(
                speaker, granted="math" in granted, policy_allowed=permission.allowed, risk="low"
            )
        ):
            return VoiceResponse(
                "Speaker verification is uncertain or rejected; no task executed.",
                "",
                TaskState.BLOCKED,
                Epistemic.UNKNOWN,
            )
        task = self.runtime.create(Intent(intent), initiator="owner-voice-acceptance")
        stop.check()
        task = self.runtime.run(task.id, self.transports)
        stop.check()
        results = [r for r in self.runtime.store.all("result") if r["task_id"] == task.id]
        evidence = [e for e in self.runtime.store.all("evidence") if e["task_id"] == task.id]
        if task.state == TaskState.VERIFIED and results:
            return VoiceResponse(
                "The result is " + str(results[-1]["value"]) + ".",
                task.id,
                task.state,
                Epistemic.VERIFIED,
                tuple(e["id"] for e in evidence),
                ("math",),
            )
        return VoiceResponse(
            "The task is " + task.state.value + "; no verified result is available.",
            task.id,
            task.state,
            Epistemic.UNKNOWN,
        )
