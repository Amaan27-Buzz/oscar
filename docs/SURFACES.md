# OSCAR Surfaces and Embodiments

OSCAR is one intelligence expressed through multiple devices. These surfaces must share identity, task state, permissions, Personal Policy and memory rather than becoming separate assistants.

## Sunday — mobile

Sunday is OSCAR on the phone.

Primary goals:

- voice and text access to the same OSCAR session/history
- proactive notifications and alerts
- phone calls/messages/actions subject to platform permissions
- AI call answering under explicit Personal Policy where technically supported
- WhatsApp/Telegram/other app communication where supported
- mobile meetings/transcription/notes
- system-wide dictation/input assistance
- camera, microphone, location and sensor context
- biometric/PIN confirmation for sensitive actions
- remote access to OSCAR tasks and delegated Workers
- continuity while moving away from the desk

Example:

```text
start task on desktop
→ leave desk
→ Sunday keeps task state
→ OSCAR notifies when blocked/complete
→ continue by voice on phone
```

Communication behavior is governed by `docs/COMMUNICATION.md` and `docs/PERSONAL-POLICY.md` rather than hard-coded app-specific assumptions.

## OSCAR Desktop — Windows and macOS

The desktop app is OSCAR's native presence on a computer, not OSCAR's host.

The Windows implementation is expected to be the deepest initial integration because Latch targets Windows heavily. macOS should follow the same capability model with platform-appropriate adapters.

Planned desktop capabilities:

- native lightweight app / overlay
- voice and text interaction
- push/hold-to-talk and Sentry participation
- system-wide dictation
- meeting transcription/notes where supported
- avatar/state presence
- screen/cursor/selection/active-window context
- notifications and task progress
- permission/approval surfaces
- machine-worker health/capability status
- delegated Worker status/management
- handoff to Sunday

The desktop UI should avoid becoming another giant chat sidebar. The primary mental model is the current OSCAR interaction plus searchable history/timeline when needed.

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

When the computer is off, those capabilities disappear; OSCAR remains alive through edge/cloud/mobile paths.

This machine-worker concept is distinct from delegated **Workers** such as `SceneLab Social` or `ClearLane Release`. A delegated Worker may use a machine worker node as one execution surface.

## Delegated Worker surface

Workers are created/managed by OSCAR and should have a minimal visibility/control UI rather than a dense agent dashboard.

Example:

```text
Workers

SceneLab Social      Active
ClearLane Release    Waiting for CI
University Admin     Idle
Research             Working
```

Opening a Worker can show:

- objective/responsibility
- current state/blocker
- capabilities it can use
- autonomy/approval rules
- recent consequential actions
- pause/resume/edit/delete controls

The primary Worker interface remains natural language: "OSCAR, pause the SceneLab worker" or "let it publish ordinary feature posts without asking."

See [WORKERS.md](WORKERS.md).

## OSCAR Edge — embedded always-on presence

### ESP32 gateway

Responsibilities:

- Wi-Fi/network
- Latch Edge connection
- local event routing
- wake/VAD/audio front end where practical
- display/status coordination
- short-term state
- OTA/configuration
- communication with Pico

### RP2040/Pico controller

Responsibilities:

- deterministic GPIO
- sensors
- buttons
- relays
- motors/actuators
- timing-sensitive behavior
- interlocks and emergency safety

Cloud intelligence must never be required for local hardware safety.

## Desk / physical OSCAR

The physical embodiment can combine:

- microphone/speaker
- OSCAR avatar/status display
- physical mute/stop/PTT controls
- presence sensors
- workbench telemetry
- cameras via suitable nodes
- expressive but purposeful movement
- future environment controls

The goal is presence and utility, not building a humanoid robot for its own sake.

## Kinetable integration

Kinetable is OSCAR's hardware workshop rather than a duplicate hardware editor inside OSCAR.

Long-term flow:

```text
"I want a desk presence detector with an OLED"
        ↓
OSCAR routes engineering work to Kinetable
        ↓
use actual component inventory
        ↓
design + simulate + generate firmware
        ↓
user builds/provisions device
        ↓
new device advertises OSCAR capabilities
```

Kinetable should eventually support provisioning hardware nodes into OSCAR/Latch Edge with the correct identity, capabilities and safety metadata.

## ChatGPT surface

ChatGPT through Latch is another OSCAR interaction surface.

Required directions:

```text
ChatGPT → Latch → OSCAR
OSCAR → Latch → ChatGPT
```

The user should be able to ask ChatGPT to inspect or operate OSCAR capabilities when permitted, while OSCAR can also invoke ChatGPT for suitable reasoning/workflows through the abstracted wake path.

## Communication surfaces

Calls, meetings, messaging and dictation may be executed by different devices/apps, but they are one logical OSCAR communication subsystem.

Examples:

```text
cellular call          → Sunday / telephony capability
WhatsApp message       → official integration or Sunday app capability
Zoom meeting on laptop → desktop communication capability
in-person meeting      → authorized phone/desk microphone
system-wide dictation  → Sunday IME/accessibility or desktop input adapter
```

OSCAR should choose the strongest legitimate integration path and expose only capabilities that are actually available.

See [COMMUNICATION.md](COMMUNICATION.md).

## Cross-surface continuity

The same task should survive surface changes.

Example:

```text
Sunday: "OSCAR, investigate the Kinetable issue."
        ↓
OSCAR delegates to PC/Codex when available
        ↓
user sits at desk
        ↓
Desktop: "What did Codex find?"
        ↓
OSCAR resolves "Codex" and "that issue" from shared state
```

Communication is continuous too:

```text
OSCAR takes a call on Sunday
→ records approved summary/action item
→ user asks on desktop "what did they need?"
→ LRA resolves the call context
```

No manual chat transfer should be required.

## Capability presence

Every node joins/leaves dynamically.

```text
Sunday online      → mobile/communication capabilities available
PC online          → Codex/desktop capabilities available
ESP32 online       → physical capabilities available
camera node online → visual context available
app integration up → app-specific communication capability available
```

OSCAR plans against what exists **now**, not assumptions about one permanent device.

## Avatar continuity

The same OSCAR avatar/expression language should appear where useful across Sunday, desktop and physical displays.

The avatar is functional state communication:

- idle
- listening
- thinking
- speaking
- success
- confused
- alert
- Sentry
- sleeping
- muted
- error

The yellow face should retain the weighted joystick/puck movement inside the blue shell, with motion mapped to attention and system state.
