# Roadmap

This roadmap is slice-based. Each slice should leave OSCAR in a coherent, testable state and update the README plus affected docs in the same change.

## Status legend

- ✅ Complete
- 🚧 In progress
- ⏭️ Next
- ◻️ Planned

## Slice 00 — Repository foundation ✅

**Goal:** establish the product definition before implementation.

Deliverables:

- canonical OSCAR product definition
- architecture plan
- comprehensive feature inventory
- voice/Sentry design
- onboarding/Voice Match plan
- avatar interaction language
- security model
- brand assets organized under `assets/brand/`
- README status table and documentation links

Exit condition: repository clearly defines what OSCAR is, what it is not, and the planned implementation order.

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

## Slice 05 — OSCAR core router ◻️

**Goal:** create the decision layer that chooses the right execution path.

Deliverables:

- typed intent model
- task/context state
- policy hooks
- capability selection
- deterministic vs tool vs model routing
- Jev integration for intent/epistemic decisions
- explicit “need context / inspect source / ask user” states

Exit condition: representative requests route correctly without unnecessarily invoking heavy models.

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

## Slice 07 — Sunday ◻️

**Goal:** ship OSCAR's mobile embodiment.

Deliverables:

- Android app shell
- OSCAR identity/avatar
- voice + text session
- notifications
- Latch connection
- task continuity
- phone capability advertisement
- initial safe phone actions
- biometric confirmation surface

Exit condition: a task can move between Sunday and another OSCAR surface without becoming a separate assistant/session silo.

## Slice 08 — PC Worker ◻️

**Goal:** turn an online computer into an optional specialist execution node.

Deliverables:

- worker pairing
- dynamic capability discovery
- filesystem/terminal primitives
- Codex integration
- computer-use integration
- browser/IDE/app launching
- Antigravity/specialist software adapters where feasible
- progress/result callbacks
- cancellation and disconnect recovery

Exit condition: OSCAR can delegate a specialized software task, observe it, verify the result and survive the worker disappearing.

## Slice 09 — Memory and context ◻️

**Goal:** provide durable cross-device continuity without indiscriminate context stuffing.

Deliverables:

- LRA integration boundary
- Supermemory backend
- retrieval policy
- task/project/device memory types
- provenance/confidence metadata
- remember/forget/update flows
- context handoff between Sunday, desk, ChatGPT and PC

Exit condition: OSCAR can retrieve relevant prior context when needed and avoid retrieval when it already knows enough.

## Slice 10 — Sentry Mode ◻️

**Goal:** make OSCAR continuously present without continuous cloud surveillance.

Deliverables:

- Passive/Aware/Guard/Away/Sleep modes
- sensor/device event ingestion
- local rules/baselines
- event fusion
- importance/urgency/confidence/interruptibility scoring
- notification/speech escalation policy
- Sunday alerts
- example workbench/presence anomaly flows

Exit condition: OSCAR can remain quietly aware for extended periods and surface only configured meaningful events.

## Slice 11 — First-run commissioning + Voice Match ◻️

**Goal:** make setup comprehensive enough for safe personalized autonomy.

Deliverables:

- identity/preferences flow
- multi-condition voice enrollment
- speaker verification profile
- authorization classes
- device/environment discovery
- service connections
- Sentry configuration
- Sunday/PC pairing
- permission matrix
- end-to-end calibration

Exit condition: a new installation ends with verified health/permission/voice status rather than untested configuration.

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

Exit condition: avatar motion always maps to actual OSCAR state and works across phone and suitable desk displays.

## Slice 13 — Protocols, routines, skills and plugins ◻️

**Goal:** make OSCAR extensible and able to reuse learned workflows safely.

Deliverables:

- protocol schema
- routine/event triggers
- pause/resume/cancel
- `SKILL.md`-style skill contract
- plugin/tool discovery
- skill/protocol proposal/generation flow
- permission review for generated automation
- versioning and rollback

Exit condition: OSCAR can safely create/use a reusable workflow without self-granting authority.

## Slice 14 — Environment / workbench integration ◻️

**Goal:** connect richer physical and visual context.

Deliverables:

- camera-capable node path
- component/workbench telemetry
- device state correlation
- physical protocol execution
- environment/device inventory
- specialist visual/engineering tool hooks

Exit condition: OSCAR can reason from actual workbench/environment data and execute safe approved actions.

## Slice 15 — Reliability and security pass ◻️

**Goal:** prove the system behaves correctly under failure and attack-relevant conditions.

Deliverables:

- credential rotation/revocation
- replay/idempotency checks
- audit trail
- provider/node outage tests
- partial-task recovery
- Voice Match spoof-resistance evaluation
- local safety tests
- rate limiting
- permission regression tests
- privacy/retention controls

Exit condition: major failure modes are tested and documented, not merely assumed.

## Slice 16 — Unified alpha ◻️

**Goal:** demonstrate the complete product loop.

Reference scenario:

```text
Sentry detects meaningful event
→ OSCAR evaluates locally
→ invokes cloud intelligence if needed
→ uses Sunday/ChatGPT to involve user if required
→ delegates specialist work to PC if available
→ controls safe edge action
→ verifies outcome
→ stores important result in memory
→ reports succinctly
```

Exit condition: edge + voice + ChatGPT + SwitchRoute + Sunday + PC worker + memory + Sentry operate as one coherent OSCAR system.

## Slice definition of done

Every slice must include:

- implementation complete for the scoped deliverable
- tests for important behavior
- explicit limitations/follow-ups
- security/safety review where relevant
- README status update
- affected docs updated
- next slice clearly identified
