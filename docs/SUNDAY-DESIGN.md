# Sunday visual direction

Sunday is OSCAR on the phone. This document captures the durable mobile interaction direction; `DESIGN.md` is the global design system and `TASTE.md` is the qualitative quality bar.

## Surface mode

**Present, not launched.** Sunday should feel like the phone embodiment of an intelligence that is already there. It must help the user speak, type, understand OSCAR's current state, approve actions and receive meaningful proactive information without looking like a chatbot or productivity dashboard.

## Direction contract

**THESIS — Quietly Alive.** Sunday is sparse, warm and responsive. Its character comes from OSCAR's weighted physical presence, fluid state transitions and immediate response. It refuses transcript-first chat, giant microphone CTAs, card walls and generic AI ornament.

**PLAYFUL PRECISION.** Use broad whitespace, editorial hierarchy and minimal chrome, with precise tactile controls and state-driven motion. Personality is approachable but never cute-first.

**MATERIAL.** Warm cream/off-white canvas, graphite/near-black typography, OSCAR blue/yellow identity, minimal red expression marks, restrained muted-orange warning cues, subtle natural depth and line iconography. Blue is presence, not the default color for every action.

**STORY.** At a glance the user should understand whether OSCAR is present, acoustically aware, actively listening, working, verifying, waiting, blocked, muted or offline — without confusing these states.

**FORM.** Native Android/mobile composition, not a responsive desktop/web layout placed in a phone frame. Use sheets, notifications, platform permission patterns and thumb-reachable controls when useful. Avoid permanent navigation unless real information architecture requires it.

## The first viewport

The first viewport should answer only a few questions:

1. Is OSCAR present and healthy?
2. Does anything actually need my attention?
3. What meaningful thing is happening, if any?
4. How do I naturally continue by voice or text?

Do not fill the viewport just because OSCAR has many capabilities.

A calm state may legitimately be almost empty, but the composition must still feel intentional rather than unfinished.

## Presence and acoustic state model

Sunday must not reduce voice to `Talk to OSCAR` versus `Type instead`.

### Sentry aware

Local low-cost acoustic awareness may be active for:

- wake word;
- VAD / speech presence;
- deterministic hot/reflex commands;
- Voice Map events;
- configured sound events;
- barge-in while OSCAR is speaking.

This is **not** the same as cloud STT or continuous transcription.

### Listening

A conversational turn is active and speech recognition is running. This is an explicit active state.

### Muted

Normal conversational listening is disabled. Permitted safety/reflex/hot commands may remain locally available according to policy. The UI must not imply complete hardware microphone shutdown unless that is actually true.

### Acoustic awareness disabled

Local acoustic processing is genuinely disabled. This is a stronger privacy state than ordinary mute and must be presented distinctly.

### Typing

Typing is another input modality into the same OSCAR context. Choosing text does not turn Sentry or the voice architecture off.

## Primary surfaces

### Home / present

Purpose: communicate presence and what matters now.

- OSCAR presence should be visible but not dominate half the screen;
- one concise state or greeting is enough;
- surface at most one meaningful active/background item by default;
- if nothing matters, say so simply;
- voice/text interaction should be available without a giant `Talk to OSCAR` CTA;
- a small acoustic/Sentry state can be available contextually;
- secondary navigation should nearly disappear until needed.

Do not use unrelated project names as placeholder content in design exploration.

### Listening

- transition immediately from the existing home/presence geometry;
- OSCAR should react before cloud reasoning begins;
- waveform/levels only while real audio is active;
- stop/cancel/barge-in are obvious and thumb-friendly;
- transcript may appear progressively but is not the hero;
- do not replace the whole screen with a generic listening poster.

### Thinking / working

- show the real runtime state rather than a spinner;
- use concise language such as `Looking into it`, `Running a task`, `Waiting for approval`, `Verifying`;
- keep task detail one layer deeper;
- the avatar/object becomes more deliberate and less playful;
- never display `Working` if the task is actually blocked or disconnected.

### Verifying

Verification is a first-class visual state distinct from execution.

- tighter/more deliberate motion;
- evidence/result detail available on demand;
- do not show celebratory completion until verification is actually satisfied where applicable.

### Speaking

- subtle cadence response only;
- no literal mouth animation unless it reaches the product quality bar;
- human speech/barge-in interrupts immediately;
- the listening state should grow naturally from the speaking state rather than resetting the whole layout.

### Sentry / awareness

Purpose: explain what OSCAR is aware of without becoming surveillance software.

- calm composition;
- show active mode (`Passive`, `Aware`, `Guard`, `Away`, `Sleep`) only when useful;
- distinguish local awareness from transcription/recording;
- show only meaningful events by default;
- allow the user to inspect what OSCAR is aware of and why;
- expose privacy/retention controls one layer deeper;
- use stronger confirmation for sensitive configuration changes where policy requires it.

### Muted / private

- reduce motion immediately;
- label the actual privacy/listening state clearly;
- do not show fake waveform/listening animation;
- distinguish ordinary mute from acoustic awareness fully disabled.

### Offline / degraded

- preserve the calm visual identity;
- say which capability disappeared rather than throwing a generic error page;
- keep local/reflex functionality visible if it still works;
- avoid stacking banners/modals.

## Navigation

Do not assume `Home / Work / History` or a four-tab assistant app.

Navigation should emerge from real product use. Likely deeper destinations may include:

- current work / tasks;
- history/memory search;
- Workers/Protocols;
- Sentry/environment;
- devices/capabilities;
- settings/privacy.

But normal Sunday use should remain presence-first and context-driven. OSCAR's continuous LRA history must not regress into a chat-list product.

## Interaction surface

Voice and text are peers in one continuous context.

Avoid a permanent giant microphone button or search-bar clone.

A good interaction surface may:

- remain compact while idle;
- reveal text input when focused;
- react to wake/listening without replacing the whole page;
- morph into live audio/transcript only during an active turn;
- collapse back into presence after the turn resolves.

The exact component should be discovered through implementation and visual iteration, not frozen by a static mockup.

## Fluid motion

Sunday should feel alive through **continuous state transformation**, not decorative animation.

Core rule:

> State A should physically become State B where practical.

Examples:

```text
present
→ wake detected
→ OSCAR shifts toward attention
→ existing interaction region opens into Listening
→ utterance becomes task state
→ Working becomes Verifying
→ result resolves into the same spatial system
```

Use:

- shared elements;
- geometry morphing;
- weighted springs;
- gesture-linked movement;
- contextual expansion;
- content choreography;
- velocity continuity.

Avoid generic page fades, bouncing controls, particles and motion that delays input.

Typical UI transitions should begin within 120–220 ms. Avatar/physical movement may settle over 180–450 ms depending on meaning and distance.

Respect reduced motion and keep the UI completely usable when motion is disabled.

## Avatar behavior on Sunday

The avatar is a **presence object**, not the whole product.

- small/medium in everyday home states;
- larger only when a dedicated interaction moment earns it;
- position/weight before facial expression;
- neutral face by default;
- expression marks minimal;
- serious states reduce animation amplitude;
- notification/icon variants preserve recognizable identity without toy-like rendering.

## Native behavior

- use Android-native navigation, sheets, text entry, permissions and biometric confirmation where appropriate;
- respect safe areas, keyboard/inset behavior and one-handed reach;
- use haptics to reinforce wake, confirmation and meaningful transitions;
- do not build Sunday as a web view with mobile dimensions;
- accessibility and reduced-motion support are part of the product, not polish.

## Robustness cases

Every Sunday surface should be checked against:

- no current tasks;
- many background tasks while only the most relevant is surfaced;
- long task/title text;
- microphone unavailable;
- network/provider unavailable;
- desktop/Edge offline;
- Sentry unavailable;
- OSCAR working and an alert arriving simultaneously;
- rapid switching between voice and text;
- blocked, partial and unknown verification;
- reduced motion.

The UI should degrade calmly instead of collapsing into error chrome.

## Design-development workflow

Do not design the entire Sunday app in one pass.

Use Kaizen:

```text
study real shipping mobile patterns
→ build one real surface
→ inspect on target viewport/device
→ identify the largest visual/interaction weakness
→ improve it
→ verify again
→ expand only after the pattern survives
```

When available, use Appllama MCP/App Design Skill for research into real shipping mobile patterns and Impeccable for critique. Neither is a product/runtime dependency.

Prefer coded UI once the direction is promising. Static image generation may support original assets, but should not become the source of truth for the whole interface.

## Anti-patterns

Reject Sunday designs that drift toward:

- chatbot landing pages;
- giant `Talk to OSCAR` / `Type instead` choices;
- giant greetings or mascot-centered poster layouts;
- generic bottom navigation without proven IA;
- card walls;
- blue CTA buttons everywhere;
- glass/gradient AI styling;
- low-information screens whose whitespace is accidental;
- surveillance/security-dashboard Sentry;
- static screens with motion added only at the end;
- unrelated personal projects as sample content;
- success styling before verification.
