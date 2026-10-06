# First-Time Setup / Commissioning

OSCAR's first-run experience should feel like commissioning a personal system, not clicking through generic app permissions.

Setup establishes identity, Persona, Voice Identity, Voice Match/Map, Connection Grid, devices, model/search providers, Personal Policy, OSCAR Mobile/Android capabilities, Sentry/capture behavior and safety before proactive/autonomous behavior is trusted.

## Goals

- become useful immediately;
- collect only information that materially improves operation;
- verify integrations instead of assuming they work;
- make privacy/permissions understandable;
- distinguish perception, retention and action authority;
- distinguish Voice Match, Voice Map, Sentry awareness and recording/capture;
- establish owner control through OSCAR Mobile;
- configure a recognizable OSCAR Persona without weakening truth/safety;
- finish with evidence-backed system health.

## Setup flow

### 1. Welcome / one intelligence

Explain briefly:

- OSCAR Mobile is OSCAR on the phone;
- desktop machines are optional execution nodes;
- Edge handles persistent local presence/reflex/safety;
- cloud can provide replaceable rendezvous/durable coordination;
- all of them form one Connection Grid;
- OSCAR is intended to act as an ambient Chief of Staff, not only an on-demand chat surface;
- Latch/SwitchRoute are not required external runtime products.

### 2. User identity

Configure preferred name/form of address, timezone/locale, basic quiet hours, concise/conversational preference and broad proactivity preference.

### 3. OSCAR Persona

Let the user choose a starting character or describe it naturally. Starting profiles may include Wry, Steady, Spark, Formal or Custom.

Expose only a few understandable traits initially: humor, candor, warmth, formality, brevity and initiative.

Truthfulness, safety and permission boundaries are fixed and cannot be turned down by Persona settings.

### 4. Personal Policy starter rules

Seed only high-value areas:

- interruption/focus behavior;
- fixed vs flexible schedule classes;
- schedule autonomy: suggest-only vs bounded auto-replan;
- calls/messages/replies;
- notification source/retention/action rules;
- Orb/overlay visibility behavior;
- meeting/capture retention;
- schedule/privacy disclosure;
- send/publish confirmation;
- Worker autonomy;
- Sentry behavior;
- Connection Grid remote-continuation/power preferences.

Natural-language interpretation of consequential policy should be shown as a structured candidate and owner-confirmed before activation.

### 5. OSCAR Voice Identity

Validate stable voice and relevant modes: normal, quiet/night, focused/serious, alert and representative/professional.

### 6. Voice Match

Collect realistic owner samples and explain Voice Match is identity evidence, not a password.

### 7. Optional Voice Map

Explain:

```text
Voice Match = authorization evidence
Voice Map   = who appears to be speaking
```

Known-person enrollment requires appropriate consent. Unknown remains unknown.

### 8. Self-voice suppression / wake / reflex

Verify OSCAR can speak without retriggering wake or mapping its own TTS as a person while human barge-in still works.

Test deterministic commands such as `Oscar`, `Mute`, `Stop`, `Cancel`, `Listen`, `Sentry`, `Stand down`, `Pause capture`.

### 9. Connection Grid commissioning

Pair available roles:

```text
OSCAR Mobile      owner control / approvals / notifications / current context
Cloud       rendezvous / durable coordination
Desktop     high-capability execution
Edge        local presence / reflex / safety
```

Verify node identity, pairing, scoped credentials, transport health, reconnect and capability advertisement.

### 10. Cloud deployment choice

Offer simple choices such as free-first supported coordinator, bring-my-cloud, local-only for now, and future managed OSCAR hosting if available.

Provider free tiers change. Discover/verify the selected deployment instead of hard-coding marketing assumptions.

### 11. Model + search providers

Configure native Model Router providers/constraints and verify at least one real reasoning path plus fallback/degradation where practical.

Configure search/live-source providers. Current/freshness-sensitive facts should use current authoritative sources rather than stale priors.

### 12. OSCAR Mobile / Android system integration

On supported Android devices, configure separately:

- selected assistant role / voice-interaction integration;
- microphone/camera/location permissions;
- notification-listener access;
- application-overlay permission for the OSCAR Orb;
- home-screen widgets;
- biometric/PIN approval;
- battery/background-service expectations where relevant.

Do not present these as one `full access` switch.

OEM/device behavior must be tested on the real phone rather than assumed from emulator support.

### 13. Orb setup

If overlay is enabled, choose defaults for:

- visible compact presence;
- retreat/hide during video, reading, presentation or focus contexts;
- edge/hotspot invocation;
- app-specific exclusions;
- manual `hide/show/stay hidden` behavior;
- reduced motion/accessibility.

Verify hiding the Orb does not accidentally imply or change microphone/Sentry state.

### 14. Widgets

Offer a small set of useful widgets rather than a configuration wall:

- Presence / invoke OSCAR;
- Next commitment;
- Focus task;
- active Worker;
- Grid health;
- Privacy/Sentry;
- daily brief.

Verify widget state restores correctly after process restart.

### 15. Notification awareness

If enabled:

- verify posted/removed notification events arrive;
- configure app/person/source exclusions;
- default sensitive banking/OTP/password-like content away from durable memory;
- configure whether summaries are allowed;
- separately configure reply authority;
- verify a notification with a real reply action works only within policy;
- verify a notification without a reply action does not fabricate capability.

### 16. Chief-of-Staff context

Configure current sources needed for useful day coordination:

- timezone/time/date;
- weather;
- calendar/free-busy;
- tasks/deadlines;
- location/travel context if wanted;
- notifications/communications;
- current media/focus/activity signals where supported.

Define fixed vs flexible commitments explicitly enough for schedule automation.

Test a harmless scenario such as:

```text
current calendar + task + weather
→ detect a real schedule risk
→ suggest a change
→ user approves or an explicit policy allows it
→ mutate calendar/task through a real capability
→ read back and verify
```

### 17. Edge discovery

Discover available ESP32/Pico, microphones/speakers, displays, sensors, relays, cameras and other capability-bearing devices. Show capabilities rather than raw GPIO unless Advanced is opened.

### 18. PC machine-node pairing

Detect Codex, terminal, filesystem, browser/computer use, IDE, Git, Python, FFmpeg, GPU/local models and installed apps.

Test remote continuation:

```text
start harmless long-running task
→ leave task active
→ observe from OSCAR Mobile
→ pause/cancel or let complete
→ verify result
```

Remote power is tested only if a real sleep/shutdown/wake mechanism exists.

### 19. Permission matrix

Use human-readable capability classes and separate **perceive / retain / act**.

Example:

| Context/capability | Perceive | Retain | Act |
|---|---|---|---|
| public weather | allow | current cache | n/a |
| private calendar | user choice | event metadata per policy | edit only if granted |
| notifications | explicit Android grant | source-specific | reply only when real action + authority |
| location | user choice | off by default | planning input only |
| microphone | conversational/wake choice | separate capture policy | n/a |
| send message | source-specific read | per policy | confirm or explicit Personal Policy |
| Worker execution | task context | bounded evidence | allow/ask |
| Context Capture | source-specific | explicit retention | no implicit external action |
| critical financial/security action | source-specific | minimal | strong approval |

### 20. Communication defaults

Configure actual supported calls/messages/email/meetings/dictation and retention behavior. Do not claim unsupported app audio/control capability.

### 21. Sentry awareness

Configure modes and explicitly separate local wake/VAD, Voice Map, sound classification, activated STT, ambient/context STT, raw audio retention, transcript retention, summary retention and memory extraction.

### 22. Optional Context Capture / Daily Journal

If wanted, configure source-by-source capture for calls, supported app calls/messages, email, meetings, voice notes, in-person conversations and other approved sources.

For each source choose consent/disclosure behavior, raw-media retention, transcript retention, summary/memory retention and exclusions.

### 23. Personal protocols / routines

Offer high-value examples such as leaving → Away mode, machine online → advertise capability, long-running desktop task → keep running + report to OSCAR Mobile, sleep routine, incoming call while unavailable, or morning/day brief.

### 24. Worker autonomy

Explain temporary/persistent Workers and configure bounded retry/reroute plus major-action confirmation defaults.

### 25. Avatar / motion / feedback

Choose motion intensity, acknowledgement sound/haptics and reduced-motion preference. Verify avatar/Orb state maps to actual runtime state.

### 26. End-to-end test

Test a chain such as:

```text
current context / voice / notification
→ World Model / Controller
→ permission + Personal Policy
→ capability/search/model route
→ remote/local execution
→ result
→ verification
→ response through current surface
```

Where available also test Sentry states, barge-in/self-voice suppression, provider fallback, Grid disconnect/reconnect, remote desktop continuation, OSCAR Mobile owner control, capture pause/retention, Persona context trigger, notification exclusions/replies, Orb retreat, widget refresh and emergency stop.

## Completion screen

Show only verified status, for example:

```text
OSCAR READY

Core loop              Verified
Connection Grid         Healthy / Partial
Cloud coordinator       Connected / Not configured
Model/search providers  3 available
OSCAR voice             Verified
Persona                 Custom
Voice Match             Enrolled
Sentry                   Aware
Daily Journal           Off / Configured
OSCAR Mobile assistant role    Selected / Not available / Not configured
Orb overlay              Verified / Off
Notifications            Allowed / Limited / Off
Schedule automation      Suggest-only / Policy-scoped
Desktop                  Optional / Connected
Edge                     Optional / Connected
```

Never show `Ready` for something that was not actually tested.
