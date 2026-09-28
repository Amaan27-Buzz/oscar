# First-Time Setup / Commissioning

OSCAR's first-run experience should feel like commissioning a personal system, not clicking through generic app permissions.

The setup establishes identity, voice, devices, safety, services, permissions and behavior before proactive features are enabled.

## Goals

- make OSCAR useful immediately after setup
- collect only information that materially improves operation
- test every critical integration rather than assuming it works
- make permissions understandable
- make Voice Match and Sentry behavior explicit
- finish with a complete system health check

## Setup flow

### 1. Welcome and product model

Explain briefly:

- OSCAR is one intelligence across phone, desk, ChatGPT and optional computers
- Sunday is OSCAR on the phone
- the laptop is optional
- local edge hardware handles reflexes/safety
- cloud models handle heavy reasoning

### 2. Identity and interaction preferences

Configure:

- preferred name/form of address
- concise vs conversational replies
- proactive behavior level
- whether acknowledgements should be spoken, visual or both
- default quiet hours
- notification preferences

### 3. Voice enrollment

Collect multiple samples across realistic conditions:

- normal voice
- quieter voice
- louder voice
- several phrases
- close to the microphone
- farther away
- room background noise
- different positions

If Sunday is paired, optionally gather samples through the phone microphone as well.

The setup should report enrollment quality and repeat weak samples.

### 4. Voice Match policy

Explain that Voice Match is an identity signal, not a password.

Configure policies for:

- harmless commands
- personal information
- messages/actions
- Sentry controls
- sensitive actions
- critical actions requiring phone biometric/PIN/explicit approval

Test with:

- owner voice
- deliberately changed delivery
- non-owner sample if available

### 5. Wake and reflex commands

Calibrate and test:

- wake word
- `Mute`
- `Stop`
- `Cancel`
- `Listen`
- `Sentry`
- `Stand down`

Each should visibly show measured latency and success/failure during setup.

### 6. Edge hardware discovery

Discover and identify:

- ESP32 gateway
- Pico/RP2040 controller
- displays
- microphones/speakers
- sensors
- relays
- motors/servos
- cameras through connected nodes

The setup should show capabilities, not raw ports, unless the user opens an advanced view.

### 7. Environment model

Let the user define relevant places and hardware zones such as:

- room
- desk
- electronics workbench
- entrance/door
- future home zones

Associate installed sensors/devices with those zones.

### 8. Cloud and account connections

Configure:

- Latch
- ChatGPT path
- SwitchRoute
- GitHub and other plugins/connectors as needed
- voice providers where required

Each connection should be tested end to end.

### 9. Sunday pairing

Pair the phone and verify:

- notifications
- voice/text continuity
- camera/microphone permissions as chosen
- phone actions
- biometric confirmation path
- Sentry alerts

### 10. PC worker pairing

If a computer is available, install/connect the worker and detect capabilities.

Example display:

```text
PC-Amaan
✓ Codex
✓ Computer Use
✓ PowerShell
✓ Browser
✓ VS Code
✓ Git
✓ Python
✓ FFmpeg
✓ NVIDIA GPU
```

The user should not need to manually define tools that can be safely detected.

### 11. Permission matrix

Use human-readable action classes rather than one broad “full access” switch.

Example:

| Capability | Default |
|---|---|
| Read weather | Always |
| Read calendar | Allow/deny during setup |
| Control room lights | Allow/deny during setup |
| Run Codex on paired PC | Allow/ask |
| Send a message | Confirm |
| Delete important files | Confirm |
| Change Sentry security settings | Strong confirmation |
| Critical financial/security action | Phone biometric/PIN + explicit approval |

Permissions should be editable later.

### 12. Sentry setup

Configure:

- enabled modes
- sensors used in each mode
- quiet hours
- alert channels
- camera use
- known/unknown speaker behavior
- workbench/device checks
- normal baseline observation period

Run a simulated event so the user sees exactly what OSCAR does.

### 13. Personal protocols/routines

Offer a few useful starting examples without forcing automation:

- “I'm leaving” → Away Mode + configured checks
- laptop online → expose PC worker capabilities
- workbench left powered while away → verify + notify
- sleep routine → Sleep Mode + suppress nonurgent speech

OSCAR can later propose routines from repeated behavior, but setup should not generate a large automation burden.

### 14. Avatar and feedback calibration

Choose/configure:

- avatar motion intensity
- acknowledgement sound level
- spoken vs visual acknowledgements
- serious/quiet mode behavior

Test listening, thinking, speaking, sentry and muted states.

### 15. End-to-end test

Before setup completes, test a chain that crosses multiple layers:

```text
voice command
→ local recognition/wake
→ OSCAR core
→ Latch/cloud tool or model
→ result
→ spoken reply
→ Sunday notification (optional)
```

Also test:

- reflex command while TTS is playing
- cloud unavailable fallback
- PC worker offline behavior
- Sentry event
- emergency stop path

## Setup completion screen

Show a concise operational summary:

```text
OSCAR READY

Edge gateway       Online
Pico controller    Online
Voice Match        Enrolled
Wake/reflex         Passed
Latch               Connected
ChatGPT path        Connected
SwitchRoute         Connected
Sunday              Paired
PC worker           Online / Optional
Sentry              Aware
Safety checks       Passed
```

Do not claim readiness for any component whose test failed.
