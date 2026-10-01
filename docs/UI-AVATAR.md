# Avatar + Interaction Language

## Identity

OSCAR's avatar is a core interaction surface, not decorative branding.

The current visual identity consists of:

- a blue outer body/shell
- a yellow circular face/puck inside it
- minimal red facial features
- simple, readable geometry that works from app-icon size to large voice surfaces

The avatar should communicate system state through motion and expression without becoming visually noisy.

## Primary motion concept

The yellow face moves inside the blue shell like a **weighted joystick head / magnetic puck**.

The current Sunday experiment keeps the shell compact and treats it as a physical presence object. State, direction and constrained movement carry more meaning than facial expressions. The same object stays mounted across Home, Awareness and input changes. No permanent idle loop is required. See [the two-surface study](../prototypes/sunday/README.md); its state is scripted until connected to an authoritative runtime.

The study includes small eye/mouth shapes drawn as SVG paths after manual reference feedback. Listening focuses, Speaking opens the mouth and curves the eyes, and Working/Verifying/Waiting/Blocked/Alert remain restrained. Facial interpolation respects reduced motion; labels and puck position remain the primary state signals. Ordinary Sentry awareness does not use an angry expression.

Motion characteristics:

- responsive but not twitchy
- soft spring/inertia
- subtle overshoot
- physically believable weighting
- direction can indicate attention or focus
- never random movement merely to look “AI-like”

This should become one of OSCAR/Sunday's signature UI behaviors.

## State language

| State | Expression / motion direction |
|---|---|
| Idle | calm neutral face; slow minimal settling motion |
| Wake acknowledgement | quick focused shift toward input/source |
| Listening | attentive/open expression; subtle tracking/breathing |
| Thinking | measured drift/orbit or small internal movement; no generic spinner dependency |
| Speaking | expression synchronized lightly with cadence; avoid literal mouth flapping unless it looks excellent |
| Success | brief positive acknowledgement; restrained bounce/settle |
| Confused | small tilt/offset; clearly uncertain, not comedic |
| Alert | centered/focused posture; reduced playful motion |
| Sentry | watchful, stable, directional awareness cues |
| Sleep | lowered activity, reduced brightness/motion |
| Muted | restrained motion and explicit conversation-mute label; acoustic policy remains separate |
| Error | clear but calm failure state; avoid alarming animation for recoverable errors |

## Default expression

The wink is a strong personality expression, but should not be the only default face. Use it as a playful acknowledgement or occasional idle beat.

The standard idle state should be calmer and more neutral so OSCAR can also feel credible during work, safety and Sentry contexts.

## Serious mode

OSCAR must be able to become more serious without changing identity.

In alert, security, safety or focused-work contexts:

- reduce playful motion
- center/steady the yellow face
- use cleaner, more focused expressions
- reduce animation amplitude
- prioritize information hierarchy over personality

## Voice choreography

Avatar state must be driven by real system state:

```text
wake detected   → acknowledge
VAD active      → listening
intent resolved → transition
model/tool wait → thinking/working
TTS active      → speaking
barge-in        → speaking stops immediately → listening
sentry event    → alert/sentry state
```

The avatar must not claim “thinking” if OSCAR is actually blocked or disconnected. Failure/blocker states should be explicit.

## Sunday

On Sunday, the avatar is expected to be one of the primary UI elements:

- home/assistant surface
- voice session
- listening indicator
- proactive notification identity
- Sentry status
- onboarding/calibration
- compact bubble/overlay where Android permits

Motion should adapt to display size and power state.

## Desk / physical surfaces

On small OLED/TFT/LED hardware, preserve the same state language even if the full artwork cannot be rendered.

Examples:

- simplified eyes/face
- directional puck/offset representation
- status color/light patterns where a screen is unavailable
- shared state names across hardware and software

## Accessibility

Do not rely on expression alone to convey critical state.

Important states should also have at least one of:

- text label
- sound cue
- haptic cue on Sunday
- distinct iconography

Animation intensity/reduced-motion preferences should be supported.

## Asset locations

Brand/icon assets live under:

```text
assets/brand/
```

The README and apps should reference the canonical assets from this directory rather than duplicating files at repository root.
