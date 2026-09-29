# Roadmap

This roadmap is slice-based. Each slice should leave OSCAR in a coherent, testable state and update the README plus affected docs in the same change.

All implementation slices are also governed by `ENGINEERING.md`: keep scope coherent, boundaries explicit, failure behavior intentional and code simple enough to evolve safely.

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
- orchestration/learning/skills/protocol plan
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

Exit condition: repository clearly defines what OSCAR is, what it is not, how it should look/feel, how it should be engineered, how coding agents should work in it, and the planned implementation order.

## Slice 01 — Edge runtime skeleton ⏭️

**Goal:** create the always-on local runtime boundary.

Deliverables:

- ESP32 gateway project structure
- Pico/RP2040 controller project structure
- explicit event/message schema between them
- device identity and version reporting
- health/status heartbeat
- basic command/response path
- local watchdog and safe-default behavior
- host-side simulator/tests where practical

Exit condition: ESP32 and Pico can boot, identify themselves, exchange typed events/commands and report health without cloud intelligence.

## Slice 02 — Reflex engine ◻️

**Goal:** make immediate deterministic behavior real.

Deliverables:

- local intent/reflex state machine
- mute/stop/cancel primitives
- simple local device commands
- active-task cancellation IDs
- emergency-stop path
- latency instrumentation
- safety validation on Pico

Exit condition: reflex actions work without Internet/model calls and meet latency targets.

## Slice 03 — Latch Edge + capability registry ◻️

**Goal:** securely connect OSCAR Edge to Latch without exposing the local network.

Deliverables:

- persistent outbound secure session
- device pairing/identity
- scoped credentials
- capability advertisement
- event correlation IDs
- reconnect/backoff
- remote command/result transport
- audit metadata

Exit condition: Latch can discover the edge node's capabilities and call safe test tools end to end.

## Slice 04 — Voice core ◻️

**Goal:** establish low-latency natural voice interaction.

Deliverables:

- microphone/audio pipeline
- local wake word + VAD
- streaming STT abstraction
- TTS abstraction
- streaming/chunked playback
- barge-in
- echo cancellation strategy
- first-audio/command latency metrics

Exit condition: user can wake OSCAR, speak a request, receive a spoken reply and interrupt it naturally.

## Slice 05 — OSCAR core router / Jev + policy hooks ◻️

**Goal:** create the decision layer that chooses the right execution, knowledge and policy path.

Deliverables:

- typed intent model
- task/context state
- Personal Policy evaluation hook
- permission/policy hooks
- capability selection
- deterministic vs tool vs model vs Worker routing
- Jev integration for intent + epistemic decisions
- explicit `known / recall / verify / reason / delegate / ask` states
- safe worker-repair/reroute decision path
- latency instrumentation for routing

Exit condition: representative requests route correctly without unnecessarily invoking heavy models, guessing missing context or bypassing explicit user policy.

## Slice 06 — Cloud brains ◻️

**Goal:** give OSCAR autonomous reasoning without depending on the laptop.

Deliverables:

- SwitchRoute integration
- route/fallback policy
- ChatGPT through Latch
- OSCAR → ChatGPT wake abstraction
- ChatGPT → OSCAR tool path
- async task callbacks
- graceful provider failure

Exit condition: OSCAR can choose ChatGPT or SwitchRoute, receive results and continue a task with the PC off.

## Slice 07 — Sunday + communication runtime ◻️

**Goal:** ship OSCAR's mobile embodiment and the first real communication surface.

Deliverables:

- Android app shell
- OSCAR identity/avatar
- voice + text session
- notifications
- Latch connection
- task continuity
- phone capability advertisement
- initial safe phone/app actions
- call/message integration boundary using native/official paths first
- AI call-handling policy hooks where the platform permits
- mobile meeting transcription/notes boundary
- system-wide dictation/input path where practical
- biometric confirmation surface

Exit condition: a task can move between Sunday and another OSCAR surface without becoming a separate assistant/session silo, and Sunday can expose real phone/communication capabilities without fabricating unsupported app control.

## Slice 08 — Desktop + machine worker nodes ◻️

**Goal:** create native desktop presence and turn online computers into specialist execution nodes.

Deliverables:

- Windows native/lightweight app shell
- macOS-compatible surface plan and adapter boundary
- voice/text interaction + OSCAR presence UI
- system-wide dictation path
- desktop meeting transcription/notes boundary
- screen/cursor/selection/active-window context
- machine-worker pairing and dynamic capability discovery
- filesystem/terminal primitives
- Codex integration
- computer-use integration
- browser/IDE/app launching
- Antigravity/specialist adapters where feasible
- progress/result callbacks
- cancellation and disconnect recovery

Exit condition: OSCAR can interact naturally on desktop, delegate a specialist software task, observe it, verify the result and survive the machine worker disappearing.

## Slice 09 — Memory, context + Personal Policy ◻️

**Goal:** provide durable cross-device continuity and authoritative user preferences without a conventional chat-sidebar dependency.

Deliverables:

- LRA integration boundary
- active-context + episodic-history model
- Supermemory backend
- Jev retrieval/verification decisions
- task/project/device/procedural memory types
- Personal Policy store distinct from inferred memory
- natural-language preference create/edit/remove flow
- policy scoping, precedence and conflict resolution
- provenance/confidence metadata
- remember/forget/update flows
- context handoff between Sunday, desktop, ChatGPT, edge and Workers
- searchable history/timeline surface
- inspectable Personal Policy surface

Exit condition: OSCAR can retrieve relevant prior context when needed, preserve continuous interaction across devices, apply explicit preferences reliably and avoid confusing inferred memory with authority.

## Slice 10 — Sentry Mode ◻️

**Goal:** make OSCAR continuously present without continuous cloud surveillance.

Deliverables:

- Passive/Aware/Guard/Away/Sleep modes
- sensor/device event ingestion
- local rules/baselines
- event fusion
- importance/urgency/confidence/interruptibility scoring
- Personal Policy-aware interruption decisions
- notification/speech escalation policy
- Sunday alerts
- example workbench/presence anomaly flows

Exit condition: OSCAR can remain quietly aware for extended periods and surface only configured meaningful events.

## Slice 11 — First-run commissioning + Voice Match ◻️

**Goal:** make setup comprehensive enough for safe personalized autonomy without forcing the user through endless settings.

Deliverables:

- identity/basic interaction preferences
- small high-value Personal Policy setup with open-ended later editing by voice/chat
- call/message autonomy defaults
- meeting transcription/retention defaults
- Worker autonomy defaults
- multi-condition voice enrollment
- speaker verification profile
- authorization classes
- device/environment discovery
- service connections
- Sentry configuration
- Sunday/desktop pairing
- permission matrix
- end-to-end calibration

Exit condition: a new installation ends with verified health/permission/voice status and understandable initial policy rather than untested configuration.

## Slice 12 — Avatar / presence UI ◻️

**Goal:** turn the OSCAR character into a coherent state-driven interface.

Deliverables:

- reusable avatar component
- joystick/puck motion physics
- expression/state system
- listening/thinking/speaking choreography
- serious/Sentry states
- reduced-motion accessibility
- compact/icon variants

Exit condition: avatar motion always maps to actual OSCAR state and works across Sunday, desktop and suitable desk displays.

## Slice 13 — Workers, learning, skills, routines, protocols and plugins ◻️

**Goal:** make OSCAR capable of creating/managing delegated teammates and learning reusable procedures so repeated work becomes faster and more autonomous.

Deliverables:

- delegated Worker schema/lifecycle/state
- voice/chat Worker creation/editing
- temporary, task and persistent Worker types
- Worker capability/permission/context envelope
- Worker collaboration/handoff/dependency model
- Jev self-repair/reroute/escalation loop
- simple Worker management UI
- social-media Worker reference implementation using scoped connectors/device capabilities
- procedural memory capture from successful executions
- route/tool outcome history
- reusable procedure distillation
- `SKILL.md`-style portable skill contract
- plugin/tool discovery
- protocol schema + durable state
- routine/time/event triggers
- protocol-driven Worker creation/termination
- pause/resume/cancel
- self-created skill/routine/protocol candidate flow
- permission review for generated automation
- verification requirements
- versioning and rollback
- measurable repeated-task latency/cost improvement

Exit condition: OSCAR can create a Worker from natural language, let it use the best available device/service capabilities, recover from routine problems without unnecessary escalation, learn a successful workflow and reuse it later without self-granting authority.

## Slice 14 — Kinetable + environment/workbench ◻️

**Goal:** connect hardware engineering, richer physical context and provisioned OSCAR devices.

Deliverables:

- Kinetable integration contract
- hardware project/inventory handoff
- firmware/provisioning path into OSCAR/Latch Edge
- camera-capable node path
- component/workbench telemetry
- device state correlation
- physical protocol execution
- environment/device inventory
- specialist visual/engineering tool hooks

Exit condition: OSCAR can route hardware work to Kinetable, reason from actual workbench/environment data, and onboard an approved device as a capability-bearing OSCAR node.

## Slice 15 — Reliability and security pass ◻️

**Goal:** prove the system behaves correctly under failure and attack-relevant conditions.

Deliverables:

- credential rotation/revocation
- replay/idempotency checks
- audit trail
- provider/node outage tests
- partial-task recovery
- Worker retry/reroute/escalation tests
- communication-action attribution tests
- Personal Policy conflict/permission regression tests
- Voice Match spoof-resistance evaluation
- local safety tests
- rate limiting
- privacy/retention controls
- generated-skill/protocol/Worker safety tests

Exit condition: major failure modes are tested and documented, not merely assumed.

## Slice 16 — Unified alpha ◻️

**Goal:** demonstrate the complete product loop.

Reference scenario:

```text
Sentry/communication/device event occurs
→ OSCAR/Jev evaluates locally
→ Personal Policy + permissions applied
→ retrieves context if needed
→ invokes ChatGPT/SwitchRoute if reasoning is needed
→ creates/delegates Worker when the objective warrants it
→ involves user through Sunday/desktop only when required
→ delegates specialist work to the best tool/device
→ controls safe edge action if relevant
→ verifies outcome
→ stores important + procedural memory
→ improves reusable skill/protocol if appropriate
→ reports succinctly
```

Exit condition: edge + voice + communication + ChatGPT + SwitchRoute + Sunday + desktop machine nodes + delegated Workers + LRA/Supermemory + Personal Policy + learning + Sentry + Kinetable integration operate as one coherent OSCAR system.

## Slice definition of done

Every slice must include:

- implementation complete for the scoped deliverable
- design remains no more complex than the current requirement justifies
- responsibilities/boundaries and authoritative state ownership are clear
- tests for important behavior and meaningful failure modes
- timeout/retry/reconnect/cancellation/idempotency behavior addressed where relevant
- explicit limitations/follow-ups
- security/safety review where relevant
- critical-path performance measured/budgeted where relevant
- README status update
- affected docs updated
- next slice clearly identified
