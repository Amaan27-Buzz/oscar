"""Live federation adapters reuse scoped files, native retrieval and Connector Fabric outcomes."""

import hashlib
import json
from collections.abc import Callable
from time import time

from .capabilities import ScopedFiles
from .connectors import ConnectorOutcome
from .continuity import ContextObservation
from .contracts import Epistemic
from .freshness import Authority, SourceRef
from .retrieval import RetrievalProvider, RetrievalRequest


class FileContextSource:
    id = "native-current-files"

    def __init__(self, files: ScopedFiles, allowed_scope: str, selected_paths: dict[str, str]):
        self.files, self.allowed_scope, self.selected_paths = files, allowed_scope, selected_paths
        if len(selected_paths) > 16:
            raise ValueError("too many active files")

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.allowed_scope:
            raise PermissionError("file context scope denied")
        observations = []
        for key, path in self.selected_paths.items():
            content = self.files.read(path)
            if len(content) > 16_000:
                raise ValueError("active file context bound")
            source = SourceRef(
                "local://selected-files/" + path,
                Authority.LIVE_API,
                "local",
                time(),
                5,
                evidence_id=hashlib.sha256(content).hexdigest(),
            )
            observations.append(
                ContextObservation(key, content.decode(), scope, source, Epistemic.KNOWN)
            )
        return tuple(observations)


class SearchContextSource:
    id = "native-search-freshness"

    def __init__(
        self, provider: RetrievalProvider, allowed_scope: str, check_cancel: Callable[[], None]
    ):
        self.provider, self.allowed_scope, self.check_cancel = provider, allowed_scope, check_cancel

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.allowed_scope:
            raise PermissionError("search scope denied")
        request = RetrievalRequest(query, result_limit=4)
        if not self.provider.supports(request):
            raise ValueError("source does not support this current query")
        result = self.provider.retrieve(request, self.check_cancel)
        return tuple(
            ContextObservation(
                "search:" + str(index), fact.text, scope, fact.source, Epistemic.REPORTED
            )
            for index, fact in enumerate(result.facts)
        )


class ConnectorContextSource:
    """Invoke an authorized task-scoped retrieval callback; never upgrades API testimony."""

    id = "native-connectors"

    def __init__(
        self,
        retrieve_outcome: Callable[[str], ConnectorOutcome],
        allowed_scope: str,
        selected_fields: tuple[str, ...],
    ):
        self.retrieve_outcome, self.allowed_scope = retrieve_outcome, allowed_scope
        self.selected_fields = selected_fields

    def retrieve(self, query: str, scope: str) -> tuple[ContextObservation, ...]:
        if scope != self.allowed_scope:
            raise PermissionError("connector context scope denied")
        outcome = self.retrieve_outcome(query)
        if not outcome.result.success or outcome.source is None:
            raise ValueError("connector current state unavailable")
        return tuple(
            ContextObservation(
                "connector:" + key,
                json.dumps(outcome.payload[key]),
                scope,
                outcome.source,
                Epistemic.REPORTED,
            )
            for key in self.selected_fields
            if key in outcome.payload
        )
