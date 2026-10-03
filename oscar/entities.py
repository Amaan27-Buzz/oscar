"""Small evidence-backed identity graph; matching names never merges identities."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from time import time

from .contracts import Epistemic, record
from .credentials import redact_runtime_secrets
from .storage import StateConflict, Store


class EntityType(StrEnum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    ACCOUNT = "Account"
    SERVICE = "Service"
    DEVICE = "Device"
    PROJECT = "Project"
    REPOSITORY = "Repository"
    TASK = "Task"
    DOCUMENT = "Document"
    EVENT = "Event"
    COURSE = "Course"


@dataclass(frozen=True)
class Entity:
    id: str
    kind: EntityType
    label: str
    created_at: float


@dataclass(frozen=True)
class EntityRelation:
    id: str
    subject: str
    relation: str
    target: str
    evidence_id: str
    observed_at: float


class EntityGraph:
    def __init__(self, store: Store, redact: Callable[[str], str] = redact_runtime_secrets):
        self.store, self.redact = store, redact

    def add(self, entity: Entity) -> None:
        if (
            not entity.id
            or not entity.label
            or len(entity.label) > 200
            or self.redact(json.dumps(record(entity))) != json.dumps(record(entity))
        ):
            raise ValueError("invalid entity")
        try:
            existing = self.store.get("entity", entity.id)
            if existing != record(entity):
                raise StateConflict("existing identity cannot be silently overwritten")
        except KeyError:
            self.store.put("entity", entity.id, record(entity))

    def _evidence(self, identifier: str, expected: dict[str, str]) -> None:
        evidence = self.store.get("evidence", identifier)
        if evidence["matches"] is not True or evidence["status"] not in {
            Epistemic.KNOWN,
            Epistemic.VERIFIED,
        }:
            raise ValueError("relation/identity needs supporting authoritative evidence")
        try:
            claims = json.loads(evidence["detail"])
        except (ValueError, TypeError):
            raise ValueError("entity mapping evidence needs explicit claim fields") from None
        if claims != expected:
            raise ValueError("unrelated evidence cannot establish entity identity/relation")

    def bind(
        self, entity_id: str, provider: str, account: str, native_id: str, evidence_id: str
    ) -> None:
        self.store.get("entity", entity_id)
        self._evidence(
            evidence_id,
            {
                "entity_id": entity_id,
                "provider": provider,
                "account": account,
                "native_id": native_id,
            },
        )
        if not all((provider, account, native_id)) or any(
            "\x00" in v for v in (provider, account, native_id)
        ):
            raise ValueError("identity binding needs provider, account and native ID")
        key = json.dumps([provider, account, native_id])
        if self.redact(key) != key:
            raise ValueError("credential material cannot enter entity identities")
        with self.store.transaction():
            try:
                current = self.store.get("entity_identity", key)
                if current["entity_id"] != entity_id:
                    raise StateConflict("identity conflict; unknown entities stay separate")
            except KeyError:
                self.store.put(
                    "entity_identity",
                    key,
                    {
                        "entity_id": entity_id,
                        "provider": provider,
                        "account": account,
                        "native_id": native_id,
                        "evidence_id": evidence_id,
                        "observed_at": time(),
                    },
                )

    def relate(self, relation: EntityRelation) -> None:
        if relation.relation not in {
            "belongs_to",
            "member_of",
            "owns",
            "uses",
            "related_to",
            "assigned_to",
            "stored_in",
            "scheduled_at",
            "source_identity_for",
        }:
            raise ValueError("unsupported relation")
        self.store.get("entity", relation.subject)
        self.store.get("entity", relation.target)
        self._evidence(
            relation.evidence_id,
            {"subject": relation.subject, "relation": relation.relation, "target": relation.target},
        )
        self.store.put("entity_relation", relation.id, record(relation))

    def forget(self, entity_id: str, *, owner_authorized: bool) -> None:
        if not owner_authorized:
            raise PermissionError("entity deletion requires owner authority")
        with self.store.transaction():
            for relation in self.store.all("entity_relation"):
                if entity_id in {relation["subject"], relation["target"]}:
                    self.store.delete("entity_relation", relation["id"])
            for identity in self.store.all("entity_identity"):
                if identity["entity_id"] == entity_id:
                    key = json.dumps(
                        [identity["provider"], identity["account"], identity["native_id"]]
                    )
                    self.store.delete("entity_identity", key)
            self.store.delete("entity", entity_id)
