# OSCAR Surfaces and Embodiments

## Current Slice 10 Windows candidate

WPF compact/expanded presence, canonical Orb, tray/global invocation, shared Core tasks, signed contextual approvals and explicit context are implemented as a software/reference candidate. Reliable insertion uses registered UIA ValuePattern with expected-value fencing and independent readback. Mac/Linux, normal owner use and real voice/device acceptance are not claimed. See [Desktop foundation](DESKTOP-FOUNDATION.md).

OSCAR is one intelligence expressed through multiple devices. Surfaces share identity, tasks, permissions, Personal Policy, Persona, memory, Voice Identity and capability contracts rather than becoming separate assistants.

Cross-device coordination uses OSCAR-owned transport/capability contracts and the Connection Grid.

## Shared surface principles

Across OSCAR Mobile, desktop and physical surfaces:

- OSCAR should feel **present**, not repeatedly launched;
- voice and text are peers in one continuous context;
- Sentry awareness is distinct from active Listening and from recording/capture;
- UI state reflects real runtime/verification state;
- complexity is progressively disclosed;
- fluid motion preserves continuity where practical;
- each platform gets a native composition rather than the same layout at different widths;
- Persona affects tone/expression but not truth, permissions or safety;
- current context is freshness-qualified;
- perception, retention and action authority remain separate.

The visual/interaction direction is defined by `DESIGN.md` and `TASTE.md`.

## Connection Grid

The Grid is the product-visible relationship between:

- **OSCAR Mobile** — owner control/approval/notifications/Chief-of-Staff presence;
- **OSCAR Core on replaceable hosts** — identity/state/memory/task coordination;
- **Desktop nodes** — high-capability execution;
- **Home Node (future)** — owner's Galaxy Tab S6 Lite (2021), local Grid/bridge roles
  only after OSCAR is fully deployed and the main Core architecture is operational;
- **OSCAR Edge** — ESP32/Pico nerves/reflexes/sensors/actuators with deterministic safety.

Oracle is the preferred free-first persistent Core candidate; Vercel Python/Fluid
Functions are a bounded API/web/relay candidate. Neither is deployed here. The
Home Node is not a Gate B requirement and does not imply Android can host the full
Qdrant/Neo4j/ML stack. See [DEPLOYMENT.md](DEPLOYMENT.md).

Normal UI stays compact:

```text
OSCAR Mobile        Here
Cloud         Healthy
Desktop       Working · 1 task
Desk Edge     Aware
```

Expand only when the user needs capabilities, task ownership, health, permissions or remote controls.

## OSCAR Mobile — mobile

OSCAR Mobile is OSCAR on the phone and the preferred everyday owner-control and Chief-of-Staff surface.

Primary goals:

- voice/text access to the same OSCAR relationship;
- persistent presence rather than `launch assistant` behavior;
- selected Android assistant integration where supported and chosen by the user;
- optional attention-aware OSCAR Orb overlay;
- configurable home-screen widgets;
- current time/weather/calendar/tasks/notification/communication context;
- clear Sentry Aware / Listening / Muted / Awareness Off states;
- proactive alerts and `what needs me now?` synthesis;
- task/Worker supervision;
- Connection Grid controls;
- calls/messages/email/meeting capability where platform support permits;
- notification awareness after explicit grant;
- legitimate notification replies only when a real reply action/integration exists;
- optional Context Capture/Daily Journal controls;
- camera/location/sensors where authorized;
- biometric/PIN approval for sensitive actions;
- Persona configuration/preview;
- seamless continuity when leaving the desk.

OSCAR Mobile must not frame normal use as `Talk to OSCAR` versus `Type instead`.

### Orb presence

The Orb is available without permanently obstructing content.

```text
normal context
→ compact Orb

video / reading / presentation / focus
→ retreat to edge anchor / hidden hotspot

assistant gesture / hotspot / voice / tap
→ reappear immediately
```

Overlay state is best-effort UI, not a correctness dependency. Hiding the Orb does not imply microphone/capture state.

### Widgets

Widgets may expose next commitment, focus task, Worker state, Grid health, privacy/Sentry state or one-tap OSCAR invocation. They should remain glanceable and native, not mini dashboards.

### Notifications

Notification-listener access is a current-context capability, not unrestricted access to the source app. Source/app/person exclusions and independent retention/reply authority are mandatory.

See `MOBILE-DESIGN.md` and `CHIEF-OF-STAFF.md`.

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

OSCAR Mobile can inspect/pause/cancel/approve. After verified completion, OSCAR may sleep/shut down the PC when a real capability and policy permit it.

Remote power-on is only presented if Wake-on-LAN/remote-management/approved power capability is available.

## Delegated Worker surface

Workers remain underneath OSCAR. Show responsibility, current meaningful action, state, blocker/approval and result—not an agent-operations dashboard.

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
OSCAR Mobile / Desktop / Desk speaker
```

Underlying TTS can differ while intended identity remains recognizable.

Voice Match/Voice Map share semantics while preserving source/confidence metadata. OSCAR's own TTS is excluded from speaker learning and wake loops.

## Sentry participation

A surface can contribute wake/VAD/hot commands, Voice Map events, sound events, motion/presence, device health, camera/sensor observations, current app/device context and communication events.

Persistent awareness is different from active Listening and different from durable recording.

Authorized surfaces/channels may contribute selected calls/messages/mail/meetings/in-person conversations to Context Capture/Daily Journal according to source capability and retention policy.

## Chief-of-Staff continuity

Current schedule/task/communication state should survive surface changes.

```text
Desktop task running
→ OSCAR Mobile sees task + next commitment
→ user leaves
→ notification changes schedule
→ World Model updates
→ OSCAR suggests/executes permitted replan
→ user returns to Desktop
→ same objective/commitment state continues
```

No manual chat transfer.

## Persona surfaces

Persona should be editable conversationally and manually with compact trait controls/context rules. Truthfulness/safety are visibly non-configurable.

## Communication surfaces

Calls, messaging, notifications, email, meetings, dictation and continuity capture may execute through different devices/apps while remaining one logical communication subsystem.

Integration priority:

```text
native OS / official API
→ official connector/plugin
→ authorized device automation / notification action
→ computer-use/accessibility fallback
→ unsupported / ask
```

## Capability presence

Every node joins/leaves dynamically.

```text
OSCAR Mobile online      → mobile/owner/context controls
Cloud online       → rendezvous/durable coordination
PC online          → machine capabilities
Edge online        → physical/local capabilities
adapter online     → app/channel capability
```

OSCAR plans against what exists now.

## Avatar / motion continuity

The same blue-shell/yellow-puck interaction language appears where useful.

Motion should express real state with shared geometry and continuity. States include Idle, Sentry Aware, Listening, Speaking, Working, Verifying, Waiting, Blocked, Done, Muted, Awareness Off and Offline/Degraded.

Identity is shared; composition remains platform-native.

## Invariants

1. Surfaces are embodiments of one OSCAR identity, not separate assistants.
2. Surface disappearance must not erase durable task/context state.
3. OSCAR Mobile is the primary owner-control/Chief-of-Staff surface, not a hardware-safety override.
4. Overlay/widget/avatar UI never substitutes for actual runtime state.
5. Perception, retention and action authority stay independent.
6. Platform-specific capabilities remain unverified until exercised on target hardware.
7. Notification visibility never implies unrestricted source-app access.

## Current Slice 08 — 2026-10-06

Owner closure scope: **COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**.
Physical status: `DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`.
Quality candidate is under validation in PR #14. Gate C remains PARTIAL.
See [Voice Core](VOICE-CORE.md), [quality pass](VOICE-QUALITY.md) and
[consolidated acceptance](GATE-C-CONSOLIDATED-ACCEPTANCE.md).
Slice 09 software is authorized after Slice 08 integration; device acceptance is
owner-deferred. Slice 10, deployment and Home Node remain out of scope.

## Current Slice 09 — 2026-10-06

Slice 08 PR #14 merged; accepted main/work baseline
`92a11aa05083f1983186976ba64bd30aa9f1f2a0`. Slice 08 is
**COMPLETE FOR SOFTWARE / REFERENCE VOICE FOUNDATION**; physical voice is
`DEFERRED_BY_OWNER / CONSOLIDATED_GATE_C_ACCEPTANCE_REQUIRED`, never physical PASS.
OSCAR Mobile Kotlin/Compose rebuild is on `club-c/slice-09-sunday`, draft PR #15
into `work`, **PARTIAL / OWNER_DEVICE_ACCEPTANCE_NOT_RUN**. Core/loopback,
Gradle/JVM/emulated evidence is separate from actual phone/OEM acceptance.
See [OSCAR Mobile foundation](MOBILE-FOUNDATION.md) for implementation, limits and the next owner boundary.
Slice 09 must not merge in this run. Gate C remains PARTIAL. Slice 10, deployment
and Home Node are not started. Post-alpha Operating Logs, specialist-model training
and home-server migration remain documented future work, not implemented.
