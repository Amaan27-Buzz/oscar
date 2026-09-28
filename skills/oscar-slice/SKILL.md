---
name: oscar-slice
description: Implement one OSCAR roadmap slice or narrow sub-slice end to end, including architecture checks, tests, failure handling, documentation updates, and next-slice status. Use when the user asks to execute, continue, complete, or review a numbered OSCAR slice.
---

# OSCAR slice delivery skill

1. Read `AGENTS.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and the relevant domain docs.
2. Identify the exact slice/sub-slice boundary. Do not silently expand scope.
3. Inspect existing code and connected infrastructure before designing replacements.
4. Prefer existing specialist systems: Latch, SwitchRoute, Jev, LRA/Supermemory, Kinetable, Codex/computer-use workers, Sunday and edge nodes.
5. Write an explicit test checklist before declaring the slice complete.
6. Implement real states only. Preserve blockers/failures rather than substituting demo behavior.
7. Verify important failure modes, disconnect/retry behavior, permissions and safety boundaries.
8. For hardware work, distinguish simulator/host tests from physical-device verification.
9. For UI work, invoke the `oscar-ui` skill/design context and perform bounded visual verification.
10. Update `README.md`, `docs/ROADMAP.md`, affected domain docs, `docs/DECISIONS.md` when invariants change, and `CHANGELOG.md` for meaningful milestones.
11. Mark a slice complete only when implementation, tests, limitations and docs agree.
12. Identify the next slice clearly.

Never bypass deterministic hardware safety, self-grant permissions, or make the PC a required host for core OSCAR availability.
