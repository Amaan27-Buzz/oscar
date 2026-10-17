# OSCAR — Active product direction

**Owner direction updated 2026-10-18.** This is the current user-facing product brief. It reconciles the approved Desktop design, the selected Mobile design baseline, and later runtime ambitions. It is **not** an implementation/acceptance receipt. Read it with [canonical slice numbering](SLICE-NUMBERING.md), the [roadmap](ROADMAP.md), [feature backlog](FEATURES.md), [current checked status](CURRENT-STATUS.md) and [active groups](DELIVERY-PLAN.md).

## Active delivery priority

One Core on a secure replaceable cloud host (Oracle Always Free **candidate**, not deployed) → one authenticated remote Grid → the approved Windows/Android apps connected to the **same OSCAR** → complete real computer use, MCP/plugins, Secure/Full Access, voice, native automations and Chief of Staff → scoped operational alpha. Dedicated home-server laptop comes when available, then physical ESP32/Pico (deferred, not cancelled). Gate C/D remain PARTIAL and Gate E not passed. See [delivery plan](DELIVERY-PLAN.md).

## North star

OSCAR is **one persistent multimodal personal intelligence**, not a collection of separate chatbots, a plugin dashboard or an animated chat toy. It can converse, recall relevant history, reason, use authorized computer and device capabilities, supervise tasks, delegate to subordinate Workers, and eventually perceive changing context and initiate useful work. Desktop, Android, voice and future Edge surfaces are embodiments of the **same authoritative Core**.

- **One continuing relationship:** a chronological conversation, durable OSCAR-owned Event Archive/Memory Fabric, bounded active model context and source-backed compaction/retrieval. Compaction must not delete original history or create a separate chat-thread product.
- **Natural action:** text editing, dictation, file/app/browser control and contextual computer use are capabilities invoked through Conversation, not dedicated first-class Text Tools/Act destinations. Observation, retention and mutation remain separately authorized.
- **Activity:** approachable record of what OSCAR is doing, what finished, what failed, what was verified and what needs intervention. Technical evidence remains available on inspection.
- **Automations:** one-time delegated jobs, recurring schedules, triggers, conditional watches, named persistent Workers and continuing Protocols. A Worker has a responsibility, identity within OSCAR, permitted scope, lifecycle and autonomy; it is **subordinate**, not a second assistant. An automation defines *when/why* to run; a Worker may execute it. A simple trigger need not instantiate a Worker. Do not populate these pages with invented functioning bots.
- **Awareness:** Sentry supplies persistent, permissioned environmental/device/current-event signals when implemented. Ambient awareness is **not** synonymous with microphone capture, transcription or storage.
- **Chief of Staff:** schedule, communication, reminders and context become an integrated OSCAR ability accessible on both platforms, with mobile-optimized presentation.

## Two native applications, different emphases

| Embodiment | Responsibility | Current direction |
|---|---|---|
| **Desktop Companion** | Persistent, small expressive presence | Canonical unchanged Orb, minimal truthful state, Workspace launch, immediate supported voice/privacy controls; shortcut management in overflow, Access and Sentry quick selectors reflecting actual availability. No chat, task list, signing or automation manager |
| **Desktop Workspace** | Full-size conversational/operational experience | Conversation, Automations, Activity, Devices, Preferences; contextual capabilities in Conversation, detailed reviews in Workspace/native UI. Restrained neumorphic paper/graphite surfaces |
| **Android app** | Portable personal presence and owner-control | Shared Core conversation, automation oversight, Activity, Grid, quick decisions, native voice/assistant/permission integration, future Chief of Staff/Sentry. Native Compose composition, **not** a shrunk Desktop |
| **Future Orb overlay, widget and Edge** | Short glanceable presence/control | No replicated dashboards and no authority implied by an animation |

**Design status:** Desktop Group 2.5A was owner-approved **provisionally** and merged in [PR #5](https://github.com/Amaan27-Buzz/oscar/pull/5) at merge commit `43c15d37a6421d438b8101d5e322489ae452b20d`. Final integrated visual and physical acceptance is **deferred**, not PASS. The canonical Orb SVG is unchanged.

**Mobile Group 2.5B:** the owner selected the Codex ImageGen/Figma direction (15 hero screens, one design-system board, five component boards) for native production Android implementation. The separate Gemini Argon `oscar-ui-test` experiment was rejected; do not port its code, tokens or layouts. The 56-experience planning scope is information architecture, not 56 pages. Three bottom destinations are Conversation / Automations / Activity; Devices and Preferences stay one tap away in the app bar, with Today in Conversation and Awareness/Access in Preferences. Software, emulator, owner visual and physical acceptance remain separate. See [Group 2.5B implementation and evidence](ui/mobile/group25b/README.md).

## Independent operating dimensions

**Mobile owner acceptance — 2026-10-16:** Group 2.5B UI/UX is **APPROVED / PASS**.
The approved composition is preserved during [engineering closure](ui/mobile/group25b/FINAL-CLOSURE.md).
Real audio, biometric/PIN, OEM commissioning and remote CI remain separate.

| Domain | Choices | Meaning |
|---|---|---|
| **Access authority** | Ask / Secure / Full Access | Ask: consent before state changes. Secure: ordinary autonomous operation, protected/consequential action consent. **Full Access: genuine unrestricted owner-delegated autonomy over technically available capabilities, without OSCAR per-action prompts after explicit activation.** |
| **Awareness / invocation** | Manual / Trigger-only / Sentry | Explicit interaction vs supported triggers vs permissioned continuous awareness. Sentry modes: Passive, Aware, Guard, Away, Sleep |
| **Worker autonomy** | Manual / Supervised / Autonomous | Degree of independent delegated execution; never independently raises Core authority |
| **Perception, capture, retention** | Source-specific independent grants | Permission to observe does not grant retention; neither grants mutation. Mic mute, active listening, wake/VAD, ambient acoustic analysis, recording, transcription and memory are different |

**Important implementation boundary:** Secure/Full Access activation, signed standing delegation and distributed revocation are **not built**. Only current Ask-style enforcement is reported by Desktop; exact-action signing and critical-risk blockers remain. Full Access does not invent OS/platform access or defeat external mandatory controls; future activation must preserve provenance, revocation and local physical safety. A bounded local Sentry lifecycle and durable Executive/Worker scheduling are integrated as Group 3 software; real environmental delivery, native authoring, broad communications and Chief-of-Staff integrations are not accepted.

## Visual direction and interaction

- **Quietly Alive / Playful Precision**, with the owner-approved **restrained neumorphic** material direction as the present Desktop baseline. Soft raised/inset treatment must support readable hierarchy and focus, not become an excessive shadow aesthetic.
- Original brand: warm cream/paper and graphite with OSCAR blue/yellow/red; Mobile may introduce **purposeful original feature-specific illustrations and bold editorial compositions** inside a coherent palette. No generic AI dashboard/card wall or indistinguishable repeated screens.
- Canonical `assets/brand/oscar-orb.svg` **must remain unchanged**. Expression is separate from actual sensing/task truth.
- No technical labels (archive schemas, debug IDs, retention grants, model internals) in everyday Conversation. Evidence/diagnostics remain inspectable when relevant.

## Future — Adaptive Interface Engine (AIE)

OSCAR should not be limited to responding in static prose. Within the **same conversation**, it can eventually choose and compose trusted interactive views: comparison tables, editable plans, timelines/calendars, diagrams, simple simulations, charts, device controls or live Worker views. The interface can update as work advances and the user interacts; Desktop and Android render the same **typed, versioned and capability-negotiated UI description** through their own trusted native components. No unrestricted model-generated HTML/JS or bypass of existing Core action authorization.

Group 3 integrated **bounded typed foundations** for Slices 16–17, not the full interactive AIE. Broader components, Slice 19 security/accessibility hardening and Slice 20 real cross-device validation remain pending. See [Adaptive Interface Engine](ADAPTIVE-INTERFACE.md).

## Acceptance discipline

Do not mark a design board, browser demo, native emulator, mocked Worker, reference voice or simulated Edge task as production acceptance. The Core/Worker/Memory software foundations have documented scope, but full real-device, owner, Sentry, delegated Full Access and end-to-end autonomy acceptance remain future gates. Preserve historical reports verbatim; this current document supersedes **old instructions**, not historical evidence.
