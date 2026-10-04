# OSCAR Engineering Standard

This file is the durable engineering quality bar for OSCAR. It applies to application code, services, firmware, shared libraries, protocols, plugins, skills and automation.

The goal is not theoretical architectural purity. The goal is code that remains understandable, testable, replaceable and dependable as OSCAR grows across many runtimes and devices.

## North star

**Simple boundaries, strong contracts, boring reliability.**

Prefer the smallest design that solves the current problem cleanly and leaves a clear path for change. Avoid both short-lived hacks and speculative architecture for requirements that do not yet exist.

A good change should make the system easier to understand or at minimum not make its code health worse.

## 1. Keep the system simple

- Add a component, abstraction, dependency, service or layer only when it solves a concrete problem.
- Keep critical paths short, especially wake/reflex, safety, permissions and task cancellation.
- Prefer straightforward control flow over cleverness.
- Do not introduce generic frameworks for one current use case.
- Do not implement hypothetical future requirements unless a current contract requires the extension point.
- Prefer deleting accidental complexity over documenting around it.

**Rule:** abstraction must pay rent. If removing an abstraction makes the code easier to understand without losing a real requirement, remove it.

## 2. Modular by responsibility, not by file count

Modules should have **high cohesion and low coupling**.

- Group code that changes for the same reason.
- Keep unrelated policy, transport, persistence, UI and device concerns separate.
- Depend on explicit interfaces/contracts across subsystem boundaries.
- Keep domain logic independent from transport/framework details where practical.
- Adapters may depend on domain contracts; domain code should not depend on a specific provider unless that provider is itself the domain.
- Avoid god objects, manager classes that own unrelated concerns, global mutable state and circular dependencies.

A module is not “modular” merely because the implementation is split across many files. Prefer a few clear modules over fragmentation into tiny wrappers with no independent meaning.

## 3. Reuse behavior, not accidental similarity

- Extract shared code when the behavior and invariants are genuinely shared.
- Do not create premature utilities because two call sites happen to look similar.
- Prefer one authoritative implementation for protocol validation, permission checks, retries, serialization and safety-critical rules.
- Keep platform-specific behavior behind narrow adapters instead of spreading `if platform` logic through domain code.
- Reusable components must have a clear owner, contract and test surface.

**Rule of three is guidance, not law:** tolerate small duplication until the shared concept is understood; then extract the concept, not merely the repeated syntax.

## 4. Strong, explicit contracts

OSCAR spans firmware, mobile, desktop, cloud services and external agents, so boundaries must be unambiguous.

- Prefer typed domain objects over loosely shaped dictionaries/maps.
- Make invalid states difficult or impossible to represent when practical.
- Validate untrusted/external input at boundaries.
- Define required/optional fields explicitly.
- Use stable identifiers, versioned schemas and documented compatibility expectations for cross-process/device protocols.
- Distinguish commands, events, state snapshots, artifacts/results and errors rather than overloading one message type.
- Preserve correlation/task IDs across distributed work.
- Do not silently coerce malformed input into plausible values.

For public or cross-component APIs, design for evolution: additive compatible changes first; breaking changes require an explicit migration/version plan.

## 5. Dependency discipline

Every dependency creates maintenance, security and compatibility cost.

Before adding one:

1. Is the capability already present in the language/platform/repository?
2. Is the problem large enough to justify another dependency?
3. Is the project actively maintained and appropriate for the target runtime?
4. Can it be isolated behind an adapter so OSCAR can replace it later?
5. What happens if it becomes unavailable or changes behavior?

- Pin/lock versions through the ecosystem's normal mechanism.
- Do not wrap every dependency “just in case”; wrap external systems when OSCAR needs a stable internal contract or multiple implementations.
- Avoid duplicate libraries that solve the same problem without a clear reason.

## 6. Reliability is designed, not patched on

Assume networks fail, processes restart, devices disappear and providers time out.

- Define timeouts for remote operations.
- Retry only transient failures and use bounded retry/backoff.
- Avoid retry storms and duplicated retry layers.
- Make repeatable remote commands idempotent where feasible.
- Persist enough task/Protocol state to recover long-running responsibilities safely.
- Use durable checkpoints/leases/heartbeats where work must survive executor loss.
- Detect abandoned/stuck/zombie work and make reclaim behavior explicit.
- Isolate failures so one provider/node does not collapse unrelated OSCAR capabilities.
- Use health/status reporting where a component is long-lived.
- Prefer graceful degradation to pretending a capability is available.
- Explicitly define safe defaults and restart/reconnect behavior.

Hardware and security-critical behavior must fail safe, not merely fail quietly.

## 7. Errors are part of the API

- Never swallow errors that change user-visible or system behavior.
- Preserve enough context to diagnose failures without leaking secrets.
- Separate expected domain failures from programmer defects and infrastructure failures.
- Return/propagate structured errors across important internal boundaries.
- Messages should say what failed and, where useful, whether it is retryable or requires user action.
- Do not use exceptions/panics for routine control flow where the language provides explicit result types.

A blocked task is a real state. Do not present it as `thinking`, `working` or success.

## 8. Epistemic integrity and verification

OSCAR must never present an unverified result as fact merely because a tool, Worker or model reported success.

- Distinguish execution success from objective verification.
- Preserve task states such as `result_received`, `verifying`, `verified`, `partially_verified`, `failed`, `blocked` and `unknown` where they matter.
- Preserve claim/evidence states such as direct/known, inferred, recalled, reported, verified and unknown.
- A Worker/tool response is testimony/evidence, not automatically truth.
- Define a verification strategy for consequential changes before declaring completion.
- Prefer independent verification when practical: read-after-write, tests after code edits, browser/device checks after UI/hardware changes, API reads after mutations.
- Report limitations explicitly when verification covers only part of the objective.
- Never upgrade memory, inference or another agent's report to `verified` without evidence.
- Unknown is preferable to guessing.
- User confidence or preference does not alter factual state; disagree when evidence/constraints require it.
- When new evidence contradicts an earlier claim, correct it explicitly and propagate the correction to affected state/docs/tasks.

See `docs/EPISTEMIC-INTEGRITY.md` for the canonical product contract.

**Completion rule:** only claim unqualified `Done`/`Fixed` when the completion condition has been verified wherever verification is technically possible.

## 9. State ownership must be obvious

For each mutable piece of state, an engineer should be able to answer: **who owns it, who may change it, and what is authoritative?**

- Prefer a single authoritative owner for mutable state.
- Derive/cache secondary state rather than allowing multiple components to mutate competing copies.
- Avoid global mutable state.
- Make persistence and retention explicit.
- Separate durable task/Protocol state from transient UI state and derived memory.
- External live systems remain authoritative for their current state; cached memory is not automatically truth.

## 10. Concurrency requires a reason

Concurrency can improve latency and responsiveness but rapidly increases failure modes.

- Add parallelism only when it provides measurable or necessary value.
- Make cancellation and ownership explicit.
- Avoid shared mutable state where message passing/ownership works better.
- Bound queues, buffers and Worker counts.
- Define ordering guarantees when consumers rely on them.
- Test races, cancellation, shutdown and reconnect paths for concurrent components.

## 11. Performance: measure first, optimize the real path

OSCAR must feel immediate, but maintainability should not be sacrificed for imagined micro-optimizations.

- Establish latency budgets for user-critical paths.
- Instrument before optimizing.
- Optimize bottlenecks supported by measurements.
- Keep reflex/safety paths deterministic and minimal.
- Stream work when it materially reduces perceived latency.
- Avoid unnecessary allocations/copies on embedded or audio hot paths where measurements justify the work.
- Document non-obvious optimizations and preserve a correctness test around them.

## 12. Security and permissions are architectural boundaries

- Least privilege by default.
- Deny/fail safely when authorization is uncertain.
- Validate at trust boundaries even when upstream code “should” have validated.
- Keep credentials and personal data out of logs and source control.
- Permission checks belong in authoritative execution paths, not only UI controls.
- Generated Skills/Protocols cannot expand their own authority.
- Sensitive actions need attributable audit context.
- Prefer established cryptographic/security primitives over custom implementations.

## 13. Tests protect contracts, not implementation trivia

Use the smallest level of test that proves the important behavior.

- Unit-test domain logic and edge cases.
- Contract-test subsystem/provider/protocol boundaries.
- Integration-test real component interaction where mocks would hide meaningful failure modes.
- End-to-end tests should cover a small set of critical journeys rather than duplicate all lower-level coverage.
- Regression bugs get a regression test when practical.
- Refactoring should preserve existing behavior under tests.
- Tests should be deterministic, isolated and readable.
- Avoid asserting private implementation details unless those details are themselves a required contract.
- For learned automation, test candidate procedures before promotion when representative replay/evaluation is possible.

For hardware changes, clearly distinguish simulator/host tests from verification on the actual device.

## 14. Observability without telemetry clutter

Operationally important components should expose enough information to understand what happened.

Prefer structured signals such as:

- task/correlation ID;
- component/node ID;
- operation name;
- outcome/error category;
- execution status;
- verification status/evidence reference;
- duration/latency;
- retry/reconnect count where relevant.

Do not log secrets, full private conversations, voice biometrics or raw sensitive payloads by default. Observability exists to debug the system, not to collect everything.

## 15. Code should explain itself

- Choose names based on domain meaning, not temporary implementation detail.
- Keep functions focused and reasonably small; split when multiple responsibilities become apparent.
- Comments primarily explain **why**, invariants, trade-offs and surprising constraints — not obvious syntax.
- Public/cross-module behavior needs documentation at the boundary.
- Prefer explicit code over “magic” conventions that only one contributor understands.

If a large comment is required to explain ordinary control flow, simplify the code first.

## 16. Change discipline

OSCAR is slice-based; changes should also be reviewable and reversible.

- One change should have one coherent purpose.
- Prefer small, independently understandable PRs/sub-slices.
- Keep unrelated refactors separate from feature/bug changes when they materially obscure the review.
- Do not rewrite working modules solely for style.
- Preserve working behavior after each merged change.
- Migrations must be staged so intermediate repository states remain valid.
- Breaking protocol/schema changes require explicit migration and rollback thinking.

## 17. Refactor when evidence says to

Refactoring is warranted when there is evidence such as:

- repeated difficult changes across the same boundaries;
- duplicated domain rules;
- growing conditional/platform branching;
- hard-to-test behavior;
- frequent regressions;
- a module with multiple unrelated reasons to change;
- measured performance/reliability problems caused by the current structure.

Do not perform broad “future-proofing” rewrites without such evidence.

## 18. Architecture decisions need trade-offs

For a meaningful new subsystem or boundary, record:

- the problem;
- constraints;
- chosen design;
- important alternatives considered;
- failure modes;
- migration/rollback implications when relevant.

Use `docs/DECISIONS.md` for durable system invariants. Do not create architecture ceremony for routine implementation details.

## Engineering review checklist

Before declaring a code change complete, ask:

- **Scope:** Is this the smallest coherent solution?
- **Simplicity:** Is there unnecessary abstraction or cleverness?
- **Boundaries:** Are responsibilities and dependencies clear?
- **Reuse:** Did we centralize actual shared behavior without premature abstraction?
- **Contracts:** Are external/cross-module inputs typed, validated and evolvable?
- **Failure:** What happens on timeout, restart, disconnect, duplicate request or unavailable provider?
- **State:** Is the authoritative owner obvious?
- **Truth:** What evidence supports every completion/success claim?
- **Verification:** Did we verify the objective independently where practical, and report unverified surfaces explicitly?
- **Security:** Are privilege, permissions and sensitive data handled at the real execution boundary?
- **Tests:** Do tests cover contracts and meaningful failure cases?
- **Operations:** Can a failure be diagnosed without exposing private data?
- **Performance:** Is critical-path performance measured rather than assumed?
- **Changeability:** Can this component be modified or replaced without unrelated rewrites?
- **Documentation:** Are non-obvious decisions and public contracts documented?

## Anti-patterns

Reject or redesign code that trends toward:

- god classes/services;
- shared mutable global state;
- circular dependencies;
- speculative plugin/framework layers;
- one generic `utils` module containing unrelated logic;
- duplicated permission/safety/protocol validation;
- deep inheritance for code reuse;
- hidden network calls in otherwise local-looking functions;
- unbounded retries, queues or background tasks;
- catch-all error handling that converts failures to success/defaults;
- provider-specific types leaking through the entire core;
- treating another agent/tool's success report as verified completion;
- UI states that display success/working while the runtime is blocked or failed;
- tests coupled primarily to private implementation details;
- premature microservices simply to appear modular;
- large rewrites when a small migration/refactor would solve the problem.

## Definition of durable code

For OSCAR, “lasting code” does **not** mean code that never changes. It means code that can change safely because responsibilities are clear, contracts are explicit, tests protect behavior, dependencies are controlled, failures are understood and completion claims are evidence-backed.

When simplicity and extensibility conflict, prefer the simpler implementation **unless an existing requirement proves the extension point is needed now**.

## Owner scope decision — 2026-10-05

Slice 07: **COMPLETE FOR SOFTWARE / SIMULATED EDGE FOUNDATION**.
**PHYSICAL EDGE ACCEPTANCE DEFERRED BY OWNER** — `DEFERRED_BY_OWNER / NOT_PHYSICALLY_VERIFIED`.
Protocol, firmware, Grid integration, ESP32/Pico cross-builds and deterministic
safety contracts in simulation are accepted for continuation. Historical
simulator evidence remains **SIMULATED**. No physical GPIO, watchdog, UART,
E-stop or ESP32/Pico silicon PASS is claimed. Gate C remains **PARTIAL**.

Return to real ESP32/Pico acceptance during Slice 15 physical/device expansion
and/or Slice 16 reliability/security hardening. Physical failure, loss/recovery,
watchdog and safety/reflex verification remain mandatory before Slice 17
Unified Alpha can PASS. The hardware acceptance guide is preserved.
The owner authorizes Slice 08 after Slice 07 integration; Slice 09/10, deployment
and Galaxy Tab Home Node remain outside this work.
