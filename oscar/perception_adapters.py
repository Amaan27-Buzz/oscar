"""Bridge existing authorized live-context sources into the current-state projection."""

import hashlib

from .continuity import LiveContextSource
from .contracts import Epistemic
from .freshness import Authority
from .perception import PerceptionFabric
from .world_model import Observation, ObservationKind, WorldState, reference


class ContextPerceptionAdapter:
    def __init__(
        self,
        fabric: PerceptionFabric,
        source: LiveContextSource,
        source_id: str,
        entity_id: str,
        kind: ObservationKind,
    ):
        reference(source_id)
        reference(entity_id)
        self.fabric, self.source = fabric, source
        self.source_id, self.entity_id, self.kind = source_id, entity_id, kind

    def poll(self, query: str = "current status") -> tuple[WorldState, ...]:
        if not isinstance(query, str) or not 1 <= len(query) <= 1000:
            raise ValueError("bounded context query required")
        world = self.fabric.world
        epoch = self.fabric.acquisition_epoch(self.source_id)
        context = self.source.retrieve(query, world.relationship)
        # Includes empty replies: revocation during retrieval cannot adopt a new grant.
        if self.fabric.acquisition_epoch(self.source_id) != epoch:
            raise PermissionError("source changed during acquisition")
        if len(context) > 32:
            raise ValueError("bounded context observations required")
        states = []
        for item in context:
            now = world.clock()
            if item.scope != world.relationship or not item.source.current(now):
                raise PermissionError("context source scope/freshness mismatch")
            if item.source.authority not in {Authority.LIVE_API, Authority.OFFICIAL_DOCS}:
                raise ValueError("recalled/cache/model content cannot become a live observation")
            if item.state not in {Epistemic.KNOWN, Epistemic.REPORTED, Epistemic.VERIFIED}:
                raise ValueError("unknown/inferred context cannot become reported current state")
            with world.store.lock:
                source = world.source(self.source_id)
                sequence = source["last_sequence"] + 1
                identifier = hashlib.sha256(
                    f"{self.source_id}:{epoch}:{sequence}".encode()
                ).hexdigest()
                observation = Observation(
                    identifier,
                    self.source_id,
                    epoch,
                    sequence,
                    self.entity_id,
                    item.key,
                    self.kind,
                    item.value,
                    item.source.observed_at,
                    min(
                        item.source.observed_at + item.source.ttl_seconds,
                        item.source.observed_at + 3600,
                    ),
                    1.0,
                    evidence_id=item.source.evidence_id,
                )
                states.append(self.fabric.ingest(observation)[1])
        return tuple(states)
