# Build Gates

Build Gates group detailed roadmap slices into larger manual verification checkpoints. They do not replace slice exit conditions.

The fast developer-alpha target remains 2–3 days for a vertical proof, followed by continuous hardening.

At each Gate:

1. run automated tests;
2. run the manual scenarios;
3. inspect authoritative resulting state;
4. record blockers/limitations;
5. do not upgrade simulated/reported behavior to verified real behavior;
6. continue only when the foundation is coherent enough.

## Gate A — Brain

**Slices:** 01–04

Prove:

```text
request
→ Jev
→ capability/model decision
→ native transport/router
→ execution
→ evidence
→ verification
→ truthful report
```

Manual scenarios:

- canonical file-write/read verification objective;
- fake executor success must not become verified;
- deterministic request avoids heavy model;
- Auto/Fast/Balanced/Heavy routing;
- manual provider/model selection;
- failed credential/provider fallback;
- Local mode with no silent cloud fallback;
- simulated remote capability node connect/disconnect;
- initial Connection Grid node/health state;
- coherent reference coordinator/Transport/Grid path with durable objective preservation;
- route/usage history contains no secrets.

**Pass:** native core/transport/model routing works without Latch/SwitchRoute deployment and remote node loss does not erase objective state.

Current checkpoint: **PASS for Club A foundation — all three Tavily slots authenticate;
source provenance, bounded official constraints and qualified UNKNOWN semantics pass.**
Core Loop/Jev/reference Grid proofs and the focused routing
acceptance remain verified; see [CLUB-A-CHECKPOINT.md](CLUB-A-CHECKPOINT.md).

Acceptance does not require simultaneous availability of every provider. A genuine
no-eligible-route BLOCKED result is correct under current capability/funding/capacity
policy. Temporary provider limits are not architectural defects when bounded
reranking finds an eligible alternative, or truthful blocking records that none
exists. Shared cooldowns must not disable unrelated pools; UNKNOWN remains UNKNOWN.
Live combined search is verified with current native inventories and official-source
evidence/explicit UNKNOWN resolutions; native inventory or synthetic tests alone
cannot establish this acceptance. **Club A acceptance remains preserved; the current Club B reference foundation
is PARTIAL, as recorded in [CLUB-B-CHECKPOINT.md](CLUB-B-CHECKPOINT.md).**

The current foundation review accepts coherent reference Transport/Grid contracts. Public TLS/outbound rendezvous, independent network stores and a cloud coordinator path using a configured deployment target remain later Grid integration acceptance requirements; they are not claimed verified by Gate A. This refines the previous public-deployment gate expectation without changing the architecture or silently completing broader slice deliverables.

## Gate B — Can Do Work

**Slices:** 05–06

Prove a useful real machine objective plus memory/policy continuity.

Manual scenarios:

- real repository bug delegated to coding specialist then independently tested;
- terminal/filesystem/browser/computer-use capability;
- installed app selected as capability, not host;
- machine node disconnect mid-task → blocked/recoverable, not false success;
- long-running task remains active while user leaves;
- Sunday/cloud can observe and cancel/pause that task through Grid test harness/surface where available;
- optional machine sleep/shutdown after verified completion if capability is real;
- stale memory vs authoritative live source → live source wins;
- natural-language Personal Policy change affects later behavior.

**Pass:** OSCAR can do verified useful work while remaining conceptually independent of the computer executing it.

## Gate C — Embodied OSCAR

**Slices:** 07–10

Prove physical, voice, mobile and desktop embodiments share one OSCAR.

Manual scenarios:

- ESP32/Pico advertises capabilities and executes a safe action with local safety independent of cloud;
- wake OSCAR by voice and complete a real task;
- barge-in/self-voice suppression;
- Voice Match vs Voice Map distinction;
- multi-device voice arbitration;
- Persona profile changes tone/voice/motion without changing truth/permission;
- Sunday owner-control surface shows Connection Grid state;
- start task on Desktop, leave, inspect/control from Sunday;
- one supported communication path;
- Dictate/Edit/Ask/Act against real desktop context;
- degraded Grid state when one embodiment goes offline.

**Pass:** phone, desktop, voice and Edge feel like one intelligence with shared task state and owner control.

## Gate D — JARVIS Layer

**Slices:** 11–14

Prove current-world awareness, persistent Sentry, commissioning and durable delegated work.

Manual scenarios:

- combine at least three live sources into one World Model answer;
- stale source becomes uncertain/unknown;
- Sentry remains persistently aware without active conversation;
- verify UI/runtime distinction: Sentry Aware vs Listening vs Muted vs Awareness Off;
- trigger a physical/acoustic Sentry event and verify policy-aware escalation;
- if Context Capture/Daily Journal enabled: capture one legitimately supported source, verify retention policy, pause and delete/forget path;
- unsupported call/app capture must remain unsupported;
- first-time commissioning includes Persona, Grid and capture privacy choices;
- create a durable Worker and inspect progress/evidence;
- competing objectives exercise Executive Planner;
- teach one workflow and keep it experimental until evaluated;
- avatar states match actual Working/Verifying/Blocked/Done state.

**Pass:** OSCAR maintains coherent current awareness, durable responsibilities and optional continuity capture without collapsing privacy or evidence boundaries.

## Gate E — Unified Alpha

**Slices:** 15–17

Deliberately break the integrated system.

Manual scenarios:

- onboard/control at least one additional physical capability;
- provider/auth failure → bounded recovery;
- cloud coordinator loss while desktop task continues locally;
- Sunday offline while existing permitted work continues without fabricated owner approval;
- Desktop loss → lease expiry/reclaim;
- Edge loss → physical capabilities disappear while software OSCAR remains available;
- Grid reconnect/resync;
- Action Ledger/Undo for reversible and irreversible actions;
- unknown/partial/blocked/failed reporting;
- Voice Match spoof / Voice Map false-positive checks;
- capture-source failure, retention/deletion and privacy regression checks;
- Persona cannot reduce truthfulness/safety/confirmation;
- one complete scenario across perception/communication → World Model/Jev → policy → planning → capability/model routing → Grid node/Worker/device → ledger/artifact → verification → voice/text result.

**Pass:** major subsystems operate as one evidence-backed developer alpha and remaining limitations are explicit.

## Fast-build cadence

```text
Day 1
Gate A + core Gate B path

Day 2
Gate B completion + Gate C core paths

Day 3
Gate C completion + Gate D/E integration shell
```

This is intentionally aggressive. Anything not genuinely verified remains planned/partial and is hardened afterward.

## Status

| Gate | Slices | Status |
|---|---|---|
| Gate A — Brain | 01–04 | PASS for Club A foundation — focused routing and final evidence-qualified search accepted; manual review stop |
| Gate B — Can Do Work | 05–06 | PARTIAL — reference foundation passes; full manual criteria pending |
| Gate C — Embodied OSCAR | 07–10 | Planned |
| Gate D — JARVIS Layer | 11–14 | Planned |
| Gate E — Unified Alpha | 15–17 | Planned |

A Gate status changes only after its manual checklist has actually been run.
