# First-Time Setup / Commissioning

OSCAR's first-run experience should feel like commissioning a personal system, not clicking through generic app permissions.

The setup establishes identity, OSCAR Voice Identity, Voice Match, optional Voice Map, devices, safety, services, permissions and behavior before proactive features are enabled.

## Goals

- make OSCAR useful immediately after setup;
- collect only information that materially improves operation;
- test critical integrations rather than assuming they work;
- make permissions understandable;
- make Voice Match, Voice Map and Sentry behavior explicit;
- verify OSCAR's own voice path and self-voice suppression;
- establish a few high-value Personal Policy rules without forcing dozens of settings;
- finish with a complete system-health check.

## Setup flow

### 1. Welcome and product model

Explain briefly:

- OSCAR is one intelligence across phone, desk, cloud providers and optional computers;
- Sunday is OSCAR on the phone;
- the laptop is optional;
- local Edge hardware handles reflexes/safety;
- cloud models handle heavy reasoning;
- Workers can be created later by describing a responsibility;
- OSCAR owns its transport/capability and model-routing infrastructure natively.

Do not present Latch or SwitchRoute as external products the user must install/configure. Their useful architecture has been folded into OSCAR.

### 2. Identity and interaction preferences

Configure only high-value defaults:

- preferred name/form of address;
- concise vs conversational replies;
- proactive behavior level;
- spoken/visual acknowledgement preference;
- quiet hours;
- notification preferences.

### 3. Personal Policy starter rules

Offer a small number of useful areas:

- interruption/focus behavior;
- call/message autonomy;
- meeting transcription/note retention;
- schedule/privacy disclosure;
- send/publish confirmation rules;
- Worker autonomy;
- Sentry behavior;
- local acoustic-awareness/transcription rules.

Make clear that the user can change these later by ordinary voice/chat.

### 4. OSCAR Voice Identity

Let the user hear and validate OSCAR's intended synthesized voice.

Test:

- normal speaking mode;
- quiet/night mode;
- focused/serious mode;
- alert clarity;
- representative/call mode where planned;
- pronunciation of a few user/project names;
- first-audio latency;
- streaming/chunking behavior.

The configured result becomes OSCAR's `VoiceProfile`, not merely a provider voice ID.

If multiple TTS providers/fallbacks are configured, test whether they preserve the intended identity well enough and record any known degradation.

### 5. Owner Voice Match enrollment

Collect samples across realistic conditions:

- normal/quiet/loud voice;
- multiple phrases;
- close/far microphone distance;
- different room positions;
- realistic background noise;
- desk microphone and Sunday where applicable.

Report enrollment quality and repeat weak samples.

### 6. Voice Match policy

Explain that Voice Match is an identity/authorization signal, not a password.

Configure policies for harmless commands, personal information, messages/actions, call handling, Sentry controls, sensitive actions and critical actions requiring stronger confirmation.

### 7. Optional Voice Map enrollment

Explain the distinction:

```text
Voice Match = is this an authorized speaker for this action?
Voice Map   = who appears to be speaking in the environment?
```

Voice Map is optional and perception-oriented.

For owner and any deliberately enrolled known speakers:

- collect representative samples only with appropriate consent;
- label/link the voice profile to a canonical person only when confirmed;
- show confidence/quality;
- configure retention for embeddings/profiles;
- explain that recognition never grants action permission;
- allow leaving everyone except the owner as `unknown` by default.

Do not silently infer identities from one ambient conversation.

### 8. Self-voice suppression test

OSCAR must prove it can speak without recognizing its own output as another person or retriggering itself.

Test while TTS is active:

- acoustic echo cancellation/playback reference;
- TTS-origin tagging;
- Voice Map exclusion;
- wake-loop prevention;
- real human barge-in.

The setup should fail this check visibly if OSCAR cannot distinguish its own playback from external speech on the current surface.

### 9. Wake and reflex commands

Calibrate/test:

- wake word;
- `Mute`;
- `Stop`;
- `Cancel`;
- `Listen`;
- `Sentry`;
- `Stand down`.

Show measured latency and success/failure.

### 10. Native transport + capability pairing

Initialize OSCAR's native Transport + Capability Fabric:

- installation/device identity;
- secure pairing keys/scoped credentials;
- node discovery;
- transport health;
- reconnect behavior;
- capability advertisement.

The user should see devices/capabilities, not historical Latch terminology.

### 11. Model providers

Configure the providers the user wants OSCAR's native Model Router to use.

Possible setup includes:

- ChatGPT/OpenAI path where available;
- other model providers;
- optional local model capabilities;
- provider priority/cost/privacy constraints.

Verify at least one reasoning path and one fallback/degradation case where practical.

Do not present SwitchRoute as a separate required service.

### 12. Edge hardware discovery

Discover/identify where available:

- ESP32 gateway;
- Pico/RP2040 controller;
- displays;
- microphones/speakers;
- sensors;
- relays;
- motors/servos;
- cameras through suitable nodes.

Show capabilities rather than raw ports unless advanced view is opened.

### 13. Environment model

Let the user define relevant places/zones such as room, desk, electronics workbench, entrance and future home zones.

Associate sensors/devices with those zones.

### 14. Sunday pairing

Pair the phone and verify:

- notifications;
- voice/text continuity;
- OSCAR VoiceProfile behavior on phone;
- camera/microphone permissions;
- phone/app actions;
- actual call/message capabilities;
- dictation/input path;
- meeting capture path;
- biometric confirmation;
- Voice Match/Voice Map participation where supported;
- Sentry alerts.

Do not claim support for a call/app action that the platform does not expose.

### 15. PC machine-worker pairing

If a computer is available, connect the machine node through native OSCAR transport and detect capabilities such as Codex, Computer Use, PowerShell, browser, IDE, Git, Python, FFmpeg and GPU support.

The user should not manually define safely detectable capabilities.

### 16. Permission matrix

Use human-readable action classes rather than one broad `full access` switch.

Examples:

| Capability | Example default |
|---|---|
| Read harmless public info | Always |
| Read calendar/personal context | Allow/deny during setup |
| Run Codex on paired PC | Allow/ask |
| Send a message | Confirm or Personal Policy |
| Answer a call as user | Ask/allow by Personal Policy |
| Publish social content | Ask by default |
| Delete important files | Confirm |
| Change Sentry security settings | Strong confirmation |
| Critical financial/security action | Phone biometric/PIN + explicit approval |

Voice Map cannot create permission. Personal Policy may restrict authority but cannot create ungranted permission.

### 17. Communication defaults

Test/configure actual capabilities available on the user's devices:

- call handling;
- caller exceptions;
- messaging autonomy;
- meeting transcription/notes;
- raw audio/transcript retention;
- callback/scheduling;
- dictation mode defaults;
- schedule/privacy disclosure.

### 18. Sentry setup

Configure:

- enabled modes: Passive/Aware/Guard/Away/Sleep;
- sensors used in each mode;
- quiet hours;
- alert channels;
- camera use;
- **local acoustic-awareness level**;
- known/unknown speaker behavior from Voice Map;
- sound-event classes;
- workbench/device checks;
- normal baseline period.

Explicitly separate these toggles/policies:

```text
listen locally for wake/VAD
recognize known/unknown speakers
classify configured sounds
transcribe activated speech
retain transcripts
retain raw audio
```

They are not one permission.

Run at least one simulated Sentry event so the user sees exactly what OSCAR does.

### 19. Personal protocols/routines

Offer a few useful examples without forcing automation:

- leaving → Away mode + configured checks;
- laptop online → expose machine capabilities;
- workbench left powered while away → verify + notify;
- sleep routine → Sleep mode + suppress nonurgent speech;
- incoming call while unavailable → apply communication policy.

### 20. Worker autonomy

Explain Workers in one sentence: OSCAR can create temporary or persistent sub-agents for delegated responsibilities.

Offer optional defaults for retry/reroute, routine messages, publishing and major-announcement confirmation.

### 21. Avatar and feedback calibration

Choose/configure avatar motion intensity, acknowledgement sound level, spoken vs visual acknowledgements and serious/quiet mode behavior.

Test listening, thinking, speaking, sentry, muted, verifying, blocked and done states.

### 22. End-to-end test

Before setup completes, test a chain such as:

```text
voice command
→ local wake / Voice Match
→ OSCAR Core / Jev
→ Personal Policy + permission
→ native Model Router or capability path
→ native Transport to executor if needed
→ result
→ verification
→ spoken reply through OSCAR VoiceProfile
```

Also test:

- reflex command while TTS is playing;
- self-voice suppression while OSCAR speaks;
- unknown speaker event if Voice Map is enabled;
- provider unavailable fallback;
- PC machine node offline behavior;
- one configured communication action where available;
- Personal Policy edit by voice/text;
- Sentry event;
- emergency stop path.

## Setup completion screen

Show a concise operational summary based on verified checks, for example:

```text
OSCAR READY

Core loop             Verified
Native transport      Healthy
Model providers       2 available
OSCAR voice           Verified
Voice Match           Enrolled
Voice Map             Owner only
Acoustic Sentry       Local wake + speaker events
Sunday                Connected
Desktop worker        Optional / Connected
Edge                   Optional / Connected
```

Do not show `Ready` for a subsystem that was not actually tested. Use `Not configured`, `Unavailable`, `Partial` or `Failed` when that is the evidence-backed state.
