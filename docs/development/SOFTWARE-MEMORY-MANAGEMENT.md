# Native canonical memory management — 2026-10-22

Desktop Preferences and Android Memory now read a bounded projection from the
existing canonical Event Archive, and stage exact correction/forget reviews using
the existing Assistance owner-signature transport. Neither surface creates a
second memory store. Clearing drafts and forgetting retained memory remain
separate controls.

## Authority and scope

- Inspection requires current `memory:read` in both the device and session grants,
  plus `memory.read` Personal Policy. There is no content projection by default.
- Mutations additionally require `memory:manage`, current enrolled owner signing,
  the existing native approval scope and `memory.manage` Personal Policy.
- The offline Grid invitation option `--memory-control` explicitly grants read
  and management only. It does not grant retention. Existing invitations acquire
  no new authority.
- A correction requires an explicit `retain: true` and a current source-appropriate
  retention grant and policy: canonical `retain`, Desktop conversation retention
  for conversation sources, or `archive:retain` for remote Grid sources. An erase
  grant cannot become permission to retain a new statement. Node and source policy
  conditions remain part of these checks.

The signed request binds the relationship, selected memory ID, full content and
record digest, source event digests, current archive generation, exact replacement
statement or explicit source-deletion choice, and affected dependent memory IDs.
Another relationship, a stale generation, changed content, changed policy,
revocation, expiry or a consumed review rejects the change.

## Canonical behavior and failure handling

A correction appends an owner-reported correction source and uses the existing
MemoryWriter temporal supersession validation. The previous statement remains
historical evidence. The correction inherits its source sensitivity, project,
entities, context and expiry; it does not extend retention or become verified
truth. Current recall admits the replacement only.

Forgetting uses the existing canonical tombstones, FTS removal and optional source
deletion/cascade. The exact affected IDs are checked by authoritative SQLite
readback. Configured derived indexes receive the tombstones through their existing
deletion contract. A failed derived deletion returns `partially_verified`; the
canonical admission/generation filter still excludes forgotten records. Success
describes canonical forgetting, not secure erasure of WAL, backups or physical
storage. Keeping sources deliberately leaves the original conversation available.

Composable archive writes use `BEGIN IMMEDIATE` for the outer transaction and
nested savepoints. Source append, supersession and readback commit together; a
failure rolls back the inserted correction source too. The existing multi-thread
retention test covers the read-before-write locking case.

The owner review is consumed in the authority store before the archive mutation.
Current owner/session/node scopes and Personal Policy are then rechecked under
the authority-store transaction, held through canonical mutation in Store-to-Archive
lock order. Deterministic tests withdraw the session, node or scope between review
consumption and that recheck; each operation stays consumed without changing memory.
This is a conservative boundary across the two existing SQLite databases: a crash
or execution error leaves a pending/unknown mutation and never silently replays the
signed request. A fresh explicit review is required after inspecting current
canonical state. Consumed and expired memory-review payloads are stripped, and
other outstanding memory reviews for the same relationship are invalidated, so
the review ledger does not become a second retained copy of deleted content.

Native clients clear their displayed/recovered conversation projection after a
memory mutation response and refresh canonical history. The active recall context
is also invalidated. Active tasks are not cancelled by forgetting historical
memory. This does not claim to erase separately held private drafts or external
executor artifacts.

## Bounds and verification

The current native view shows up to 20 recent current records within 12 KB, with
2,000-character excerpts and an explicit truncation label. Corrections are bounded
to 2,000 characters; exact reviews exceeding the native display bound are rejected.
Older-page search and bulk/history-wide deletion are not exposed by this view.

Local synthetic tests exercise real signed Assistance and Desktop envelopes,
canonical conversation refresh, current/temporal recall, FTS deletion, persisted
archive reopening, duplicate review rejection, generation/content/relationship
drift, failed derived deletion, rollback, unavailable grants and node-specific
Personal Policy. Desktop interaction tests stage unsigned reviews; Android JVM
tests validate the same bounded management schema. See the dedicated
[receipt](../evidence/software-completion/memory-management-2026-10-22.json).

Configured-index rebuild remains the existing offline recovery operation. A memory
read/manage grant does not authorize exporting canonical records to a new provider
or spending. This batch adds no provider setup or native rebuild authority.

The actual disposable API 35 native campaign passed rendered correction/forget
reviews, decline without mutation, native Keystore Grid proof, exact host-signed
synthetic owner approvals, independent canonical SQLite/FTS readback, source
preservation, consumed-review rejection, canonical/encrypted-history refresh and
activity recreation without replay. It also read back removal of an Android
Sentry notice after real synthetic session revocation. Fixture packages and Core
credentials/processes were removed and checked. See the separate
[native receipt](../evidence/software-completion/android-memory-2026-10-22.json).
Activity recreation does not establish process-death acceptance, and host synthetic
approval does not establish owner biometrics.

The configured real derived indexes also passed their
[separate acceptance](SOFTWARE-MEMORY-INDEX-ACCEPTANCE.md). Physical-device,
real owner activation and personal-memory acceptance remain unverified. No push
or CI was used for this work.
