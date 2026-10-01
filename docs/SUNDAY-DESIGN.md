# Sunday visual direction

Sunday is OSCAR on the phone. This document captures the durable mobile interaction direction; `DESIGN.md` is the global design system and `TASTE.md` is the qualitative quality bar.

## Surface mode

**Present, not launched.** Sunday should feel like the phone embodiment of an intelligence that is already there. It must help the user speak, type, understand OSCAR's current state, approve actions, supervise remote work and receive meaningful proactive information without looking like a chatbot or productivity dashboard.

## Direction contract

**THESIS — Quietly Alive.** Sunday is sparse, warm and responsive. Its character comes from OSCAR's weighted physical presence, fluid state transitions and immediate response. It refuses transcript-first chat, giant microphone CTAs, card walls and generic AI ornament.

**PLAYFUL PRECISION.** Use broad whitespace, editorial hierarchy and minimal chrome, with precise tactile controls and state-driven motion. Personality is approachable but never cute-first.

**MATERIAL.** Warm cream/off-white canvas, graphite/near-black typography, OSCAR blue/yellow identity, minimal red expression marks, restrained muted-orange warning cues, subtle natural depth and line iconography. Blue is presence, not the default color for every action.

**STORY.** At a glance the user should understand whether OSCAR is present, acoustically aware, actively listening, working, verifying, waiting, blocked, muted, degraded or offline — without confusing those states.

**FORM.** Native Android/mobile composition, not a responsive desktop/web layout placed in a phone frame. Use sheets, notifications, platform permission patterns and thumb-reachable controls when useful. Avoid permanent navigation unless real information architecture requires it.

## The first viewport

The first viewport should answer only a few questions:

1. Is OSCAR present and healthy?
2. Does anything actually need my attention?
3. What meaningful thing is happening, if any?
4. How do I naturally continue by voice or text?

Do not fill the viewport just because OSCAR has many capabilities.

## Presence and acoustic state model

Sunday must not reduce voice to `Talk to OSCAR` versus `Type instead`.

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

## Primary surfaces

### Home / present

Purpose: communicate presence and what matters now.

- OSCAR presence visible but not half the screen;
- one concise greeting/state;
- at most one meaningful active/background item by default;
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

### Sentry / awareness

Purpose: explain what OSCAR is aware of without surveillance aesthetics.

- calm composition;
- modes shown only when useful;
- distinguish awareness from transcription/recording;
- show only meaningful events by default;
- evidence/source and privacy controls one layer deeper.

### Continuity Capture / Daily Journal

When explicitly enabled, Sunday should make selected capture sources and retention understandable without turning into a recorder app.

Show:

- current capture level: `Awareness only`, `Context capture` or `Daily journal`;
- source availability for calls/messages/email/meetings/in-person conversation;
- what is being retained: raw audio / transcript / summary / memory;
- quick `Pause capture`;
- delete/forget/source-exclusion controls;
- clear unavailable/unsupported source states.

The UI must never suggest covert recording or hide active capture state.

### Connection Grid

Sunday is the preferred owner control surface.

The normal Grid view should stay compact:

```text
Sunday        Here
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
- no fake listening waveform.

### Offline / degraded

- preserve calm identity;
- say which capability disappeared;
- show what still works;
- use Connection Grid availability semantics where useful (`Local`, `Connected`, etc.);
- avoid stacked banners/modals.

## Remote task continuation

Sunday should make it ordinary to walk away from a computer while work continues.

```text
Desktop task running
→ user leaves with Sunday
→ Sunday shows current state/executor
→ approve / pause / cancel / inspect remotely
→ task finishes
→ OSCAR verifies result where possible
→ optional machine sleep/shutdown if policy/capability permits
```

Do not make this look like a separate remote-desktop product.

## Navigation

Do not assume a standard `Home / Work / History` assistant app.

Likely deeper destinations may include current work, history/memory, Workers/Protocols, Sentry/Journal, Connection Grid/devices, Persona and settings/privacy, but normal use should remain presence-first and context-driven.

## Interaction surface

Voice and text are peers.

Avoid a permanent giant microphone button or generic search-bar clone.

A good interaction surface remains compact while idle, opens for text when focused, reacts to wake/listening in-place, morphs into live audio/transcript only during the turn, then resolves back into presence/task state.

## Fluid motion

Sunday should feel alive through **continuous state transformation**, not decorative animation.

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
- neutral face by default;
- minimal expression marks;
- serious/Sentry states reduce playfulness;
- Persona may subtly change acknowledgement style but not runtime truth.

## Native behavior

- Android-native navigation/sheets/text entry/permissions/biometric patterns;
- safe areas/keyboard/insets/one-handed reach;
- haptics for meaningful state changes;
- never a web view pretending to be native;
- accessibility and reduced motion are product requirements.

## Robustness cases

Check Sunday against:

- no tasks;
- many background tasks with only the relevant one surfaced;
- long text;
- microphone unavailable;
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
- hidden/ambiguous recording state;
- network-admin Connection Grid;
- LLM-parameter Persona UI;
- static screens with motion sprinkled on later;
- success styling before verification.
