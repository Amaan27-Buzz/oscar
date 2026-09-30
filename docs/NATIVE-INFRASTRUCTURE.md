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

## Edge

ESP32-class devices use a small native OSCAR Edge transport/client rather than requiring the full desktop/runtime stack.

Preferred network behavior remains outbound-first so the home network does not need exposed inbound ports.

# 2. OSCAR Model Router

## Purpose

Provide native model/provider selection without making SwitchRoute a runtime dependency.

The router absorbs the useful SwitchRoute logic directly into OSCAR.

## Responsibilities

- provider/model registry;
- task/capability suitability;
- latency/cost/quality policy;
- provider availability and health;
- fallback chains;
- model-specific context limits/capabilities;
- structured/vision/audio/tool-use capability metadata;
- user/project/provider policy;
- routing telemetry and outcome history;
- graceful degradation.

Conceptually:

```text
Jev decides: is model reasoning needed?
        ↓
OSCAR Model Router decides: which allowed model/provider?
        ↓
provider adapter
        ↓
reported/inferred result
        ↓
OSCAR verification if the objective requires it
```

Jev and the Model Router are different:

- **Jev** decides whether reasoning/retrieval/tool/delegation/ask-user is the right class of action.
- **OSCAR Model Router** chooses the concrete model/provider after a model path has been selected.

## ChatGPT

ChatGPT remains an important intelligence provider/surface, but it is reached through OSCAR-owned transport/provider adapters.

OSCAR should not require a separately deployed Latch service simply to communicate with ChatGPT.

If a ChatGPT-specific wake/trigger mechanism is needed, that implementation detail sits behind the native transport/provider boundary so it can change without changing OSCAR Core.

# 3. Reuse policy

The separate Latch/SwitchRoute repositories can be mined for:

- protocol ideas;
- routing heuristics;
- type definitions;
- failure handling;
- provider adapters;
- tests;
- security lessons.

But integration follows this rule:

> Reuse proven logic where useful; do not preserve a separate service boundary merely because an earlier prototype had one.

Any code copied/adapted into OSCAR must still meet OSCAR's current contracts, engineering rules and tests.

# 4. Ownership and availability

Native ownership avoids a false dependency chain:

```text
OSCAR
  ├─ owns task semantics
  ├─ owns transport semantics
  ├─ owns capability discovery
  ├─ owns model routing
  └─ treats providers/devices/tools as replaceable adapters
```

This preserves the existing invariants:

- laptop independence;
- device-mesh execution;
- provider replaceability;
- capability loss without OSCAR identity loss;
- evidence-backed reporting;
- no single external prototype becoming the hidden host.
