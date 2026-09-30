# OSCAR Surfaces and Embodiments

OSCAR is one intelligence expressed through multiple devices. These surfaces share identity, task state, permissions, Personal Policy, memory, Voice Identity and capability contracts rather than becoming separate assistants.

All cross-device coordination uses OSCAR-owned transport/capability contracts. The separate Latch project is reference/prototype material, not a required runtime.

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

Example:

```text
start task on desktop
→ leave desk
→ Sunday keeps task state
→ OSCAR notifies when blocked/verified complete
→ continue by voice on phone
```

Communication behavior is governed by `docs/COMMUNICATION.md` and `docs/PERSONAL-POLICY.md`.

## OSCAR Desktop — Windows and macOS

The desktop app is OSCAR's native presence on a computer, not OSCAR's host.

Windows is expected to be the deepest initial integration. macOS follows the same capability model with platform-appropriate adapters.

Planned desktop capabilities:

- native lightweight app/overlay;
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

The desktop UI should avoid becoming another giant chat sidebar.

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

Workers are created/managed by OSCAR and should have a minimal visibility/control UI rather than a dense dashboard.

The primary interface remains natural language: `pause the SceneLab worker`, `let it publish ordinary feature posts without asking`.

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

Voice Match and Voice Map also share profile semantics across surfaces while preserving source-device/confidence metadata.

OSCAR's own speaker output must be excluded from Voice Map learning/identity updates and should not retrigger wake logic. Real human barge-in must remain functional.

See [VOICE-SENTRY.md](VOICE-SENTRY.md).

## Kinetable integration

Kinetable is OSCAR's specialist hardware workshop rather than a duplicate editor inside OSCAR.

Long-term flow:

```text
"I want a desk presence detector with an OLED"
→ OSCAR routes engineering work to Kinetable
→ use actual inventory
→ design + simulate + generate firmware
→ user builds/provisions device
→ device joins native OSCAR transport
→ device advertises capabilities
```

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
- Voice Map speaker events;
- configured sound events;
- motion/presence;
- device health;
- camera/sensor observations;
- current app/device context.

These become Perception/World Model events. Continuous local acoustic awareness does not imply continuous cloud transcription or raw-audio retention.

## Cross-surface continuity

The same task should survive surface changes.

```text
Sunday: "OSCAR, investigate the Kinetable issue."
→ OSCAR delegates to PC/Codex when available
→ user sits at desk
→ Desktop: "What did Codex find?"
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
PC online          → Codex/desktop capabilities
ESP32 online       → physical capabilities
camera node online → visual context
app adapter up     → app/channel capability
```

OSCAR plans against what exists **now**, not assumptions about one permanent device.

## Avatar continuity

The same OSCAR avatar/expression language should appear where useful across Sunday, desktop and physical displays.

States include idle, listening, thinking, speaking, working, verifying, waiting, success, confused, alert, Sentry, sleeping, muted, blocked and error.

The yellow face retains weighted joystick/puck movement inside the blue shell, with motion mapped to attention and real system state.
