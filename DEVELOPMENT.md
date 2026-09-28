# Development

OSCAR is implemented as a sequence of coherent product slices. The current implementation order and status live in `docs/ROADMAP.md`.

## Repository layout

```text
oscar/
├── README.md
├── AGENTS.md
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
│   ├── VOICE-SENTRY.md
│   ├── ONBOARDING.md
│   ├── UI-AVATAR.md
│   └── SECURITY.md
└── .github/
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE.md
    ├── CODEOWNERS
    └── workflows/
```

Implementation directories are added by the slice that owns them rather than creating empty architecture prematurely. Planned top-level implementation areas include OSCAR core, desktop/mobile surfaces, edge firmware, shared protocols/contracts and tests.

## Development sequence

For each slice:

1. Read the product/architecture/decision docs.
2. Define the smallest coherent deliverable and explicit test checklist.
3. Research existing libraries/tools when the path is uncertain; do not brute-force around a known limitation.
4. Implement modularly.
5. Test happy paths and relevant failure/safety paths.
6. Record limitations honestly.
7. Update README, ROADMAP, affected docs and CHANGELOG in the same change.
8. Only then mark the slice complete and advance the `Next` marker.

## Specialist-first rule

OSCAR should orchestrate the best available capability instead of reproducing it poorly. The implementation should preserve this behavior from the beginning: coding agents for repository work, computer-use for GUI verification, Kinetable for hardware workflows, Latch for connected execution, SwitchRoute for general model routing, and LRA/Supermemory for long-term memory.

## Local data

Runtime state, secrets, memory exports, recordings and device credentials must remain outside version control. The root `.gitignore` reserves common local paths for this purpose; individual slices may extend it when new runtimes are introduced.

## Build commands

There is no canonical build command yet because Slice 00 contains architecture/documentation only. Each implementation slice must add its exact setup/build/test commands here once the relevant runtime exists.
