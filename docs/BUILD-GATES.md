# Build Gates

This document groups OSCAR's detailed implementation slices into larger manual verification milestones.

The slice roadmap remains canonical for implementation scope. Build Gates do **not** replace individual slice exit conditions. They are deliberate stop points where the combined system is exercised manually before adding more surface area.

The current development strategy is a fast developer-alpha sprint followed by continuous hardening. A 2–3 day sprint is an execution target, not a reason to claim unverified completeness or skip safety/reliability work.

## Gate philosophy

At each Gate:

1. run the relevant automated tests;
2. run the manual scenarios below;
3. inspect real resulting state rather than relying only on executor/tool success;
4. record blockers and limitations;
5. do not call the Gate passed when a required scenario is only simulated unless the Gate explicitly allows simulation;
6. continue to the next group only when the current foundation is coherent enough to support it.

A Gate may be passed for **developer alpha** while still carrying clearly documented hardening follow-ups.

## Gate A — Brain

**Slices:** 01–04

**Purpose:** prove that OSCAR can understand a request, choose a path, execute through typed contracts, route intelligence automatically, verify results and report truthfully.

Includes:

- OSCAR Core Loop;
- TypeSafe Jev;
- native OSCAR Transport + Capability Catalog;
- native OSCAR Model Router;
- provider/model/credential pools;
- automatic + manual routing;
- evidence/verification boundary.

### Manual scenarios

1. Run the canonical test-workspace file objective and verify independent completion evidence.
2. Force an executor to report success without making the expected change; verify OSCAR refuses to mark it complete.
3. Route a deterministic request without invoking a heavy model.
4. Route a reasoning request through Auto mode and inspect the provider/model/credential decision.
5. Exercise Fast/Balanced/Heavy Duty routing on representative requests.
6. Pin a provider/model manually and verify policy still applies.
7. Put one credential into a failed/rate-limited state and verify eligible credential/provider fallback.
8. Use Local mode and verify no silent cloud fallback occurs.
9. Disconnect/reconnect a simulated capability node and verify capability state changes cleanly.
10. Inspect route/usage history and confirm raw secrets/prompt contents are not exposed.

### Gate A pass condition

A request can travel through:

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

with explainable routing and no dependency on separate Latch or SwitchRoute deployments.

---

## Gate B — Can Do Work

**Slices:** 05–06

**Purpose:** make OSCAR useful on a real computer and persistent enough to remember context and obey explicit user policy.

Includes:

- first real machine Worker/node;
- terminal/filesystem/Git;
- Codex and other available coding executors;
- browser/computer-use path;
- installed-app capability discovery where technically available;
- LRA + Supermemory;
- Personal Policy;
- live context/search;
- source authority.

### Manual scenarios

1. Give OSCAR a real repository bug; delegate implementation to a coding specialist and independently rerun tests/inspect repository state.
2. Use terminal/filesystem capabilities directly for a simple task.
3. Exercise browser/computer-use fallback on an action without a stronger API/CLI path.
4. Disconnect the machine node mid-task and verify the task becomes recoverable/blocked rather than falsely complete.
5. Ask about an earlier project decision and verify memory retrieval.
6. Ask a current-state question where stale memory conflicts with a live source; verify the live source wins.
7. Create/edit a Personal Policy rule in natural language and verify it affects a later decision.
8. Verify a coding executor or installed app is selected as a capability, not treated as the OSCAR host.

### Gate B pass condition

OSCAR can complete and verify a useful real-world software objective, recover historical context, respect explicit policy and remain conceptually independent of the computer providing the capabilities.

---

## Gate C — Embodied OSCAR

**Slices:** 07–10

**Purpose:** attach the physical, voice, phone and desktop embodiments to the already working OSCAR core.

Includes:

- ESP32/Pico Edge + reflexes;
- Voice Input;
- stable OSCAR Voice Identity;
- Voice Match;
- Voice Map;
- multi-device voice arbitration;
- Sunday;
- communication/Channel Gateway;
- Desktop Interaction Runtime;
- terminal/computer-use/installed-app control surfaced naturally.

### Manual scenarios

1. ESP32/Pico node advertises capabilities and executes a safe test action while local safety remains independent of cloud intelligence.
2. Wake OSCAR by voice, complete a real core task and receive spoken output.
3. Interrupt OSCAR while it is speaking and verify barge-in/self-voice suppression.
4. Verify Voice Match and Voice Map produce distinct authorization/perception outcomes.
5. Trigger the same wake event near multiple surfaces and verify only one owns the turn.
6. Start a task on desktop and continue/inspect it from Sunday.
7. Exercise one real communication path supported by the device/platform.
8. Use Dictate/Edit/Ask/Act against current desktop context.
9. Ask OSCAR to use terminal, computer use or an installed application and verify the strongest available legitimate capability path is selected.

### Gate C pass condition

OSCAR feels like the same intelligence across desk hardware, voice, phone and desktop, with shared task state and no separate assistant silos.

---

## Gate D — JARVIS Layer

**Slices:** 11–14

**Purpose:** move from a capable assistant to a persistent contextual executive system.

Includes:

- World Model;
- Perception Fabric;
- acoustic/physical Sentry;
- first-run commissioning;
- avatar/presence state;
- Executive Planner;
- durable Workers;
- Skills/Protocols;
- teach-by-demonstration;
- learned automation evaluation.

### Manual scenarios

1. Combine current state from at least three sources into one World Model answer.
2. Let one source go stale and verify OSCAR exposes uncertainty instead of treating stale state as current.
3. Trigger an acoustic/physical Sentry event and verify local-first processing plus policy-aware escalation.
4. Run first-time commissioning end to end, including voice/privacy choices and verified health.
5. Create a Worker in natural language, let it run in the background, then inspect its progress/evidence.
6. Run two competing objectives and verify the Executive Planner resolves priority/resource conflict.
7. Teach or capture one reusable workflow; keep it experimental until evaluation supports promotion.
8. Confirm avatar/notification state reflects actual Working/Verifying/Blocked/Done state.

### Gate D pass condition

OSCAR maintains a coherent current situation, can manage delegated responsibilities over time and proactively surfaces only meaningful events under policy.

---

## Gate E — Unified Alpha

**Slices:** 15–17

**Purpose:** integrate engineering/workbench reach, failure handling, security and the complete end-to-end developer alpha.

Includes:

- Kinetable/general engineering integration;
- spatial/workbench capabilities;
- self-maintenance;
- reliability/security/truthfulness pass;
- unified alpha scenario.

### Manual scenarios

1. Route an engineering objective to the appropriate specialist and return a typed artifact/result.
2. Onboard at least one approved hardware capability into OSCAR.
3. Expire/break a provider or adapter credential and verify self-diagnosis plus bounded recovery/escalation.
4. Simulate provider/node loss during a durable task and verify reclaim/restart behavior.
5. Verify Action Ledger/Undo for reversible and irreversible actions.
6. Exercise unknown/partial/blocked/failed reporting deliberately.
7. Run Voice Match spoof/unknown-speaker and self-voice/echo checks.
8. Run one complete scenario crossing perception/communication → World Model/Jev → policy/planning → capability/model routing → Worker/device → Action Ledger/artifact → verification → voice/text report.

### Gate E pass condition

The major OSCAR subsystems operate as one evidence-backed developer alpha. Remaining limitations are explicitly documented rather than hidden behind a `complete` label.

## Suggested fast-build cadence

The 2–3 day sprint should optimize for **vertical proof**, not superficial breadth.

A practical target is:

```text
Day 1
Gate A + core Gate B path

Day 2
Gate B completion + Gate C core paths

Day 3
Gate C completion + Gate D/E integration skeleton
```

This is intentionally aggressive. When a subsystem cannot be genuinely verified in that window, leave it planned/partial and continue iterating after the initial alpha.

## Gate status

| Gate | Slices | Status |
|---|---|---|
| Gate A — Brain | 01–04 | Planned |
| Gate B — Can Do Work | 05–06 | Planned |
| Gate C — Embodied OSCAR | 07–10 | Planned |
| Gate D — JARVIS Layer | 11–14 | Planned |
| Gate E — Unified Alpha | 15–17 | Planned |

Gate status should only change after the manual checklist has actually been run against the relevant implementation.
