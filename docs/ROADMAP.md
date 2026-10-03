# Roadmap

This roadmap is slice-based. Each slice must leave OSCAR coherent/testable and update affected canonical docs in the same change.

All implementation follows `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`.

Related planning/contracts:

- `docs/BUILD-GATES.md`
- `docs/PRODUCT.md`
- `docs/CHIEF-OF-STAFF.md`
- `docs/ARCHITECTURE.md`
- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/MODEL-ROUTING.md`
- `docs/SEARCH-FRESHNESS.md`
- `docs/VOICE-SENTRY.md`
- `docs/PERSONA.md`
- `docs/RUNTIME-FOUNDATIONS.md`

## Implementation principle

Build OSCAR's nervous system first, then attach embodiments.

```text
objective / event
→ current context + Jev
→ capability / retrieval / model decision
→ permission + Personal Policy
→ execute
→ receive result
→ collect evidence
→ verify
→ update World Model / memory / commitments
→ report only what evidence supports
```

Early development may run on a development PC for convenience. The PC is never OSCAR's permanent host.

Availability ultimately spans:

```text
Sunday + Cloud coordinator + Desktop node(s) + OSCAR Edge
```

## Status legend

- ✅ accepted/verified for stated scope
- 🚧 implemented foundation, broader slice still partial
- ⏭️ next practical work
- ◻️ planned

## Slice 00 — Repository / architecture foundation ✅

Established product/architecture/engineering/design rules, Epistemic Integrity, World Model/Perception direction, Personal Policy, Workers/Protocols, Durable Execution Runtime, Capability Catalog, Action Ledger, Artifact Model, native transport/model-routing direction, Connection Grid, Persona and build gates.

## Slice 01 — OSCAR Core Loop ✅

Verified evidence-backed objective → action → result → independent verification loop. Fake executor success cannot become verified completion.

See [Club A checkpoint](CLUB-A-CHECKPOINT.md).

## Slice 02 — TypeSafe Jev ✅

Verified typed deterministic/epistemic routing for known/world/recall/verify/reason/reported/specialist/worker/unknown paths, with conservative handling of missing capability and freshness-sensitive retrieval.

## Slice 03 — Native Transport + Capability Catalog + Connection Grid foundation 🚧

**Reference foundation verified; broader deployment partial.**

Verified loopback/reference behavior includes scoped pairing/auth, capability advertisement/search, replay protection, correlation, cancellation, progress, heartbeats, durable leases, disconnect/expiry/reclaim and explicit availability states.

Still later: public TLS/outbound rendezvous, independent network-node stores and real Sunday/Desktop/Edge deployment.

## Slice 04 — Native Model Router + cloud intelligence ✅/🚧

**Gate A accepted for the current foundation.**

Implemented/verified scope includes:

- provider/model/credential registry and multi-key pools;
- account-product/shared-quota semantics;
- Auto/Fast/Balanced/Heavy Duty/Free First/Cheap/Local/Private/Manual/Specialist modes;
- bounded fallback and real provider evidence;
- dynamic/fresh inventory instead of trusting stale model seeds;
- Tavily behind a replaceable search-provider boundary;
- source/time/provenance-qualified current search;
- UNKNOWN rather than stale model-prior fabrication.

Public coordinator deployment and continually changing provider metadata remain operational work rather than a reason to treat Gate A as incomplete.

**Gate A — PASS.** See [Club A checkpoint](CLUB-A-CHECKPOINT.md).

## Slice 05 — First real machine Worker + remote continuation ⏭️

**Reference foundation verified; full slice partial.**

Merged Club B reference proves separate-process POSIX Worker/Git/file/terminal execution, lease/checkpoint/restart/reclaim, completed-result reuse, HTTP pause/resume/cancel and independent verification.

Next acceptance on the real Windows development laptop:

- Windows-native filesystem/process safety semantics;
- PowerShell/terminal/Git;
- real useful Codex specialist objective, not merely `--version`;
- cancellation/restart/recovery/no-duplicate execution;
- browser/computer-use path;
- installed-app capability discovery;
- remote continuation/control semantics;
- accurate trusted-host-vs-sandbox boundary.

See [Club B checkpoint](CLUB-B-CHECKPOINT.md).

## Slice 06 — LRA + Personal Policy + live context ⏭️

**Local/reference foundation verified; full slice partial. Gate B remains PARTIAL.**

Merged reference scope includes selected persistent memory, explicit structured Personal Policy, live-context federation boundaries, evidence-backed entity mappings and Connector Fabric foundations for Google plus thin Microsoft/GitHub/Slack/Notion/MCP paths.

Next acceptance:

- natural-language policy interpretation → owner-confirmed structured rule;
- actual Supermemory semantic backend when configured;
- authenticated/private service accounts + OAuth lifecycle;
- real local continuity on Windows;
- broader live context into the future Chief-of-Staff/World Model path.

**Gate B — PARTIAL** until useful real-machine work and continuity are genuinely accepted.

## Slice 07 — OSCAR Edge + reflexes ◻️

Goal: persistent local physical presence.

Deliverables:

- ESP32 gateway/client;
- Pico deterministic controller;
- typed ESP32↔Pico events;
- health/capability advertisement;
- GPIO/sensor/display test capabilities;
- watchdog/safe defaults;
- reflex/emergency-stop path;
- reconnect/offline behavior;
- optional LAN helper/Wake-on-LAN only when real;
- simulator + physical-device verification.

## Slice 08 — Voice Core + Voice Identity + Voice Match/Map + Persona runtime ◻️

Goal: natural voice interaction and stable character without weakening truth/authority.

Deliverables include wake/VAD/STT, barge-in/echo cancellation, stable VoiceProfile, speaking modes/fallback, Voice Match, Voice Map, self-voice suppression, multi-device arbitration and Persona runtime/context triggers.

## Slice 09 — Sunday + communication + Connection Grid owner controls ◻️

Goal: ship OSCAR's phone embodiment and primary everyday Chief-of-Staff surface.

Deliverables:

- native Android app shell;
- `ROLE_ASSISTANT` / voice-interaction path where supported and user-selected;
- persistent present-not-launched OSCAR behavior;
- optional permissioned OSCAR Orb application overlay;
- attention-aware Orb retreat/hide during video/reading/presentation/focus contexts;
- edge/hotspot/assistant/voice invocation and natural reappearance;
- configurable Android home-screen widgets;
- notification-listener integration after explicit grant;
- per-app/person/source notification exclusions;
- notification summaries/triage;
- legitimate notification `RemoteInput` replies when exposed;
- voice/text continuity;
- biometric/PIN approval;
- Connection Grid owner-control surface;
- remote task supervision / pause / cancel / revoke;
- initial Universal Channel Gateway actions;
- explicit per-platform capability limits;
- real-device/OEM acceptance on the target Samsung phone.

Notification access must never be treated as unrestricted access to the source app.

See [Sunday design](SUNDAY-DESIGN.md) and [Chief of Staff](CHIEF-OF-STAFF.md).

## Slice 10 — Desktop Interaction Runtime ◻️

Goal: polished native desktop embodiment.

Deliverables include compact ambient presence, Dictate/Edit/Ask/Act, focused app/window/selection/cursor/accessibility context, screenshot/visual context, approvals/task progress, Connection Grid control and fluid state transformations.

## Slice 11 — World Model + Perception Fabric + persistent Sentry + optional Daily Journal ◻️

Goal: coherent live truth about the user's digital/physical/communication environment.

Deliverables:

- World Model for people/places/devices/apps/projects/tasks/commitments;
- freshness/confidence/provenance;
- Perception Fabric across screen/device/sensor/location/communication/acoustic inputs;
- time/date/timezone context;
- weather/forecast as live external context;
- calendar/free-busy/current commitments;
- tasks/deadlines/dependencies;
- notification events/content where authorized;
- media session/activity/focus evidence where legitimately available;
- phone/device/Connection Grid state;
- Passive/Aware/Guard/Away/Sleep Sentry;
- optional Context Capture / Daily Journal;
- independent perceive/retain/act boundaries;
- importance/urgency/confidence/interruptibility scoring;
- weak activity evidence remains uncertain rather than mind-reading.

Exit: OSCAR can answer `what is true now?` and provide a current, source-qualified basis for Chief-of-Staff decisions.

## Slice 12 — Commissioning / setup ◻️

Goal: safely commission the personal system.

Deliverables include identity, Persona, Personal Policy starter rules, Voice Identity/Match/Map, Connection Grid pairing, cloud/model setup, Sunday/Desktop/Edge pairing, Sentry/capture setup and a human-readable perceive/retain/act permission matrix with evidence-backed readiness tests.

## Slice 13 — Avatar / presence UI ◻️

Goal: make real state physically legible.

Deliverables include reusable blue-shell/yellow-puck presence, weighted spring/inertia, runtime states, reduced motion and compact/overlay/widget variants. The avatar expresses real state; it never substitutes for it.

## Slice 14 — Executive Planner + durable Workers + learning ◻️

Goal: scale from isolated requests to durable delegated responsibility and Chief-of-Staff coordination.

Deliverables:

- Executive Planner across priority/deadline/dependency/resources/risk;
- explicit commitment model: fixed events, flexible blocks, deadlines/tasks, communication follow-ups, preparation/travel buffers, Worker dependencies;
- schedule conflict detection;
- focus/study/build block protection;
- weather/location/travel-aware planning when current evidence exists;
- bounded automatic replanning only under explicit Personal Policy;
- proactive morning/day brief and `what needs me now?` synthesis;
- interruption policy from attention/urgency evidence;
- Worker lifecycle/leases/checkpoints/reclaim;
- self-repair/reroute/escalation;
- Skills/Protocols and evaluated learned automation;
- Artifact/Result handoff.

See [Chief of Staff](CHIEF-OF-STAFF.md).

## Slice 15 — Physical / device capability expansion + specialist engineering ◻️

Broaden Edge/device onboarding, smart-home/environment adapters, cameras/sensors/actuators and specialist CAD/circuit/simulation/3D/numerical/diagnostic routing without creating a separate hardware-workbench runtime dependency.

## Slice 16 — Reliability/security/truthfulness hardening ◻️

Deliberately break providers, auth, Grid nodes, leases, Workers, capture sources, persona/voice identity, privacy/retention, notification/assistant/overlay permissions and physical paths. Verify graceful degradation, revocation and no false-success behavior.

## Slice 17 — Unified alpha ◻️

Run one end-to-end developer-alpha scenario across:

```text
perception / communication
→ World Model / Chief-of-Staff context / Jev
→ Personal Policy + Persona
→ Executive / Durable Runtime
→ capability / search / model routing
→ Connection Grid node
→ Worker / device / action
→ ledger / artifact
→ verification
→ voice/text/Sunday report
```

The alpha is accepted only for the surfaces genuinely exercised. Unavailable hardware/accounts/platform behavior stays partial/unknown.

## Review clubs

| Club | Slices | Focus |
|---|---:|---|
| A — Brain | 01–04 | Core + Jev + Transport/Grid foundation + adaptive Model Router |
| B — Can Do Work | 05–06 | Real machine Worker + continuation + memory/Personal Policy |
| C — Embodied Core | 07–08 | Edge/reflexes + Voice/Identity/Persona |
| D1 — Sunday | 09 | Android embodiment + communication + owner controls |
| D2 — Desktop | 10 | Desktop interaction runtime |
| E1 — Awareness | 11–13 | World Model/Sentry + commissioning + presence |
| E2 — Executive | 14 | Chief-of-Staff planner + Workers + learning |
| F — Unified Alpha | 15–17 | Physical expansion + hardening + integrated alpha |

Manual integration checkpoints remain in [BUILD-GATES.md](BUILD-GATES.md).

## Current next step

Finish the **local Windows Club B acceptance** before advancing to Slice 07. Gate B remains partial until the real laptop proves useful machine delegation and continuity. The Sunday/Chief-of-Staff direction is already canonical so later implementation does not need to rediscover product intent.
