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

- **Persistent craft standard:** preserve requested detail, finish and verification throughout OSCAR; a small scope still deserves complete execution. Study user references closely, including material depth, lighting, contact shadows, facial proportions, expressive curves and physical motion.
- Establish that quality in the runnable prototype, inspect it against the references and iterate on concrete gaps. Do not defer craft to the eventual production app or treat layout approval as approval of unfinished avatar depth/expression.
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

## Testing expectations

Every slice has an explicit checklist including relevant failure/reconnect/cancellation/idempotency/safety cases.

Where relevant test:

- provider/node loss;
- Connection Grid reconnect/lease expiry;
- remote task continuation/cancel;
- wake/VAD/STT/TTS latency;
- barge-in/self-voice suppression;
- Voice Match/Voice Map behavior;
- capture pause/retention/source-unavailable behavior;
- Persona context trigger without safety/truth regression;
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
