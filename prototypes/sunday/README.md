# Sunday interaction study

Only **Home** and **Sentry / Awareness**. This is a browser study, not a native Sunday release or Slice 00.5 completion. No OSCAR runtime exists in this checkout yet. All device/task/audio states are explicitly scripted. Nothing captures audio, transcribes, uploads, executes a task or grants permissions.

Run from this directory with Node:

```sh
npm start
npm test
```

Open http://127.0.0.1:4173/#home or http://127.0.0.1:4173/#awareness. Review controls sit outside the product composition. Select fixtures, light/dark appearance or reduced motion there. On a narrow viewport, scroll below the product to find them. Drafts survive input and surface changes during the visit, but are deliberately not stored across reloads.

## Research before code

Used **Appllama Usage** and **Appllama App Design Skill**. The paid MCP was unavailable; the user explicitly selected official-reference research. No previous Figma/image concepts were continued and no images were generated.

| Pattern / reference | Why it works | OSCAR adaptation | Do not copy |
|---|---|---|---|
| [Waterllama](https://www.waterllama.com/) / [shipping screenshots](https://apps.apple.com/us/app/water-tracker-waterllama/id1454778585): character carries the hydration state; quick beverage access | Character reinforces the functional state; frequent input has a short path | Small blue shell / weighted yellow puck carries attention; a compact combined input expands where it already lives | Giant character, collectible economy, streak pressure, multi-color challenge grid |
| [Cat on Chair](https://catonchair.app/en/) / [shipping screenshots](https://apps.apple.com/us/app/cat-on-chair-pomodoro-timer/id6746562271): calm companion beside a clear timer; secondary tools at the edges | Utility remains the readable focal point; companionship does not require constant speech | Calm object, readable state, one contextual item; no greeting ceremony | Illustrative room, rewards/trash, furniture shop, timer/task-manager IA |
| [Flighty](https://flighty.com/) / [Apple design interview](https://developer.apple.com/news/?id=970ncww4): live context stays glanceable; relevant alerts rise above detail | Current useful state arrives without repeatedly launching an app | One foreground activity, urgent attention above ongoing work, source information deeper | Flight maps, metric grids, airport-dashboard density, certainty without freshness |
| [Apple’s shipping-product motion examples](https://developer.apple.com/videos/play/wwdc2026/251/): origin-connected zoom transitions and contextual hierarchy | Continuity connects a control to its destination | Keep the actual presence object mounted; compact input grows into the active input; maintain velocity when the puck is retargeted | Liquid Glass, decorative recap springs, broad content choreography |

Inspected published screenshot sets and official descriptions, not the apps on a real phone. Cat on Chair’s initial timer/focus/reward compositions and Waterllama’s home/widget/challenge/goal compositions informed the study. This evidence does not establish their exact gesture, keyboard, back-navigation or frame-rate behavior. Motion references from the Apple presentation are documented examples, not independently measured app recordings.

## Tiny presentation model

Four independent dimensions in `state.js`:

- **Presence:** Ready, Listening, Speaking, Working, Verifying, Waiting, Blocked. A foreground turn temporarily projects Listening over background work; barge-in clears the speaking preview.
- **Acoustics:** Sentry aware, conversational listening, conversation muted, acoustic awareness disabled. Microphone and Sentry unavailability are explicit failures, separate from selected mode.
- **Attention:** quiet, background, review, urgent. Urgent attention does not discard the background objective.
- **Availability:** local microphone/Sentry, network and optional desktop. Missing sources become unknown; they cannot certify a quiet room.

Sentry policy mode (Passive / Aware / Guard / Away / Sleep) is separate from these dimensions. Mute lasts 15 minutes, ends an active turn and leaves the local-awareness selection alone. Resuming never starts a conversational turn automatically. Text preserves acoustic policy. Software awareness off never claims microphones are physically disconnected. No mode can grant new permission.

## Components and ownership

- `presence.js`: one blue shell / yellow puck with a damped physical settle. State-specific targets; no endless spinner or decorative idle loop. Interrupted motion retains current position and velocity. Reduced motion snaps to the readable state.
- `app.js`: Home, Awareness, one contextual activity, shared input dock and native dialog disclosures. All ephemeral state belongs here; presentation rules are in `state.js`.
- `styles.css`: neutral palette, system type, 4px spacing family, light/dark appearance, safe-area padding and visible keyboard focus. No design-system package.
- `server.mjs`: loopback-only Node static server. No dependencies or production service architecture.

Home’s acoustic-state control leads to Awareness; the same presence object remains mounted in the shared composition. Awareness → contextual mode/privacy/source disclosure → evidence is progressively revealed. Browser Back navigates the two surface hashes; Escape closes native dialogs or the input preview. There is no transcript feed.

## Checklist defined before acceptance

- Inspect Home/Awareness at phone, small-phone and desktop viewports.
- Exercise every visible control, back, Escape, text/voice repetition, draft preservation and mute/resume.
- Inspect long titles, no activities, several activities with one surfaced, Working, Verifying, Waiting, Blocked, review, speaking/barge-in and alert during work.
- Inspect missing Sentry/microphone, desktop offline, no network and acoustic awareness off.
- Inspect light/dark and reduced motion. Check horizontal overflow, tap targets and readable state labels.
- Review motion as a sequence; verify state does not wait on animations.

## Inspection and Kaizen record

Browser inspection covered 390×844, 320×568 and the desktop review composition. All 13 fixtures were swept for state labels and horizontal overflow. Exercised mode selection, awareness off, privacy/source/evidence disclosure, mute/resume, alert during work, long-title expansion, hidden background activities and repeated text/voice switching with draft preservation. Visible primary controls measured at least 44px tall. Light/dark and the reduced-motion switch were inspected. Console inspection found no errors. `npm test` passes the two presentation-contract groups, including mute expiry, unavailable sources, alert priority, barge-in preview and background-state preservation.

Focused passes corrected navigation scroll position and sheet alignment, removed misleading wake guidance when awareness is unavailable/off, replaced reassuring blocked/waiting copy, exposed secondary background activities on demand, and separated deliberately disabled awareness from failures in the detail copy. No surface or design-system expansion was needed.

Impeccable supplied two independent assessments: heuristic/product critique and an AI-pattern detector check. The initial heuristic assessment scored 31/40; its three concrete issues were corrected above. Detector warnings about dark glow were inspected as subdued offset elevation/inset material shading rather than neon decoration. These assessments are critique evidence, not native acceptance.

Motion was reviewed through sampled browser frames and DOM geometry: the puck keeps its identity and retargets, while the input grows from its existing dock. This is low temporal sampling, not a real-time recording or proof of smooth native frame rate. No performance numbers are claimed.

### Revision after manual feedback

The first pass was too text-heavy and read as a status dashboard. The user's three supplied references clarified the desired composition: an object anchors the screen, short state text supports it, and small rounded controls live at the edges. These are visual preferences, not evidence that those concepts are shipping products.

The revision centers a 144px blue shell with an offset weighted yellow puck, removes the recessed concentric socket, shortens normal Home to `Quiet.`, and replaces the text-entry bar with a compact keyboard/microphone dock. Home's acoustic label opens Awareness. Awareness keeps `Sentry aware`, `Local · no transcription` and attention separate. Further feedback removed duplicate OSCAR/Ready labels, routine voice hints and control captions, and replaced the local-first header text with an accessible privacy icon. The palette is now soft white, gentler blue and warm yellow; the review defaults to Light while System and Dark remain available. Explanations and sources remain in contextual sheets. The input expands from its existing geometry; the presence composition makes room rather than disappearing. Focus does not scroll the page during its animation.

The user's avatar reference also informed subtle eye and mouth shapes: neutral dots and a small smile, focused Listening, curved Speaking eyes with an open mouth, an asymmetric Working glance, narrower Verifying eyes and restrained Waiting/Blocked/Alert mouths. These are secondary cues to labeled state and weighted puck movement. SVG paths morph briefly between states; reduced motion removes that interpolation. Sentry awareness is not given an angry/security face.

Rechecked all 13 fixtures at 390×844 with no horizontal overflow, long content at 320×568, light/dark, primary tap targets, native-click input expansion/dismissal and reduced motion. The original presentation-contract tests still pass. Automation that scrolls a target to center is not evidence of a user-visible navigation jump; native click checks retained a zero page scroll during input expansion/dismissal.

Remaining visual weaknesses: the calm interval on quiet Home still needs the user's taste judgment; icon-only input reduces visible copy but needs native usability validation; long/degraded states require scrolling on the smallest phone. Mode/privacy sheets still use a simple contextual entrance rather than fully shared geometry. Gesture-driven motion and task-to-result choreography remain unestablished.

## Scope limits

Native Android gestures, real software keyboard/insets, haptics, Dynamic Type, release-build frame rate, battery behavior, local wake/VAD, actual barge-in/echo suppression and real sensor evidence require a native build and devices. The browser study cannot prove them. No native framework choice is locked by this prototype.

Manual visual review is the next step. Workers, Memory, Desktop, Onboarding and the remaining Slice 00.5 scope are intentionally absent.
