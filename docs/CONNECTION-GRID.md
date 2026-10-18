# OSCAR Connection Grid

## Desktop interaction ownership

Grid now stores expiring generation-fenced interaction leases alongside existing task/executor leases. A reviewed text application binds input ownership to its Core task and rechecks it at Dispatcher; loss expires ownership. Desktop tasks are inspectable by eligible Mobile owner sessions without a private desktop task universe. Real Mobile/Desktop handoff remains owner acceptance. See [Desktop foundation](DESKTOP-FOUNDATION.md).

## Purpose

OSCAR should not feel tied to one machine. The **Connection Grid** is the persistent availability and control fabric across OSCAR Mobile, desktop machines, cloud coordination and OSCAR Edge.

The product goal is not literal immortality. Phones run out of power, clouds fail, networks split and devices reboot. The goal is **no single ordinary node failure should erase OSCAR's presence, task state or control path**.

The system should degrade gracefully rather than disappear.

```text
                     OWNER / USER
                          │
                       OSCAR Mobile
             authority console + kill switch
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
   Cloud coordinator   Desktop nodes   OSCAR Edge
   rendezvous/state    high compute     ESP32 + Pico
   durable tasks       apps/Codex       reflex/safety
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                  OSCAR Connection Grid
```

All members of the Grid use OSCAR-owned Transport + Capability Fabric contracts. Latch is not a runtime dependency.

## Core idea

Every node advertises what it can do now.

Examples:

```text
OSCAR Mobile
  notifications
  biometric approval
  phone context
  calls/messages where supported
  camera/mic/location where allowed
  owner control / stop / revoke

Desktop
  Codex
  terminal
  filesystem
  browser
  computer use
  installed apps
  GPU/local models
  long-running compute

OSCAR Edge
  wake/VAD
  local Sentry signals
  sensors
  relays/actuators
  local safety
  LAN presence
  optional Wake-on-LAN helper

Cloud
  rendezvous
  durable task coordination
  remote command routing
  provider access
  notification fan-out
  encrypted state/checkpoints
```

A node may request work on another node only through scoped capabilities and policy. `connected` never means `unrestricted remote control`.

## OSCAR Mobile is the owner control surface

OSCAR Mobile should be the highest-priority everyday owner control surface because the phone usually stays with the user while laptops and desktops come and go.

OSCAR Mobile should provide, where technically supported:

- `Pause OSCAR autonomy`;
- `Stop all non-safety work`;
- `Cancel task`;
- `Revoke node`;
- `Revoke provider/session`;
- `Mute / change Sentry mode`;
- approve sensitive work with biometric/PIN;
- inspect active tasks across machines/cloud/Edge;
- take over or redirect a task;
- request desktop shutdown after verified completion;
- request desktop wake where Wake-on-LAN or another approved power-control path exists.

The phone is **not** allowed to override deterministic physical emergency protections. Authority order remains conceptually:

```text
local hardware safety / emergency stop
        > owner security/revocation controls
        > explicit permissions + Personal Policy
        > OSCAR Executive / Workers
```

OSCAR Mobile is a control authority, not a magical guarantee of uptime. If OSCAR Mobile is offline, other permitted Grid nodes keep their existing responsibilities within policy.

## Cloud coordinator

A cloud deployment can provide an always-reachable rendezvous and durable coordination surface so remote nodes do not require inbound ports on the user's home network.

The cloud component should remain portable. OSCAR should be deployable as:

- a free-tier persistent VM/container where verified provider limits are acceptable;
- free-tier bounded API/relay functions with separately demonstrated durable state;
- a self-hosted compatible deployment;
- an optional owner-selected paid BYOC deployment.

Cloud deployment is **replaceable infrastructure**, not OSCAR's identity.

### Free-first deployment candidates

Official Oracle and Vercel sources checked on **2026-10-04**; recheck actual
account/region eligibility and limits before deployment. Detailed sources and
lifecycle constraints live in [DEPLOYMENT.md](DEPLOYMENT.md).

| Provider | Verified documented free option | Intended OSCAR role |
| --- | --- | --- |
| [Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) | A1: 2 OCPUs and 12 GB RAM total; 200 GB combined boot/block storage | strongest current first persistent/stateful Core candidate, subject to capacity, eligibility, ARM64 testing and idle reclamation |
| [Vercel Hobby](https://vercel.com/docs/plans/hobby) | free personal/non-commercial Python Functions with bounded Fluid usage | strong web/API/frontend/callback/webhook/stateless connector/relay candidate; Functions alone are not a persistent Core |

Earlier exploration included Google Cloud, Cloudflare Workers/Durable Objects,
Deno Deploy, AWS, Render and Koyeb. Their 2026-10-01 allowance observations are not
reasserted as current selections here; re-verify current free tiers and lifecycle
limits before choosing one. Paid hosts and trial-only offers are optional BYOC
choices, not the recommended free baseline. Hosting remains replaceable.

## Recommended availability shape

```text
OSCAR Core = persistent identity/state/memory/task coordination
                       |
                Connection Grid
          +------------+------------+
          |            |            |
        OSCAR Mobile       Desktop      Home Node (later)
      main phone      Worker      Galaxy Tab S6 Lite
                                     |
                                ESP32 / Pico Edge
```

Prefer Oracle Always Free for the first persistent stateful Core if actual
capacity/eligibility and ARM64 acceptance permit. Vercel is complementary bounded
Python/API/web/relay infrastructure. A temporary Function filesystem or process
memory cannot substitute for demonstrated durable archive/leases/recovery.
No deployment acceptance is claimed.

The owner's Samsung Galaxy Tab S6 Lite (2021) is a post-deployment expansion node:
local always-on Grid presence, LAN/Bluetooth, ESP32/Pico bridging and permissioned
sensors/notifications/control where Android permits. Optional local services or
lightweight survival/cache/checkpoint state require later practical testing; do not
assume the full canonical Qdrant/Neo4j/ML stack fits Android.
**Do not build the Tab/Home Node until OSCAR is fully deployed and the main Core
architecture is operational.** This is not a Gate B requirement. ESP32/Pico are
local nerves/reflexes/sensors/actuators, not full Core hosts; safety remains local
and deterministic during higher-layer loss.

Early development still uses one preferred coordinator with durable leases,
checkpoints and explicit failover rules rather than speculative consensus machinery.

## Remote continuation — Codex Remote-style behavior

The Connection Grid should make remote continuation ordinary.

Example:

```text
user starts Codex/render/build on desktop
→ task enters Durable Execution Runtime
→ user leaves home with OSCAR Mobile
→ desktop keeps working
→ progress/results flow through Connection Grid
→ OSCAR Mobile can inspect / approve / cancel / redirect
→ executor reports completion
→ OSCAR independently verifies expected result where practical
→ if Personal Policy permits: save/checkpoint work
→ optionally close apps / sleep / shut down desktop
→ task remains visible from OSCAR Mobile/cloud
```

The desktop does not need the user physically present for an already-authorized task to continue.

### Turning machines on/off

Shutdown/sleep is straightforward when the machine is online and the OS exposes a permitted capability.

Remote wake is conditional:

- Wake-on-LAN may work if hardware/network support it;
- an always-on Edge/router node may send a LAN wake packet;
- vendor-specific remote-management capability may exist;
- a smart relay may power hardware only if doing so is electrically safe and explicitly configured.

OSCAR must never claim it can power on an offline machine unless a real wake/power capability is currently available.

## Grid state model

Each node should expose compact current state:

```text
node_id
node_type
identity / pairing state
online / degraded / offline
last_seen
capabilities
active task leases
power state where known
network path
software/protocol version
health
permissions scope
revocation state
```

The World Model consumes this state. The Capability Catalog derives what is executable **now**.

## Control and arbitration

The Grid is peer-capable but not peer-unrestricted.

Rules:

1. Any authenticated node may submit only actions allowed by its scope.
2. Capability execution is checked again at the authoritative target.
3. OSCAR Mobile can revoke/pause user-authorized autonomous work but cannot defeat local hardware safety.
4. Workers cannot grant themselves new node permissions.
5. A disconnected node loses live capabilities but does not erase durable task state.
6. Duplicate/replayed commands are rejected through correlation IDs/idempotency/replay protection.
7. Task leases expire so dead executors do not remain `working` forever.
8. Reconnect restores advertised capability/state before work resumes.

## Grid UI

The Connection Grid should be visible from OSCAR Mobile and desktop as a compact operational surface, not a network-admin dashboard.

Normal view:

```text
OSCAR Grid

OSCAR Mobile        Here
Cloud         Healthy
Desktop       Working · 1 task
Desk Edge     Aware
```

Expand a node only when needed to see:

- what it is doing;
- capabilities currently available;
- active task ownership;
- health;
- remote control actions;
- permissions;
- version/update state.

Owner-level emergency controls remain immediately reachable on OSCAR Mobile.

## Availability semantics

OSCAR should use explicit availability levels rather than one binary `online` status.

```text
FULL
core + cloud + OSCAR Mobile + available nodes

CONNECTED
core available but some capability nodes absent

LOCAL
cloud unavailable; OSCAR Mobile/Edge/local paths continue where possible

REFLEX_ONLY
only deterministic Edge safety/reflex behavior remains

OFFLINE
no OSCAR compute path reachable from the current surface
```

The UI and voice behavior should report the real level.

## State replication and durability

Do not replicate all private data everywhere.

Replicate only what a node needs, using scoped encrypted state such as:

- durable task IDs/checkpoints;
- capability manifests;
- node health;
- minimal World Model state needed for the node;
- notification/event envelopes;
- artifact references rather than full artifacts where possible.

Long-term memory, private communications, transcripts and credentials follow their own storage/retention policy.

## Security

- outbound-first device connections;
- encrypted transport;
- per-node credentials;
- phone biometric/PIN for owner-critical controls;
- revocation without rebuilding the Grid;
- no shared blanket device secret;
- replay protection;
- audit every consequential remote-control action;
- provider/cloud admin credentials never sent to low-trust Edge nodes;
- cloud compromise must not bypass local safety interlocks.

See `docs/SECURITY.md`.

## Failure behavior

Examples:

```text
cloud unavailable
→ OSCAR Mobile and Edge retain allowed local capability
→ desktop task may continue locally
→ durable updates queue until rendezvous returns

OSCAR Mobile offline
→ existing tasks continue within policy
→ no new owner-critical approval can be fabricated

Desktop disappears mid-task
→ lease expires
→ task becomes waiting/blocked/reclaimable
→ never falsely complete

Edge offline
→ physical capabilities disappear
→ cloud/software OSCAR remains available
→ local hardware must fail safe independently
```

## Invariants

1. No ordinary desktop machine is OSCAR's permanent host.
2. OSCAR Mobile is the preferred owner control/kill-switch surface, not a substitute for hardware safety.
3. Edge keeps local presence/reflex/safety available even when higher layers disappear.
4. Cloud is replaceable and may be free, paid or self-hosted.
5. Remote work uses the same Durable Execution Runtime and evidence/verification model as local work.
6. Nodes control one another only through advertised, scoped capabilities.
7. OSCAR never claims remote power/control capability that is not currently available.
8. Availability degrades explicitly rather than silently disappearing.

## Implementation and delivery status (2026-10-18)

Existing local Grid, Capability Catalog and Durable Runtime remain authoritative.
The [D2 connected candidate](development/GROUP-04-D2.md) adds HTTPS proof of
possession, trusted single-use device invitations, bounded outbound polling,
scoped task admission, separate file readback, canonical archive cursors and
conservative process-loss recovery. [Protocol 2](development/GROUP-04-D2-PROTOCOL.md)
defines the shared native contract. Independent Internet-host and owner-device
acceptance remain outstanding. Gate C/D remain **PARTIAL**.

**Current:** review the D2/D3–D4 software draft and its platform-specific evidence;
separately commission approved hosts and real owner devices. Oracle remains a
candidate, not deployed. The later dedicated home-server laptop is distinct from
optional Galaxy Tab. Physical Slice 07/18 Edge is **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**
with hardware **DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED**. Historical evidence
remains in Git and the [consolidated Gate C contract](GATE-C-CONSOLIDATED-ACCEPTANCE.md).

## Tauri surface continuity

Rust projects existing Core task/capability state into local typed events; frontend state grants no authority. Worker withdrawal removes eligible Act forms. Surface restart/reconnect inspects existing shared tasks; it does not replay private work or invent task truth. Existing Grid interaction fencing remains authoritative. See [Desktop foundation](DESKTOP-FOUNDATION.md).
