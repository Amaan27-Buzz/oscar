# Native Model Routing + Provider Runtime

This document is the canonical contract for OSCAR's model/provider routing layer.

OSCAR does **not** depend on the separate SwitchRoute runtime. SwitchRoute remains a reference implementation whose proven provider, routing, quota, health, fallback and local-runtime ideas can be reused behind OSCAR-owned contracts.

The goal is broader than choosing a model name. OSCAR must decide the correct execution class, then choose the best provider/model/credential only when a model path is actually needed.

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

Initial/high-priority adapters include the providers already proven or planned through SwitchRoute-style architecture and the user's available credentials:

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

The provider registry must remain adapter/data driven. OSCAR should be able to add the wider provider set represented by projects such as OmniRoute without changing core architecture for each provider.

Do **not** freeze a large third-party provider list into the core. External catalogs change frequently. Provider support belongs in versioned adapters/manifests with capability and test metadata.

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
- UI and logs use stable masked slot identifiers such as `groq-2`;
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

See the repository-root `.env.example` for placeholder variable names.

Development rules:

- never commit the real `.env`;
- never echo raw credentials;
- never include secrets in snapshots, test fixtures, screenshots or CI output;
- never forward provider credentials to frontend/browser code;
- integration tests may use the real local credentials when explicitly run by the developer;
- CI should use mocks/test adapters unless explicitly provisioned with scoped secrets;
- results record credential slot IDs, not secret values.

## Routing modes

OSCAR supports automatic routing and explicit manual control.

| Mode | Intent |
|---|---|
| `auto` | OSCAR chooses the execution/model profile from task, policy and current runtime state. |
| `fast` | Prefer low first-token/response latency while preserving minimum capability requirements. |
| `balanced` | Balance quality, latency, reliability, quota and cost. |
| `heavy` / **Heavy Duty** | Prefer the strongest suitable reasoning/capability tier; cost/latency are secondary within policy. |
| `free_first` | Prefer confirmed free/subscription/local capacity before paid fallback. |
| `cheap` | Minimize expected monetary cost while meeting capability/quality requirements. |
| `local` | Local/private runtimes only unless the user explicitly allows fallback. |
| `private` | Use only providers/surfaces allowed by the active privacy policy. |
| `manual` | User pins provider/model and optionally a credential slot. |
| `specialist` | Task affinity/specialist capability dominates generic model ranking. |

`auto` may itself choose an effective profile such as Fast, Balanced or Heavy Duty based on the request and Personal Policy.

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
→ evaluate credential capacity/health
→ apply requested routing mode
→ rank task suitability + reliability + latency + cost/quota
→ reserve credential/capacity where needed
→ execute
→ update observations
```

No model wins merely because metadata is missing.

A provider/model with unknown price, latency, quota or capability should not receive an artificial advantage.

## Fallback semantics

Fallback is bounded and evidence-aware.

- use explicit fallback chains or re-rank currently eligible candidates;
- distinguish credential failure from provider/model failure;
- apply bounded retry/backoff;
- respect paid-fallback and privacy policy;
- preserve task correlation/provenance;
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
- material quota/rate-limit warnings.

Drill-down views may show, where available:

- requests;
- input/output tokens;
- estimated/confirmed cost;
- free/subscription usage;
- rate limits/quota;
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
Mode: Fast
Selected: Groq / model-x / groq-3
Reason: required structured output + healthy free capacity + lowest observed latency
Fallback: Google / model-y / google-1
```

The UI must never reveal raw API keys. Unknown usage/quota should be shown as unavailable/unknown rather than fabricated.

The detailed visual treatment belongs to the product-surface design slice; this document defines the data and behavior that UI must represent.

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
- routing modes;
- capability/task filtering;
- health/latency/quota/cost state;
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
3. Auto, Fast/Balanced and Heavy Duty produce explainable route choices;
4. Manual can pin a provider/model without bypassing policy;
5. local-only routing does not silently use cloud fallback;
6. provider/model failure uses bounded fallback;
7. streaming does not splice two providers after meaningful output begins;
8. usage/history records the selected provider/model/credential slot without prompt/response retention;
9. model reports remain unverified until the surrounding objective verification succeeds.

See also [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md), [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md), [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md) and [BUILD-GATES.md](BUILD-GATES.md).
