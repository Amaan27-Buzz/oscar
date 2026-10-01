# First-Time Setup / Commissioning

OSCAR's first-run experience should feel like commissioning a personal system, not clicking through generic app permissions.

Setup establishes identity, Persona, Voice Identity, Voice Match, optional Voice Map, Connection Grid, devices, cloud coordination, permissions, Sentry/capture behavior and safety before proactive/autonomous behavior is trusted.

## Goals

- become useful immediately;
- collect only information that materially improves operation;
- verify integrations instead of assuming they work;
- make privacy/permissions understandable;
- distinguish Voice Match, Voice Map, Sentry awareness and recording/capture;
- establish owner control through Sunday;
- configure a recognizable OSCAR Persona without weakening truth/safety;
- finish with evidence-backed system health.

## Setup flow

### 1. Welcome / one intelligence

Explain briefly:

- Sunday is OSCAR on the phone;
- desktop machines are optional execution nodes;
- Edge handles persistent local presence/reflex/safety;
- cloud can provide replaceable rendezvous/durable coordination;
- all of them form one Connection Grid;
- Latch/SwitchRoute are not required external products.

### 2. User identity

Configure:

- preferred name/form of address;
- basic notification/quiet-hour defaults;
- concise vs conversational response preference;
- broad proactivity preference.

### 3. OSCAR Persona

Let the user choose a starting character or describe it naturally.

Possible starting profiles:

- Wry;
- Steady;
- Spark;
- Formal;
- Custom.

Expose only a few understandable traits initially:

- humor;
- candor;
- warmth;
- formality;
- brevity;
- initiative.

Allow natural language such as:

```text
"Dry humor, concise, but serious on calls."
"Less chatty and more blunt when reviewing code."
```

Make clear that truthfulness, safety and permission boundaries are fixed and cannot be turned down by Persona settings.

See `docs/PERSONA.md`.

### 4. Personal Policy starter rules

Offer a small number of useful areas:

- interruption/focus behavior;
- calls/messages;
- meeting/capture retention;
- schedule/privacy disclosure;
- send/publish confirmation;
- Worker autonomy;
- Sentry/capture behavior.

Keep Persona and Personal Policy distinct.

### 5. OSCAR Voice Identity

Validate OSCAR's stable voice and relevant speaking modes:

- normal;
- quiet/night;
- focused/serious;
- alert;
- representative/professional.

Test pronunciation, first-audio latency, streaming/chunking and fallback degradation.

### 6. Voice Match

Collect realistic owner samples across volume, distance and noise. Show enrollment quality and explain Voice Match is an identity signal, not a password.

### 7. Optional Voice Map

Explain:

```text
Voice Match = authorization evidence
Voice Map   = who appears to be speaking
```

Known-person enrollment requires appropriate consent. Unknown voices remain unknown.

### 8. Self-voice suppression

Verify OSCAR can speak without retriggering wake or mapping its own TTS as a person, while human barge-in still works.

### 9. Wake / reflex commands

Calibrate/test deterministic commands such as:

- `Oscar`;
- `Mute`;
- `Stop`;
- `Cancel`;
- `Listen`;
- `Sentry`;
- `Stand down`;
- `Pause capture`.

### 10. Connection Grid commissioning

Initialize native OSCAR Transport + Capability Fabric and pair available nodes.

Expected roles:

```text
Sunday      owner control / approvals / notifications
Cloud       rendezvous / durable coordination (optional but recommended)
Desktop     high-capability execution
Edge        local presence / reflex / safety
```

Verify node identity, pairing, scoped credentials, transport health, reconnect and capability advertisement.

Show capability/health state, not historical Latch terminology.

See `docs/CONNECTION-GRID.md`.

### 11. Cloud deployment choice

Offer a simple choice rather than forcing infrastructure expertise:

- `Free-first` — use a supported free-tier coordinator where practical;
- `Bring my cloud` — deploy to user's AWS/GCP/Azure/Oracle/other supported target;
- `Local only for now` — reduced remote availability, clearly explained;
- future managed OSCAR hosting if/when offered.

Provider free tiers change. Setup should discover/verify the selected deployment rather than hard-code marketing assumptions.

### 12. Model providers

Configure native Model Router providers/constraints and verify at least one real reasoning route plus one fallback/degradation case where practical.

### 13. Edge discovery

Discover available ESP32/Pico, microphones/speakers, displays, sensors, relays, cameras and other capability-bearing devices.

Show capabilities rather than raw GPIO unless Advanced is opened.

### 14. Environment model

Let the user define only useful zones such as room, desk, entrance or workbench and associate relevant devices/sensors.

### 15. Sunday verification

Verify actual phone capabilities:

- notifications;
- voice/text continuity;
- biometric confirmation;
- microphone/camera permissions;
- call/message capability actually exposed;
- dictation/meeting path;
- Connection Grid owner controls;
- Sentry alerts;
- Persona/Voice Identity behavior.

### 16. PC machine-node pairing

Detect available capabilities such as Codex, terminal, filesystem, browser, computer use, IDE, Git, Python, FFmpeg, GPU/local models and installed applications.

Test remote continuation:

```text
start harmless long-running task
→ leave task active
→ observe from Sunday
→ pause/cancel or let complete
→ verify result
```

If supported, test machine sleep/shutdown after completion. Remote wake is tested only if a real Wake-on-LAN/management path exists.

### 17. Permission matrix

Use human-readable capability classes rather than `full access`.

| Capability | Example default |
|---|---|
| public harmless read | allow |
| private calendar/memory | user choice |
| run Codex on paired PC | allow/ask |
| send message | confirm or explicit Personal Policy |
| answer call as user | ask/Personal Policy |
| Context Capture / Daily Journal | off until explicitly configured |
| delete important files | confirm |
| change Sentry/capture security state | strong confirmation |
| critical financial/security action | Sunday biometric/PIN + explicit approval |

### 18. Communication defaults

Configure actual supported calls/messages/email/meetings/dictation and retention behavior.

Do not claim unsupported app audio/control capability.

### 19. Sentry awareness

Configure Passive/Aware/Guard/Away/Sleep plus sensors, quiet hours, alert channels, cameras, Voice Map behavior and acoustic-event classes.

Explicitly separate:

```text
local wake/VAD
Voice Map recognition
sound classification
activated conversational STT
ambient/context STT
raw audio retention
transcript retention
summary retention
memory extraction
```

### 20. Optional Context Capture / Daily Journal

If the user wants OSCAR to keep comprehensive daily continuity, configure source-by-source capture:

- calls where legitimately accessible;
- supported app calls;
- messages/SMS;
- email;
- meetings;
- voice notes;
- in-person conversations;
- other approved sources.

For each source choose:

- enabled/disabled;
- consent/disclosure behavior where required;
- raw media retention;
- transcript retention;
- summary/memory retention;
- people/place/time exclusions.

Offer quick privacy actions such as `Pause capture` and delete/forget controls.

### 21. Personal protocols / routines

Offer a few high-value examples:

- leaving → Away mode + configured checks;
- machine online → advertise capabilities;
- long-running desktop task → keep running + report to Sunday;
- workbench left powered while away → verify + notify;
- sleep routine → quiet output + configured safety awareness;
- incoming call while unavailable → apply communication policy.

### 22. Worker autonomy

Explain temporary/persistent Workers and configure bounded retry/reroute plus major-action confirmation defaults.

### 23. Avatar / motion / feedback

Choose motion intensity, acknowledgement sound/haptic behavior and reduced-motion preference. Verify avatar states map to actual runtime state.

### 24. End-to-end test

Test a chain such as:

```text
voice/text request
→ Jev
→ permission + Personal Policy
→ capability/model route
→ remote/local execution
→ result
→ verification
→ response through current surface
```

Also test where available:

- Sentry aware vs Listening vs Muted vs Awareness Off;
- barge-in/self-voice suppression;
- unknown speaker event;
- provider fallback;
- Connection Grid node disconnect/reconnect;
- remote desktop task continuation;
- Sunday owner pause/cancel;
- capture pause/retention behavior if enabled;
- Persona context trigger;
- emergency stop path.

## Completion screen

Show only verified status:

```text
OSCAR READY

Core loop              Verified
Connection Grid         Healthy / Partial
Cloud coordinator       Connected / Not configured
Model providers         3 available
OSCAR voice             Verified
Persona                 Custom
Voice Match             Enrolled
Voice Map               Owner only
Sentry                   Aware
Daily Journal           Off / Configured
Sunday                  Connected
Desktop                 Optional / Connected
Edge                    Optional / Connected
```

Never show `Ready` for something that was not actually tested.
