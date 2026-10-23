# Selected phone context

The local software candidate adds authenticated Android metadata to the existing
World Runtime, Perception Fabric, Sentry and read-only day briefing. There is no
second phone memory store or capture backend.

Source creation uses the existing exact signed `source_create` review. The
`android` source pins one enrolled mobile node, its current session and at most
eight explicit package IDs. It requires `android:perceive` in both node and
session. Source perception, retention and action remain independent signed
grants. A rotated session requires a newly reviewed source; old invitations or
sessions cannot silently resume capture.

The authenticated `phone_context` operation returns only that session's selected
source contracts. Observations must match the current epoch and exact next
sequence, be at most five seconds old, and contain only selected notification
counts (0-32) and media playback states. The schema excludes notification text,
sender names, track titles, positions, screenshots and arbitrary fields. Each
component states its own availability; unavailable context cannot masquerade as
an empty observed list. Source and observation leases expire within fifteen
seconds. The native publisher must acquire a new observation rather than replay
an ambiguous result.

Default retention is off. Current values live only in the existing volatile
World Model; durable records contain source/sequence/projection metadata rather
than captured values. Enabling retention still passes the separate canonical
perception retention policy. No permission to reply or control playback follows
from observing metadata. Sentry interruption and notice delivery retain their
existing independent policy checks.

Snapshot, briefing and alert reads recheck current node/session authority before
showing phone context. Session rotation/revocation/disconnection withdraws the
source lease. Local metadata opt-out can withdraw a bound source even after
Sentry mode or source selection changes. Revocation cleanup tolerates an older
subscription epoch without leaving the current epoch connected.

Local focused Python coverage verifies schema/package/identity/time/sequence/
epoch rejection, volatile storage and expiry, source-grant and retention-policy
separation, explicit Sentry delivery, local withdrawal, authenticated operation
scope, session rotation and live node-scope withdrawal. Desktop briefing checks
verify selected counts/play states and immediate hiding after source withdrawal.

Android uses the actual NotificationListener active-notification snapshot and
MediaSession playback state. Both require existing Android notification access,
independent local perception switches and explicit selected package IDs. Sharing
with Core has its own local opt-in. The foreground app and explicitly started
phone Worker reuse the existing authenticated transport and a shared five-second
publisher; there is no additional background service. Local opt-out withdraws
current context on the next publisher pass. A fifteen-second lease bounds loss of
transport. Configuration and privacy changes are rechecked before publishing.

The publisher fetches the current source contracts once and submits at most eight
unique source updates in one strict `batch` envelope. A batch can mix observations
and withdrawals; the existing single-source requests remain compatible. Core
validates every item's exact schema, source/session binding, generation,
sequence, timestamp, selected packages and perception/retention policy before
applying any item under the existing authority lock. Runtime failures still
require fresh acquisition; a batch response is never automatically replayed.
The native publisher rechecks local privacy before submitting its captured batch.

The native Worker polls every two seconds. It advertises initially and whenever
its available capability payload changes; authenticated polling continues to
renew its existing executor lease. With stable capabilities, a foreground
snapshot every five seconds, eight phone sources and the optional five-second
Companion presence read, the nominal budget is 78 requests per minute, plus one
initial advertisement. This leaves 41 of the existing 120 verified-node requests
per rolling minute for task checks/results and interaction. Phone publication
still runs every five seconds and leases still expire within fifteen seconds.
The source-pinned disposable-emulator campaign in
`docs/evidence/software-completion/android-phone-batch-2026-10-23.json` exercised
all eight sources for 65.032 seconds, with 31 independent fresh readbacks and
zero retained observations. This verifies that recorded candidate's sustained
publication; it does not establish physical-phone or Core-restart acceptance.
Earlier campaign receipts retain their original source hashes.

Core restart clears remote executor registration. An authenticated poll can now
explicitly return `advertise_required` with no delivery, before claiming any
effect. Native and Python Workers respond by advertising their current
capabilities and polling on a later pass. That recovery adds one advertisement,
preserves the existing execution journal, and never resubmits a delivery. An
ambiguous native poll/network failure still stops the native Worker for explicit
inspection, because a lost poll reply may already have claimed a delivery.
Re-advertisement does not resume effects fenced by Core restart. Backend restart
regressions and native response contracts are separate from an emulator run that
actually restarts Core; the eight-source receipt above did not restart it.

Companion has a separate, default-off local preference to retreat during
selected media playback. A real playing state moves the canonical Orb into a
compact edge control; stopping playback or withdrawing that preference restores
its prior size and position. Playback is labeled as playback and never presented
as proof that the owner is focused, watching or unavailable.

The focused Core campaign passed 58 tests in 36.556 seconds. The Desktop source
form and briefing campaign passed 10 tests, and TypeScript checking passed.
Android assemble, JVM contracts and lint passed. The actual disposable-emulator
Grid campaign passed its main native test in 31.434 seconds. It exercised a real
MediaSession without audio, an actual synthetic OS notification, signed source
configuration, independent TLS Core briefing readback, zero retained observation
rows and local withdrawal. It checked the retreat decision against that playing
session; this alone does not verify the overlay window's visual geometry.
The same campaign verified clipboard, media pause and text entry with independent
native readback. Click remains `partially_verified` in Core, with a separate
test-fixture observation. Process restoration preserved execution claims without
starting a Worker; actual revocation withdrew it. Eleven production navigation
captures and setting/app cleanup also passed. The first combined phone run lost
its Worker connection after metadata acceptance; pacing test-only Core polling
to one second passed the next complete run. That does not by itself prove the
first disconnection's cause. The later separate eight-source campaign above
supplies sustained request-budget evidence for its measured 65.032-second interval.

See `docs/evidence/software-completion/phone-context-2026-10-22.json` for exact
source hashes and verification status. No physical phone, private notification,
real account, microphone or owner capture acceptance is implied.
