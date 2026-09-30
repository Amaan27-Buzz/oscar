---
name: oscar-slice
description: Implement one OSCAR roadmap slice or narrow sub-slice end to end, including architecture checks, engineering quality, tests, failure handling, evidence-backed verification, documentation updates, and next-slice status. Use when the user asks to execute, continue, complete, or review a numbered OSCAR slice.
---

# OSCAR slice delivery skill

1. Read `AGENTS.md`, `ENGINEERING.md`, `docs/EPISTEMIC-INTEGRITY.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and the relevant domain docs.
2. Identify the exact slice/sub-slice boundary. Do not silently expand scope.
3. Inspect existing code and connected infrastructure before designing replacements.
4. Prefer the smallest coherent design; do not add speculative abstractions, services or dependencies.
5. Identify module responsibilities, authoritative state ownership, trust boundaries and important failure modes before implementation.
6. Prefer existing specialist capabilities: Jev, LRA/Supermemory, native OSCAR Transport/Model Router, Codex/computer-use Workers, Sunday, Edge nodes, and installed/connected specialist applications.
7. Keep cross-subsystem contracts typed, validated and evolvable; isolate provider/platform details behind narrow adapters where appropriate.
8. Define the slice's observable completion condition and verification plan before declaring it complete.
9. Write an explicit test checklist.
10. Implement real states only. Preserve blockers/failures/unknowns rather than substituting demo behavior.
11. Treat a tool/Worker/model `success` result as reported evidence until the expected repository/runtime/device state is inspected.
12. Verify important failure modes, disconnect/retry/cancellation/idempotency behavior, permissions and safety boundaries.
13. Verify the final objective independently where practical: read-after-write, tests, browser/device inspection, API state, telemetry, or another authoritative check.
14. If only part of the objective is verified, report `partially verified`; if verification is impossible, state that explicitly.
15. Measure or budget performance on critical paths before introducing performance-driven complexity.
16. For hardware work, distinguish simulator/host tests from physical-device verification.
17. For UI work, invoke the `oscar-ui` skill/design context and perform bounded visual verification.
18. Update `README.md`, `docs/ROADMAP.md`, affected domain docs, `docs/DECISIONS.md` when invariants change, `ENGINEERING.md` if the engineering contract changes, and `CHANGELOG.md` for meaningful milestones.
19. Re-fetch/inspect the updated canonical docs before claiming that an architecture/roadmap/status update was propagated.
20. Mark a slice complete only when implementation, tests, limitations, verification evidence and docs agree.
21. Identify the next slice clearly.

Never bypass deterministic hardware safety, self-grant permissions, make the PC a required host for core OSCAR availability, convert another agent's success report into verified completion without evidence, or trade maintainability for speculative future-proofing.
