"""Separate speaker authorization evidence, contextual perception and expression."""

from dataclasses import dataclass, replace
from math import isfinite, sqrt

from .voice_contracts import VoiceProfile, VoiceResponse


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    if not a or len(a) != len(b) or len(a) > 4096 or any(not isfinite(x) for x in a + b):
        raise ValueError("invalid speaker embedding")
    norm = sqrt(sum(x * x for x in a) * sum(x * x for x in b))
    if norm == 0:
        raise ValueError("zero speaker embedding")
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b, strict=True)) / norm))


@dataclass(frozen=True)
class SpeakerEvidence:
    speaker_id: str | None
    score: float | None
    outcome: str
    source: str
    status: str = "REPORTED"


class VoiceMatch:
    """Similarity evidence only. Explicit permission/policy remains authoritative."""

    def __init__(self, model_id: str, threshold: float = 0.8, reject: float = 0.55):
        if not model_id or not 0 <= reject < threshold <= 1:
            raise ValueError("invalid Match calibration")
        self.model_id, self.threshold, self.reject = model_id, threshold, reject
        self.enrolled: dict[str, tuple[float, ...]] = {}

    def enroll(self, speaker_id: str, vector: tuple[float, ...], *, confirmed: bool) -> None:
        if not confirmed or not speaker_id:
            raise PermissionError("explicit enrollment required")
        cosine(vector, vector)
        self.enrolled[speaker_id] = vector

    def forget(self, speaker_id: str) -> None:
        self.enrolled.pop(speaker_id, None)

    def verify(
        self, vector: tuple[float, ...], *, source_model: str, self_output: bool = False
    ) -> SpeakerEvidence:
        if self_output or source_model != self.model_id or not self.enrolled:
            return SpeakerEvidence(None, None, "uncertain", source_model)
        try:
            scores = sorted(
                ((cosine(v, vector), k) for k, v in self.enrolled.items()), reverse=True
            )
        except ValueError:
            return SpeakerEvidence(None, None, "uncertain", source_model)
        score, speaker = scores[0]
        if len(scores) > 1 and score - scores[1][0] < 0.1:
            return SpeakerEvidence(None, score, "uncertain", source_model)
        outcome = (
            "accepted"
            if score >= self.threshold
            else ("rejected" if score < self.reject else "uncertain")
        )
        return SpeakerEvidence(
            speaker if outcome == "accepted" else None, score, outcome, source_model
        )

    @staticmethod
    def permits(
        evidence: SpeakerEvidence,
        *,
        granted: bool,
        policy_allowed: bool,
        risk: str,
        stronger_confirmation: bool = False,
    ) -> bool:
        return (
            granted
            and policy_allowed
            and evidence.outcome == "accepted"
            and (risk == "low" or stronger_confirmation)
        )


class VoiceMap:
    """Owner-linked profiles are independent from authorization enrollments."""

    def __init__(self, model_id: str, threshold: float = 0.75):
        if not model_id or not 0 <= threshold <= 1:
            raise ValueError("invalid Map threshold")
        self.model_id, self.threshold = model_id, threshold
        self.known: dict[str, tuple[float, ...]] = {}
        self.anonymous: dict[str, tuple[float, ...]] = {}
        self.previous: str | None = None

    def link(self, speaker_id: str, vector: tuple[float, ...], *, confirmed: bool) -> None:
        if not confirmed or not speaker_id:
            raise PermissionError("explicit identity linkage required")
        cosine(vector, vector)
        self.known[speaker_id] = vector

    def observe(
        self,
        vectors: tuple[tuple[float, ...], ...],
        *,
        source_model: str,
        self_output: bool = False,
    ) -> tuple[SpeakerEvidence, ...]:
        if self_output:
            return ()
        result = []
        for index, vector in enumerate(vectors[:8]):
            scores: list[tuple[float, str]] = []
            if source_model == self.model_id:
                try:
                    scores = sorted(
                        ((cosine(v, vector), k) for k, v in self.known.items()), reverse=True
                    )
                except ValueError:
                    pass
            known = bool(
                scores
                and scores[0][0] >= self.threshold
                and (len(scores) == 1 or scores[0][0] - scores[1][0] >= 0.1)
            )
            speaker = scores[0][1] if known else f"speaker-{index + 1}-unknown"
            if not known and source_model == self.model_id:
                try:
                    cosine(vector, vector)
                    anonymous = sorted(
                        ((cosine(v, vector), k) for k, v in self.anonymous.items()), reverse=True
                    )
                    if anonymous and anonymous[0][0] >= self.threshold:
                        speaker = anonymous[0][1]
                    elif len(self.anonymous) < 8:
                        speaker = "speaker-" + chr(97 + len(self.anonymous)) + "-unknown"
                        self.anonymous[speaker] = vector
                except ValueError:
                    pass
            outcome = "known_probable" if known else "unknown"
            if len(vectors) > 1:
                outcome = "multiple:" + outcome
            elif self.previous is not None and speaker != self.previous:
                outcome = "speaker_changed:" + outcome
            result.append(
                SpeakerEvidence(speaker, scores[0][0] if scores else None, outcome, source_model)
            )
            self.previous = speaker
        return tuple(result)


@dataclass(frozen=True)
class PersonaProfile:
    name: str = "steady"
    warmth: int = 30
    formality: int = 60
    brevity: int = 70
    style: str = "steady"

    def __post_init__(self) -> None:
        if any(not 0 <= x <= 100 for x in (self.warmth, self.formality, self.brevity)):
            raise ValueError("invalid persona trait")

    def express(
        self, response: VoiceResponse, voice: VoiceProfile, *, serious: bool = False
    ) -> tuple[VoiceResponse, VoiceProfile]:
        # Preserve the complete claim/state/authority payload; never summarize it away.
        prefix = "" if serious or self.warmth < 60 else "All right. "
        return (
            replace(response, text=prefix + response.text),
            replace(
                voice,
                style="serious" if serious else self.style,
                mode="serious" if serious else voice.mode,
            ),
        )
