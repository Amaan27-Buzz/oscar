# Two-mark character language — reviewed v3 direction

This is an owner-review design vocabulary, not a production state schema.
All laboratory states are **SIMULATED VISUAL STATE — NO CORE EXECUTION**.

## Vocabulary

Sixteen study names reduce to twelve delivery poses and eleven operational
samples. Operational labels carry truth; a pose is never evidence of a task,
permission, emotion, sensing, listening or successful execution.

| Study | Operational sample | Delivery / mechanism | Interpretation limit |
|---|---|---|---|
| Resting | available | composed; canonical disc/wink, still | Available is a selected sample |
| Attentive | available | gaze lead, smaller eye unfolds, puck follows | No perception claim |
| Curious | available | arc lift, slight asymmetric lid, counter-tilt | OSCAR delivery, not user emotion |
| Thinking | processing | disc lid, gaze slightly up/left, tight arc | No theatrical loading loop |
| Listening | listening | directed attention with more open disc | Only explicit synthetic listening |
| Speaking | speaking | open smaller eye, stresses and finite playful puck arc | Mouthless cadence, not audio/lip sync |
| Focused | executing | directed gaze, steady serious posture | No progress percentage/result |
| Amused | available | gentle lid, lifted arc and small tilt | Brief, never rewards consent |
| Pleased | available | soft acknowledgement | Not task success or VERIFIED |
| Surprised | available | open marks, short recoil, authored recovery | Controlled recovery, not alarm theatre |
| Concerned | available/error | reserved lid angle, downward arc tension | Not inferred human distress |
| Unsure | unknown | unequal mark posture and withheld gaze | Explicit UNKNOWN label |
| Waiting | waiting | suspended lowered posture | No motion that implies work/approval |
| Interrupted | available | stop cadence, brief reorientation | Does not activate microphone |
| Asleep | available | closed/low-energy marks | Presentation only; no sensing/safety claim |
| Unavailable | unavailable | lowered puck and less engaged marks | No stale work or fake reconnect |

Muted is an additional operational/privacy study: quiet face, no conversational
listening/speaking choreography, always a text cue. Conversational mute makes no
claim about the independent acoustic/safety plane. Error is a failure label plus
restrained concern, with no alarm pulse or success recovery.

## Geometry rules

Source circles, face inset, gradients and contact shadow retain their numerical
values. `expression/react/Orb.tsx` owns the extracted SVG derivative;
`design/expression-lab/src/Orb.tsx` reexports it. Compose implements its geometry
in `mobile/expression/` with documented native raster differences.
Neutral matches the source mark coordinates and original cubic wink.

The large disc remains circular. Slanted clipping lids traverse it rather than
squashing the disc into an oval. At closure it becomes a quiet curved red mark;
closure does not weaken at low intensity. With explicit owner permission the
smaller wink unfolds into an unequal open eye. Four matching cubic segments
interpolate between its outline and a smaller oval. Stroke thickness reduces as
the filled aperture opens; the source cubic is exact at opening=0. This is
animated geometry, not an image swap. No mouth, pupil or eyebrow is added.

Gaze translates red marks together within ±14/±10 source units, with different
shape/tension on each mark. No pupils or independently wandering eyeballs.
V3 puck pose is bounded (tested within 135 source units x / 86 y, tilt within 24°).
Default speaking/executing performances each traverse more than 90 units x and
65 units y: about 53px/38px at the 340px stage. Engagement and speech explore
the shell interior instead of hovering near one offset. At neutral the original
right-offset geometry is restored. Shell rotation remains less than puck rotation;
there is no detached face or shell/puck shape deformation.

Intensity is bounded 0.35–1.0; weight 0.70–1.50. Controls cannot turn the system
into a bouncing toy or erase its neutral geometry. Small marks are a perceptual
aid; labels and static operational cues remain mandatory in future product use.

## State arbitration

The following is a **lab conflict model**, not Core/Controller logic. The lab has
no authoritative Core source and no success/approval state.

| Priority | Condition | Result | Delivery / motion restriction |
|---|---|---|---|
| 1 | unavailable boundary or operation | unavailable | subdued; suppress activity/cadence/gaze target |
| 2 | unknown boundary or operation | unknown | hesitant; suppress activity/cadence/gaze target |
| 3 | error | error | concern, no playful motion |
| 4 | owner attention / waiting | waiting | suspended, no approval or busy motion |
| 5 | conversational mute | muted | quiet; suppress listening and speech |
| 6 | processing/executing/verifying | unchanged operation | focused; suppress cheerful delivery |
| 7 | listening | listening | attentive; explicit selection required |
| 8 | speaking | speaking | exclude asleep/interrupted/subdued |
| 9 | available | available | selected restrained delivery |

Mute is retained visibly alongside higher-priority waiting/error/unavailable/
unknown labels. Owner attention cannot disappear behind a playful cue. A new
event updates resolved text and cancels incompatible cadence immediately;
physical geometry can settle without continuing the old semantic claim.
Restoration never means task VERIFIED. A pleasant face never grants permission.

## Accessibility and embedding

Keep critical labels beside the character. Do not rely on color, motion, a wink
or a sad-looking pose. The lab supplies semantic controls, visible focus,
native keyboard slider/select behavior and polite state announcements. It does
not move keyboard focus during transitions.

Reduced motion uses the target pose at each logical event. No intermediate
travel, blink or cadence; pause/scrub still work and labels retain identical
arbitration. OS preference cannot be overridden to force motion. Forced colors
preserve the identity art while allowing controls to use system colors.

At 32–48px, the two marks are identity cues, not a sixteen-emotion alphabet.
Do not demand that tiny pose differences replace readable state information.
Larger review renders are deliberately not proposed product avatar sizes.
