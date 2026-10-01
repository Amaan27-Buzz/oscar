# Sunday visual direction

Sunday is OSCAR on the phone. The current approach is a small code experiment: build, inspect, improve, simplify, verify. Only **Home** and **Sentry / Awareness** are being evaluated. The earlier large-avatar/image concept is superseded; it is not the implementation reference.

## Quietly Alive

70% restraint and whitespace, 20% tactile industrial character, 10% approachable personality. Warm neutral canvas, precise system typography, compact blue shell and weighted yellow puck. No giant greetings, chatbot feed, permanent text box, card wall, fake telemetry or generated illustration. One dominant focal idea per surface.

The avatar is a functional physical object. Position, orientation, tension and settling communicate state; faces do not carry all the meaning. Presence is already there when the user arrives.

## Three independent states

- Presence: Ready / Listening / Speaking / Working / Verifying / Waiting / Blocked.
- Acoustics: Sentry aware / conversational listening / conversation muted / acoustic awareness disabled. Unavailable microphone or Sentry is an explicit failure.
- Attention: quiet / background / useful review / urgent.

Subsystem availability and source freshness remain separate. An absent desktop is optional context loss; unavailable acoustics cannot certify a quiet room. An alert can interrupt presentation while ongoing work remains intact. Voice and text share context; entering text does not disable the voice architecture.

## Home

Compact physical presence, readable current state, at most one contextual activity, a subtle acoustic-status row and a compact combined input affordance. No permanent Talk / Type choice. The existing dock expands into input when needed; the presence object stays mounted.

After manual feedback, the study uses a centered physical shell/puck, short normal-state copy and a compact keyboard/microphone dock. Home's acoustic label is the entry to Awareness; Mode / Mute / Context are compact controls there. Privacy explanations and source evidence live behind those controls instead of repeated first-screen prose. User-supplied visual references inform composition, not runtime behavior or shipping-product claims.

Background activity details and other background activities are disclosed on demand. Blocked work is named plainly. Reported output remains distinct from verification.

## Sentry / Awareness

Local awareness is visibly different from an activated conversational Listening turn. A normal state explains local perception without presenting a surveillance dashboard. Mode, temporary conversational mute, source context and privacy are available one layer deeper. Evidence/source details sit deeper again.

Conversation mute does not imply physically dead microphones. Acoustic-awareness off is a separate software policy choice. Reflex/safety behavior depends on its local deterministic policy. Modes cannot grant permissions. Wake-word guidance is shown only when wake availability is supported by the presented state.

## Motion and continuity

One physical presence object across both surfaces. Listening orients the puck toward the user; Working is purposeful; Verifying is tighter; Waiting settles low; Blocked is constrained; Alert is immediately focused. Interrupted settling preserves position and velocity. No constant idle orbit or decorative breathing is needed.

The compact input becomes its expanded form in the same composition. UI actions take effect before animation and never depend on animation completion. Reduced motion retains labels and controls, stops spatial interpolation and removes sheet entrance movement. Screens do not cross-fade as a whole.

## Current implementation and acceptance

[prototypes/sunday/README.md](../prototypes/sunday/README.md) contains research sources, component/state ownership, run commands, test checklist, review notes and limits. It uses the Appllama skills with user-authorized official-reference research because the MCP is a paid feature. No images were generated and no prior Figma attempt was continued.

The repository has no established native mobile stack. This dependency-free browser study is isolated and explicitly scripted. It captures no audio, connects no device and executes no task. It does not select production architecture or complete Slice 00.5, Sunday, voice or avatar runtime slices.

Browser inspection can establish composition, state presentation and interaction behavior. Native Android keyboard/insets, gestures, haptics, accessibility settings, release-build performance, acoustic privacy, real barge-in and sensor truth need a native implementation and device evidence.

Stop after these two surfaces. Manual review precedes any Workers, Memory, Desktop, Onboarding or broader visual-system work.
