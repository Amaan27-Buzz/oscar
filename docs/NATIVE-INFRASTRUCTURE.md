# Native OSCAR Infrastructure

This document defines OSCAR-owned transport, capability, model-routing and availability infrastructure.

## Core decision

OSCAR does **not** depend on Latch or SwitchRoute as completed external products.

Their useful architecture/logic is folded into OSCAR natively:

1. **OSCAR Transport + Capability Fabric** — informed by Latch.
2. **OSCAR Model Router** — informed by SwitchRoute.
3. **OSCAR Connection Grid** — the availability/control fabric connecting Sunday, cloud, desktop and Edge through those native contracts.

The separate repositories remain reference/prototype sources only.

# 1. OSCAR Transport + Capability Fabric

## Purpose

Provide one secure typed transport between OSCAR Core and capability-bearing surfaces such as:

- desktop machine nodes;
- Sunday;
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
   ├─ Sunday
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
                 Sunday
        owner controls + approvals
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
   Cloud        Desktop(s)     Edge
 rendezvous      execution   local reflex
```

Detailed behavior lives in [CONNECTION-GRID.md](CONNECTION-GRID.md).

## Roles

### Sunday

- preferred everyday owner-control surface;
- biometric/PIN confirmation;
- inspect/pause/cancel/revoke work;
- remote task continuation;
- notifications and handoff.

Sunday is not a substitute for local physical safety and is not assumed infallibly online.

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
→ user leaves with Sunday
→ desktop continues
→ progress/results flow through Grid
→ Sunday can inspect / approve / cancel
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
Jev decides: reasoning needed?
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
Jev                  = which class of action?
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

Gate A should prove native transport/model routing. Gate B should prove useful machine work and remote continuation. Later gates should prove Connection Grid failover/degradation, Sunday owner controls and Edge safety separation.
