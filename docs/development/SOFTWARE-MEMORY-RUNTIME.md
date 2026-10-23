# Configured memory runtime and conversation recall

Updated 2026-10-23. Synthetic local software acceptance; no personal-memory or
hosted deployment acceptance.

`oscar.local_memory` composes the existing Memory Fabric inside the normal Harness,
Cloud Core and CLI. Configuration is explicit, defaults off, and requires
`authorized_local_projection: true`, a relationship and absolute local model/index
paths. Optional Neo4j must use literal loopback and a credential reference. Cached
FastEmbed dense/reranker and BM25 artifacts load locally; unavailable or outdated
indexes preserve canonical archive fallback. SQLite/WAL/FTS remains authoritative.

Read-only `memory.recall` is advertised by the normal Core. Controller memory
preflight supplies bounded canonical provenance. Desktop and authenticated Grid
conversation use the same executor and current `memory:read` permission. Recall
does not require management or permission to retain a new interaction. Existing
enrollments do not acquire new scopes silently.

Replies remain `RECALLED`, `INFERRED` or `UNKNOWN`, with at most 32 canonical source
IDs. A worker result remains `REPORTED`; it cannot promote historical evidence to
current verification. Source admission and current session/read permission are
rechecked when presenting a reply. Forgotten sources withdraw old answers.

When `request_retained` is false, query and answer are transient. Snapshot omission
on session withdrawal or process restart removes the presentation. Native clients
derive these turns from current tasks without adding them to their canonical
history caches. A retained request may persist, but the recalled answer is not
copied into durable task results.

The [actual runtime receipt](../evidence/software-completion/memory-runtime-2026-10-23.json)
records cached-model inference, embedded Qdrant and actual Graphiti/Neo4j through
normal composition. Archive-only paraphrase retrieval missed; both derived paths
returned the exact canonical source. Signed Desktop review and signed HTTP Grid
recall, read without retention/manage, restart, withdrawal, missing-index fallback
and physical derived deletion passed in 8.438 seconds. The 121-test focused
regression passed in 62.028 seconds. No non-loopback network attempt was observed.

An earlier real campaign exposed a Windows embedded-Qdrant collection-recreation
problem: an open SQLite collection could reload a deleted point. Canonical
admission blocked resurrection, but physical projection deletion failed. Rebuild
now deletes all points using the public API and independently checks the count
before recreation. The failed receipt remains preserved.

The synthetic Neo4j container and its anonymous volumes were removed. This
campaign uses a loopback HTTP test transport and synthetic owners; native rendered
acceptance is recorded separately. Secure disk erasure, public hosting, genuine
ARM64, owner data and physical-device acceptance remain unclaimed.
