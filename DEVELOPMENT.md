# Development

OSCAR is implemented as a sequence of coherent product slices. The current implementation order and status live in `docs/ROADMAP.md`.

`ENGINEERING.md` is the repository-wide implementation quality standard. It defines the expected approach to modularity, reuse, contracts, dependencies, reliability, state ownership, testing, security, performance and change discipline.

## Repository layout

```text
oscar/
├── README.md
├── AGENTS.md
├── ENGINEERING.md
├── DESIGN.md
├── TASTE.md
├── CONTRIBUTING.md
├── DEVELOPMENT.md
├── CHANGELOG.md
├── SECURITY.md
├── SUPPORT.md
├── CODE_OF_CONDUCT.md
├── assets/
│   └── brand/
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── FEATURES.md
│   ├── ROADMAP.md
│   ├── DECISIONS.md
│   ├── MEMORY.md
│   ├── ORCHESTRATION.md
│   ├── SURFACES.md
│   ├── SUNDAY-DESIGN.md
│   ├── VOICE-SENTRY.md
│   ├── ONBOARDING.md
│   ├── UI-AVATAR.md
│   ├── AGENT-CONTEXT.md
│   └── SECURITY.md
├── skills/
└── .github/
    ├── ISSUE_TEMPLATE/
    ├── instructions/
    ├── PULL_REQUEST_TEMPLATE.md
    ├── CODEOWNERS
    └── workflows/
```

Implementation directories are added by the slice that owns them rather than creating empty architecture prematurely. Planned top-level implementation areas include OSCAR core, desktop/mobile surfaces, edge firmware, shared protocols/contracts and tests.

## Development sequence

For each slice:

1. Read the product/architecture/decision docs plus `ENGINEERING.md`.
2. Define the smallest coherent deliverable and explicit test checklist.
3. Identify subsystem boundaries, authoritative state ownership and failure behavior before adding abstractions.
4. Research existing libraries/tools when the path is uncertain; do not brute-force around a known limitation.
5. Implement with high cohesion, low coupling and explicit typed contracts.
6. Test happy paths plus relevant failure, timeout, retry, cancellation, reconnect, permission and safety paths.
7. Measure critical-path performance before optimizing it.
8. Record limitations honestly.
9. Update README, ROADMAP, affected docs and CHANGELOG in the same change.
10. Only then mark the slice complete and advance the `Next` marker.

## Engineering defaults

Prefer:

- simple designs over speculative generality;
- one authoritative owner for mutable state;
- typed, validated boundaries over loosely shaped payloads;
- narrow adapters for external providers/platforms;
- bounded retries/timeouts/queues;
- contract and integration tests at meaningful boundaries;
- small reviewable changes over broad rewrites;
- explicit failures over silent fallback to misleading defaults.

Avoid creating microservices, plugin frameworks, generic managers, deep inheritance trees or shared utility layers until a real requirement demonstrates the need. Reuse actual domain behavior, not coincidental code shape.

## Specialist-first rule

OSCAR should orchestrate the best available capability instead of reproducing it poorly. The implementation should preserve this behavior from the beginning: coding agents for repository work, computer-use for GUI verification, installed/connected engineering tools for hardware/design/simulation, native OSCAR Transport for connected execution, native OSCAR Model Router for model selection, and LRA/Supermemory for long-term memory.

Physical actions remain native OSCAR Edge/device capabilities. Engineering applications are replaceable capabilities, not architectural dependencies.

## Local data

Runtime state, secrets, memory exports, recordings and device credentials must remain outside version control. The root `.gitignore` reserves common local paths for this purpose; individual slices may extend it when new runtimes are introduced.

## Build commands

There is no canonical build command yet because Slice 00 contains architecture/documentation only. Each implementation slice must add its exact setup/build/test commands here once the relevant runtime exists.
