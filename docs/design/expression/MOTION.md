# Motion language and complete transitions

Proposal v2. Finite, deterministic, interruptible laboratory performance.

## Timing and apparent weight

Gaze begins immediately and acquires an explicitly selected target in 95ms.
From rest, puck travel starts 45ms later; moving retargets retain velocity without
that delay. Arc tension arrives over 170ms, lid/open-eye changes over 210ms.
Puck and shell use a damped analytic spring
(damping ratio 0.84, angular frequency 19/√weight); shell has 1.35× effective
weight. Facial curves use smoothstep. The puck settles within a finite 700ms
window; the last residual is snapped only after it is visually negligible.

The tiny spring overshoot is physical settling, not a bounce loop. Rest contains
no animation timer. There is no periodic breathing, random gaze, procedural
blinking, orbiting loader or repeating task flourish. Reviewer-triggered blink
has one 160ms close/reopen envelope after 80ms, suppressed in privacy/degraded
states and reduced motion.

With the owner's additional permission, synthetic speaking opens the smaller eye
and performs two phrase stresses around 650/1050ms on a finite playful puck arc
between 400–1400ms. Executing has one arcing arrival at 240–900ms, then holds
rather than looping as false progress. These do not read audio. A new interruption,
mute, unavailable, error or waiting event removes speech choreography in the
same render; the new physical pose then settles.

Operational/delivery retargeting samples current pose and physical velocity.
Boundary changes stop incompatible motion immediately and start a zero-velocity
settle; new sequence studies also start with zero velocity. Playback does not
queue obsolete reactions. Pause freezes the timeline; replay uses the same
initial pose/events; scrub analytically samples it rather than replaying hidden
frames. Playback speed affects virtual time, not shape limits. Hidden tabs pause
rather than catching up later. Settings are explicit studies, not personality
preferences or durable user state.

## Transition map

Every event is a manually selected synthetic state. Holds allow interpretation;
these are not production timing promises or automatic task transitions.

| Sequence | Events and holds | Why it behaves this way |
|---|---|---|
| Rest → attentive → listening | rest 0; attentive 900ms; listening 2300ms | Attention does not imply microphone activation; listening requires a separate event |
| Listening → thinking → responding | listen 0; process 1600; speak 3400; rest 5200 | Gaze withdraws for concentration, returns for a finite phrase, then releases |
| Working → owner approval | executing 0; waiting 1700 | Work motion stops; patient posture does not approve or pressure |
| Thinking → interrupted → attentive | process 0; interruption 1600; attention 2250 | Immediate semantic stop with a brief reorientation, no automatic listening |
| Curious → amused → composed | curious 0; amused 1600; composed 2650 | One asymmetric inflection followed by a clean return |
| Available → unavailable | attentive 0; unavailable 1700 | Availability loss suppresses activity immediately; posture withdraws without drama |
| Unavailable → restored | unavailable 0; explicit available 1900; rest 3100 | Restoration is explicit, no inferred reconnect or success celebration |
| Active → resting | execute 0; release 2000; rest 3200 | Lower energy settles toward stillness; no claimed completed task |
| Speaking → interrupted | speak 0; interruption 1600; attention 2300 | Speech beat stops; readiness returns without activating a microphone |
| Muted → explicitly available | muted 0; available 1700; rest 2900 | Only a new synthetic state releases conversational mute |

Standalone surprise recovers at 850ms; amusement and pleasure release at 1400ms;
interruption reorients to attentive at 650ms. Recovery retains operational state
and re-runs arbitration. A new event replaces all old beats, including recovery;
it cannot later resurrect speech/availability or a success claim.

Sequence boundaries have a readable held pose, not a continuous cycle. Replay is
a reviewer action. A GIF loops for convenient review; the actual lab does not.

## Evaluation method

Inspect actual rendered geometry at 32/48/64/96/128/192 CSS pixels. Inspect timed
frame strips and real-time playback, including repeated retargeting mid-travel.
Critique differences in aperture, arc tension, gaze lead, puck inertia and recovery
before changing surrounding UI. Compare reduced-motion samples at the same
logical events. Record uncertainties as owner-review questions, not visual PASS.
