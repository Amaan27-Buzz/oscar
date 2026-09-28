# Sunday visual direction

Sunday is OSCAR on the phone. This document captures the current mobile visual direction; `DESIGN.md` remains the global design system and `TASTE.md` the qualitative quality bar.

## Surface mode

**Operate.** Sunday must help the user speak, type, understand OSCAR’s state, approve actions and receive meaningful proactive information. Expression may never obscure familiar mobile affordances or task state.

## Direction contract

**THESIS — Quietly Alive.** Sunday is a minimal native assistant surface whose character comes from OSCAR’s moving avatar and immediate response. It refuses the conventional assistant layout of transcript-first chat, dense cards and generic AI ornament.

**OWN-WORLD.** Soft white/air canvas, deep navy typography, OSCAR blue shell, yellow face, minimal red expression marks, broad natural shadows, thin line icons and restrained blue focus states. Controls are sparse and platform-native. Secondary detail recedes into sheets/rows rather than permanent panels.

**STORY.** The user should understand in a glance whether OSCAR is idle, listening, thinking/working, speaking, muted or in Sentry. The phone feels inhabited by the same OSCAR that exists on desktop and physical hardware, not like a separate chatbot app.

**FIRST VIEWPORT.** The avatar is the dominant object. Home pairs it with a short contextual greeting/current state and one voice/text entry surface near the thumb zone. Listening removes unnecessary navigation and gives the avatar/state, live audio feedback and immediate stop/cancel controls visual priority. Thinking/working shows what OSCAR is doing without turning the screen into a verbose progress dashboard. Sentry uses a calmer, focused avatar plus only the meaningful monitoring/alert controls.

**FORM.** Native mobile assistant/presence surface with object-led composition, not a messenger UI. Use sheets, native navigation and contextual rows as needed. The current concept image is a direction for density/personality, not a pixel-perfect layout contract.

**FINISH.** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Primary states

### Home / present

- avatar large and central;
- neutral or occasional playful acknowledgement, not permanent wink;
- one short contextual line (`Good morning`, current task, or meaningful pending state);
- one combined voice/text entry affordance;
- secondary navigation only if real product IA requires it;
- avoid empty feature cards merely to fill space.

### Listening

- immediate state change on wake/press;
- avatar shifts toward/focuses on input;
- waveform or level visualization only while actual audio is active;
- mic/stop/cancel controls are obvious and thumb-friendly;
- transcript can appear progressively but is not the hero;
- barge-in and cancellation must feel instant.

### Thinking / working

- avatar movement becomes more measured;
- concise real state such as `Looking things up`, `Handing this to Codex`, or `Waiting for approval` beats a generic spinner;
- expose task detail only on demand;
- never display “thinking” for a disconnected/blocked system.

### Speaking

- expression and puck movement respond lightly to cadence;
- do not animate a literal mouth unless it reaches the project quality bar;
- tapping/voice interruption stops speech immediately and returns to listening.

### Sentry

- calm, centered/focused composition;
- subtle warm/red state light is allowed but no militaristic or cyberpunk treatment;
- show only the active mode and meaningful monitored states/alerts;
- urgent items outrank decorative status information;
- changing sensitive Sentry settings may require Voice Match and/or stronger phone confirmation.

### Muted / sleep

- reduced motion;
- unmistakable state label/icon in addition to facial expression;
- no fake listening animation.

## Navigation

Do not assume a four-tab assistant app merely because the concept image shows one. Validate the actual information architecture first.

Likely destinations may include:

- Home / Presence
- Memory / history search
- Capabilities / tools
- Sentry
- Settings / profile

But surfaces should be consolidated where possible. OSCAR’s continuous LRA history should not regress into a chat-list sidebar/tab full of conversation threads.

## Motion

The avatar is the motion anchor.

- puck movement uses spring/inertia and meaningful direction;
- surrounding UI moves less;
- state changes are quick (typically 120–220 ms UI, 180–450 ms avatar motion);
- acknowledgement can begin locally before cloud reasoning starts;
- reduced-motion mode preserves state through position, labels and minimal fades.

## Native behavior

- use Android/native navigation, sheets, text entry, permissions and biometric confirmation patterns where appropriate;
- respect safe areas, keyboard/inset behavior and one-handed reach;
- haptics can reinforce wake, confirmation and critical state transitions;
- Sunday may share brand components with desktop, but must not be a responsive web screen inside a phone shell.

## What to keep from the current concept

- white/soft neutral canvas;
- deep navy copy;
- dominant blue/yellow OSCAR avatar;
- friendly but sparse state copy;
- generous whitespace;
- focused listening/thinking/Sentry state screens;
- expression/state strip as a design-development reference, not a shipping UI element;
- yellow face moving inside the blue shell as the signature interaction.

## What to refine during implementation

- make the idle face more neutral than the permanent wink;
- validate whether bottom navigation is actually necessary;
- reduce card-like rows where a native list/sheet communicates better;
- ensure Sentry feels calm rather than angry;
- derive thinking/working animation from actual task state instead of decorative bubbles/spinners;
- test the avatar at small notification/bubble sizes as well as full-screen scale.
