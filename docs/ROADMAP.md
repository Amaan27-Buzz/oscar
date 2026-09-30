# Roadmap

This roadmap is slice-based. Each slice should leave OSCAR in a coherent, testable state and update the README plus affected docs in the same change.

All implementation slices are governed by `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`: keep scope coherent, boundaries explicit, failure behavior intentional, code simple enough to evolve safely, and completion claims no stronger than the available evidence.

The benchmark documents are part of roadmap planning:

- `docs/JARVIS-GAP-REVIEW.md`
- `docs/COMPETITIVE-BENCHMARK.md`
- `docs/RUNTIME-FOUNDATIONS.md`

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

During early development this loop may run on a development computer for convenience. That does **not** make the computer OSCAR's permanent host; the contracts must remain portable so desktop, Sunday, Edge and cloud execution surfaces can attach later without changing OSCAR's identity or core semantics.

## Status legend

- ✅ Complete
- 🚧 In progress
- ⏭️ Next
- ◻️ Planned

## Slice 00 — Repository foundation ✅

**Goal:** establish the product, design, engineering and agent-development contract before implementation.

Deliverables:

- canonical OSCAR product definition
- architecture plan
- comprehensive feature inventory
- LRA/Supermemory/Jev memory plan
- Personal Policy/preference model
- communication layer plan for calls, meetings, messaging and dictation
- delegated Worker/sub-agent model
- orchestration/learning/Skills/Protocols plan
- JARVIS/VoiceOS gap benchmark covering World Model, Perception Fabric, Executive Planner, Action Ledger/Undo and Interaction Runtime
- final competitor benchmark against VoiceOS, MCU JARVIS, ChatGPT, Claude, Gemini, Grok Bot, OpenClaw, Hermes and Pi
- Universal Channel Gateway design
- Durable Execution Runtime design
- Capability Catalog + Dynamic Tool Search design
- Learned Automation Evaluation Pipeline design
- Artifact / Result Model design
- Epistemic Integrity contract: reported vs observed vs verified outcomes, explicit uncertainty and evidence-backed completion claims
- Sunday/desktop/edge surface plan
- voice/Sentry design
- onboarding/Voice Match plan
- avatar interaction language
- **Quietly Alive** design system in `DESIGN.md`
- qualitative design/taste rules in `TASTE.md`
- canonical engineering/system-design quality bar in `ENGINEERING.md`
- Sunday mobile visual direction
- canonical `AGENTS.md` plus Claude, Gemini, Copilot and Cursor adapters
- portable `SKILL.md` workflows for OSCAR UI and slice delivery
- coding-agent context documentation
- security model
- brand assets under `assets/brand/`
- repository support files and GitHub templates/checks
- README status table and documentation links

Exit condition: repository clearly defines what OSCAR is, what it is not, how it should look/feel, how it should be engineered, how it should reason about truth/verification, how agents should work in it, and the planned implementation order.

## Slice 01 — OSCAR Core Loop ⏭️

**Goal:** prove the smallest end-to-end OSCAR execution loop before building embodiments or hardware.

Deliverables:

- minimal core package/service boundary with no desktop-host assumption
- typed `Objective`, `Task`, `Capability`, `Action`, `Result`, `Evidence` and `ArtifactRef` contracts
- explicit task states such as `planned`, `executing`, `result_received`, `verifying`, `verified`, `partially_verified`, `failed`, `blocked`, `cancelled` and `unknown`
- explicit completion-condition and verification-strategy contracts
- minimal local capability registry
- minimal Durable Execution Runtime foundation with persisted task state, cancellation and retry budget
- Action Ledger foundation for consequential actions
- Artifact / Result Model foundation
- simple CLI/test harness rather than product UI
- one deliberately small reference capability, such as scoped test-workspace file write/read
- independent verifier that checks resulting state instead of trusting the executor result
- evidence-backed final reporting
- tests proving `reported success` cannot become `verified` without evidence

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

Exit condition: a representative objective can travel through `objective → capability → action → result → evidence → verification → ledger/artifact → truthful report`, and a deliberately false executor-success report cannot produce a verified completion state.

## Slice 02 — TypeSafe Jev ◻️

**Goal:** add the fast intent + epistemic decision layer on top of the proven Core Loop.

Deliverables:

- typed intent model
- typed epistemic routes: `known / world / recall / verify / reason / reported / specialist / worker / unknown`
- deterministic routing where sufficient
- capability-selection hook into the Core Loop
- explicit current-evidence vs recall vs inference distinctions
- ask-user path only when retrieval/verification cannot safely resolve ambiguity
- repair/reroute decision contract for recoverable failures
- Personal Policy and permission evaluation hooks, even before full policy storage exists
- latency instrumentation for routing
- tests for incorrect certainty, unsupported capability and unknown-state handling

Exit condition: representative requests route through deterministic execution, verification or ask-user paths without unnecessary heavy-model calls, guessed personal context or false certainty.

## Slice 03 — Latch + Capability Catalog ◻️

**Goal:** connect OSCAR to external execution surfaces through stable capability contracts without making any one computer the host.

Deliverables:

- Latch transport boundary for OSCAR task/action/result events
- node/session identity
- scoped credentials
- capability advertisement
- lightweight capability manifest schema
- Capability Catalog
- Dynamic Tool Search / progressive contract loading
- searchable metadata: suitability, permissions, risk, availability, surface, latency/cost hints, reliability and undo metadata
- event/task correlation IDs
- reconnect/backoff
- bounded remote command/result transport
- audit/provenance metadata
- simulated/local reference node proving the protocol before Edge hardware exists

Exit condition: OSCAR can discover a capability on another execution node, load only its relevant contract, invoke it through Latch, receive a structured result and independently verify the objective without assuming that node permanently hosts OSCAR.

## Slice 04 — Cloud intelligence: ChatGPT + SwitchRoute ◻️

**Goal:** add cloud reasoning as a selectable capability, not as the definition of OSCAR.

Deliverables:

- SwitchRoute integration
- model/provider route and fallback policy
- ChatGPT through Latch
- OSCAR → ChatGPT wake/trigger abstraction
- ChatGPT → OSCAR tool path
- async callbacks into Durable Execution Runtime
- structured model/agent outputs recorded as `reported`/`inferred`, never automatically `verified`
- graceful provider failure/degradation
- Jev decisions for when a model is unnecessary vs useful

Exit condition: OSCAR can choose deterministic execution, ChatGPT or SwitchRoute appropriately and preserve evidence boundaries between model claims and verified state.

## Slice 05 — First real machine Worker ◻️

**Goal:** make OSCAR genuinely useful through an optional computer node while preserving laptop independence as an architectural invariant.

Deliverables:

- lightweight Windows machine-node runtime
- pairing through Latch
- dynamic capability advertisement
- scoped filesystem and terminal primitives
- Git/repository capability
- Codex integration
- browser/computer-use integration where practical
- task progress/result callbacks
- cancellation and disconnect handling
- restart/reconnect recovery for an active task
- independent test/state verification after specialist completion
- first meaningful Worker/objective flow

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

Exit condition: OSCAR can delegate a useful software objective to a real machine/Codex capability, survive ordinary executor failure/disconnect, and verify completion independently where practical.

## Slice 06 — LRA + Personal Policy + live context ◻️

**Goal:** add persistent continuity and authoritative user preferences after the execution loop already works.

Deliverables:

- LRA integration boundary
- active-context + episodic-history model
- Supermemory backend
- task/project/device/procedural memory types
- Jev recall vs live-verification decisions
- Personal Policy store distinct from inferred memory
- natural-language preference create/edit/remove flow
- policy scoping, precedence and conflict resolution
- provenance/confidence metadata
- remember/forget/update flows
- universal live context/search abstraction over connected authoritative sources
- source-authority and staleness rules
- initial canonical entity/relationship graph for people, accounts, devices and projects
- explicit `recalled / inferred / reported / verified` distinctions

Exit condition: OSCAR can recover relevant historical context, query current authoritative context when needed, and apply explicit user preferences without confusing memory or inference with current verified truth.

## Slice 07 — OSCAR Edge + reflexes ◻️

**Goal:** attach the persistent physical embodiment after the core contracts are already proven in software.

Deliverables:

- ESP32 gateway project structure
- Pico/RP2040 deterministic controller project structure
- Latch Edge client/protocol using the existing capability contracts
- explicit typed event/message schema between ESP32 and Pico
- device identity/version reporting
- health heartbeat
- capability advertisement into the existing catalog
- GPIO/sensor/display test capabilities
- local watchdog and safe-default behavior
- deterministic reflex state machine
- emergency-stop path
- simple local device commands
- hardware latency instrumentation
- reconnect/offline behavior
- host simulator/tests plus real-device verification
- explicit simulator-vs-hardware evidence reporting

Exit condition: ESP32 and Pico join OSCAR as capability-bearing nodes, preserve deterministic safety without cloud intelligence, and work through the same task/result/evidence contracts already proven by software nodes.

## Slice 08 — Voice core + multi-device arbitration ◻️

**Goal:** make the proven OSCAR loop naturally accessible by voice without changing its task semantics.

Deliverables:

- microphone/audio pipeline
- local wake word + VAD
- streaming STT abstraction
- TTS abstraction
- streaming/chunked playback
- barge-in
- echo-cancellation strategy
- first-audio/command latency metrics
- voice/text task continuity
- wake/listen identity across devices
- multi-device arbitration using confidence, proximity, active-device context and explicit priority
- one-owner-per-turn rule with handoff/failover

Exit condition: the user can wake OSCAR, invoke the same Core Loop by voice, receive a spoken response, interrupt it naturally and avoid several listening surfaces answering the same utterance.

## Slice 09 — Sunday + communication + Universal Channel Gateway ◻️

**Goal:** ship OSCAR's phone embodiment and prove communication as a first-class capability family.

Deliverables:

- Android app shell
- OSCAR identity/avatar surface
- voice + text session
- notifications
- Latch connection
- task/context continuity
- phone capability advertisement
- initial safe phone/app actions
- Universal Channel Gateway event/action envelope
- first adapters using native/official paths first
- canonical participant/entity IDs across supported channels
- explicit per-channel capability limits
- Android cellular-call capability study and implementation where legitimate
- WhatsApp/Telegram-style app action/call capability study
- audio access/loopback and VoIP gateway fallback study
- AI call-handling policy hooks where supported
- mobile meeting transcription/notes boundary
- mobile dictation/input path where practical
- biometric confirmation surface

Exit condition: a task can move between Sunday and another OSCAR surface without becoming a separate assistant/session, and communication adapters expose only capabilities actually supported by the device/platform.

## Slice 10 — Desktop Interaction Runtime ◻️

**Goal:** turn the already-capable machine node into a polished native desktop embodiment and match the practical VoiceOS interaction baseline.

Deliverables:

- native/lightweight Windows app shell
- macOS adapter boundary/plan
- OSCAR presence UI
- first-class `Dictate / Edit / Ask / Act` runtime
- focused app/window/text-field context
- selected-text operations
- cursor target + accessibility-tree context
- screenshot/visual context
- point-and-talk flows such as “what is this?”, “reply to him” and “fix this button”
- text insertion/rewrite with accessibility/clipboard fallbacks
- system-wide dictation
- user-visible undo when the Action Ledger exposes real compensation
- desktop meeting transcription/notes boundary
- task/progress/approval surfaces
- verification state exposed separately from executor completion

Exit condition: OSCAR can understand and act on the current desktop target with low-friction VoiceOS-grade interaction while preserving the same evidence, permission and task semantics as the headless machine Worker.

## Slice 11 — World Model + Perception Fabric + Sentry ◻️

**Goal:** give OSCAR one coherent live representation of what is happening across the user's digital and physical environment.

Deliverables:

- World Model graph for people, places, devices, apps, projects, objects, tasks and relationships
- separation of current evidence vs historical memory
- Perception Fabric ingesting screen/accessibility state, app/device events, sensors, location, audio events and authorized camera observations
- state freshness/confidence/provenance
- fusion of Sunday, desktop, Edge, calendar, communication and Worker state
- entity resolution expansion across communication/context sources
- Passive/Aware/Guard/Away/Sleep Sentry modes
- local rules/baselines
- importance/urgency/confidence/interruptibility scoring
- Personal Policy-aware interruption decisions
- predictive signals for obvious schedule/task/device risk where confidence can be measured
- notification/speech escalation policy

Exit condition: OSCAR can answer “what is true now?” from a coherent live model, distinguish stale/unknown state and react to meaningful events without treating old memory as current truth.

## Slice 12 — First-run commissioning + Voice Match ◻️

**Goal:** make setup safe and useful without forcing the user through an exhaustive settings product.

Deliverables:

- identity/basic interaction preferences
- small high-value Personal Policy setup with open-ended later voice/chat editing
- call/message autonomy defaults
- meeting transcription/retention defaults
- Worker autonomy defaults
- multi-condition voice enrollment
- speaker verification profile
- authorization classes
- device/environment discovery
- service/channel connections
- Sentry configuration
- Sunday/desktop/Edge pairing
- permission matrix
- end-to-end calibration

Exit condition: a new installation ends with verified health/permission/voice status and understandable initial policy rather than untested configuration.

## Slice 13 — Avatar / presence UI ◻️

**Goal:** turn OSCAR's character into a coherent state-driven interface across suitable surfaces.

Deliverables:

- reusable avatar component
- joystick/puck motion physics
- expression/state system
- listening/thinking/speaking choreography
- explicit Working / Verifying / Waiting / Blocked / Done / Failed states
- serious/Sentry states
- reduced-motion accessibility
- compact/icon variants

Exit condition: avatar motion always maps to actual OSCAR state and never displays success/working/thinking when the runtime is failed, blocked or still unverified.

## Slice 14 — Executive Planner + durable Workers + learning ◻️

**Goal:** scale the proven single-objective loop into durable delegated teammates and concurrent objectives without turning OSCAR into a swarm the user must manage.

Deliverables:

- Executive Planner over tasks/Workers/Protocols
- priority/deadline/dependency/resource/risk/interruptibility model
- scheduling, parallelization, pause/pre-emption and rerouting
- delegated Worker schema/lifecycle/state
- voice/chat Worker creation/editing
- temporary, task and persistent Worker types
- Worker capability/permission/context envelope
- Worker collaboration/handoff/dependency model
- Durable Execution Runtime expansion: leases, heartbeats, checkpoints, reclaim, zombie/stuck detection and restart/resume
- Jev self-repair/reroute/escalation loop
- simple Worker management UI
- social-media Worker reference implementation using scoped channels/device capabilities
- procedural memory capture from successful executions
- route/tool outcome history
- reusable procedure distillation
- `SKILL.md`-style portable Skill contract
- teach-by-demonstration flow for supported desktop/phone workflows
- Capability Catalog / Dynamic Tool Search for Workers and Protocols
- Protocol schema + durable state
- routine/time/event triggers
- Protocol-driven Worker creation/termination
- pause/resume/cancel
- Learned Automation Evaluation Pipeline: candidate → replay/evaluate → compare → permission/safety review → promote/reject/rollback
- Artifact/Result handoff between Workers using typed references
- measurable repeated-task latency/cost/reliability improvement

Exit condition: OSCAR can coordinate multiple objectives as one executive system, create a Worker from natural language, survive executor loss, discover capabilities progressively, learn/be taught a workflow, evaluate it before promotion and reuse it without self-granting authority.

## Slice 15 — Kinetable + spatial/workbench + general engineering ◻️

**Goal:** connect specialist hardware engineering, richer physical perception and general engineering/simulation tools.

Deliverables:

- Kinetable integration contract
- hardware project/inventory handoff
- firmware/provisioning path into OSCAR/Latch Edge
- camera-capable node path
- component/workbench telemetry
- device-state correlation
- physical Protocol execution
- environment/device inventory
- spatial perception experiments combining camera + sensor + World Model state
- specialist visual/engineering tool hooks
- routing boundary for CAD, 3D, numerical simulation, diagnostics, reconstruction and optimization tools
- Artifact/Result records for generated designs, firmware, simulations and diagnostics

Exit condition: OSCAR can route engineering work to the appropriate specialist, reason from actual workbench/environment data and onboard an approved device as a capability-bearing OSCAR node.

## Slice 16 — Self-maintenance, reliability, security + truthfulness pass ◻️

**Goal:** prove the system can diagnose itself and behaves correctly under failure, adversarial and verification-relevant conditions.

Deliverables:

- self-health model for auth, connectors, providers, device capabilities, storage and latency
- stale/broken capability detection
- safe automatic repair/rollback where confidence and permission allow
- credential rotation/revocation
- replay/idempotency checks
- Action Ledger integrity + undo/compensation tests
- evidence/verification-state integrity tests
- tests ensuring `reported success` cannot become `verified` without evidence
- tests ensuring partial/unknown/blocked states are surfaced honestly
- audit trail
- provider/node outage tests
- durable-task reclaim/restart/zombie tests
- Worker retry/reroute/escalation tests
- communication-action attribution tests
- Personal Policy conflict/permission regression tests
- Voice Match spoof-resistance evaluation
- local hardware-safety tests
- rate limiting
- privacy/retention controls
- learned Skill/Protocol/Worker promotion/rollback tests

Exit condition: OSCAR can detect its own degraded state, repair safe failures when possible, ask for minimum intervention otherwise, and never claim success beyond what it can verify.

## Slice 17 — Unified alpha ◻️

**Goal:** demonstrate the complete product loop across software, cloud, phone and physical embodiments.

Reference scenario:

```text
Perception/Sentry/communication/device event occurs
→ Perception Fabric updates World Model
→ OSCAR/Jev evaluates current truth + memory
→ Personal Policy + permissions applied
→ Executive Planner prioritizes objective/resources
→ Durable Execution Runtime persists task/checkpoint state
→ Capability Catalog finds the best available specialist/tool/channel
→ retrieves live or historical context if needed
→ invokes ChatGPT/SwitchRoute if reasoning is needed
→ creates/delegates Worker when the objective warrants it
→ delegates specialist work to the best tool/device
→ Channel Gateway handles communication when relevant
→ Action Ledger records consequential changes
→ Artifact/Result Model records durable outputs
→ verification checks objective completion
→ undo is offered only when a real compensation exists
→ World Model / memory are updated from verified evidence
→ learned automation is evaluated before promotion
→ report only what the evidence supports
```

Exit condition: Core Loop + Jev + Latch + cloud intelligence + machine Worker + memory/policy + Edge + voice + Sunday/communication + desktop Interaction Runtime + World Model + Perception Fabric + Executive Planner + Durable Execution Runtime + Capability Catalog + Channel Gateway + Action Ledger + Artifact/Result Model + Workers + learning + Sentry + Kinetable integration operate as one coherent OSCAR system with evidence-backed reporting.

## Post-alpha horizon — P2 domains

These are intentionally deferred until the unified alpha is coherent:

- health/wearable context with strict permission/privacy boundaries
- smart-home capability contracts
- robotics/camera/room-infrastructure contracts
- future vehicle/drone integration where safe and legally appropriate
- optional cloud Worker node as an advertised capability rather than a foundational dependency

These should plug into the same capability, World Model, policy, permission, Durable Runtime, Artifact and Action Ledger abstractions rather than creating parallel architectures.

## Slice definition of done

Every slice must include:

- implementation complete for the scoped deliverable
- design remains no more complex than the current requirement justifies
- responsibilities/boundaries and authoritative state ownership are clear
- tests for important behavior and meaningful failure modes
- timeout/retry/reconnect/cancellation/idempotency behavior addressed where relevant
- explicit limitations/follow-ups
- explicit verification state and supporting evidence for completion claims
- security/safety review where relevant
- critical-path performance measured/budgeted where relevant
- README status update
- affected docs updated
- next slice clearly identified

A slice is not `Complete` because an agent/tool said so. Its exit condition must be verified against repository/runtime/device evidence where verification is possible.