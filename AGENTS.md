# AGENTS.md

Canonical instructions for Codex and other coding agents working on OSCAR.

Keep this file compact; detailed truth lives in the linked domain docs.

## Read first

For any implementation task:

- `README.md`
- `ENGINEERING.md`
- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/EPISTEMIC-INTEGRITY.md`
- relevant domain docs.

Load additionally when relevant:

### Transport / availability / routing

- `docs/NATIVE-INFRASTRUCTURE.md`
- `docs/CONNECTION-GRID.md`
- `docs/MODEL-ROUTING.md`
- `docs/RUNTIME-FOUNDATIONS.md`

### Search / live truth

- `docs/SEARCH-FRESHNESS.md`

### Ambient context / schedule / proactive assistance

- `docs/CHIEF-OF-STAFF.md`
- `docs/PERSONAL-POLICY.md`
- `docs/COMMUNICATION.md`
- `docs/SURFACES.md`

### Voice / Sentry / communication

- `docs/VOICE-SENTRY.md`
- `docs/COMMUNICATION.md`
- `docs/ONBOARDING.md`
- `docs/SECURITY.md`

### Persona / UI / motion

- `DESIGN.md`
- `TASTE.md`
- `docs/PERSONA.md`
- `docs/UI-AVATAR.md`
- `docs/SUNDAY-DESIGN.md`
- `docs/SURFACES.md`

### Connectors / continuity

- `docs/CONNECTOR-FABRIC.md`
- `docs/CLUB-B-CHECKPOINT.md`
- `docs/MEMORY.md`
- `docs/PERSONAL-POLICY.md`

### Workers / orchestration

- `docs/ORCHESTRATION.md`
- `docs/WORKERS.md`
- `docs/RUNTIME-FOUNDATIONS.md`

Treat these as current product contract. If code/docs disagree, investigate rather than silently choosing one.

## Working style

- One coherent slice/sub-slice at a time.
- Inspect existing infrastructure before inventing replacements.
- Prefer the smallest robust design.
- High cohesion / low coupling; avoid god objects and wrapper forests.
- Do not create fake/demo states that imply unfinished capability works.
- Preserve failure, blocked, partial and unknown states.
- Use specialist tools when they are the right executor.
- Do not add a dependency without a concrete reason.
- Update durable docs in the same change when a real invariant changes.
- When an objective is freshness-sensitive, retrieve current authoritative evidence before relying on memory/model priors.

## Native infrastructure

Do **not** make Latch or SwitchRoute runtime dependencies.

```text
Latch ideas/logic       → native OSCAR Transport + Capability Fabric
SwitchRoute ideas/logic → native OSCAR Model Router
```

Reuse proven code/patterns only when they still fit OSCAR contracts/tests.

## Connection Grid

OSCAR availability spans:

```text
Sunday      = preferred owner control / approvals / notifications
Cloud       = replaceable rendezvous + durable coordination
Desktop     = high-capability execution
Edge        = local presence / reflex / safety
```

Rules:

- no ordinary desktop is the permanent host;
- nodes advertise only real current capabilities;
- any cross-node control is scoped and rechecked at the target;
- Sunday may pause/cancel/revoke user-authorized work but never bypass local hardware safety;
- cloud is replaceable/free-tier/paid/BYOC infrastructure, not identity;
- executor loss expires leases and must not leave tasks falsely `working`;
- remote sleep/shutdown/wake is offered only when a real capability exists;
- availability is explicit: Full / Connected / Local / Reflex-only / Offline where useful.

See `docs/CONNECTION-GRID.md`.

## Ambient Chief-of-Staff invariant

OSCAR is not merely an on-demand assistant surface. It should continuously integrate authorized current context and help coordinate the user's day.

Potential live inputs include time/date/timezone, weather, calendar, tasks/deadlines, location/mobility, device/app/media state, notifications, communications, Worker/Protocol state and Sentry/Edge observations.

Rules:

- volatile context is freshness-qualified and source-backed;
- weak activity signals remain uncertain rather than becoming confident mind-reading;
- perception, durable retention and authority to act are separate grants;
- schedule/task/communication mutations require real capability + permission/Personal Policy + verification;
- proactivity ranges from silent context update to inform/suggest/act/interrupt rather than one global `proactive` switch;
- attention state should reduce unnecessary interruption and visual obstruction;
- if OSCAR can safely and legitimately perform a user objective itself, do not force the user through unnecessary manual steps.

See `docs/CHIEF-OF-STAFF.md`.

## Evidence and completion claims

A tool call, commit, Worker/model message or API `success` is not automatically proof of the objective.

For meaningful work:

1. define observable completion;
2. execute;
3. inspect authoritative resulting state;
4. run appropriate tests/device/visual/source verification;
5. report only what evidence supports.

Use distinctions such as `reported`, `verifying`, `verified`, `partially verified`, `failed`, `blocked`, `unknown`.

Do not say `done`, `fixed`, `works` or equivalent when evidence is only partial/reported.

## Core invariants

1. Laptop/desktop nodes are optional.
2. Hardware safety is local/deterministic.
3. Reflex actions do not wait for frontier models.
4. Voice and text share task/context state.
5. Sunday is OSCAR on the phone, not a second assistant.
6. LRA + Supermemory provide continuous history/memory.
7. World Model owns current-state representation; memory is not automatically current truth.
8. Jev chooses execute/retrieve/verify/reason/delegate/ask class.
9. Model routing and executable capability selection are separate.
10. Nodes advertise capabilities dynamically.
11. Consequential actions are permission-aware, attributable and evidence-backed.
12. Long-running work uses Durable Execution Runtime when persistence/recovery matters.
13. Voice Match and Voice Map are distinct; recognition is not authorization.
14. OSCAR owns stable Voice Identity independent of TTS vendor.
15. Sentry is persistent local-first awareness when enabled.
16. Sentry awareness, active Listening and durable recording/capture are separate states.
17. Optional Context Capture/Daily Journal is source-specific, explicit and retention-controlled.
18. OSCAR's own TTS is excluded from Voice Map/wake loops while human barge-in remains functional.
19. Connection Grid degrades rather than treating one node as hidden host.
20. Persona changes expression, never truth/safety/permission.
21. Freshness-sensitive/current claims require live authoritative retrieval when available; recalled/model-prior data must not be presented as current truth.
22. OSCAR is a context-aware Chief of Staff: current context can drive quiet assistance, schedule/task coordination and proactive suggestions/actions within explicit authority.
23. `CAN PERCEIVE`, `CAN RETAIN` and `CAN ACT` are independent permission/retention boundaries.

## Search / freshness rules

Search is a first-class capability, not a fallback excuse for stale reasoning.

- classify whether current/live truth materially matters;
- prefer authoritative APIs/live sources over web summaries when available;
- preserve source URL/identity, publication/update time and retrieval time;
- stale cached/provider manifests are hints, not current authority;
- model/provider availability, pricing, quota and deprecation checks are freshness-sensitive;
- before changing provider metadata, retrieve current official catalogs/deprecations and credential-visible inventory; preserve source/time/product scope;
- distinguish provider support, account listing, generation and funding; a 403 against a retired model does not diagnose credential health;
- preserve old evidence with an explicit correction; do not rewrite failed observations;
- the manifest is a bootstrap/retirement seed; hosted inventory refresh must fail closed when stale/unavailable;
- keys can share capacity: configure account products/quota pools and never multiply capacity by credential count; unknown cost/quota remains UNKNOWN;
- if live lookup is unavailable, report that the answer may be stale instead of guessing;
- Tavily is the first implemented search adapter with three credential slots, not an architectural dependency;
- search results are evidence inputs, not automatically verified truth.

See `docs/SEARCH-FRESHNESS.md`.

## Sentry / capture rules

Persistent Sentry may consume local wake/VAD/Voice Map/sound/device/presence events continuously when enabled.

Do not equate that with continuous cloud STT.

Optional capture may include selected calls/messages/mail/meetings/in-person conversations **only** where platform capability, permission and consent/legal requirements allow.

Keep separate:

```text
local awareness
active conversational STT
ambient/context STT
raw audio retention
transcript retention
summary retention
memory extraction
```

Unsupported app/call capture remains unsupported.

Never design covert recording as the default.

## Sunday / Android rules

Sunday should use legitimate Android platform capabilities rather than pretending to have system privilege.

- target the Android assistant role / voice-interaction contracts where supported and explicitly selected by the user;
- a persistent Orb overlay is optional, permissioned and attention-aware; it may retreat during video/reading/presentation/focus rather than obstruct content;
- home-screen widgets should be glanceable state/action surfaces, not dashboards;
- notification-listener access may feed current context only after explicit user grant;
- notification visibility does not imply full app access;
- a notification reply is actionable only when a legitimate reply action/`RemoteInput` or another authorized integration exists;
- Android/OEM-specific behavior remains unverified until exercised on the target device;
- overlay/notification/assistant permissions never imply retention or action authority.

See `docs/SUNDAY-DESIGN.md`, `docs/CHIEF-OF-STAFF.md` and `docs/SECURITY.md`.

## Persona rules

Persona may configure humor, candor, warmth, formality, brevity, playfulness, initiative, pushback and context triggers.

- factual integrity cannot be lowered;
- serious/security/safety context may suppress humor;
- Persona cannot grant permissions;
- Persona cannot hide uncertainty/failure;
- user can edit Persona manually or by natural language;
- Persona and Personal Policy are different layers.

See `docs/PERSONA.md`.

## Voice/audio rules

- Voice Input, Voice Identity, Voice Match and Voice Map remain separate contracts.
- Unknown speakers remain unknown rather than guessed.
- Voice profiles/embeddings are sensitive.
- Self-voice suppression uses playback reference/echo cancellation/TTS tagging where feasible.
- Test barge-in while OSCAR speaks.

## Specialist delegation

Examples:

- repository implementation/debugging → Codex or another coding capability;
- GUI-only operation → computer-use capability;
- knowledge workspace → native connector/plugin;
- engineering/design/simulation → installed specialist tools + Edge/device capabilities;
- model reasoning → Jev then native Model Router;
- physical device action → advertised Edge/device capability.

## UI / design quality

Durable direction: **Quietly Alive + Playful Precision**.

- warm restrained material system;
- one dominant idea per surface;
- progressive disclosure;
- fluid state continuity: State A should physically become State B where practical;
- avatar is a weighted presence object, not a giant mascot;
- desktop/mobile are native distinct compositions;
- no generic AI dashboard, card wall, glass/neon/purple-gradient slop or fake telemetry;
- Sentry must not look like surveillance software;
- Connection Grid must not look like a network-admin console;
- Persona must not look like raw LLM parameter tuning.

For design exploration, use real shipping-app research + coded UI + visual critique + Kaizen iteration. `image-prompts/` is reference material, not canonical implementation.

Simplicity must preserve craftsmanship. Prototypes that establish a visual pattern must demonstrate real depth, expression, motion, finish and verification now rather than deferring those details to a later implementation.

## Testing expectations

Every slice has an explicit checklist including relevant failure/reconnect/cancellation/idempotency/safety cases.

Where relevant test:

- provider/node loss;
- Connection Grid reconnect/lease expiry;
- remote task continuation/cancel;
- freshness-sensitive query vs stale cache/model prior;
- search credential failover and source provenance;
- wake/VAD/STT/TTS latency;
- barge-in/self-voice suppression;
- Voice Match/Voice Map behavior;
- capture pause/retention/source-unavailable behavior;
- Persona context trigger without safety/truth regression;
- Android assistant/overlay/widget/notification behavior on a real target phone separately from emulator tests;
- attention-aware Orb retreat/reappearance without making overlay state a correctness dependency;
- notification source exclusions and perceive/retain/act separation;
- schedule mutation readback and fixed-vs-flexible commitment rules;
- reduced motion / target viewport visual inspection;
- simulator vs real hardware separately.

## Secrets / personal data

Never commit or casually log:

- API/provider keys;
- OAuth/device credentials;
- private memory exports;
- raw conversation archives;
- Voice Map embeddings/profiles;
- private camera/mic recordings;
- local `.env` secrets.

Use ignored local fixtures or synthetic test data.

## Club B reference boundaries

- Use Connector Fabric manifests as Grid catalog sources; do not add another registry.
- Stage private connector inputs as transient references; expired inputs BLOCK, never replay blindly.
- Read-back needs granted read scope and the same account; mutation reports remain REPORTED.
- Machine terminal/agent execution is opt-in trusted host authority, not cwd sandboxing.
- Selected retention requires authorization; recalled memory stays RECALLED.
- Windows/user hardware, authenticated private accounts and Supermemory remain unverified.
- Gate B remains PARTIAL until its actual manual criteria are met.
