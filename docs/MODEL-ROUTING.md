# Native Model Routing + Provider Runtime

This document is the canonical contract for OSCAR's model/provider routing layer.

OSCAR does **not** depend on the separate SwitchRoute runtime. SwitchRoute remains a reference implementation whose proven provider, routing, quota, health, fallback and local-runtime ideas can be reused behind OSCAR-owned contracts.

The goal is broader than choosing a model name. OSCAR must decide the correct execution class, then choose the best provider/model/credential only when a model path is actually needed.

## Core principle — the infrastructure evolves, the model does not define OSCAR

OSCAR is **not one model** and is not permanently tied to the providers available during initial development.

The durable system is:

```text
Jev
→ capability/model decision
→ adaptive Model Router
→ provider/model/credential pool
→ observed outcome
→ updated routing evidence
```

Providers, models, quotas, free tiers, prices and model quality change. The router therefore treats them as replaceable runtime resources described by versioned metadata and observed evidence.

Rules:

- never hard-code one model as OSCAR's permanent brain;
- never hard-code `task X = model Y forever`;
- discover/reload provider/model metadata where practical;
- re-rank on each task using current capability, capacity and observed performance;
- preserve provenance for claims about model power, limits and reliability;
- allow new provider adapters without redesigning OSCAR Core;
- learned routing preferences remain reversible and cannot override privacy, permissions or explicit user policy.

## Decision hierarchy

Do not collapse all routing into one generic router.

```text
request / objective
      ↓
     Jev
      ↓
what class of work is required?
├─ deterministic capability / tool
├─ retrieval / live verification
├─ model reasoning
├─ specialist agent / coding executor
├─ computer use / installed application
└─ ask user
      ↓
if model reasoning
→ OSCAR Model Router
→ provider → model → credential

if executable/specialist work
→ Capability Catalog / execution selection
→ Codex / Claude Code / OpenCode / terminal / computer use / app / device
```

**Jev** decides whether reasoning, retrieval, execution, delegation or clarification is appropriate.

**OSCAR Model Router** chooses the concrete model/provider/credential after a model path is selected.

**Capability selection** chooses an executable specialist or device. Coding agents such as Codex, Claude Code and OpenCode are not treated as ordinary text-generation provider keys merely because they ultimately use models.

## Provider classes

OSCAR's catalog distinguishes provider classes rather than putting everything in one flat list.

### 1. Hosted model providers

Initial/high-priority adapters include providers already proven or planned through SwitchRoute-style architecture and the user's available credentials:

- OpenAI;
- Anthropic;
- Google AI Studio / Gemini;
- xAI;
- Mistral AI;
- DeepSeek;
- Cohere;
- GroqCloud;
- Cerebras;
- NVIDIA NIM;
- SambaNova;
- Together AI;
- Fireworks AI;
- DeepInfra;
- OpenRouter;
- Hugging Face Inference Providers;
- Z.ai;
- Ollama Cloud;
- custom public OpenAI-compatible endpoints where safely supported.

The provider registry must remain adapter/data driven. Provider support belongs in versioned adapters/manifests with capability and test metadata.

Do **not** freeze a large third-party provider list into core architecture.

### 2. Local/private model runtimes

Planned local runtimes include:

- Ollama;
- LM Studio;
- vLLM;
- llama.cpp;
- SGLang;
- LocalAI;
- other explicitly configured OpenAI-compatible local runtimes.

Local runtimes are capabilities of a machine/node. They are not proof that OSCAR itself is hosted on that machine.

### 3. Coding / agent executors

Examples:

- Codex;
- Claude Code;
- OpenCode;
- Gemini CLI;
- other installed coding/agent runtimes discovered through the Capability Catalog.

These executors can have subscription/OAuth/provider behavior of their own. OSCAR selects them based on task suitability, availability, permissions and observed reliability rather than pretending every coding agent is just another `/chat/completions` model.

### 4. Specialist AI providers

The same architecture may later cover capability-specific providers such as:

- STT;
- TTS;
- embeddings;
- reranking;
- search/research;
- image generation;
- video generation;
- other specialist inference services.

Specialist selection should use capability-specific metadata rather than one universal quality score.

## Credential pools

A provider may have multiple independent credentials.

Example:

```text
GroqCloud
├─ groq-1
├─ groq-2
├─ groq-3
└─ groq-4
```

Each credential slot tracks its own operational state where available:

```text
credential_id
provider_id
health
validity
rate-limit state
quota/capacity
concurrency
cooldown
last-used time
request/token usage
estimated/confirmed cost
recent errors
latency observations
reset/expiry information
```

Rules:

- credential values are never exposed to UI, logs, task prompts, artifacts or telemetry;
- UI/logs use masked slot identifiers such as `groq-2`;
- one failing/rate-limited credential does not mark the whole provider unavailable;
- quota that is unknown is **unknown**, not unlimited;
- price that is unknown is **unknown**, not free;
- credential validity is distinct from transient provider/model health;
- credentials may be rotated/revoked independently.

## Local development credential contract

The repository-root `.env` is local-only and ignored by Git.

The initial developer pool is expected to support:

- 4 GroqCloud keys;
- 4 OpenRouter keys;
- 2 NVIDIA NIM keys;
- 3 Google AI Studio keys;
- 2 Z.ai keys;
- 2 Ollama Cloud keys;
- optional local runtime URLs for Ollama, LM Studio and vLLM.

This pool is a **starting fleet, not the provider boundary**.

See the repository-root `.env.example` for placeholder variable names.

Development rules:

- never commit the real `.env`;
- never echo raw credentials;
- never include secrets in snapshots, test fixtures, screenshots or CI output;
- never forward provider credentials to frontend/browser code;
- integration tests may use the real local credentials when explicitly run by the developer;
- CI should use mocks/test adapters unless explicitly provisioned with scoped secrets;
- results record credential slot IDs, not secret values.

## Current Ollama Cloud free-credit model metadata

For the current developer account, free usage credits are available for these Ollama Cloud models:

- `gemma3:31b`
- `gpt-oss:120b`
- `gpt-oss:20b`
- `nemotron-3-nano:30b`
- `nemotron-3-super`
- `nemotron-3-ultra`

Treat this list as current runtime/development metadata supplied by the user, **not** a permanent hard-coded allowlist. Provider discovery/configuration should be able to replace or extend it when Ollama Cloud changes the account's available models.

## Routing modes

OSCAR supports automatic routing and explicit manual control.

| Mode | Intent |
|---|---|
| `auto` | OSCAR chooses the execution/model profile from task, policy and current runtime state. |
| `fast` | Prefer low first-token/response latency while preserving minimum capability requirements. |
| `balanced` | Balance quality, latency, reliability, quota and cost. |
| `heavy` / **Heavy Duty** | Prefer the strongest suitable reasoning/capability tier; cost/latency are secondary within policy. |
| `free_first` | Prefer confirmed free/subscription/local capacity, using scarcity-aware allocation before paid fallback. |
| `cheap` | Minimize expected monetary cost while meeting capability/quality requirements. |
| `local` | Local/private runtimes only unless the user explicitly allows fallback. |
| `private` | Use only providers/surfaces allowed by the active privacy policy. |
| `manual` | User pins provider/model and optionally a credential slot. |
| `specialist` | Task affinity/specialist capability dominates generic model ranking. |

`auto` may itself choose an effective profile such as Fast, Balanced, Heavy Duty or Free First based on the request and Personal Policy.

Users can override routing per request, session/project or durable Personal Policy where appropriate.

Examples:

```text
"Use Heavy Duty for this research task."
"Keep this project local only."
"Prefer Groq for low-latency classification."
"Always use Codex for repository implementation unless unavailable."
"Use this OpenRouter model just for this request."
```

A manual override cannot bypass permission, privacy, safety or availability constraints.

## Free-first and scarcity-aware allocation

The current development environment is dominated by free accounts/free credits. OSCAR should therefore optimize for **available free capacity + sufficient model power**, rather than blindly using one favorite model or always selecting the largest model.

The routing objective is:

```text
1. satisfy required capability/context/tool constraints
2. prefer currently usable free/subscription/local capacity
3. choose sufficient task-fit/model power
4. prefer reliable healthy routes
5. optimize latency for the task
6. preserve scarce high-value quota when a cheaper/plentiful route is sufficient
7. use paid fallback only when explicit policy permits
```

This creates intentional behavior such as:

- **GroqCloud** can absorb many small/fast tasks when its healthy limits and suitable models make it efficient;
- **Google AI Studio** and **Z.ai** can carry broader or stronger work when their current free capacity and model fit are favorable;
- **OpenRouter** can expose valuable models but lower free limits should be treated as scarce capacity and preserved for tasks where those models materially help;
- **Ollama Cloud** should use the currently available free-credit model set according to task fit and remaining capacity rather than pinning one model;
- local runtimes can win when privacy, availability or cost makes them preferable and the local model is sufficiently capable.

These are routing heuristics, not permanent provider rankings. Actual model inventory, quotas, quality and reliability can change.

### Scarcity score

Where enough data exists, a route can derive a scarcity signal from:

```text
remaining confirmed quota/credits
reset horizon
recent consumption rate
concurrency/rate limit pressure
number of equivalent alternative routes
quality uniqueness for the requested task
```

A scarce route should not be consumed for trivial work when a plentiful route meets the same quality requirement.

Unknown capacity stays unknown; do not invent numerical scarcity from missing provider data.

## Model and task metadata

Do not hard-code `task X = model Y forever`.

Models/providers change. OSCAR should maintain explicit metadata plus observed runtime history.

Relevant capability/affinity classes can include:

- general conversation;
- reasoning;
- coding;
- research;
- vision;
- audio;
- long context;
- tool use;
- structured output;
- extraction;
- classification;
- low-latency reflex support;
- STT;
- TTS;
- embeddings;
- reranking;
- multimodal generation.

A model record can include, where known:

```text
provider/model identity
capability flags
context/output limits
quality tier / task-affinity evidence
latency observations
reliability observations
price metadata
free/subscription capacity metadata
scarcity/reset metadata
privacy/location policy metadata
tool/structured-output support
vision/audio support
last verified metadata time
```

Provider claims, benchmark data and OSCAR's own observations must retain provenance. Unknown metadata stays unknown.

## Candidate filtering and ranking

Routing should happen in stages:

```text
required capability
→ remove unavailable/incompatible candidates
→ enforce permissions/privacy/provider policy
→ enforce context/input/output requirements
→ evaluate credential health + current capacity
→ identify free/subscription/local eligible pool
→ apply requested routing mode
→ rank task suitability/model power
→ rank reliability + latency
→ apply scarcity/quota-preservation pressure
→ reserve credential/capacity where needed
→ execute
→ observe outcome
→ update routing evidence
```

No model wins merely because metadata is missing, because it is largest, or because it won the previous request.

A provider/model with unknown price, latency, quota or capability should not receive an artificial advantage.

## Adaptive routing and learning

OSCAR should change routing as infrastructure changes.

Useful observations include:

- verified task success/failure;
- provider/model errors;
- latency;
- structured-output/tool-call reliability;
- rate-limit pressure;
- current/recent quota exhaustion;
- fallback frequency;
- task-class quality evidence;
- context-window/tool/vision compatibility.

Observed history may influence later ranking, but:

- one success/failure must not permanently define a model;
- stale observations decay or become stale;
- model/provider version changes can invalidate old evidence;
- user manual choices and policy remain authoritative;
- the router must remain explainable: `why this route now?` should have an evidence-backed answer.

## Fallback semantics

Fallback is bounded and evidence-aware.

- use explicit fallback chains or re-rank currently eligible candidates;
- distinguish credential failure from provider/model failure;
- apply bounded retry/backoff;
- respect paid-fallback and privacy policy;
- preserve task correlation/provenance;
- re-evaluate capacity and scarcity after a rate-limit/quota event;
- once a streaming answer has emitted meaningful output, do not append a second provider's continuation as though it were one coherent response;
- model/provider success remains `REPORTED`/`INFERRED` until the objective is independently verified where verification matters.

## Provider health and quota

The native router should absorb the useful separation proven in SwitchRoute:

- credential validity;
- transient provider/model health;
- rolling latency;
- circuit-breaker state;
- quota/capacity;
- concurrency;
- free-credit/subscription capacity;
- reset horizon where known;
- price/cost policy;
- routing strategy.

A configured distributed state backend may be introduced when concurrency actually requires it. Early development should not add infrastructure merely to mimic a previous deployment architecture.

## Manual assignment and learned preference

Manual selection must coexist with automation.

The user may:

- choose a provider;
- choose a model;
- optionally choose a specific credential slot for diagnostics;
- set a temporary routing mode;
- create durable preferences such as project-local-only or preferred coding executor;
- disable a provider/model;
- control paid fallback;
- cap paid usage where measurable.

OSCAR may learn operational affinity from verified outcomes, latency and failure history, but learned routing cannot silently create new authority or override explicit policy.

## Usage, history and UI contract

The product should expose a calm **Intelligence / Providers** surface rather than a generic telemetry dashboard.

At a glance it should be possible to see:

- connected providers;
- number of configured credential slots;
- provider/key health;
- local runtime online/offline state;
- current default routing mode;
- whether automatic routing is enabled;
- material quota/rate-limit/free-credit warnings.

Drill-down views may show, where available:

- requests;
- input/output tokens;
- estimated/confirmed cost;
- free/subscription usage;
- rate limits/quota;
- reset horizon;
- latency;
- error/success rate;
- models used;
- provider/model/credential history;
- fallback/circuit events;
- coding-agent/executor history;
- route decisions and explanation;
- manual overrides/policies.

Routing history should be inspectable in a concise form, for example:

```text
Task: repository debugging
Path: specialist executor
Selected: Codex
Reason: coding affinity + project access + healthy node
Fallback: Claude Code
Verification: tests + repository state
```

or:

```text
Task: short extraction
Mode: Free First
Selected: Groq / model-x / groq-3
Reason: sufficient task power + healthy plentiful free capacity + low latency
Preserved: scarce OpenRouter free route
Fallback: Google / model-y / google-1
```

The UI must never reveal raw API keys. Unknown usage/quota should be shown as unavailable/unknown rather than fabricated.

## Observability and privacy

Routing telemetry should be content-minimal by default.

Useful metadata includes:

- task/request ID;
- route mode;
- capability class;
- provider/model/credential slot;
- timings;
- token counts where available;
- cost estimate/confirmed cost;
- capacity/scarcity evidence where known;
- fallback reason;
- error category;
- verification/result linkage.

Do not persist prompt/response/tool/upload contents merely to support router analytics.

## Slice ownership

### Slice 03

Provides the Capability Catalog/transport foundation that lets providers, machine nodes and executors advertise capabilities.

### Slice 04

Implements the first native Model Router:

- provider/model/credential registry;
- multi-key pools;
- initial real adapters using the developer `.env`;
- dynamic provider/model inventory boundary;
- routing modes;
- capability/task filtering;
- health/latency/quota/free-credit/cost state;
- scarcity-aware Free First routing;
- model-power/task-fit ranking;
- bounded fallback;
- route history/usage data;
- manual override;
- ChatGPT/provider adapter path;
- local-runtime discovery boundary.

### Slice 05

Adds real coding/agent executors and machine capabilities such as Codex, Claude Code/OpenCode where available, terminal, browser/computer use and installed applications.

## Initial manual verification

Before Gate A can pass, manually verify at least:

1. multiple credentials for one provider can be loaded without leaking values;
2. an unhealthy/rate-limited credential can fail over to another eligible credential;
3. Auto, Fast/Balanced, Heavy Duty and Free First produce explainable route choices;
4. Free First considers current free capacity **and** sufficient task/model power rather than always choosing one provider;
5. a plentiful suitable route can preserve a scarcer higher-value free route for harder work;
6. a quota/rate-limit change causes the next request to re-rank rather than remain pinned;
7. Ollama Cloud's current free-credit model inventory can be represented without hard-coding it into core architecture;
8. Manual can pin a provider/model without bypassing policy;
9. local-only routing does not silently use cloud fallback;
10. provider/model failure uses bounded fallback;
11. streaming does not splice two providers after meaningful output begins;
12. usage/history records the selected provider/model/credential slot without prompt/response retention;
13. model reports remain unverified until the surrounding objective verification succeeds.

See also [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md), [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md), [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md) and [BUILD-GATES.md](BUILD-GATES.md).

## Club A implementation checkpoint

`oscar/router.py` filters required capability/quality/context/output budgets, policy, credential availability and cooldown before ranking. Auto/Free First prefer eligible configured free/subscription/local routes; sufficient smaller models and known plentiful quota can preserve stronger scarce routes. Heavy Duty prioritizes eligible strength, Specialist task affinity, Fast latency, Balanced the combined evidence, and Cheap known monetary cost. Manual pins never expand privacy/cost/availability policy; Local never silently chooses cloud.

`config/development-models.json` is replaceable developer metadata, including the six user-supplied Ollama Cloud models. Initial quality/context figures are conservative configuration, not observed benchmarks. Funding declarations for the initial free pools do not establish remaining quota or credential validity. NVIDIA/Z.ai funding remains unknown; the live harness performs read-only model discovery until cost policy is configured. `config/local-template.json` contains disabled Ollama/LM Studio/vLLM interfaces with no assumed model inventory.

OpenAI-compatible, Google generateContent and Ollama chat adapters are in `oscar/providers.py`. Supported request paths currently cover text, JSON structured output and streaming; images/audio/tool execution are not implemented. Additional OpenAI-compatible providers can be configured by manifest; a genuinely different protocol requires a new adapter. ChatGPT product-surface connectors remain pending.

Credential state is separate from secrets. The environment is the sole credential input for this harness; `.env` is neither read nor written. Error bodies, raw prompts, responses and keys are excluded from route history. Provider responses stay REPORTED. Independent objective evidence can link into history; response reliability and objective success are learned separately with priors and decaying observations. Explicit policies remain authoritative.

Observed request/token headers can establish quota; absent/stale balances remain unknown, including after consumption without a fresh header. Scarcity currently uses confirmed remaining requests, with explicit pressure for unknown capacity; full credit/reset/consumption forecasting is future work. No quota percentages or current model benchmarks are invented. Paid routing is off by default; known-price fallback budgets are cumulative, while unknown-price routing requires a separate explicit allowance.

The automated and real loopback contracts are verified; **hosted integrations remain BLOCKED by environment network policy**. See [CLUB-A-CHECKPOINT.md](CLUB-A-CHECKPOINT.md) for exact attempted operations, models and masked slots. Live credential failover, hosted quota adaptation and hosted objective quality remain unverified.
