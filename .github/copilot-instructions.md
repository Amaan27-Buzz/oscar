# GitHub Copilot repository instructions

OSCAR's canonical project rules live in `AGENTS.md`. Follow them for architecture, safety, slice discipline, testing and documentation. For implementation/system-design work, also follow `ENGINEERING.md` and `docs/EPISTEMIC-INTEGRITY.md`.

For orchestration/Workers/Protocols/channels/durable execution, also read `docs/RUNTIME-FOUNDATIONS.md` plus the relevant domain docs.

Before UI/UX/frontend/mobile/desktop work, read `DESIGN.md`, `TASTE.md`, `docs/UI-AVATAR.md` and `docs/SURFACES.md`.

Key constraints:

- implement one scoped slice/sub-slice at a time;
- prefer the smallest coherent solution and avoid speculative abstractions/frameworks;
- keep responsibilities cohesive, coupling low, boundaries typed and state ownership obvious;
- validate at trust boundaries and design timeout/retry/reconnect/cancellation behavior deliberately;
- never fabricate functional states or successful actions;
- treat tool/agent success as reported evidence until the resulting state is verified where practical;
- never claim `done`, `fixed` or equivalent beyond available evidence;
- preserve partial/blocked/failed/unknown states explicitly;
- prefer specialist tools/agents over reimplementing them poorly;
- keep hardware safety deterministic and local;
- keep reflex commands off heavy-model paths;
- preserve Sunday as OSCAR on the phone, not a separate assistant;
- update README/roadmap/domain docs with completed slices and verify those docs before claiming propagation is complete;
- for UI, avoid generic AI dashboards, card walls, glassmorphism, neon HUDs and purple gradient AI styling;
- visually verify substantial UI work and respect reduced motion/native platform behavior.
