# Roadmap

This roadmap is slice-based. Each slice must leave OSCAR coherent/testable and update affected docs in the same change.

All slices follow `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`.

Related planning docs:

- `docs/BUILD-GATES.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/MODEL-ROUTING.md`
- `docs/SEARCH-FRESHNESS.md`
- `docs/VOICE-SENTRY.md`
- `docs/PERSONA.md`
- `docs/RUNTIME-FOUNDATIONS.md`

## Implementation principle

Build OSCAR's nervous system first, then attach embodiments.

```text
objective
→ choose capability
→ execute
→ receive result
→ collect evidence
→ verify
→ record action/artifact
→ report only what evidence supports
```

Early development may run on a development PC for convenience. The PC is never OSCAR's permanent host.

Availability ultimately spans the **Connection Grid**:

```text
Sunday + Cloud coordinator + Desktop node(s) + OSCAR Edge
```

## Status legend

- ✅ Complete
- 🚧 In progress
- ⏭️ Next
- ◻️ Planned

## Slice 00 — Repository / architecture foundation ✅

Established product, architecture, engineering/design rules, Epistemic Integrity, World Model, Perception Fabric, Personal Policy, Workers/Protocols, Durable Execution Runtime, Capability Catalog, Action Ledger, Artifact Model, Voice/Sentry architecture, native transport/model routing, Connection Grid direction, Persona direction and build-gate strategy.

## Slice 01 — OSCAR Core Loop ✅

**Checkpoint:** implemented and verified for scoped file objectives and deterministic addition. The CLI proof independently reads exact file bytes and rejects a lying executor. See [Club A evidence](CLUB-A-CHECKPOINT.md).

**Goal:** prove the smallest evidence-backed execution loop.

Deliverables:

- typed `Objective`, `Task`, `Capability`, `Action`, `Result`, `Evidence`, `ArtifactRef`;
- explicit task/verification states;
- minimal capability registry;
- durable task persistence/cancel/retry foundation;
- Action Ledger + Artifact foundations;
- CLI/test harness;
- independent verifier;
- tests proving executor success cannot become verified without evidence.

Exit: a representative objective completes through `objective → action → evidence → verification → truthful report`.

## Slice 02 — TypeSafe Jev ✅

**Checkpoint:** typed deterministic routing and all nine epistemic decision routes are implemented and tested. Calendar, memory, specialist and Worker paths block when no capability exists. This is a conservative grammar, not a general natural-language parser.

**Goal:** add fast intent + epistemic routing.

Deliverables:

- typed intent;
- `known / world / recall / verify / reason / reported / specialist / worker / unknown` routes;
- deterministic paths when sufficient;
- capability-selection hook;
- repair/reroute/ask-user rules;
- latency instrumentation;
- uncertainty/unsupported-capability tests.

## Slice 03 — Native Transport + Capability Catalog + Connection Grid foundation 🚧

**Checkpoint: reference foundation VERIFIED; broader deployment PARTIAL.** Authenticated loopback HTTP execution, scopes, replay protection, correlation, cancellation, progress, heartbeat state, durable leases, disconnect/expiry/reclaim and five availability levels are verified. This foundation satisfies the current Gate A review scope. Public TLS/outbound rendezvous deployment, independent network-node stores and real embodiments require later acceptance scenarios.

**Goal:** connect OSCAR to remote capability nodes through OSCAR-owned contracts.

Deliverables:

- typed task/event/result protocol;
- node/session identity;
- pairing/scoped credentials;
- capability advertisement/search;
- reconnect/backoff/correlation IDs;
- audit/provenance;
- simulated/local reference node;
- cloud rendezvous/coordinator interface;
- Connection Grid node-state model;
- durable node leases/last-seen/health;
- explicit availability levels such as Full / Connected / Local / Reflex-only / Offline;
- portable coordinator deployment boundary supporting free-tier/paid/BYOC targets;
- no runtime dependency on Latch.

Exit: OSCAR discovers/invokes a capability on another node and survives node disconnect without losing objective state.

## Slice 04 — Native Model Router + cloud intelligence 🚧

**Checkpoint: hosted/routing foundation VERIFIED; broader integrations PARTIAL.** Four real hosted providers and 11 credential slots succeeded. Auto/Free First/Fast/Balanced/Heavy Duty and Manual pins have live evidence, as do real credential failover, bounded cross-provider recovery and reranking after an actual rate-limit observation. The live suite passed 162 checks; all 113 contract tests and quality checks pass. Groq HTTP 403 and Z.ai HTTP 429 are now treated as evidence that the seeded model/account metadata must be refreshed from live/current sources before attributing failure to credentials or provider capacity. Real quota remains unknown; scarcity counterfactuals use explicitly labeled fixtures. Local runtime instances, ChatGPT product surfaces and quality/quota calibration remain unverified. See [Club A evidence](CLUB-A-CHECKPOINT.md).

**Goal:** add provider/model/credential routing.

Deliverables:

- provider/model registry;
- multi-key credential pools;
- task/model affinity;
- health/quota/rate/latency/cost state;
- Auto / Fast / Balanced / Heavy Duty / Free First / Cheap / Local / Private / Manual / Specialist modes;
- fallback/circuit behavior;
- local runtimes;
- provider usage/history UI data contract;
- ChatGPT/other provider adapters;
- no runtime dependency on SwitchRoute;
- model output remains reported/inferred until verified where required.

**Manual milestone:** Gate A — Brain **PASS for the implemented foundation; manual review pending**. Public Grid deployment remains later integration work. **Stop here. Slice 05 has not started.**

## Post-Gate-A correction — live search + freshness ⏭️

The provider-model review exposed a general OSCAR requirement: volatile information cannot be trusted from stale manifests or model priors.

Before/with Club B, add the smallest first-class search/freshness path described in [SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md).

Deliverables:

- three Tavily credential slots (`TAVILY_API_KEY_1..3`) with masked credential-pool health/failover semantics;
- search as a Capability Catalog capability, not a hard-coded Jev special case;
- freshness classification for stable vs freshness-sensitive/live-state objectives;
- authoritative-source preference and source/retrieval timestamps;
- stale-provider/model metadata refresh through live inventory/current official docs before treating seeded IDs as current truth;
- bounded search retries/failover with 401/429/plan-limit handling;
- search results remain evidence inputs rather than automatically verified truth.

First acceptance objective:

> `What are the currently supported models and relevant free/developer access constraints for OSCAR's configured intelligence providers right now?`

Expected path:

```text
freshness-sensitive objective
→ live search/provider inventory
→ authoritative current sources
→ source-backed synthesis
→ evidence/retrieval timestamps
→ no stale model-prior claim presented as current
```

This is a correction to the source-of-truth policy, not a rollback of Gate A's verified core/runtime contracts.

## Slice 05 — First real machine Worker + remote continuation ◻️

**Goal:** make OSCAR useful through a real optional computer node.

Deliverables:

- Windows machine-node runtime;
- filesystem/terminal/Git;
- Codex and other installed coding agents where available;
- browser/computer-use path;
- installed-app capability discovery;
- task progress/cancel/reconnect;
- independent post-execution verification;
- long-running task continues after user leaves;
- Sunday/cloud-visible task state;
- remote pause/cancel/approve;
- optional machine sleep/shutdown after verified completion when policy/capability allow;
- Wake-on-LAN only when a real wake path exists.

Exit: useful repository/system objective can run remotely, survive ordinary disconnect and report verified/partial/blocked state truthfully.

## Slice 06 — LRA + Personal Policy + live context ◻️

**Goal:** add persistent continuity, explicit behavior rules and freshness-aware live retrieval.

Deliverables:

- LRA + Supermemory integration;
- active context + episodic history;
- procedural/project/device memory;
- Personal Policy store distinct from memory/Persona;
- natural-language policy editing;
- authority/staleness rules;
- live federated context/search;
- Tavily search adapter with three credential slots and replaceable search-provider boundary;
- freshness-sensitive query detection and live-source routing;
- source/provenance/retrieval-time metadata;
- current authoritative evidence outranks recalled/model-prior information;
- canonical entity graph foundation.

**Manual milestone:** Gate B — Can Do Work.

## Slice 07 — OSCAR Edge + reflexes ◻️

**Goal:** attach persistent local physical presence.

Deliverables:

- ESP32 gateway/client;
- Pico deterministic controller;
- typed ESP32↔Pico events;
- health/capability advertisement;
- GPIO/sensor/display test capabilities;
- local watchdog/safe defaults;
- reflex/emergency-stop path;
- reconnect/offline behavior;
- optional LAN helper capability such as Wake-on-LAN where hardware/network support it;
- simulator + physical-device verification.

## Slice 08 — Voice Core + Voice Identity + Voice Match/Map + Persona runtime ◻️

**Goal:** make the proven OSCAR loop natural by voice and establish character.

Deliverables:

- wake/VAD/STT;
- barge-in/echo cancellation;
- stable provider-independent VoiceProfile;
- speaking modes/fallback mapping;
- Voice Match;
- Voice Map;
- self-voice suppression;
- multi-device arbitration;
- PersonaProfile with configurable humor/candor/warmth/formality/brevity/playfulness/initiative/pushback;
- context trigger rules;
- truth/safety/permission invariants that Persona cannot override.

Exit: user can wake/interact naturally, hear a stable OSCAR voice and observe Persona changes without compromising evidence/safety semantics.

## Slice 09 — Sunday + communication + Connection Grid owner controls ◻️

**Goal:** ship OSCAR's phone embodiment.

Deliverables:

- Android app shell;
- present-not-launched home interaction;
- voice/text task continuity;
- notifications;
- biometric approval;
- Connection Grid owner-control surface;
- pause/cancel/revoke node/session controls;
- active remote-task supervision;
- Persona UI;
- Universal Channel Gateway foundation;
- initial supported call/message/email/meeting actions;
- explicit per-platform capability limits.

## Slice 10 — Desktop Interaction Runtime ◻️

**Goal:** polished native desktop embodiment.

Deliverables:

- compact OSCAR presence/overlay;
- expanded workspace only when needed;
- Dictate / Edit / Ask / Act;
- focused app/window/selection/cursor/accessibility context;
- screenshot/visual context;
- point-and-talk;
- approvals/task progress;
- Connection Grid state/control;
- fluid shared-element state transitions;
- verification state separate from executor completion.

**Manual milestone:** Gate C — Embodied OSCAR.

## Slice 11 — World Model + Perception Fabric + persistent Sentry + optional Daily Journal ◻️

**Goal:** create a coherent live picture of the user's digital/physical/communication environment.

Deliverables:

- World Model for people/places/devices/apps/projects/tasks;
- Perception Fabric across screen/device/sensor/location/communication/acoustic inputs;
- freshness/confidence/provenance;
- Passive/Aware/Guard/Away/Sleep Sentry;
- persistent local acoustic plane;
- explicit Sentry Aware vs Listening vs Muted vs Awareness Off states;
- optional Context Capture/Daily Journal;
- selected calls/messages/mail/meetings/in-person conversations where legitimately available;
- per-source capture capability checks;
- raw/transcript/summary/memory retention controls;
- consent/disclosure/privacy-zone controls;
- pause/delete/forget controls;
- no covert/default continuous recording;
- importance/urgency/confidence/interruptibility scoring.

Exit: OSCAR can answer `what is true now?`, remain persistently aware and, when explicitly configured, build a provenance-qualified daily continuity record without confusing awareness with recording.

## Slice 12 — Commissioning / setup ◻️

**Goal:** safely commission the personal system.

Deliverables:

- user identity;
- Persona setup;
- Personal Policy starter rules;
- Voice Identity calibration;
- Voice Match / optional Voice Map;
- Connection Grid pairing;
- free-tier/paid/BYOC cloud-coordinator choice;
- model providers;
- Sunday/Desktop/Edge pairing;
- Sentry setup;
- optional capture/journal source + retention configuration;
- permission matrix;
- end-to-end health tests;
- evidence-backed final readiness screen.

## Slice 13 — Avatar / presence UI ◻️

**Goal:** make OSCAR state physically legible.

Deliverables:

- reusable blue-shell/yellow-puck component;
- weighted spring/inertia;
- Idle/Listening/Speaking/Working/Verifying/Waiting/Blocked/Done/Sentry/Muted/Offline states;
- Persona-sensitive but truth-preserving expression amplitude;
- reduced-motion support;
- compact/icon variants.

## Slice 14 — Executive Planner + durable Workers + learning ◻️

**Goal:** scale from one objective to durable delegated responsibilities.

Deliverables:

- Executive Planner;
- Worker lifecycle/types;
- priorities/dependencies/deadlines/resources/risk;
- durable leases/heartbeats/checkpoints/reclaim;
- self-repair/reroute/escalation;
- Worker management visibility;
- Skills/Protocols;
- teach-by-demonstration;
- Learned Automation Evaluation Pipeline;
- Artifact/Result handoff.

**Manual milestone:** Gate D — JARVIS Layer.

## Slice 15 — Physical / device capability expansion + specialist engineering ◻️

**Goal:** broaden physical-world reach without a dedicated hardware-workbench product dependency.

Deliverables:

- additional Edge/device onboarding;
- sensors/relays/displays/motors/cameras;
- smart-home/environment adapters where legitimate;
- device inventory/health/capability discovery;
- firmware/provisioning through available specialist tools;
- CAD/circuit/simulation/3D/numerical/diagnostic tool routing;
- physical Protocol execution with deterministic local safety;
- typed engineering Artifacts/Results.

## Slice 16 — Self-maintenance + reliability/security/truthfulness pass ◻️

**Goal:** deliberately break OSCAR and prove graceful behavior.

Deliverables/tests include:

- provider/auth failures;
- Connection Grid cloud/Sunday/Desktop/Edge node loss;
- lease expiry/reclaim/restart;
- remote-task continuation;
- owner-control/revocation paths;
- capture-source failure and retention/deletion verification;
- consent/privacy regression tests;
- Persona cannot reduce truth/safety/permission;
- Voice Match spoof/Voice Map false positives;
- self-voice/echo;
- Action Ledger/Undo integrity;
- local hardware safety;
- learned-automation rollback.

## Slice 17 — Unified alpha ◻️

**Goal:** one evidence-backed developer alpha across core, Grid, models, machine work, memory, voice, Sunday, desktop, Edge, Sentry, Persona, Workers and physical capability.

Run one complete scenario crossing:

```text
perception / communication
→ World Model / Jev
→ Personal Policy + Persona presentation
→ Executive / task runtime
→ capability/model routing
→ Connection Grid node
→ Worker/device/action
→ ledger/artifact
→ verification
→ voice/text report
```

**Manual milestone:** Gate E — Unified Alpha.

## Build cadence

The initial 2–3 day sprint optimizes for vertical proof, not superficial completeness.

```text
Day 1  Gate A + basic Gate B
Day 2  Gate B + Gate C core
Day 3  Gate C + Gate D/E integration shell
```

Anything not genuinely verified remains planned/partial and is hardened after the first developer alpha.
