# OSCAR Surfaces and Embodiments

OSCAR is one intelligence expressed through multiple devices. Surfaces share identity, tasks, permissions, Personal Policy, Persona, memory, Voice Identity and capability contracts rather than becoming separate assistants.

Cross-device coordination uses OSCAR-owned transport/capability contracts and the Connection Grid.

## Shared surface principles

Across Sunday, desktop and physical surfaces:

- OSCAR should feel **present**, not repeatedly launched;
- voice and text are peers in one continuous context;
- Sentry awareness is distinct from active Listening and from recording/capture;
- UI state reflects real runtime/verification state;
- complexity is progressively disclosed;
- fluid motion preserves continuity where practical;
- each platform gets a native composition rather than the same layout at different widths;
- Persona affects tone/expression but not truth, permissions or safety.

The visual/interaction direction is defined by `DESIGN.md` and `TASTE.md`.

## Connection Grid

The Grid is the product-visible relationship between:

- **Sunday** — owner control/approval/notifications;
- **Cloud coordinator** — rendezvous and durable coordination;
- **Desktop nodes** — high-capability execution;
- **OSCAR Edge** — persistent local perception/reflex/safety.

Normal UI stays compact:

```text
Sunday        Here
Cloud         Healthy
Desktop       Working · 1 task
Desk Edge     Aware
```

Expand only when the user needs capabilities, active task ownership, health, permissions or remote controls.

See `CONNECTION-GRID.md`.

## Sunday — mobile

Sunday is OSCAR on the phone and the preferred everyday owner-control surface.

Primary goals:

- voice/text access to the same OSCAR relationship;
- persistent presence rather than `launch assistant` behavior;
- clear Sentry Aware / Listening / Muted / Awareness Off states;
- notifications/proactive alerts;
- task/Worker supervision;
- Connection Grid controls;
- calls/messages/email/meeting capability where platform support permits;
- optional Context Capture/Daily Journal controls;
- camera/location/sensors where authorized;
- biometric/PIN approval for sensitive actions;
- Persona configuration/preview;
- seamless continuity when leaving the desk.

Sunday must not frame normal use as `Talk to OSCAR` versus `Type instead`.

Example:

```text
start task on Desktop
→ leave home
→ Sunday retains task visibility/control
→ OSCAR notifies when blocked or verified complete
→ approve/cancel/redirect remotely
```

See `SUNDAY-DESIGN.md`.

## OSCAR Desktop — Windows/macOS

The desktop app is OSCAR's native presence on a computer, not OSCAR's host.

Planned capabilities:

- compact ambient presence/overlay;
- voice/text with shared Voice Identity/Persona;
- push/hold-to-talk and Sentry participation;
- Dictate / Edit / Ask / Act;
- screen/cursor/selection/app context;
- meeting/dictation support;
- approvals/task progress;
- fluid compact→expanded transitions;
- Connection Grid state/control;
- machine-worker health/capabilities;
- remote continuation when the user leaves;
- deeper task/history/artifact/settings workspace only when needed.

Do not turn desktop into a giant chat sidebar or dashboard.

## Machine Worker node

The visible desktop app and machine execution node are related but conceptually separate.

A machine may advertise:

```text
codex
claude-code / opencode / other coding agents
computer-use
terminal / powershell
browser
filesystem
IDE / Git
Python / FFmpeg / Blender
GPU / local-model support
installed specialist apps
```

When the computer disappears, those capabilities disappear but durable task state remains and OSCAR continues elsewhere.

## Remote continuation

A machine task may continue without the user being physically present.

Sunday can inspect/pause/cancel/approve. After verified completion, OSCAR may sleep/shut down the PC when a real capability and policy permit.

Remote power-on is only presented if Wake-on-LAN/remote-management/approved power capability is available.

## Delegated Worker surface

Workers remain underneath OSCAR. The user should see responsibility, current meaningful action, state, blocker/approval and result — not an agent-operations dashboard.

## OSCAR Edge

### ESP32 gateway

- Wi-Fi/network;
- native Edge transport;
- wake/VAD/audio front end where practical;
- local Sentry events;
- display/status coordination;
- short-lived state;
- OTA/configuration;
- communication with Pico;
- optional LAN helper capabilities such as Wake-on-LAN where supported.

### RP2040/Pico controller

- GPIO/sensors/buttons;
- relays/motors/actuators;
- deterministic timing;
- interlocks/emergency safety.

Cloud intelligence is never required for local physical safety.

## Desk / physical OSCAR

Physical embodiment can combine microphone/speaker, avatar/status display, mute/stop/PTT controls, Sentry acoustic front end, Voice Map events, presence sensors, cameras through suitable nodes and expressive but purposeful movement.

## Voice continuity

```text
OSCAR Voice Identity
        + Persona context
        ↓
Sunday / Desktop / Desk speaker
```

Underlying TTS can differ while intended identity remains recognizable.

Voice Match/Voice Map share semantics while preserving source/confidence metadata. OSCAR's own TTS is excluded from speaker learning and wake loops.

## Sentry surface participation

Sentry is distributed and persistent when enabled.

A surface can contribute:

- wake/VAD/hot commands;
- Voice Map speaker events;
- sound events;
- motion/presence;
- device health;
- camera/sensor observations;
- current app/device context;
- communication events.

Persistent awareness is different from active Listening and different from durable recording.

### Optional Context Capture / Daily Journal

Sunday/desktop/authorized microphones and channel adapters can contribute selected calls/messages/mail/meetings/in-person conversations to continuity capture where technically and legally permitted.

The UI must expose capture state, source, retention and pause/delete controls clearly.

See `VOICE-SENTRY.md` and `COMMUNICATION.md`.

## Persona surfaces

Persona should be editable conversationally and manually.

Surface requirements:

- starting profiles/custom description;
- compact core trait controls;
- context trigger rules;
- preview of text/voice/motion behavior;
- truthfulness/safety visibly non-configurable.

See `PERSONA.md`.

## Physical/device and engineering expansion

Physical systems join OSCAR through native capability contracts. CAD, circuit design/simulation, firmware, diagnostics and other engineering work routes to whichever installed/connected specialist tools are available.

## ChatGPT / model-provider surface

ChatGPT and other providers are intelligence capabilities reached through native OSCAR routing. ChatGPT-to-OSCAR interaction uses an OSCAR-owned connector/path, not a required Latch service.

## Communication surfaces

Calls, messaging, email, meetings, dictation and continuity capture may execute through different devices/apps while remaining one logical communication subsystem.

Integration priority:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation
→ computer-use/accessibility fallback
→ unsupported / ask
```

## Cross-surface continuity

The same task/context survives surface changes.

```text
Desktop task running
→ Sunday shows state/control
→ user returns to desk
→ Desktop expands the same objective/result
```

No manual chat transfer.

## Capability presence

Every node joins/leaves dynamically.

```text
Sunday online      → mobile/owner controls
Cloud online       → rendezvous/durable coordination
PC online          → machine capabilities
Edge online        → physical/local capabilities
adapter online     → app/channel capability
```

OSCAR plans against what exists now.

## Avatar / motion continuity

The same blue-shell/yellow-puck interaction language appears where useful.

Motion should express real state with shared geometry and continuity: compact presence can expand into Listening/task/detail rather than teleporting between unrelated screens.

States include Idle, Sentry Aware, Listening, Speaking, Working, Verifying, Waiting, Blocked, Done, Muted, Awareness Off and Offline/Degraded.

Identity is shared; composition remains platform-native.
