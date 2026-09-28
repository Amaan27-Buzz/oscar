---
name: oscar-slice
description: Implement one OSCAR roadmap slice or narrow sub-slice end to end, including architecture checks, engineering quality, tests, failure handling, documentation updates, and next-slice status. Use when the user asks to execute, continue, complete, or review a numbered OSCAR slice.
---

# OSCAR slice delivery skill

1. Read `AGENTS.md`, `ENGINEERING.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and the relevant domain docs.
2. Identify the exact slice/sub-slice boundary. Do not silently expand scope.
3. Inspect existing code and connected infrastructure before designing replacements.
4. Prefer the smallest coherent design; do not add speculative abstractions, services or dependencies.
5. Identify module responsibilities, authoritative state ownership, trust boundaries and important failure modes before implementation.
6. Prefer existing specialist systems: Latch, SwitchRoute, Jev, LRA/Supermemory, Kinetable, Codex/computer-use workers, Sunday and edge nodes.
7. Keep cross-subsystem contracts typed, validated and evolvable; isolate provider/platform details behind narrow adapters where appropriate.
8. Write an explicit test checklist before declaring the slice complete.
9. Implement real states only. Preserve blockers/failures rather than substituting demo behavior.
10. Verify important failure modes, disconnect/retry/cancellation/idempotency behavior, permissions and safety boundaries.
11. Measure or budget performance on critical paths before introducing performance-driven complexity.
12. For hardware work, distinguish simulator/host tests from physical-device verification.
13. For UI work, invoke the `oscar-ui` skill/design context and perform bounded visual verification.
14. Update `README.md`, `docs/ROADMAP.md`, affected domain docs, `docs/DECISIONS.md` when invariants change, `ENGINEERING.md` if the engineering contract changes, and `CHANGELOG.md` for meaningful milestones.
15. Mark a slice complete only when implementation, tests, limitations and docs agree.
16. Identify the next slice clearly.

Never bypass deterministic hardware safety, self-grant permissions, make the PC a required host for core OSCAR availability, or trade maintainability for speculative future-proofing.
