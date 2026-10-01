# OSCAR Surfaces and Embodiments

OSCAR is one intelligence expressed through multiple devices. These surfaces share identity, task state, permissions, Personal Policy, memory, Voice Identity and capability contracts rather than becoming separate assistants.

All cross-device coordination uses OSCAR-owned transport/capability contracts. The separate Latch project is reference/prototype material, not a required runtime.

## Shared surface principles

Across Sunday, desktop and physical surfaces:

- OSCAR should feel **present**, not repeatedly launched;
- voice and text are peers in one continuous context;
- local acoustic awareness is distinct from active conversational listening;
- UI state must reflect real runtime/verification state;
- complexity is progressively disclosed;
- motion preserves continuity where practical instead of replacing one page with another;
- each platform gets a native composition rather than the same layout at different widths.

The visual/interaction direction is defined by `DESIGN.md` and `TASTE.md`.

## Sunday — mobile

Sunday is OSCAR on the phone.

Primary goals:

- voice and text access to the same OSCAR session/history;
- stable OSCAR VoiceProfile where the platform permits;
- Voice Match/Voice Map participation where supported;
- proactive notifications and alerts;
- phone calls/messages/actions subject to platform permissions;
- AI call answering under explicit Personal Policy where technically supported;
- WhatsApp/Telegram/other app communication where supported;
- mobile meetings/transcription/notes;
- system-wide dictation/input assistance;
- camera, microphone, location and sensor context;
- biometric/PIN confirmation for sensitive actions;
- remote access to OSCAR tasks and delegated Workers;
- continuity while moving away from the desk.

Sunday must not frame ordinary use as a permanent `Talk to OSCAR` / `Type instead` choice. If Sentry acoustic awareness is enabled, OSCAR may already be locally processing wake/VAD/hot-command/Voice Map/sound-event signals while not actively transcribing.

Conceptually:

```text
Sentry aware         = local low-cost acoustic awareness may be active
Listening            = active conversational turn / STT
Muted                = ordinary conversational listening off; permitted local reflex/safety commands may remain
Awareness disabled   = local acoustic plane actually disabled
Typing               = another input modality in the same OSCAR context
```

See [SUNDAY-DESIGN.md](SUNDAY-DESIGN.md) and [VOICE-SENTRY.md](VOICE-SENTRY.md).

Cross-device example:

```text
start task on desktop
→ leave desk
→ Sunday keeps task state
→ OSCAR notifies when blocked or verified complete
→ continue by voice or text on phone
```

Communication behavior is governed by `docs/COMMUNICATION.md` and `docs/PERSONAL-POLICY.md`.

## OSCAR Desktop — Windows and macOS

The desktop app is OSCAR's native presence on a computer, not OSCAR's host.

Windows is expected to be the deepest initial integration. macOS follows the same capability model with platform-appropriate adapters.

Planned desktop capabilities:

- native lightweight app/overlay;
- compact ambient OSCAR presence;
- contextual expansion rather than a permanent giant assistant window;
- voice/text interaction using the same OSCAR VoiceProfile;
- push/hold-to-talk and Sentry participation;
- Voice Match/Voice Map participation when microphone access allows;
- system-wide dictation;
- meeting transcription/notes;
- avatar/state presence;
- screen/cursor/selection/active-window context;
- notifications/task progress;
- permission/approval surfaces;
- machine-worker health/capability status;
- Worker status/management;
- handoff to Sunday.

The desktop UI should avoid becoming another giant chat sidebar or dashboard.

Where practical, a compact presence should physically/spatially transform into contextual detail rather than teleporting into an unrelated window:

```text
compact presence
→ contextual overlay
→ task/interaction state
→ verification/result
→ compact presence
```

## Machine Worker node

The user-facing desktop app and high-capability machine worker can share infrastructure but are conceptually different.

The machine worker advertises capabilities such as:

```text
codex
computer-use
terminal
powershell/shell
browser
filesystem
IDE
Git
Python
FFmpeg
Blender
GPU/local support models
specialist software
```

When the computer is off, those capabilities disappear; OSCAR remains alive through other available surfaces.

## Delegated Worker surface

Workers are created/managed by OSCAR and should have minimal visibility/control UI rather than a dense dashboard.

The primary interface remains natural language and contextual control. Worker surfaces should expose responsibility, current meaningful state, capability use, approvals, artifacts/evidence and blockers without turning OSCAR into an agent-management console.

See [WORKERS.md](WORKERS.md).

## OSCAR Edge — embedded always-on presence

### ESP32 gateway

Responsibilities:

- Wi-Fi/network;
- small native OSCAR Edge transport client;
- local event routing;
- wake/VAD/audio front end where practical;
- local Sentry acoustic events where hardware permits;
- display/status coordination;
- short-term state;
- OTA/configuration;
- communication with Pico.

### RP2040/Pico controller

Responsibilities:

- deterministic GPIO/sensors/buttons;
- relays/motors/actuators;
- timing-sensitive behavior;
- interlocks/emergency safety.

Cloud intelligence must never be required for local hardware safety.

## Desk / physical OSCAR

The physical embodiment can combine:

- microphone/speaker;
- OSCAR avatar/status display;
- stable OSCAR voice output where speaker hardware exists;
- physical mute/stop/PTT controls;
- wake/VAD/Sentry acoustic front end;
- Voice Map speaker events where compute/hardware permits;
- presence sensors;
- workbench telemetry;
- cameras via suitable nodes;
- expressive but purposeful movement;
- future environment controls.

The goal is presence and utility, not building a humanoid robot for its own sake.

## Voice continuity across surfaces

Voice is part of identity, not a per-device afterthought.

```text
OSCAR Voice Identity
        ↓
provider-independent VoiceProfile
        ↓
Sunday / Desktop / Desk speaker
```

Each surface may use a different local/cloud TTS implementation, but should preserve the same intended voice character/prosody as closely as possible.

Voice Match and Voice Map share profile semantics across surfaces while preserving source-device/confidence metadata.

OSCAR's own speaker output must be excluded from Voice Map learning/identity updates and should not retrigger wake logic. Real human barge-in must remain functional.

See [VOICE-SENTRY.md](VOICE-SENTRY.md).

## Physical device and engineering capability expansion

Physical and engineering work stays inside the same capability model rather than depending on a dedicated hardware-workbench product.

Example:

```text
"I want a desk presence detector with an OLED"
→ OSCAR discovers installed/connected engineering capabilities
→ routes CAD/circuit/simulation/firmware work to suitable specialist tools where available
→ user builds/provisions device
→ device joins native OSCAR transport
→ device advertises sensors/actions/capabilities
```

OSCAR can then control and observe the resulting device directly through Edge/device capability contracts.

## ChatGPT / model-provider surface

ChatGPT is an important reasoning surface/provider, but OSCAR owns the surrounding transport/routing contracts.

Conceptually:

```text
OSCAR/Jev
→ native OSCAR Model Router
→ ChatGPT or another configured provider
```

Where ChatGPT can invoke OSCAR capabilities, that path also goes through OSCAR-owned provider/transport adapters.

Do not model ChatGPT as requiring a separately deployed Latch service.

## Communication surfaces

Calls, meetings, messaging and dictation may execute through different devices/apps, but they are one logical OSCAR communication subsystem.

Examples:

```text
cellular call          → Sunday / telephony capability
WhatsApp message       → official integration or Sunday app capability
Zoom meeting on laptop → desktop communication capability
in-person meeting      → authorized phone/desk microphone
system-wide dictation  → Sunday IME/accessibility or desktop input adapter
```

OSCAR should choose the strongest legitimate integration path and expose only capabilities actually available.

## Sentry surface participation

Sentry is distributed but coherent.

A surface may contribute:

- wake/VAD;
- deterministic hot/reflex commands;
- Voice Map speaker events;
- configured sound events;
- motion/presence;
- device health;
- camera/sensor observations;
- current app/device context.

These become Perception/World Model events. Continuous local acoustic awareness does not imply continuous cloud transcription or raw-audio retention.

Sentry UI should expose meaningful state without becoming a surveillance dashboard. Normal mode should remain calm; evidence/source detail lives one layer deeper.

## Cross-surface continuity

The same task should survive surface changes.

```text
Sunday: "OSCAR, investigate this issue."
→ OSCAR delegates to an available PC/coding capability
→ user sits at desk
→ Desktop: "What did the coding worker find?"
→ shared state resolves the reference
```

Communication is continuous too:

```text
OSCAR takes a call on Sunday
→ records approved summary/action item
→ user asks on desktop "what did they need?"
→ LRA resolves call context
```

No manual chat transfer should be required.

## Capability presence

Every node joins/leaves dynamically.

```text
Sunday online      → mobile/communication capabilities
PC online          → coding/desktop capabilities
ESP32 online       → physical capabilities
camera node online → visual context
app adapter up     → app/channel capability
```

OSCAR plans against what exists **now**, not assumptions about one permanent device.

## Avatar continuity

The same OSCAR presence/expression language should appear where useful across Sunday, desktop and physical displays.

States include present/idle, Sentry aware, listening, thinking/working, speaking, verifying, waiting, done/verified, partial, alert, sleeping, muted, acoustic-awareness-disabled, blocked, error and offline/degraded.

The yellow face retains weighted magnetic-puck/joystick movement inside the blue shell, with motion mapped to attention and real system state.

## Cross-surface motion continuity

Motion should reinforce the idea that these are embodiments of one system.

Shared rules:

- state changes preserve geometry where practical;
- controls expand from their cause/source;
- motion is weighted and responsive, not decorative;
- animation never blocks actions or hides failure;
- reduced-motion mode preserves all meaning;
- low-power/degraded surfaces may simplify motion without changing state semantics.

Identity is shared; composition remains platform-native.
