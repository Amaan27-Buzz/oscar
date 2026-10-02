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

Run from the repository root using Python 3.12+ on a POSIX host. The current file capability uses directory file descriptors and rejects symlink traversal; Windows machine execution is not yet verified.

```sh
python -m pip install '.[dev]'
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m unittest discover -s tests -t . -v
python -m scripts.check_repository
python -m oscar proof
python -m oscar grid-proof
```

The runtime itself has no third-party dependencies. `python -m oscar --help` lists developer commands. Use `--state`, `--workspace`, and `--manifest` before the subcommand to select durable state, an explicit filesystem scope and replaceable provider metadata. Defaults use ignored `.oscar/` and the checkout’s `config/development-models.json`. Installed CLI use outside this checkout requires an explicit manifest path.

Export credentials through the execution environment; the CLI never reads or writes `.env`. `python -m oscar credentials` prints only variable names and present/missing. `python -m oscar live-providers` deliberately performs real network calls and records a safe report under `.oscar/`; it is excluded from ordinary tests/CI. No key material is logged or serialized. Network denials are reported with the required hostname; preserve proxy/TLS rather than bypassing controls.

Use `inspect TASK_ID`, `cancel TASK_ID`, and `resume TASK_ID` for durable state. Resume is bounded and refuses replay of an action whose side effects are ambiguous. Cancellation is cooperative; blocking provider I/O may finish its bounded read before cancellation is observed, and cancellation cannot undo a side effect already committed. A target cancellation acknowledgement is REPORTED, not objective completion.

The full hosted verification suite is explicit and excluded from ordinary tests/CI:

```sh
python -m scripts.verify_club_a_live --run-live --allow-unknown-cost-diagnostics --report .oscar/live-review.json
```

The unknown-cost flag permits bounded NVIDIA/Z.ai diagnostics without declaring their funding free. Omit it for discovery-only verification of those providers. The script reuses the native runtime/router/adapters, creates fresh ignored diagnostic state, and records masked slot IDs, categorical failures and independent comparison evidence. Numerical scarcity tests use labeled synthetic balances; actual remaining provider quota stays unknown when headers are absent. Provider/account availability is reported separately from runtime assertions.

See [docs/CLUB-A-CHECKPOINT.md](docs/CLUB-A-CHECKPOINT.md) for the passed foundation Gate A matrix, known limits and manual review stop.
