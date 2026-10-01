# Roadmap

This roadmap is slice-based. Each slice should leave OSCAR in a coherent, testable state and update the README plus affected docs in the same change.

All implementation slices are governed by `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`: keep scope coherent, boundaries explicit, failure behavior intentional, code simple enough to evolve safely, and completion claims no stronger than the available evidence.

Related planning documents:

- `docs/JARVIS-GAP-REVIEW.md`
- `docs/COMPETITIVE-BENCHMARK.md`
- `docs/RUNTIME-FOUNDATIONS.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/MODEL-ROUTING.md`
- `docs/BUILD-GATES.md`
- `docs/VOICE-SENTRY.md`

The implementation order is deliberately **software-core first, hardware later**. OSCAR's final architecture still requires always-on Edge hardware, but the first implementation milestone should prove OSCAR's own nervous system before attaching phone, voice and physical embodiments.

The first loop to prove is:

```text
objective
→ choose capability
→ execute
→ receive result
→ collect evidence
→ verify
→ record action/artifact
→ report only what the evidence supports
```

During early development this loop may run on a development computer for convenience. That does **not** make the computer OSCAR's permanent host.

Two earlier projects are architectural inputs rather than required external products:

- Latch architecture/logic → folded into **native OSCAR Transport + Capability Fabric**;
- SwitchRoute architecture/logic → folded into **native OSCAR Model Router**.

OSCAR must not depend on either separate repository being complete or separately deployed.

Hardware/engineering follows the same rule: physical control is native OSCAR Edge/device capability work. CAD, circuit design, simulation, firmware and other engineering tasks route to whichever installed or connected specialist tools are actually available rather than to one mandatory workbench product.

## Status legend

- ✅ Complete
- 🚧 In progress
- ⏭️ Next
- ◻️ Planned

## Slice 00 — Repository foundation ✅

**Goal:** establish the product, design, engineering and agent-development contract before implementation.

Deliverables include:

- canonical product/architecture definition;
- feature inventory;
- LRA/Supermemory/Jev memory plan;
- Personal Policy;
- communication/Workers/Protocols plans;
- World Model + Perception Fabric;
- Executive Planner;
- Universal Channel Gateway;
- Durable Execution Runtime;
- Capability Catalog + Dynamic Tool Search;
- Action Ledger + Artifact/Result Model;
- Learned Automation Evaluation Pipeline;
- Epistemic Integrity;
- Voice/Sentry/Voice Match direction;
- native OSCAR transport/model-routing decision;
- design/engineering/agent guidance;
- repository support and checks.

Exit condition: repository clearly defines OSCAR's product, architecture, engineering rules, truth/verification model, implementation order and major system contracts.

## Slice 01 — OSCAR Core Loop ⏭️

**Parallel visual experiment, awaiting manual review:** `prototypes/sunday/` evaluates only Home and Sentry/Awareness with scripted, disconnected states. See its [research, model and verification notes](../prototypes/sunday/README.md). It establishes no production mobile stack and completes neither Slice 00.5 nor Slices 09/13. Core Loop remains next.

**Goal:** prove the smallest end-to-end OSCAR execution loop before building embodiments or hardware.

Deliverables:

- minimal core package/service boundary with no desktop-host assumption;
- typed `Objective`, `Task`, `Capability`, `Action`, `Result`, `Evidence` and `ArtifactRef` contracts;
- explicit task states such as `planned`, `executing`, `result_received`, `verifying`, `verified`, `partially_verified`, `failed`, `blocked`, `cancelled` and `unknown`;
- completion-condition and verification-strategy contracts;
- minimal local capability registry;
- minimal Durable Execution Runtime foundation with persisted task state, cancellation and retry budget;
- Action Ledger foundation;
- Artifact / Result Model foundation;
- simple CLI/test harness rather than product UI;
- one small reference capability such as scoped test-workspace file write/read;
- independent verifier;
- evidence-backed final reporting;
- tests proving `reported success` cannot become `verified` without evidence.

Reference demonstration:

```text
"Create hello.txt containing OSCAR online in the test workspace"
→ select filesystem capability
→ write file
→ executor reports success
→ OSCAR reads file independently
→ compare expected vs actual
→ mark VERIFIED
→ report completion with evidence
```

Exit condition: a representative objective can travel through `objective → capability → action → result → evidence → verification → ledger/artifact → truthful report`, and a false executor-success report cannot produce a verified completion state.

## Slice 02 — TypeSafe Jev ◻️

**Goal:** add the fast intent + epistemic decision layer on top of the proven Core Loop.

Deliverables:

- typed intent model;
- typed epistemic routes: `known / world / recall / verify / reason / reported / specialist / worker / unknown`;
- deterministic routing where sufficient;
- capability-selection hook;
- current-evidence vs recall vs inference distinctions;
- ask-user path only when retrieval/verification cannot safely resolve ambiguity;
- repair/reroute decision contract;
- Personal Policy/permission hooks;
- latency instrumentation;
- tests for incorrect certainty, unsupported capability and unknown-state handling.

Exit condition: representative requests route through deterministic execution, verification or ask-user paths without unnecessary heavy-model calls, guessed personal context or false certainty.

## Slice 03 — Native OSCAR Transport + Capability Catalog ◻️

**Goal:** connect OSCAR to external execution surfaces through OSCAR-owned transport/capability contracts.

This slice folds the useful Latch architecture into OSCAR rather than integrating Latch as a required external service.

Deliverables:

- native typed task/event/action/result transport boundary;
- node/session identity;
- pairing and scoped credentials;
- capability advertisement;
- lightweight capability manifests;
- Capability Catalog;
- Dynamic Tool Search / progressive contract loading;
- metadata for suitability, permissions, risk, availability, surface, latency/cost, reliability and undo;
- event/task correlation IDs;
- reconnect/backoff;
- bounded remote command/result transport;
- progress/streaming callbacks where useful;
- audit/provenance metadata;
- simulated/local reference node proving the protocol before Edge hardware exists;
- clear documentation that the separate Latch repo is reference/prototype material, not a runtime dependency.

Exit condition: OSCAR can discover a capability on another node, load only its relevant contract, invoke it through native transport, receive a structured result and independently verify the objective without assuming that node hosts OSCAR.

## Slice 04 — Native OSCAR Model Router + cloud intelligence ◻️

**Goal:** add cloud reasoning as a selectable capability using OSCAR-owned routing logic.

This slice folds the useful SwitchRoute architecture/logic into OSCAR rather than requiring SwitchRoute as a separately deployed product.

Deliverables:

- native provider/model registry;
- independent credential pools per provider;
- task/capability suitability metadata;
- latency/cost/quality policy;
- provider/model/credential health and availability;
- fallback chains and circuit behavior;
- model capability metadata: tool use, structured output, vision/audio/context limits where relevant;
- automatic modes (`Auto`, `Fast`, `Balanced`, `Heavy Duty`, `Free First`, `Cheap`, `Local`, `Private`, `Specialist`) plus explicit manual selection;
- ChatGPT provider/surface adapter through native OSCAR transport;
- async callbacks into Durable Execution Runtime;
- structured model/agent outputs recorded as `reported`/`inferred`, never automatically `verified`;
- graceful provider degradation;
- Jev decisions for when a model is unnecessary vs useful;
- route/outcome/usage telemetry for later learning;
- explicit documentation that the separate SwitchRoute repo is reference/prototype material, not a runtime dependency.

Exit condition: Jev can decide that reasoning is needed, the native router can choose/fallback among allowed providers/models/credentials, manual override works, and OSCAR preserves the evidence boundary between model claims and verified state.

**Manual milestone:** complete **Gate A — Brain** from `docs/BUILD-GATES.md` after Slices 01–04.

## Slice 05 — First real machine Worker ◻️

**Goal:** make OSCAR genuinely useful through an optional computer node while preserving laptop independence.

Deliverables:

- lightweight Windows machine-node runtime;
- pairing through native OSCAR transport;
- dynamic capability advertisement;
- scoped filesystem/terminal/Git primitives;
- Codex integration;
- other installed coding-agent capabilities when available;
- browser/computer-use integration where practical;
- installed-app capability discovery/automation through the strongest legitimate integration path;
- task progress/result callbacks;
- cancellation and disconnect handling;
- restart/reconnect recovery;
- independent test/state verification after specialist completion;
- first meaningful Worker/objective flow.

Reference objective:

```text
"Check this repository, find why the tests fail, fix it and make sure they pass."
→ discover repository/Codex/terminal capabilities
→ delegate implementation
→ receive specialist report
→ independently run/inspect tests and repository state
→ VERIFIED / PARTIAL / FAILED
→ report evidence
```

Exit condition: OSCAR can delegate a useful software objective to a real machine/coding capability, survive ordinary executor failure/disconnect and verify completion independently where practical.

## Slice 06 — LRA + Personal Policy + live context ◻️

**Goal:** add persistent continuity and authoritative user preferences after the execution loop already works.

Deliverables:

- LRA integration boundary;
- active-context + episodic-history model;
- Supermemory backend;
- task/project/device/procedural memory types;
- Jev recall vs live-verification decisions;
- Personal Policy store distinct from inferred memory;
- natural-language preference create/edit/remove;
- policy scoping/precedence/conflict resolution;
- provenance/confidence metadata;
- remember/forget/update flows;
- universal live context/search abstraction;
- source-authority and staleness rules;
- initial canonical entity/relationship graph;
- explicit `recalled / inferred / reported / verified` distinctions.

Exit condition: OSCAR can recover relevant historical context, query current authoritative context when needed and apply explicit user preferences without confusing memory or inference with current verified truth.

**Manual milestone:** complete **Gate B — Can Do Work** after Slices 05–06.

## Slice 07 — OSCAR Edge + reflexes ◻️

**Goal:** attach the persistent physical embodiment after the core contracts are proven in software.

Deliverables:

- ESP32 gateway project structure;
- Pico/RP2040 deterministic controller project structure;
- small native OSCAR Edge transport client/protocol;
- typed event/message schema between ESP32 and Pico;
- device identity/version reporting;
- health heartbeat;
- capability advertisement into the existing catalog;
- GPIO/sensor/display test capabilities;
- local watchdog/safe-default behavior;
- deterministic reflex state machine;
- emergency-stop path;
- simple local device commands;
- hardware latency instrumentation;
- reconnect/offline behavior;
- simulator tests plus real-device verification;
- explicit simulator-vs-hardware evidence reporting.

Exit condition: ESP32 and Pico join OSCAR as capability-bearing nodes, preserve deterministic safety without cloud intelligence and use the same native task/result/evidence contracts as software nodes.

## Slice 08 — Voice Core + OSCAR Voice Identity + Voice Map ◻️

**Goal:** make the proven OSCAR loop naturally accessible by voice and establish the always-on local acoustic primitives Sentry will later consume.

Deliverables:

### Voice input
- microphone/audio pipeline;
- local wake word + VAD;
- streaming STT abstraction;
- barge-in;
- echo cancellation;
- first-audio/command latency metrics;
- voice/text task continuity.

### OSCAR Voice Identity
- provider-independent `VoiceProfile` contract;
- stable OSCAR voice across desktop/Sunday/desk where possible;
- natural prosody/modulation rather than a generic provider default;
- pronunciation lexicon/control;
- normal / quiet-night / focused-serious / alert / representative speaking modes;
- streaming/chunked TTS;
- provider fallback mapping that preserves identity as closely as possible;
- self-voice tagging/playback reference so OSCAR never learns or reacts to its own TTS as an external speaker.

### Voice Match
- owner/authorized-speaker verification interface;
- confidence scores;
- explicit separation from high-risk authentication.

### Voice Map
- local speaker-profile/embedding abstraction;
- `owner / known / recognized-but-unverified / unknown / multiple / uncertain` states;
- optional linkage to canonical people with provenance/confidence;
- speaker-change/presence events without requiring full transcription;
- privacy/retention controls for voice profiles;
- explicit rule that Voice Map recognition does not grant permission;
- OSCAR's own synthesized voice excluded from enrollment/identity updates.

### Multi-device arbitration
- wake/listen identity across devices;
- confidence/proximity/active-device arbitration;
- one-owner-per-turn rule;
- handoff/failover.

Exit condition: the user can wake OSCAR, invoke the Core Loop by voice, hear a stable OSCAR voice, interrupt naturally, avoid duplicate device responses, and generate local confidence-qualified speaker events without continuous cloud transcription.

## Slice 09 — Sunday + communication + Universal Channel Gateway ◻️

**Goal:** ship OSCAR's phone embodiment and prove communication as a first-class capability family.

Deliverables:

- Android app shell;
- OSCAR identity/avatar + stable voice profile;
- voice + text session;
- notifications;
- native OSCAR transport connection;
- task/context continuity;
- phone capability advertisement;
- initial safe phone/app actions;
- Universal Channel Gateway event/action envelope;
- first native/official adapters;
- canonical participant/entity IDs;
- explicit per-channel capability limits;
- cellular/app-call capability studies;
- audio access/loopback and VoIP fallback study;
- AI call-handling policy hooks where supported;
- mobile meeting transcription/notes;
- system-wide dictation/input path where practical;
- biometric confirmation;
- Voice Map/Voice Match participation subject to platform support.

Exit condition: a task can move between Sunday and another OSCAR surface without becoming a separate assistant/session, and communication adapters expose only capabilities actually supported by the device/platform.

## Slice 10 — Desktop Interaction Runtime ◻️

**Goal:** turn the capable machine node into a polished native desktop embodiment and match the practical VoiceOS interaction baseline.

Deliverables:

- native/lightweight Windows app shell;
- macOS adapter boundary/plan;
- OSCAR presence UI;
- stable OSCAR voice output/input integration;
- first-class `Dictate / Edit / Ask / Act` runtime;
- focused app/window/text-field context;
- selected-text operations;
- cursor target + accessibility-tree context;
- screenshot/visual context;
- point-and-talk;
- accessibility/clipboard insertion fallbacks;
- system-wide dictation;
- Action-Ledger-backed undo where real;
- meeting transcription/notes;
- task/progress/approval surfaces;
- verification state separate from executor completion.

Exit condition: OSCAR can understand and act on the current desktop target with low-friction VoiceOS-grade interaction while preserving the same evidence, permission and task semantics as the headless machine Worker.

**Manual milestone:** complete **Gate C — Embodied OSCAR** after Slices 07–10.

## Slice 11 — World Model + Perception Fabric + Sentry ◻️

**Goal:** give OSCAR one coherent live representation of what is happening across the user's digital, acoustic and physical environment.

Deliverables:

- World Model graph for people, places, devices, apps, projects, objects, tasks and relationships;
- current evidence separated from historical memory;
- Perception Fabric ingesting screen/accessibility state, app/device events, sensors, location, authorized camera observations and local acoustic events;
- state freshness/confidence/provenance;
- fusion of Sunday, desktop, Edge, calendar, communication and Worker state;
- entity resolution expansion across communication/context sources;
- Passive/Aware/Guard/Away/Sleep Sentry modes;
- **always-on local acoustic Sentry plane** when enabled: wake, VAD/speech presence, Voice Map classification, speaker-change/multiple-speaker events, configured sound-event classes and barge-in;
- explicit no-continuous-cloud-audio default;
- explicit distinction between speech presence, identity classification and permission to transcribe/retain content;
- OSCAR self-voice suppression during Sentry listening;
- importance/urgency/confidence/interruptibility scoring;
- Personal Policy-aware interruption decisions;
- predictive signals for obvious schedule/task/device risk;
- notification/speech escalation policy.

Exit condition: OSCAR can answer `what is true now?` from a coherent live model, distinguish stale/unknown state and react to meaningful physical/acoustic/digital events without continuously uploading room audio or treating old memory as current truth.

## Slice 12 — First-run commissioning + Voice Match/Voice Map ◻️

**Goal:** make setup safe and useful without forcing the user through an exhaustive settings product.

Deliverables:

- identity/basic interaction preferences;
- Personal Policy starter rules;
- communication/meeting/Worker autonomy defaults;
- owner Voice Match enrollment across varied conditions;
- optional known-person Voice Map enrollment/labeling with consent and retention controls;
- explicit explanation that Voice Map recognition is perception, not authorization;
- OSCAR Voice Identity calibration/listening test and fallback behavior;
- self-voice suppression test while OSCAR speaks;
- wake/reflex tests;
- authorization classes;
- device/environment discovery;
- service/channel connections;
- Sentry configuration including local acoustic awareness/transcription-retention choices;
- Sunday/desktop/Edge pairing;
- permission matrix;
- end-to-end calibration.

Exit condition: a new installation ends with verified health/permission/voice status, understandable policy, working owner Voice Match, correctly configured Voice Map/Sentry privacy and a verified OSCAR voice path.

## Slice 13 — Avatar / presence UI ◻️

**Goal:** turn OSCAR's character into a coherent state-driven interface across suitable surfaces.

Deliverables:

- reusable avatar component;
- joystick/puck motion physics;
- expression/state system;
- listening/thinking/speaking choreography;
- explicit Working / Verifying / Waiting / Blocked / Done / Failed states;
- serious/Sentry states;
- reduced-motion accessibility;
- compact/icon variants.

Exit condition: avatar motion always maps to actual OSCAR state and never displays success/working/thinking when the runtime is failed, blocked or still unverified.

## Slice 14 — Executive Planner + durable Workers + learning ◻️

**Goal:** scale the proven single-objective loop into durable delegated teammates and concurrent objectives.

Deliverables:

- Executive Planner over tasks/Workers/Protocols;
- priority/deadline/dependency/resource/risk/interruptibility model;
- scheduling, parallelization, pause/pre-emption and rerouting;
- delegated Worker schema/lifecycle/state;
- voice/chat Worker creation/editing;
- temporary/task/persistent Worker types;
- Worker capability/permission/context envelope;
- Worker collaboration/handoff/dependency model;
- Durable Execution Runtime expansion: leases, heartbeats, checkpoints, reclaim, zombie detection and restart/resume;
- Jev self-repair/reroute/escalation;
- Worker management UI;
- social-media Worker reference;
- procedural-memory capture;
- route/tool outcome history;
- `SKILL.md` Skill contract;
- teach-by-demonstration;
- Capability Catalog search for Workers/Protocols;
- Protocol schema + durable state;
- routine/time/event triggers;
- pause/resume/cancel;
- Learned Automation Evaluation Pipeline;
- Artifact/Result handoff;
- measurable repeated-task latency/cost/reliability improvement.

Exit condition: OSCAR can coordinate multiple objectives, create a Worker naturally, survive executor loss, discover capabilities progressively, learn/be taught workflows, evaluate them before promotion and reuse them without self-granting authority.

**Manual milestone:** complete **Gate D — JARVIS Layer** after Slices 11–14.

## Slice 15 — Physical / Device Capability Expansion + specialist engineering ◻️

**Goal:** broaden OSCAR's physical-world reach and engineering capability without introducing a dedicated hardware-workbench product dependency.

Deliverables:

- onboarding/provisioning path for additional OSCAR Edge and capability-bearing devices;
- sensors, buttons, relays, displays, motors/actuators and cameras through typed capability contracts;
- custom ESP32/Pico projects joining native OSCAR transport;
- smart-home/environment adapters where useful and legitimate;
- device inventory, health, availability and capability discovery;
- firmware/programming/provisioning through available specialist tools;
- workbench/environment telemetry;
- device-state correlation with World Model/Perception;
- physical Protocol execution with local deterministic safety;
- spatial perception experiments where useful;
- CAD, circuit design/simulation, 3D, numerical simulation, diagnostics, reconstruction and optimization routed to installed/connected specialist applications;
- Artifact/Result records for generated designs, firmware, simulations and diagnostics.

Exit condition: OSCAR can onboard, discover, control, observe and verify representative physical devices through native capability contracts, while engineering work is routed to the best available specialist tool rather than a mandatory product.

## Slice 16 — Self-maintenance, reliability, security + truthfulness pass ◻️

**Goal:** prove the system diagnoses itself and behaves correctly under failure, adversarial and verification-relevant conditions.

Deliverables:

- self-health model for auth, transport adapters, model providers, device capabilities, storage and latency;
- stale/broken capability detection;
- safe automatic repair/rollback;
- credential rotation/revocation;
- replay/idempotency checks;
- Action Ledger integrity + undo tests;
- evidence/verification-state integrity tests;
- tests preventing `reported success` → `verified` without evidence;
- partial/unknown/blocked reporting tests;
- audit trail;
- provider/node outage tests;
- durable-task reclaim/restart/zombie tests;
- Worker retry/reroute/escalation tests;
- Personal Policy regressions;
- Voice Match spoof-resistance evaluation;
- Voice Map false-positive/unknown-speaker evaluation;
- OSCAR self-voice suppression/echo tests;
- local hardware-safety tests;
- rate limiting/privacy/retention controls;
- learned automation promotion/rollback tests.

Exit condition: OSCAR can detect degraded state, repair safe failures when possible, ask for minimum intervention otherwise and never claim success beyond what it can verify.

## Slice 17 — Unified alpha ◻️

**Goal:** demonstrate the complete product loop across software, cloud, voice, phone and physical embodiments.

Reference scenario:

```text
Perception/Sentry/communication/device event occurs
→ local audio/sensor perception may update Voice Map / World Model
→ OSCAR/Jev evaluates current truth + memory
→ Personal Policy + permissions applied
→ Executive Planner prioritizes objective/resources
→ Durable Execution Runtime persists task/checkpoint state
→ Capability Catalog finds the best available specialist/tool/channel
→ native OSCAR Model Router selects a model only when needed
→ native OSCAR Transport carries work to the chosen node/surface
→ Worker/specialist executes
→ Channel Gateway handles communication when relevant
→ Action Ledger records consequential changes
→ Artifact/Result Model records durable outputs
→ verification checks objective completion
→ World Model / memory update from evidence
→ OSCAR replies through its stable Voice Identity or text
→ report only what the evidence supports
```

Exit condition: Core Loop + Jev + native transport + native model routing + machine Worker + memory/policy + Edge + Voice Identity/Voice Match/Voice Map + Sunday/communication + desktop Interaction Runtime + World Model + Perception Fabric + Sentry + Executive Planner + Durable Runtime + Capability Catalog + Channel Gateway + Action Ledger + Artifact Model + Workers + learning + physical/device expansion operate as one coherent evidence-backed OSCAR system.

**Manual milestone:** complete **Gate E — Unified Alpha** after Slices 15–17.

## Post-alpha horizon — P2 domains

These are intentionally deferred until the unified alpha is coherent:

- health/wearable context with strict permission/privacy boundaries;
- broader smart-home capability contracts;
- robotics/camera/room-infrastructure contracts;
- future vehicle/drone integration where safe and legally appropriate;
- optional cloud Worker node as an advertised capability rather than a foundational dependency.

## Slice definition of done

Every slice must include:

- implementation complete for the scoped deliverable;
- design no more complex than the current requirement justifies;
- clear responsibilities/boundaries and authoritative state ownership;
- tests for important behavior and meaningful failure modes;
- timeout/retry/reconnect/cancellation/idempotency behavior where relevant;
- explicit limitations/follow-ups;
- explicit verification state and evidence for completion claims;
- security/safety/privacy review where relevant;
- critical-path performance measured/budgeted where relevant;
- README status update;
- affected docs updated;
- next slice clearly identified.

A slice is not `Complete` because an agent/tool said so. Its exit condition must be verified against repository/runtime/device evidence where verification is possible.
