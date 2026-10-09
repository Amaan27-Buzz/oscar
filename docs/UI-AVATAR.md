# Avatar + Interaction Language

## Current character-design contract — Slice 11

This document is the durable design intent; [Slice 11 Expression/Character
System](EXPRESSION-CORE.md) owns the current detailed character vocabulary,
interactive Expression Lab and shared renderer contract. Next design stages
are **11.1 character language → 11.2 interactive lab → owner review → 11.3
shared rendering**, then **12 Desktop UX / 13 Mobile UX**. Full state-aware
cross-device Presence is Slice 16.

The old desktop compact A/B/C exercises are *not* accepted art: all three
reused essentially one static smiling face and generic beige widgets. The
owner expects a genuinely responsive character with nuanced eye/gaze timing,
asymmetry, weight, anticipation, microreaction, rest/idle, interruptions and
perceptual continuity. The companion reference images show expressive
presence, not an alternate mascot to copy. Study character **before**
polishing frame/card/window treatments. Reject emoji faces and cosmetic
looping animations.

The canonical `assets/brand/oscar-orb.svg` must not be overwritten;
derived expressions must be separately versioned and visually owner-reviewed.
Only authoritative operational state controls truth/safety/approval; delivery
cues never infer user emotion or verified outcome. See
[canonical numbering](SLICE-NUMBERING.md).



## Identity

OSCAR's avatar is a core interaction surface, not decorative branding and not a mascot that should dominate every screen.

The visual identity consists of:

- a blue outer body/shell;
- a yellow circular face/puck inside it;
- minimal red facial marks;
- simple geometry that works from app-icon size to larger voice/presence surfaces.

The avatar should communicate attention and runtime state primarily through **position, weighting, motion and restraint**, with expression as a secondary cue.

## Presence object, not mascot

The avatar should feel like a small precision physical/digital object.

Good qualities:

- satin/soft material impression;
- precise circular geometry;
- believable contact/depth relationship between shell and puck;
- controlled highlights/shadows;
- small-to-medium scale in ordinary UI;
- very limited facial marks.

Avoid:

- giant centered mascot compositions;
- toy-like glossy 3D rendering;
- independently invented facial geometry that changes the canonical Orb identity;
- emoji-like expressions;
- making the avatar the only source of hierarchy or meaning.

The product must remain useful and composed even when the avatar is rendered very small.

## Primary motion concept

The yellow face moves inside the blue shell like a **weighted magnetic puck / joystick head**.

Motion characteristics:

- responsive but not twitchy;
- believable inertia;
- soft spring;
- slight overshoot;
- controlled settling;
- directional attention;
- lower amplitude during serious/focused work;
- no random motion merely to look alive.

The puck should feel as though it has mass and a preferred resting position.

## Continuous-interface role

The avatar should help preserve spatial/state continuity across interactions.

Example:

```text
Present
→ wake detected
→ puck shifts toward attention
→ nearby interaction surface opens
→ Listening
→ Working
→ Verifying
→ resolved result
```

Where practical, the same object should persist across these transformations rather than disappear and reappear in unrelated page layouts.

On desktop, a compact OSCAR presence can expand into a contextual overlay from its actual origin. On OSCAR Mobile, the presence object can recompose with the current interaction instead of requiring a full-screen mode switch.

## State language

| State | Expression / motion direction |
|---|---|
| Idle / Present | canonical Orb appearance; almost still; subtle settling only |
| Wake acknowledgement | quick focused shift toward input/source |
| Sentry aware | stable, watchful orientation; low-amplitude motion |
| Listening | focused orientation/tension toward active input; no fake waveform when audio is inactive |
| Thinking / Working | deliberate measured movement; no generic spinner dependency |
| Verifying | tighter, more precise movement; restrained expression |
| Waiting | relaxed/suspended posture; no fake busy animation |
| Speaking | light cadence response; preserve barge-in readiness |
| Done / Verified | brief calm resolution only after verification where applicable |
| Partially verified | unresolved/contained posture; no success flourish |
| Blocked | visibly constrained/still; never presented as `Working` |
| Confused / Unknown | small offset/tilt; uncertainty without comedy |
| Alert | immediate focused posture; minimal playful movement |
| Sleep | reduced brightness/activity while permitted reflex/safety awareness may remain |
| Muted | immediate reduction of conversational-listening motion; clear state label/icon |
| Acoustic awareness disabled | stronger privacy/off state distinct from ordinary mute |
| Error | clear but calm failure state; avoid alarming animation for recoverable errors |
| Offline | stable unavailable/degraded cue without implying complete OSCAR absence if other surfaces remain |

## Default expression

The standard idle appearance uses the canonical Orb source, including its curved wink.

Additional animated expressions can appear as a brief acknowledgement or earned
personality beat, derived from the canonical source. Credibility during serious
work, safety, Sentry and verification comes from truthful state and restrained
motion; the source artwork must not be silently replaced or redrawn.

## Serious mode

OSCAR becomes more serious by **reducing** expressive motion, not by changing identity.

In alert, security, safety, verification or focused-work contexts:

- reduce animation amplitude;
- center/steady the yellow puck;
- use cleaner expression marks;
- suppress playful secondary movement;
- prioritize information hierarchy and state truth.

## Voice choreography

Avatar state must be driven by real system state:

```text
wake/reflex detected         → acknowledge
Sentry local awareness only  → aware, not Listening
conversational STT active    → Listening
intent resolved              → transition to task state
model/tool execution         → Working
objective/result check       → Verifying
verification satisfied       → Done/Verified
blocked dependency           → Blocked
TTS active                   → Speaking
barge-in                     → Speaking stops → Listening
Sentry meaningful event      → Sentry/Alert
```

The avatar must never display `Thinking`, `Working` or `Done` when OSCAR is actually blocked, failed, partially verified or merely waiting.

## Sentry / mute semantics

The avatar must not conflate microphone/privacy states.

- `Sentry aware` may mean local wake/VAD/hot-command/Voice Map/sound-event processing is active.
- `Listening` means an active conversational turn/STT.
- `Muted` means ordinary conversational listening is disabled, while permitted local safety/reflex commands may remain.
- `Acoustic awareness disabled` means the local acoustic plane is actually off.

Critical privacy states must always have a text/icon cue in addition to expression/motion.

## OSCAR Mobile

On OSCAR Mobile, the avatar is a recurring presence rather than a full-screen mascot.

Expected uses:

- home/presence;
- voice session;
- listening indicator;
- proactive notification identity;
- Sentry state;
- onboarding/calibration;
- compact system/notification variants where Android permits.

Scale and motion should adapt to current task, display size, battery/power state and reduced-motion preference.

## Desktop

On desktop, OSCAR may begin as a compact presence and expand into contextual UI.

The avatar/object should maintain spatial continuity when possible:

```text
compact presence
→ contextual overlay
→ task/progress state
→ verified result
→ compact presence
```

Do not make every desktop interaction open a separate unrelated assistant window.

## Desk / physical surfaces

On small OLED/TFT/LED hardware, preserve the same state language even if the full artwork cannot be rendered.

Examples:

- simplified eyes/face;
- directional puck/offset representation;
- status light patterns where a screen is unavailable;
- shared state names across hardware and software.

Hardware safety state must not depend on decorative animation.

## Motion timing and performance

Typical guidance:

- UI/shared-element response begins within ~120–220 ms;
- avatar physical travel/settling may take ~180–450 ms depending on meaning;
- urgent interruption/barge-in response should begin immediately;
- no animation may delay a safety/reflex action or task cancellation;
- runtime state changes must not depend on animation completion.

Use compositor-friendly movement where practical. Avoid expensive blur/filter effects as a core part of avatar motion.

## Reduced motion

Reduced-motion mode must preserve meaning through:

- static puck position;
- text state;
- iconography;
- small opacity/position changes where permitted;
- haptics/sound where appropriate and allowed.

The interface should remain fully understandable with animation disabled.

## Accessibility

Do not rely on expression alone to convey critical state.

Important states should also have at least one of:

- text label;
- sound cue;
- haptic cue on OSCAR Mobile;
- distinct iconography.

Color alone is never sufficient for critical state.

## Asset locations

Brand/icon assets live under:

```text
assets/brand/
```

Apps and docs should reference canonical assets from this directory rather than duplicating them at repository root.

[oscar-orb.svg](../assets/brand/oscar-orb.svg) is the canonical source and actual
intended OSCAR appearance, including its curved wink. Prefer it on scalable
surfaces. Future runtime variants derive from this artwork and must preserve its
core identity; motion guidance is not permission to independently redraw it.
See [brand assets](../assets/brand/README.md) for retained raster compatibility files.
