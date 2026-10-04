# OSCAR Connection Grid

## Purpose

OSCAR should not feel tied to one machine. The **Connection Grid** is the persistent availability and control fabric across Sunday, desktop machines, cloud coordination and OSCAR Edge.

The product goal is not literal immortality. Phones run out of power, clouds fail, networks split and devices reboot. The goal is **no single ordinary node failure should erase OSCAR's presence, task state or control path**.

The system should degrade gracefully rather than disappear.

```text
                     OWNER / USER
                          │
                       Sunday
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
Sunday
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

## Sunday is the owner control surface

Sunday should be the highest-priority everyday owner control surface because the phone usually stays with the user while laptops and desktops come and go.

Sunday should provide, where technically supported:

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

Sunday is a control authority, not a magical guarantee of uptime. If Sunday is offline, other permitted Grid nodes keep their existing responsibilities within policy.

## Cloud coordinator

A cloud deployment can provide an always-reachable rendezvous and durable coordination surface so remote nodes do not require inbound ports on the user's home network.

The cloud component should remain portable. OSCAR should be deployable as:

- a lightweight persistent VM/container;
- an event-driven/serverless coordinator where long-lived process state is unnecessary;
- a user-supplied paid cloud deployment;
- a free-tier deployment where the provider's limits are acceptable.

Cloud deployment is **replaceable infrastructure**, not OSCAR's identity.

### Free / low-cost deployment candidates

Provider offerings change, so re-verify before deployment. As researched on **2026-10-01**:

| Provider | Useful current free option | Suitability for OSCAR |
|---|---|---|
| Oracle Cloud | Always Free AMD/Ampere compute and related storage/network services | Strong candidate for a small persistent coordinator when capacity/account availability permits |
| Google Cloud | Free Tier includes one `e2-micro` instance per month in eligible US regions plus limited disk/egress | Good small persistent coordinator option; billing/account eligibility still applies |
| Cloudflare Workers + Durable Objects | Workers Free plan; SQLite-backed Durable Objects available on Free; hibernating WebSockets supported | Excellent rendezvous/event/control-plane option; not a general always-running VM |
| Deno Deploy | Free plan with request/egress allowances | Good stateless/event API or lightweight coordinator; not a conventional persistent daemon |
| AWS | Lambda has always-free monthly request/compute allowance; new EC2 free access is credit/time limited | Good serverless or paid BYOC option; do not treat EC2 as forever-free |
| Render | Free web services exist but spin down after inactivity and have monthly limits | Development/fallback only, not the sole always-on coordinator |
| Koyeb | One free web instance but it scales to zero after inactivity | Development/fallback only, not the sole always-on coordinator |
| Fly.io | Short free trial; persistent Machines are paid | Paid low-cost option, not a free baseline |

OSCAR should support a **BYOC** path for AWS, GCP, Azure, Oracle, Hetzner, DigitalOcean, Vultr or any compatible deployment target without making one provider mandatory.

## Recommended availability shape

For the first practical alpha:

```text
Cloud rendezvous / durable coordination
        │
        ├── Sunday = owner control + notifications + remote supervision
        ├── Desktop = high-capability executor
        └── Edge = local always-on perception/reflex/safety
```

A useful free-first baseline can combine:

- Cloudflare Durable Objects/Workers for rendezvous/control-plane behavior where suitable;
- Oracle Always Free or Google Free Tier VM when a persistent lightweight coordinator is desired;
- Sunday as the owner's always-carried control surface;
- OSCAR Edge as the local always-on reflex/presence layer.

Do not build distributed consensus machinery before there is a concrete need. Early OSCAR can use one preferred coordinator with durable leases/checkpoints and explicit failover rules.

## Remote continuation — Codex Remote-style behavior

The Connection Grid should make remote continuation ordinary.

Example:

```text
user starts Codex/render/build on desktop
→ task enters Durable Execution Runtime
→ user leaves home with Sunday
→ desktop keeps working
→ progress/results flow through Connection Grid
→ Sunday can inspect / approve / cancel / redirect
→ executor reports completion
→ OSCAR independently verifies expected result where practical
→ if Personal Policy permits: save/checkpoint work
→ optionally close apps / sleep / shut down desktop
→ task remains visible from Sunday/cloud
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
3. Sunday can revoke/pause user-authorized autonomous work but cannot defeat local hardware safety.
4. Workers cannot grant themselves new node permissions.
5. A disconnected node loses live capabilities but does not erase durable task state.
6. Duplicate/replayed commands are rejected through correlation IDs/idempotency/replay protection.
7. Task leases expire so dead executors do not remain `working` forever.
8. Reconnect restores advertised capability/state before work resumes.

## Grid UI

The Connection Grid should be visible from Sunday and desktop as a compact operational surface, not a network-admin dashboard.

Normal view:

```text
OSCAR Grid

Sunday        Here
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

Owner-level emergency controls remain immediately reachable on Sunday.

## Availability semantics

OSCAR should use explicit availability levels rather than one binary `online` status.

```text
FULL
core + cloud + Sunday + available nodes

CONNECTED
core available but some capability nodes absent

LOCAL
cloud unavailable; Sunday/Edge/local paths continue where possible

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
→ Sunday and Edge retain allowed local capability
→ desktop task may continue locally
→ durable updates queue until rendezvous returns

Sunday offline
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
2. Sunday is the preferred owner control/kill-switch surface, not a substitute for hardware safety.
3. Edge keeps local presence/reflex/safety available even when higher layers disappear.
4. Cloud is replaceable and may be free, paid or self-hosted.
5. Remote work uses the same Durable Execution Runtime and evidence/verification model as local work.
6. Nodes control one another only through advertised, scoped capabilities.
7. OSCAR never claims remote power/control capability that is not currently available.
8. Availability degrades explicitly rather than silently disappearing.

## Gate B local completion candidate — 2026-10-04

Separate local owner-control/core/Worker processes now demonstrate continued execution across control disconnect/Core termination, natural lease expiry, reconnect and independently verified exactly-once recovery. Authority still shares SQLite plus loopback HTTP; independent stores/public remote deployment/phone control remain unverified. Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).
