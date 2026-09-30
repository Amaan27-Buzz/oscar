# Native OSCAR Infrastructure

This document clarifies how the ideas proven in Amaan's separate Latch and SwitchRoute projects are used inside OSCAR.

## Core decision

OSCAR does **not** depend on Latch or SwitchRoute as completed external products.

Those repositories are design/reference implementations whose useful architecture and logic are folded into OSCAR natively.

The canonical OSCAR runtime therefore owns two internal subsystems:

1. **OSCAR Transport + Capability Fabric** — derived from the useful Latch architecture.
2. **OSCAR Model Router** — derived from the useful SwitchRoute routing logic.

The external repositories may remain useful as prototypes, experiments or sources of reusable ideas/code, but OSCAR must not require them to be separately deployed or complete in order to function.

# 1. OSCAR Transport + Capability Fabric

## Purpose

Provide one secure typed transport between OSCAR Core and capability-bearing surfaces such as:

- desktop machine nodes;
- Sunday;
- Edge devices;
- cloud/background workers;
- ChatGPT/tool surfaces;
- external plugins/connectors;
- specialist applications.

This subsystem absorbs the relevant architectural ideas from Latch directly into OSCAR.

## Responsibilities

- node/session identity;
- pairing and scoped credentials;
- bidirectional events/actions/results;
- capability advertisement;
- task/result correlation IDs;
- reconnect/backoff;
- streaming/progress callbacks;
- permission-aware dispatch;
- audit/provenance metadata;
- secure outbound rendezvous for private devices;
- transport version negotiation;
- cancellation and task-control messages;
- health/heartbeat state where appropriate.

## Native protocol boundary

Conceptually:

```text
OSCAR Core
   │
   ├── typed task/event/result protocol
   │
OSCAR Transport + Capability Fabric
   │
   ├── Sunday
   ├── Desktop nodes
   ├── Edge
   ├── cloud/background executors
   └── external capability adapters
```

No transport implementation gets to own OSCAR's identity, memory, policy or task semantics.

## ChatGPT plugin / connector

ChatGPT should reach OSCAR through an **OSCAR-owned plugin/connector**, not through a required Latch plugin/runtime.

The plugin is a thin doorway into OSCAR. It may expose scoped operations such as task submission/status/cancellation, capability discovery, Worker control, artifact retrieval and approved state queries, but it does not contain OSCAR's intelligence or become a second orchestration system.

Conceptually:

```text
ChatGPT
   ↓
OSCAR plugin / connector
   ↓
OSCAR Transport + Capability Fabric
   ↓
OSCAR Core
```

Sunday, desktop, Edge and other nodes use the same native transport concepts directly rather than being routed through ChatGPT.

## Edge

ESP32-class devices use a small native OSCAR Edge transport/client rather than requiring the full desktop/runtime stack.

Preferred network behavior remains outbound-first so the home network does not need exposed inbound ports.

# 2. OSCAR Model Router

## Purpose

Provide native model/provider/credential selection without making SwitchRoute a runtime dependency.

The router absorbs the useful SwitchRoute logic directly into OSCAR, including the separation of provider identity, credential validity, transient health, quota/capacity, latency, cost policy, routing strategy and bounded fallback.

Detailed routing behavior is canonical in [MODEL-ROUTING.md](MODEL-ROUTING.md).

## Responsibilities

- provider/model registry;
- multi-credential pools per provider;
- task/capability suitability;
- automatic and manual routing modes;
- latency/cost/quality policy;
- provider/model/credential health and availability;
- quota/rate/concurrency state where known;
- fallback chains;
- model-specific context limits/capabilities;
- structured/vision/audio/tool-use capability metadata;
- local/private runtime discovery boundaries;
- user/project/provider policy;
- routing telemetry and outcome history;
- graceful degradation.

Conceptually:

```text
Jev decides: what class of work is needed?
        ↓
model reasoning selected?
        ↓
OSCAR Model Router
        ↓
provider → model → credential
        ↓
reported/inferred result
        ↓
OSCAR verification if the objective requires it
```

Jev and the Model Router are different:

- **Jev** decides whether reasoning/retrieval/tool/delegation/ask-user is the right class of action.
- **OSCAR Model Router** chooses the concrete model/provider/credential after a model path has been selected.
- **Capability selection** chooses executable specialists such as Codex, Claude Code, OpenCode, terminal, computer use, installed applications, Sunday or Edge devices.

Do not flatten model providers and coding/agent executors into one generic provider list.

## Routing modes

The native router supports automatic behavior plus explicit user control. Planned profiles include:

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

Auto may choose an effective mode based on task, Personal Policy and current provider/capability state. Manual selection cannot bypass permission/privacy/safety boundaries.

## Provider breadth

OSCAR should support an extensible adapter catalog rather than a frozen list embedded in core logic.

The initial development set includes the user's available GroqCloud, OpenRouter, NVIDIA NIM, Google AI Studio, Z.ai and Ollama Cloud credentials plus local Ollama/LM Studio/vLLM endpoints. The broader compatibility target includes the hosted/local provider families already explored in SwitchRoute and the long-tail adapter pattern demonstrated by OmniRoute-style catalogs.

Provider breadth is a registry/adapter problem, not a reason to enlarge OSCAR Core.

## Credential pools and usage

Providers may expose multiple credential slots. Each slot is independently health/quota/rate/usage tracked where the provider exposes enough data.

The UI may show masked slot IDs, usage, models, latency, cost, quota, errors and routing history, but it must never reveal raw key values.

Unknown quota is not unlimited. Unknown price is not free. Unknown latency/quality must not receive an artificial routing advantage.

The local development credential layout is documented in the repository-root `.env.example`; real `.env` values remain local and ignored by Git.

## ChatGPT

ChatGPT remains an important intelligence provider/surface, but it is reached through OSCAR-owned transport/provider adapters.

OSCAR should not require a separately deployed Latch service simply to communicate with ChatGPT.

If a ChatGPT-specific wake/trigger mechanism is needed, that implementation detail sits behind the native transport/provider boundary so it can change without changing OSCAR Core.

# 3. Reuse policy

The separate Latch/SwitchRoute repositories can be mined for:

- protocol ideas;
- provider catalogs/adapters;
- routing heuristics and strategies;
- quota/capacity handling;
- circuit-breaker/health logic;
- budget/cost logic;
- model normalization;
- local runtime handling;
- type definitions;
- failure handling;
- tests;
- security lessons.

But integration follows this rule:

> Reuse proven logic where useful; do not preserve a separate service boundary merely because an earlier prototype had one.

Any code copied/adapted into OSCAR must still meet OSCAR's current contracts, engineering rules and tests.

# 4. Development credentials

The developer may provide real provider credentials through a local repository-root `.env` for manual integration testing.

Rules:

- real secrets never enter Git;
- `.env.example` contains placeholders only;
- secrets are never printed, snapshotted, sent to frontend code or copied into documentation;
- telemetry records provider/model plus masked credential-slot IDs, not secret values;
- automated CI uses mocks/test adapters unless scoped secrets are deliberately configured;
- provider metadata/usage that cannot be measured remains explicitly unknown.

# 5. Ownership and availability

Native ownership avoids a false dependency chain:

```text
OSCAR
  ├─ owns task semantics
  ├─ owns transport semantics
  ├─ owns capability discovery
  ├─ owns model routing
  ├─ owns routing/usage history
  └─ treats providers/devices/tools as replaceable adapters
```

This preserves the existing invariants:

- laptop independence;
- device-mesh execution;
- provider replaceability;
- capability loss without OSCAR identity loss;
- evidence-backed reporting;
- no single external prototype becoming the hidden host.

# 6. Verification milestones

Detailed slices remain in `ROADMAP.md`. Cross-slice manual verification milestones are defined in [BUILD-GATES.md](BUILD-GATES.md).

The first routing implementation belongs to Gate A and must be manually exercised against real local developer credentials where appropriate before it is treated as a proven developer-alpha path.
