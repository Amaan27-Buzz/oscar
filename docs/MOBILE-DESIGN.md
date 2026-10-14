# OSCAR Mobile visual direction

## Current Group 2.5B direction — 2026-10-14

**Status: design exploration, not final production Mobile UI approval.** [Desktop Group 2.5A](../docs/PRODUCT-DIRECTION.md) received interim owner approval and merged into `main`. OSCAR Mobile should use the shared character and a coherent **restrained neumorphic** material language, but remain a genuinely native Compose experience rather than a narrow Desktop replica.

The owner is exploring **15 independent key screens, one palette/typography/illustration design board and five reusable component boards**, alongside a **separate complete UI-only Kotlin/Jetpack Compose prototype** in `oscar-ui-test` outside this repository. The broader 56-experience inventory is an information architecture, not 56 new production destinations or verified capabilities. Original feature-specific illustrations, expressive typography, varied compositions, warm cream/graphite, blue/yellow Orb identity, restrained raised/inset tactile controls, coherent dark mode and legibility/accessibility take priority over card walls or generic chat layouts. Keep `assets/brand/oscar-orb.svg` unchanged. Static designs/standalone prototype remain concept/demo material until approved and deliberately integrated into `mobile/` with real Core-bound behavior.

Mobile and Desktop offer the same OSCAR Core capabilities with platform-specific emphases: mobile prioritizes portable presence, permissions, notifications, remote decisions, Sentry and Chief-of-Staff presentation; Desktop prioritizes deep work and computer execution. Conversation is continuous; Text Tools/Act are contextual abilities, not app destinations. Automations, Activity, Devices and Preferences are logical areas, with native navigation decided by usability. Secure/Full Access, real Sentry and persistent Worker runtime are unavailable pending backend slices; prototype controls must not imply activation. **Adaptive UI is later Slice 16/17/19/20 work**, not a requirement for this visual mockup; see [AIE](ADAPTIVE-INTERFACE.md) and [active product direction](PRODUCT-DIRECTION.md).

## Current Mobile design sequencing

The Mobile functional foundation is **Slice 09**. Final Mobile UX redesign
is **Slice 13**, after reviewed **Slice 11 Expression/Character System**,
using a shared operational-state vocabulary with Desktop Slice 12.
Full cross-device Presence is Slice 16. Historical `09R` identifiers are
retained only in earlier artifacts; see [slice numbering](SLICE-NUMBERING.md).

The previous static smiling Orb on beige card experiments are not the design
target. OSCAR should have nonverbal reactions, expressive timing, attention
and meaningful gestures while remaining technically restrained. On Android,
build a dedicated native Compose renderer rather than importing desktop UI
frames. Do not copy the small reference companion mascot or infer task truth,
human emotion, microphone availability or permissions from expression.



OSCAR Mobile is OSCAR on the phone. This document captures the durable mobile interaction direction; `DESIGN.md` is the global design system and `TASTE.md` is the qualitative quality bar.

## Surface mode

**Present, not launched.** OSCAR Mobile should feel like the phone embodiment of an intelligence that is already there. It must help the user speak, type, understand OSCAR's current state, approve actions, supervise remote work and receive meaningful proactive information without looking like a chatbot or productivity dashboard.

OSCAR Mobile is also the strongest everyday **Chief-of-Staff surface**: current schedule, tasks, weather, notifications, communications and active work should converge into one calm answer to `what needs me now?` rather than forcing the user to manually reconcile separate apps.

See `CHIEF-OF-STAFF.md`.

## Direction contract

**THESIS — Quietly Alive.** OSCAR Mobile is expressive, warm and responsive. Its character comes from OSCAR's weighted physical presence, original illustration-led composition, restrained neumorphic depth, fluid state transitions and immediate response. It refuses chat-thread management, giant microphone CTAs, card walls and generic AI ornament.

**PLAYFUL PRECISION.** Use broad whitespace, editorial hierarchy and minimal chrome, with precise tactile controls and state-driven motion. Personality is approachable but never cute-first.

**MATERIAL.** Warm cream/off-white canvas, graphite/near-black typography, OSCAR blue/yellow identity, minimal red expression marks, restrained muted-orange warning cues, subtle natural depth and line iconography. Blue is presence, not the default color for every action.

**STORY.** At a glance the user should understand whether OSCAR is present, acoustically aware, actively listening, working, verifying, waiting, blocked, muted, degraded or offline — without confusing those states.

**FORM.** Native Android/mobile composition, not a responsive desktop/web layout placed in a phone frame. Use sheets, notifications, platform permission patterns and thumb-reachable controls when useful. Avoid permanent navigation unless real information architecture requires it.

## Android system presence

### Future direction reaffirmed — documentation only, 2026-10-04

The local Club B pass does not implement OSCAR Mobile/voice/UI or advance Slice 07.
Future OSCAR Mobile acceptance must distinguish four independent controls:

| Control | Meaning | Does not grant |
|---|---|---|
| Presence | Selected `ROLE_ASSISTANT`/`VoiceInteractionService`, optional Orb and widgets | Context access, retention or action authority |
| Context awareness | Permissioned time/date/weather/calendar/tasks/device/notification signals feeding World Model | Retention or mutation authority |
| Retention | Explicit source/app/person-scoped storage and forget policy | Authority to send or edit |
| Authority to act | Scoped owner-controlled calendar/task updates and legitimate notification `RemoteInput` replies | Missing OS/provider capability or unrelated permissions |

The Orb is normally visible, retreats/hides for video/reading/presentation/focus,
retains a supported hidden edge/hotspot invocation and reappears naturally after
the attention context ends. Configurable home-screen widgets surface current
time/date/weather/calendar/tasks/device context without fabricating unavailable
sources. Notification-listener summaries require permission, with sensitive-content
controls by source/app/person; reply requires a real exposed action. Prefer official
connectors/APIs to UI automation. Chief-of-Staff schedule conflicts and replanning
consume freshness-qualified World Model state; automatic calendar/task changes
remain owner-controlled and independently verified.

Quick controls must independently pause awareness, disable overlay, disable a
notification source, exclude a person/app and forget retained context. No Android
or OEM behavior is verified by this Windows pass. All assistant/overlay/hotspot/
widget/notification/reply behavior remains untested on the actual Samsung phone.

OSCAR Mobile should integrate with Android through legitimate platform capabilities instead of visually pretending to be a system assistant.

Target direction, subject to Android/OEM support and explicit user choice:

- qualify for the Android assistant role where available;
- implement the appropriate `VoiceInteractionService` / voice-interaction session architecture for selected-assistant behavior;
- keep the persistent service path lightweight and move heavyweight UI/work out of it;
- support system assistant invocation gestures where the device exposes them;
- treat OEM-specific behavior as unverified until tested on the actual phone.

Being selected as the phone assistant does not grant unrelated permissions automatically. Notification access, microphone/camera/location, overlay, communication actions, retention and owner-critical authority remain separately controlled.

## The OSCAR Orb overlay

OSCAR Mobile may expose the OSCAR Orb above other apps through Android's legitimate application-overlay mechanism when the user explicitly grants that permission.

The Orb should feel **available, not intrusive**.

Conceptual behavior:

```text
ordinary use
→ compact Orb visible

video / reading / presentation / focused content
→ Orb retreats to an edge anchor or hidden hotspot

user invokes by assistant gesture / edge target / Orb / voice
→ Orb returns immediately

focus context ends
→ Orb may reappear naturally according to policy
```

Important rules:

- do not cover important content merely to prove OSCAR is `always there`;
- overlay visibility is best-effort UI, never a correctness dependency;
- Android may reposition/change overlay visibility for system reasons;
- hiding the visual Orb does not imply OSCAR's entire runtime or Sentry is off;
- a visible Orb does not imply microphone capture is active;
- manual `hide Orb`, `show Orb`, `stay hidden here` and app-specific policies should exist;
- reduced-motion and accessibility paths must preserve invocation.

Attention-aware retreat should use current evidence such as active media, presentation/focus state or explicit policy. Weak evidence should not become confident assumptions about what the user is doing.

## Home-screen widgets

OSCAR Mobile should support configurable Android widgets with genuinely glanceable information and direct actions.

Potential widget families:

- **Presence** — compact OSCAR state / tap to invoke;
- **Next** — next commitment, buffer/travel warning and meaningful conflict;
- **Focus** — current priority/task block and quick defer/complete controls;
- **Work** — one active Worker/remote task with verified state;
- **Grid** — compact OSCAR Mobile/Cloud/Desktop/Edge health;
- **Privacy** — Sentry/capture/Orb state and quick pause;
- **Brief** — morning/day summary or `what needs me now?`.

Widgets can have small/medium/large layouts but should not become miniature dashboards. They should restore from durable/current state rather than depending on fragile in-memory process state.

## The first viewport

The first viewport should answer only a few questions:

1. Is OSCAR present and healthy?
2. Does anything actually need my attention?
3. What meaningful thing is happening, if any?
4. What is the next commitment/risk if it matters?
5. How do I naturally continue by voice or text?

Do not fill the viewport just because OSCAR has many capabilities.

A useful home state may quietly combine calendar/tasks/weather/notifications/current work, but only surface the conclusion that matters. Example: `Leave by 9:20 · rain likely · assignment block moved to 4:30` is better than four disconnected cards when those facts are verified and the schedule change is authorized.

## Presence and acoustic state model

OSCAR Mobile must not reduce voice to `Talk to OSCAR` versus `Type instead`.

### Sentry aware

Local low-cost acoustic awareness may be active for wake/VAD/hot commands/Voice Map/sound events while no active conversation transcript exists.

### Listening

A conversational turn is active and speech recognition is running.

### Muted

Normal conversational listening is disabled. Permitted safety/reflex/hot commands may remain locally available according to policy.

### Acoustic awareness disabled

The local acoustic plane itself is disabled. This is stronger than ordinary mute.

### Typing

Typing is another input modality in the same OSCAR context and does not automatically disable Sentry.

## Notification awareness

When the user explicitly grants Android notification-listener access, OSCAR Mobile can ingest the notification events/content Android legitimately exposes into the Perception Fabric.

This should support:

- `what did I miss?` summaries;
- urgency/importance triage;
- linking notifications to people/projects/tasks;
- schedule/deadline-change detection;
- attention/interruption decisions;
- selected notification-driven actions when a real action exists.

Keep these boundaries explicit:

```text
can observe notification
≠ can retain notification content
≠ can reply
≠ has unrestricted access to the source app
```

Source/app/person exclusions are first-class. Banking/security/OTP/password-like content should not become durable memory by default.

## Notification replies

When a notification exposes a legitimate Android reply action/`RemoteInput`, OSCAR Mobile may use that action for a user-approved or policy-authorized reply.

If no reply action exists, OSCAR Mobile must use another legitimate connector/API/device capability or report direct reply unavailable. Do not fabricate WhatsApp/Signal/other app write access from notification visibility.

Drafting and sending remain separate states. A send attempt is not verified delivery unless authoritative evidence supports it.

## Primary surfaces

### Home / present

Purpose: communicate presence and what matters now.

- OSCAR presence visible but not half the screen;
- one concise greeting/state;
- at most one meaningful active/background item by default;
- next commitment/risk only when materially useful;
- if nothing matters, say so simply;
- voice/text interaction without a giant CTA;
- small Sentry/acoustic state contextually available;
- secondary navigation nearly disappears until needed.

### Listening

- transition from existing home geometry;
- OSCAR reacts before cloud reasoning;
- waveform/levels only while real audio is active;
- stop/cancel/barge-in obvious and thumb-friendly;
- transcript may appear progressively but is not the hero.

### Thinking / Working / Verifying

- show actual runtime state rather than spinner theatre;
- task detail one layer deeper;
- avatar motion becomes more deliberate;
- never show `Working` when blocked/disconnected;
- `Verifying` is distinct from executor completion;
- completion styling only after evidence supports it.

### Speaking

- subtle cadence response;
- human barge-in interrupts immediately;
- listening grows naturally from speaking rather than resetting the page.

### Chief-of-Staff brief

Purpose: answer `what needs me now?` from authorized current context.

Potential content:

- next fixed commitment;
- meaningful schedule conflict/risk;
- top task/deadline;
- pending communication requiring a decision;
- one relevant weather/travel factor;
- active Worker result/blocker;
- actions OSCAR already took under policy, with evidence/undo where real.

Avoid generic agenda dumps. Prefer decisions and exceptions over exhaustive feeds.

### Sentry / awareness

Purpose: explain what OSCAR is aware of without surveillance aesthetics.

- calm composition;
- modes shown only when useful;
- distinguish awareness from transcription/recording;
- show only meaningful events by default;
- evidence/source and privacy controls one layer deeper.

### Continuity Capture / Daily Journal

When explicitly enabled, OSCAR Mobile should make selected capture sources and retention understandable without turning into a recorder app.

Show:

- current capture level: `Awareness only`, `Context capture` or `Daily journal`;
- source availability for calls/messages/email/meetings/in-person conversation;
- what is being retained: raw audio / transcript / summary / memory;
- quick `Pause capture`;
- delete/forget/source-exclusion controls;
- clear unavailable/unsupported source states.

The UI must never suggest covert recording or hide active capture state.

### Schedule / commitments

The schedule surface should distinguish:

- fixed events;
- flexible blocks;
- tasks/deadlines;
- preparation/travel buffers;
- tentative/awaiting-confirmation commitments;
- communication follow-ups;
- Worker/Protocol dependencies.

The user should be able to say `move the flexible stuff`, `protect two hours for this`, `don't touch class`, `tell me what changed`, or `undo the reschedule` where a real compensation path exists.

### Connection Grid

OSCAR Mobile is the preferred owner control surface.

The normal Grid view should stay compact:

```text
OSCAR Mobile        Here
Cloud         Healthy
Desktop       Working · 1 task
Desk Edge     Aware
```

Deeper node view may expose:

- current task ownership;
- actual advertised capabilities;
- health;
- pause/cancel/revoke;
- remote sleep/shutdown if genuinely supported;
- Wake-on-LAN only when a real wake path exists.

Avoid network-admin UI.

### Persona

Persona should feel like shaping OSCAR's character, not configuring model parameters.

Offer:

- natural-language editing;
- a few core controls such as Humor, Candor, Warmth, Formality, Brevity and Initiative;
- context rules such as `university call → formal, no humor`;
- live text/voice/motion preview;
- fixed/non-configurable truthfulness and safety.

See `PERSONA.md`.

### Muted / private

- reduce motion immediately;
- label actual privacy/listening state clearly;
- distinguish mute from awareness fully disabled;
- no fake listening waveform;
- fast toggles for notification awareness, Orb overlay and capture where appropriate.

### Offline / degraded

- preserve calm identity;
- say which capability disappeared;
- show what still works;
- use Connection Grid availability semantics where useful (`Local`, `Connected`, etc.);
- avoid stacked banners/modals.

## Remote task continuation

OSCAR Mobile should make it ordinary to walk away from a computer while work continues.

```text
Desktop task running
→ user leaves with OSCAR Mobile
→ OSCAR Mobile shows current state/executor
→ approve / pause / cancel / inspect remotely
→ task finishes
→ OSCAR verifies result where possible
→ optional machine sleep/shutdown if policy/capability permits
```

Do not make this look like a separate remote-desktop product.

## Navigation

Do not assume a standard `Home / Work / History` assistant app.

Likely deeper destinations may include current work, schedule/commitments, history/memory, Workers/Protocols, Sentry/Journal, Connection Grid/devices, Persona and settings/privacy, but normal use should remain presence-first and context-driven.

## Interaction surface

Voice and text are peers.

Avoid a permanent giant microphone button or generic search-bar clone.

A good interaction surface remains compact while idle, opens for text when focused, reacts to wake/listening in-place, morphs into live audio/transcript only during the turn, then resolves back into presence/task state.

## Fluid motion

OSCAR Mobile should feel alive through **continuous state transformation**, not decorative animation.

> State A should physically become State B where practical.

Use shared elements, geometry morphing, weighted springs, gesture-linked motion, contextual expansion, content choreography and velocity continuity.

Avoid generic page fades, particles, bouncing controls and animation that delays input.

Typical UI transitions begin within 120–220 ms. Avatar/physical motion may settle over 180–450 ms depending on meaning/distance.

Respect reduced motion and keep all semantics usable without animation.

## Avatar behavior

The avatar is a **presence object**, not the whole product.

- small/medium in ordinary home states;
- larger only when a dedicated interaction earns it;
- puck position/weight before facial expression;
- [canonical Orb appearance](../assets/brand/oscar-orb.svg) by default;
- minimal expression marks;
- serious/Sentry states reduce playfulness;
- Persona may subtly change acknowledgement style but not runtime truth.

The overlay Orb and in-app avatar are the same identity language but can use different scale/interaction constraints.

## Native behavior

- Android-native navigation/sheets/text entry/permissions/biometric patterns;
- assistant-role/voice-interaction integration only through supported Android contracts;
- application overlay only after explicit overlay permission;
- notification listener only after explicit notification access;
- Glance/AppWidget-style home widgets where appropriate;
- active media session can contribute an attention signal when legitimately available;
- safe areas/keyboard/insets/one-handed reach;
- haptics for meaningful state changes;
- never a web view pretending to be native;
- accessibility and reduced motion are product requirements.

## Robustness cases

Check OSCAR Mobile against:

- no tasks;
- many background tasks with only the relevant one surfaced;
- conflicting calendar/task commitments;
- stale weather/calendar context;
- long text;
- microphone unavailable;
- notification access denied/revoked;
- overlay permission denied/revoked;
- assistant role unavailable/not selected;
- notification with and without a reply action;
- active video/media while Orb is visible;
- cloud coordinator unavailable;
- desktop/Edge offline;
- Sentry unavailable;
- active capture source unavailable;
- task running while an alert arrives;
- rapid voice/text switching;
- Persona context change mid-session;
- blocked/partial/unknown verification;
- reduced motion.

The UI should degrade calmly instead of collapsing into error chrome.

## Design-development workflow

Use Kaizen:

```text
study real shipping mobile patterns
→ build one real surface
→ inspect on target viewport/device
→ identify largest weakness
→ improve it
→ verify again
→ expand only when the pattern survives
```

Appllama/App Design research and Impeccable critique may support this workflow but are not runtime dependencies.

Prefer coded UI once the direction is promising. Static image generation is reference/asset support, not the product source of truth.

## Anti-patterns

Reject designs that drift toward:

- chatbot landing pages;
- giant `Talk to OSCAR` / `Type instead` forks;
- mascot posters;
- generic bottom navigation without proven IA;
- card walls;
- blue CTA buttons everywhere;
- glass/gradient AI styling;
- surveillance-dashboard Sentry;
- permanent intrusive chat-head behavior;
- widgets that become miniature dashboards;
- notification access presented as unrestricted app access;
- hidden/ambiguous recording state;
- network-admin Connection Grid;
- LLM-parameter Persona UI;
- static screens with motion sprinkled on later;
- success styling before verification.
