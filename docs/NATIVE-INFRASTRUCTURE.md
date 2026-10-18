# Native OSCAR Infrastructure

This document defines OSCAR-owned transport, capability, model-routing and availability infrastructure.

## Core decision

OSCAR does **not** depend on Latch or SwitchRoute as completed external products.

Their useful architecture/logic is folded into OSCAR natively:

1. **OSCAR Transport + Capability Fabric** — informed by Latch.
2. **OSCAR Model Router** — informed by SwitchRoute.
3. **OSCAR Connection Grid** — the availability/control fabric connecting OSCAR Mobile, cloud, desktop and Edge through those native contracts.

The separate repositories remain reference/prototype sources only.

# 1. OSCAR Transport + Capability Fabric

## Purpose

Provide one secure typed transport between OSCAR Core and capability-bearing surfaces such as:

- desktop machine nodes;
- OSCAR Mobile;
- Edge devices;
- cloud coordinators/background workers;
- ChatGPT/tool surfaces;
- plugins/connectors;
- specialist applications.

## Responsibilities

- node/session identity;
- pairing and scoped credentials;
- bidirectional events/actions/results;
- capability advertisement;
- task/result correlation IDs;
- reconnect/backoff;
- progress/stream callbacks;
- permission-aware dispatch;
- audit/provenance metadata;
- outbound-first rendezvous for private devices;
- protocol version negotiation;
- cancellation/control messages;
- health/heartbeat state;
- replay protection/idempotency for consequential commands.

Conceptually:

```text
OSCAR Core
   │
OSCAR Transport + Capability Fabric
   ├─ OSCAR Mobile
   ├─ Desktop nodes
   ├─ Edge
   ├─ Cloud coordinator
   └─ external capability adapters
```

No transport implementation owns OSCAR's identity, memory, Personal Policy, Persona or task semantics.

## ChatGPT plugin / connector

ChatGPT reaches OSCAR through an **OSCAR-owned plugin/connector**, not a required Latch plugin/runtime.

The connector remains thin: authenticate, expose scoped OSCAR actions/state, translate typed calls and return task/evidence/artifact state. It does not become a second orchestration system.

## Edge

ESP32-class devices use a small native OSCAR Edge client/protocol. Home devices prefer authenticated outbound sessions so users do not expose MCU services directly to the Internet.

# 2. OSCAR Connection Grid

The Connection Grid is the runtime topology built on native transport.

```text
                 OSCAR Mobile
        owner controls + approvals
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
   Cloud        Desktop(s)     Edge
 rendezvous      execution   local reflex
```

Detailed behavior lives in [CONNECTION-GRID.md](CONNECTION-GRID.md).

## Roles

### OSCAR Mobile

- preferred everyday owner-control surface;
- biometric/PIN confirmation;
- inspect/pause/cancel/revoke work;
- remote task continuation;
- notifications and handoff.

OSCAR Mobile is not a substitute for local physical safety and is not assumed infallibly online.

### Cloud coordinator

- remote rendezvous;
- durable task coordination/checkpoints;
- notification/event fan-out;
- remote routing when local nodes are behind NAT;
- optional provider access/state services.

Cloud remains portable and may be free-tier, paid or BYOC.

### Desktop nodes

- high-capability execution: Codex, terminal, filesystem, browser, computer use, installed apps, GPU/local models;
- long-running work while the user is away;
- remote progress/result/control through the Grid.

### OSCAR Edge

- local wake/VAD/Sentry signals;
- sensors/GPIO/actuators;
- deterministic safety/reflexes;
- local LAN helper capabilities such as Wake-on-LAN when supported.

## Remote continuation

A desktop task may continue after the user leaves:

```text
start task on Desktop
→ persist objective/checkpoint/lease
→ user leaves with OSCAR Mobile
→ desktop continues
→ progress/results flow through Grid
→ OSCAR Mobile can inspect / approve / cancel
→ verify result
→ optional sleep/shutdown machine if permitted
```

Remote power-on is exposed only when a real Wake-on-LAN/management/power capability is present.

## Availability

Do not model availability as one boolean.

```text
FULL        = coordinator + owner surface + available nodes
CONNECTED   = core available, some nodes absent
LOCAL       = cloud unavailable, permitted local paths continue
REFLEX_ONLY = only deterministic Edge safety/reflex path remains
OFFLINE     = no OSCAR compute path reachable from current surface
```

Durable tasks preserve state through executor loss and leases expire so dead nodes do not remain falsely `working`.

# 3. OSCAR Model Router

## Purpose

Provide native provider/model/credential selection without a SwitchRoute runtime dependency.

Detailed behavior is canonical in [MODEL-ROUTING.md](MODEL-ROUTING.md).

## Responsibilities

- provider/model registry;
- independent credential pools;
- task/capability suitability;
- automatic/manual routing modes;
- latency/cost/quality policy;
- provider/model/credential health;
- known quota/rate/concurrency state;
- fallback/circuit behavior;
- context/tool/vision/audio capability metadata;
- local/private runtime discovery;
- user/project/provider policy;
- route/outcome/usage history;
- graceful degradation.

```text
Controller decides: reasoning needed?
        ↓
OSCAR Model Router
        ↓
provider → model → credential
        ↓
REPORTED / INFERRED result
        ↓
verification if required
```

Keep these boundaries separate:

```text
Controller                  = which class of action?
Capability selection = which executor/tool/device?
Model Router         = which provider/model/credential?
```

Coding agents, terminal, computer use and installed apps are capabilities, not ordinary model-provider entries.

## Routing modes

- Auto;
- Fast;
- Balanced;
- Heavy Duty;
- Free First;
- Cheap;
- Local;
- Private;
- Manual;
- Specialist.

Manual selection still obeys privacy, permission and safety policy.

## Provider breadth

The initial development set includes GroqCloud, OpenRouter, NVIDIA NIM, Google AI Studio, Z.ai, Ollama Cloud and local Ollama/LM Studio/vLLM endpoints.

The broader provider catalog is adapter-driven. Provider breadth must not enlarge OSCAR Core.

## Credential pools

Each credential slot tracks independent health/quota/rate/usage state where measurable. UI may show masked slot IDs, usage, models, latency, cost, quota, errors and route history, never raw key values.

Unknown quota is not infinite. Unknown price is not free. Unknown latency/quality gets no artificial routing advantage.

# 4. Cloud deployment portability

OSCAR should not assume one cloud vendor.

The coordinator/runtime should support:

- lightweight VM/container deployment;
- event-driven/serverless rendezvous where appropriate;
- free-tier deployment for developer/personal use;
- paid BYOC for higher reliability.

Current deployment candidates and their limitations are maintained in `docs/CONNECTION-GRID.md` and should be re-verified before use because free tiers change.

Avoid provider-specific types leaking into core task/transport contracts.

# 5. Reuse policy

Latch/SwitchRoute prototypes may be mined for:

- protocol/provider adapters;
- routing heuristics;
- quota/capacity handling;
- health/circuit logic;
- local runtime handling;
- types;
- failure handling;
- tests;
- security lessons.

Rule:

> Reuse proven logic where useful; do not preserve a separate service boundary merely because an earlier prototype had one.

# 6. Development credentials

The developer may provide real credentials through a local repository-root `.env` for integration testing.

- real secrets never enter Git;
- `.env.example` contains placeholders only;
- secrets are never printed/snapshotted/copied to frontend/docs;
- telemetry stores provider/model + masked slot ID;
- CI uses mocks/test adapters unless scoped secrets are deliberately configured;
- unmeasured usage/quotas remain `unknown`.

# 7. Ownership

```text
OSCAR
  ├─ owns task semantics
  ├─ owns transport semantics
  ├─ owns capability discovery
  ├─ owns Connection Grid availability/control semantics
  ├─ owns model routing
  └─ treats cloud/providers/devices/tools as replaceable adapters
```

This preserves:

- desktop independence;
- device-mesh execution;
- replaceable cloud/provider infrastructure;
- capability loss without identity loss;
- evidence-backed reporting;
- explicit graceful degradation.

# 8. Verification milestones

Roadmap slices remain canonical. Build Gates in [BUILD-GATES.md](BUILD-GATES.md) provide cross-slice manual checkpoints.

Gate A should prove native transport/model routing. Gate B should prove useful machine work and remote continuation. Later gates should prove Connection Grid failover/degradation, OSCAR Mobile owner controls and Edge safety separation.

## Club A implementation checkpoint

The native foundation now lives in `oscar/contracts.py`, `storage.py`, `runtime.py`, `capabilities.py`, `grid.py` and `transport.py`. SQLite is the durable task/ledger/lease authority. Transport targets authenticate per-node sessions, recheck capability scope and bind commands to task/correlation/lease IDs. Replay nonces and action idempotency are durable. Started actions with uncertain outcomes block replay.

`python -m oscar proof` uses a real loopback HTTP reference server.
`python -m oscar grid-proof` exercises reference-node lease expiry; these historical
proofs share the coordinator SQLite store and do not establish remote operation.
The [connected candidate](development/GROUP-04-D2.md) separately implements scoped
HTTPS device sessions and independent outbound Worker processes using the same
authoritative Grid/Runtime. [Protocol 2](development/GROUP-04-D2-PROTOCOL.md)
defines native synchronization and execution fencing. Stored token digests remain
separate from provider credentials. Public-host and physical-device acceptance
are still outstanding; the legacy reference listener remains loopback-only.

`Transport` is the adapter boundary for future network deployments. This does not establish a production secure Internet transport. See [the Club A checkpoint](CLUB-A-CHECKPOINT.md). No Latch/SwitchRoute service dependency was added.

## Owner scope decision — 2026-10-05

Slice 07: **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**.
**PHYSICAL EDGE ACCEPTANCE DEFERRED BY OWNER** — `DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`.
Protocol, firmware, Grid integration, ESP32/Pico cross-builds and deterministic
safety contracts in simulation are accepted for continuation. Historical
simulator evidence remains **SIMULATED**. No physical GPIO, watchdog, UART,
E-stop or ESP32/Pico silicon PASS is claimed. Gate C remains **PARTIAL**.

Return to real ESP32/Pico acceptance during Slice 15 physical/device expansion
and/or Slice 16 reliability/security hardening. Physical failure, loss/recovery,
watchdog and safety/reflex verification remain mandatory before Slice 17
Unified Alpha can PASS. The hardware acceptance guide is preserved.
The owner authorizes Slice 08 after Slice 07 integration; Slice 09/10, deployment
and Galaxy Tab Home Node remain outside this work.
