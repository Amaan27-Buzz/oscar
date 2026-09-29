# First-Time Setup / Commissioning

OSCAR's first-run experience should feel like commissioning a personal system, not clicking through generic app permissions.

The setup establishes identity, voice, devices, safety, services, permissions and behavior before proactive features are enabled.

## Goals

- make OSCAR useful immediately after setup
- collect only information that materially improves operation
- test every critical integration rather than assuming it works
- make permissions understandable
- make Voice Match and Sentry behavior explicit
- establish a few high-value Personal Policy rules without forcing dozens of settings
- finish with a complete system health check

## Setup flow

### 1. Welcome and product model

Explain briefly:

- OSCAR is one intelligence across phone, desk, ChatGPT and optional computers
- Sunday is OSCAR on the phone
- the laptop is optional
- local edge hardware handles reflexes/safety
- cloud models handle heavy reasoning
- Workers can be created later simply by telling OSCAR what responsibility to delegate

### 2. Identity and interaction preferences

Configure only high-value defaults:

- preferred name/form of address
- concise vs conversational replies
- proactive behavior level
- whether acknowledgements should be spoken, visual or both
- default quiet hours
- notification preferences

Make clear that these are not the limit of OSCAR preferences. The user can later say things such as "do not answer family calls for me" or "for university meetings keep detailed notes" and OSCAR will update Personal Policy directly.

### 3. Personal Policy starter rules

Offer a small number of useful areas without forcing a giant settings wizard:

- interruption/focus behavior
- call/message autonomy
- meeting transcription/note retention
- schedule/privacy disclosure rules
- what may be sent/published without confirmation
- Worker autonomy defaults
- Sentry behavior

Examples:

```text
Answer unknown calls after 4 rings?        Ask / Allow / Never
Share free calendar slots?                  Allow / Ask / Never
Share event titles?                         Allow / Ask / Never
Transcribe university meetings?             On / Ask / Off
Workers may publish ordinary social posts?  Allow / Ask / Never
```

The setup should explicitly say: **you can change any of this later by simply telling OSCAR.**

See `docs/PERSONAL-POLICY.md`.

### 4. Voice enrollment

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

### 5. Voice Match policy

Explain that Voice Match is an identity signal, not a password.

Configure policies for:

- harmless commands
- personal information
- messages/actions
- call handling
- Sentry controls
- sensitive actions
- critical actions requiring phone biometric/PIN/explicit approval

Test with:

- owner voice
- deliberately changed delivery
- non-owner sample if available

### 6. Wake and reflex commands

Calibrate and test:

- wake word
- `Mute`
- `Stop`
- `Cancel`
- `Listen`
- `Sentry`
- `Stand down`

Each should visibly show measured latency and success/failure during setup.

### 7. Edge hardware discovery

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

### 8. Environment model

Let the user define relevant places and hardware zones such as:

- room
- desk
- electronics workbench
- entrance/door
- future home zones

Associate installed sensors/devices with those zones.

### 9. Cloud and account connections

Configure:

- Latch
- ChatGPT path
- SwitchRoute
- GitHub and other plugins/connectors as needed
- communication services/connectors where desired
- voice providers where required

Each connection should be tested end to end.

### 10. Sunday pairing

Pair the phone and verify:

- notifications
- voice/text continuity
- camera/microphone permissions as chosen
- phone actions
- available call/message capabilities
- available app capabilities
- dictation/input path where supported
- meeting capture path where supported
- biometric confirmation path
- Sentry alerts

Do not claim support for a call/app action that the platform does not expose.

### 11. PC machine-worker pairing

If a computer is available, install/connect the machine worker and detect capabilities.

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

### 12. Permission matrix

Use human-readable action classes rather than one broad “full access” switch.

Example:

| Capability | Default |
|---|---|
| Read weather | Always |
| Read calendar | Allow/deny during setup |
| Control room lights | Allow/deny during setup |
| Run Codex on paired PC | Allow/ask |
| Send a message | Confirm |
| Answer a call as the user | Ask/allow by Personal Policy |
| Publish an ordinary social post | Ask by default |
| Delete important files | Confirm |
| Change Sentry security settings | Strong confirmation |
| Critical financial/security action | Phone biometric/PIN + explicit approval |

Permissions should be editable later. Personal Policy may make behavior stricter, but cannot create permission that is not granted.

### 13. Communication defaults

Test and configure the actual capabilities available on the user's devices:

- call handling/answering behavior
- caller exceptions
- messaging autonomy
- meeting transcription/notes
- raw audio/transcript retention
- callback/scheduling behavior
- dictation mode defaults
- schedule/privacy disclosure rules

Use `docs/COMMUNICATION.md` as the product contract.

### 14. Sentry setup

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

### 15. Personal protocols/routines

Offer a few useful starting examples without forcing automation:

- “I'm leaving” → Away Mode + configured checks
- laptop online → expose PC machine-worker capabilities
- workbench left powered while away → verify + notify
- sleep routine → Sleep Mode + suppress nonurgent speech
- incoming call while unavailable → apply Personal Policy and configured communication handling

OSCAR can later propose routines from repeated behavior, but setup should not generate a large automation burden.

### 16. Worker autonomy

Explain Workers in one sentence: OSCAR can create temporary or persistent sub-agents for delegated responsibilities.

Offer optional defaults such as:

- may Workers retry/reroute recoverable failures automatically?
- may Workers send routine messages without asking?
- may Workers publish ordinary social posts?
- should major announcements always ask?

Do not require the user to create Workers during setup. Natural-language creation later should be enough.

See `docs/WORKERS.md`.

### 17. Avatar and feedback calibration

Choose/configure:

- avatar motion intensity
- acknowledgement sound level
- spoken vs visual acknowledgements
- serious/quiet mode behavior

Test listening, thinking, speaking, sentry and muted states.

### 18. End-to-end test

Before setup completes, test a chain that crosses multiple layers:

```text
voice command
→ local recognition/wake
→ OSCAR core / Jev
→ Personal Policy + permission check
→ Latch/cloud tool or model
→ result
→ spoken reply
→ Sunday notification (optional)
```

Also test:

- reflex command while TTS is playing
- cloud unavailable fallback
- PC machine worker offline behavior
- one configured communication action where available
- Personal Policy edit by voice/text
- Sentry event
- emergency stop path

## Setup completion screen

Show a concise operational summary:

```text
OSCAR READY

Edge gateway       Online
Pico controller    Online
Voice Match        Enrolled
Wake/reflex        Passed
Personal Policy    Ready
Latch              Connected
ChatGPT path       Connected
SwitchRoute        Connected
Sunday             Paired
Communication      Available capabilities verified
PC worker          Online / Optional
Sentry             Aware
Safety checks      Passed
```

Do not claim readiness for any component whose test failed.
