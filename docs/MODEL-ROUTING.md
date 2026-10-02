# Native Model Routing + Provider Runtime

This document is the canonical contract for OSCAR's model/provider routing layer.

OSCAR does **not** depend on the separate SwitchRoute runtime. SwitchRoute remains reference/prototype material whose useful routing, quota, health and fallback lessons may be reused behind OSCAR-owned contracts.

## Core principle

OSCAR is **not one model**.

```text
Jev
→ decide whether model reasoning is needed
→ OSCAR Model Router
→ provider → account/quota pool → model → credential
→ observed outcome
→ evidence
→ future routing adaptation
```

Providers, models, account products, free tiers, prices, quotas and model quality change. They are replaceable runtime resources, not OSCAR's identity.

Rules:

- never hard-code one model as OSCAR's permanent brain;
- never hard-code `task X = model Y forever`;
- do not treat an old successful model ID as proof that it still exists;
- refresh volatile provider/model metadata from live inventory/current official sources when freshness matters;
- preserve provenance and observation time for provider/model claims;
- re-rank on each task from current capability, availability, capacity and observed performance;
- allow new adapters without redesigning OSCAR Core;
- learned routing preferences remain reversible and cannot override privacy, permissions or explicit user policy.

See [SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md).

## Decision boundaries

Do not collapse all routing into one generic router.

```text
request / objective
      ↓
     Jev
      ↓
├─ deterministic capability
├─ live retrieval / search / verification
├─ model reasoning
├─ specialist executor / Worker
├─ computer use / installed application
└─ ask user
```

- **Jev** chooses the class of action.
- **Capability selection** chooses an executable tool/app/device/specialist.
- **Model Router** chooses provider/account-pool/model/credential only after a model path is selected.
- **Search/live retrieval** is a capability path, not just another model.

Coding agents such as Codex, Claude Code and OpenCode are executable capabilities, not ordinary `/chat/completions` models.

## Provider classes

### Hosted model providers

The initial developer environment includes:

- GroqCloud;
- OpenRouter;
- NVIDIA NIM;
- Google AI Studio;
- Z.ai;
- Ollama Cloud.

The adapter boundary must also support future providers such as OpenAI, Anthropic, xAI, Mistral, Cerebras, Together, Fireworks, DeepInfra, SambaNova, Hugging Face, Bedrock, Vertex, Azure-hosted providers and compatible future endpoints without changing core task semantics.

### Local/private runtimes

Planned runtime adapters include:

- Ollama;
- LM Studio;
- vLLM;
- llama.cpp;
- SGLang;
- LocalAI;
- explicitly configured compatible local endpoints.

A local runtime is a capability of a machine/Grid node. It does not make that machine OSCAR's permanent host.

### Specialist providers

The same capability-oriented architecture may cover STT, TTS, embeddings, reranking, search/research, image/video generation and other specialist inference services. Specialist selection uses task-specific metadata rather than one universal model score.

## Credential pools

A provider may have multiple independent credential slots.

```text
GroqCloud
├─ groq-1
├─ groq-2
├─ groq-3
└─ groq-4
```

Each slot may track, where actually observable:

```text
health
validity
account/quota pool
rate-limit state
remaining quota/capacity
reset horizon
concurrency
cooldown
last use
request/token usage
estimated/confirmed cost
recent errors
latency observations
```

Rules:

- never expose raw credentials to UI/logs/prompts/artifacts/telemetry;
- use stable masked IDs such as `groq-2`;
- one bad/rate-limited key does not automatically kill the whole provider;
- quota that is unknown remains **UNKNOWN**;
- unknown price is not free;
- credential validity is separate from model/provider health;
- account product/quota pool matters: two APIs from one company may consume different entitlements.

That last rule is important for providers such as Z.ai, where a general API balance and a Coding Plan/trial can be different resources.

## Development credentials

The current developer pool is expected to support:

- 4 GroqCloud keys;
- 4 OpenRouter keys;
- 2 NVIDIA NIM keys;
- 3 Google AI Studio keys;
- 2 Z.ai keys;
- 2 Ollama Cloud keys;
- later, 3 Tavily search keys;
- optional local Ollama/LM Studio/vLLM endpoints.

This is a starting fleet, not the provider boundary.

See `.env.example`.

Never commit or echo real secrets. Integration evidence stores masked slot IDs only.

## Discovery-first model inventory

`config/development-models.json` contains **seed candidates**, not current truth.

Before a provider/model claim is treated as current, OSCAR should prefer:

```text
live provider models/inventory endpoint
→ current official provider docs/deprecation notices
→ bounded live probe where appropriate
→ cached manifest only when still fresh enough
```

A stale manifest is a hint.

A historical HTTP 200 is historical evidence.

Neither proves current availability.

### Current seed refresh — 2026-10-02

The development seed was refreshed from current official sources after stale model IDs caused misleading provider failures.

Current candidates include:

- **Groq:** `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`;
- **OpenRouter:** `openrouter/free` as a dynamic free route rather than pinning one aging free model;
- **NVIDIA NIM:** current Nemotron 3.5 Lightning / Nemotron 3 Super / Nemotron 3 Ultra candidates;
- **Google AI Studio:** `gemini-3.5-flash-lite`, `gemini-3.8-flash`;
- **Z.ai:** `glm-5.3-flash`, `glm-5.3` with funding/account pool left unknown until live account evidence;
- **Ollama Cloud:** current cloud-catalog candidates such as GLM-5.3, GLM-5.3-Flash, DeepSeek-V4.1-Flash, DeepSeek-V4-Pro and MiniMax M3, with free-credit eligibility left unknown until account evidence.

These names are still replaceable metadata. The router must not assume they remain current next week.

## Freshness rule

Provider/model routing is inherently freshness-sensitive.

Before attributing a 403/404/429 to a key, provider or quota, check whether the requested model/endpoint/account product is itself current and valid.

For example:

```text
old model ID returns 403
≠ credential is definitely bad

current inventory says model retired
→ classify stale model metadata
→ refresh candidates
→ retry bounded current route
```

Likewise, a provider's current pricing/free-tier/limits should come from live/official evidence rather than model training memory.

## Routing modes

| Mode | Intent |
|---|---|
| `auto` | Choose the best eligible route from task + policy + current runtime evidence. |
| `fast` | Prefer low latency while meeting capability/quality floor. |
| `balanced` | Balance quality, reliability, latency, capacity and cost. |
| `heavy` / Heavy Duty | Prefer strongest suitable route within policy. |
| `free_first` | Prefer confirmed free/subscription/local capacity, scarcity-aware. |
| `cheap` | Minimize expected monetary cost while meeting requirements. |
| `local` | Local/private runtimes only; never silently fall back to cloud. |
| `private` | Use only surfaces/providers allowed by privacy policy. |
| `manual` | User pins provider/model and optionally credential slot. |
| `specialist` | Task-specific capability dominates generic model ranking. |

Manual overrides cannot bypass permission, privacy, safety or actual availability.

## Free-first + scarcity-aware allocation

The current development environment is dominated by free accounts/free credits.

The router objective is:

```text
1. satisfy required capability/context/tool constraints
2. prefer currently usable free/subscription/local capacity
3. choose sufficient task-fit/model power
4. prefer reliable healthy routes
5. optimize latency for the task
6. preserve scarce high-value quota when a plentiful adequate route exists
7. use paid fallback only if explicit policy permits
```

Examples:

- a healthy fast Groq route may absorb many small extraction/classification tasks;
- Google or another generous pool may carry broader work when current capacity/model fit is better;
- scarce OpenRouter free requests should be preserved when an adequate plentiful route exists;
- stronger NVIDIA/Ollama/Z.ai routes may be justified for harder work when their current account product actually permits it;
- local models can win for privacy/cost/availability when they are sufficiently capable.

These are heuristics, not permanent provider rankings.

### Scarcity evidence

Where available, derive scarcity from:

```text
remaining confirmed quota/credits
reset horizon
recent consumption rate
rate-limit pressure
concurrency
number of equivalent alternatives
quality uniqueness for the task
```

Unknown capacity remains unknown. Do not manufacture percentages from missing headers/account APIs.

## Model metadata

Model metadata can include, where known:

```text
provider/model identity
account/quota product
capability flags
context/output limits
task-affinity evidence
quality tier + provenance
latency/reliability observations
price metadata
free/subscription metadata
quota/reset/scarcity metadata
privacy/location constraints
tool/structured-output/vision/audio support
last verified timestamp
```

Provider claims, external benchmarks and OSCAR's own verified outcomes are different evidence sources and retain provenance.

## Candidate filtering and ranking

```text
required capability
→ refresh stale/unknown volatile metadata when needed
→ remove unavailable/incompatible candidates
→ enforce permissions/privacy/provider policy
→ enforce context/input/output constraints
→ evaluate credential/account-pool health + capacity
→ identify eligible free/subscription/local pool
→ apply routing mode
→ rank task suitability/model power
→ rank reliability + latency
→ apply scarcity pressure
→ reserve capacity where needed
→ execute
→ observe outcome
→ update evidence
```

No model wins because metadata is missing, because it is largest, or because it won the previous request.

## Adaptive routing

Useful observations include:

- task class;
- provider/model/slot;
- account/quota pool;
- verified task outcome where available;
- provider/model error;
- latency;
- structured-output/tool-call reliability;
- rate-limit/quota events;
- fallback frequency;
- context/tool/vision compatibility;
- inventory/deprecation timestamp.

Observations decay or become stale. A model/provider version change can invalidate old evidence. One success/failure never permanently defines a model.

## Failure + fallback semantics

Differentiate:

```text
credential failure
stale/deprecated model
model capability mismatch
provider failure
rate limit
quota exhaustion
account-product mismatch
network failure
network-policy block
cancelled
```

Fallback is bounded and evidence-aware.

- distinguish credential failure from provider/model metadata failure;
- bounded retry/backoff only;
- re-rank after fresh capacity/availability evidence;
- respect paid/private policies;
- preserve task correlation/provenance;
- once meaningful streaming output has been emitted, never splice another provider's continuation as if it were one coherent response;
- provider/model success remains `REPORTED`/`INFERRED` until the surrounding objective is independently verified where required.

## Search relationship

Search is not model routing, but the router may need search/live retrieval to refresh volatile metadata.

Example:

```text
need current provider route
→ cached model metadata stale
→ provider inventory + current official docs/search
→ refresh candidate evidence
→ route model
```

Tavily is the first planned search adapter with three keys. Search remains a Capability Catalog capability and can later be replaced/augmented by other providers.

See [SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md).

## Usage / history / UI contract

The product should eventually expose a calm **Intelligence / Providers** surface showing only useful operational state:

- connected providers and account products;
- masked credential-slot health;
- local runtime state;
- default routing mode;
- meaningful quota/rate-limit warnings;
- current selected routes and reasons.

Drill-down may show requests, tokens, cost, capacity, reset horizon, latency, error/success rate, models used, fallback/circuit events and route explanations.

Never expose raw keys or persist prompt/response contents merely for router analytics.

Example history:

```text
Task: short extraction
Mode: Free First
Selected: Groq / openai/gpt-oss-20b / groq-3
Reason: current model + sufficient task power + healthy free capacity + low latency
Preserved: scarcer OpenRouter route
Verification: objective-level verifier pending
```

## Slice ownership

### Slice 03

Provides Capability Catalog + transport foundations for remote/provider capabilities.

### Slice 04

Provides the first native Model Router: provider/model registry, multi-key pools, real hosted adapters, routing modes, health/capacity state, bounded fallback, route history and manual control.

Gate A verified this foundation, but provider/model metadata remains explicitly volatile and must be refreshed rather than treated as permanent truth.

### Post-Gate-A freshness correction

Before/with Club B:

- add Tavily search credentials/capability;
- implement freshness classification/live retrieval path;
- make provider/model refresh search/inventory-first;
- test the first freshness-sensitive OSCAR objective from [SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md).

### Slice 05

Adds real machine/coding-agent executors and remote continuation.

### Slice 06

Adds memory/Personal Policy/live context plus the full first-class search/freshness path.

## Verification expectations

At minimum verify:

1. multiple credentials load without leaking values;
2. unhealthy/rate-limited slot can fail over;
3. Auto/Fast/Balanced/Heavy/Free First produce explainable choices;
4. plentiful suitable capacity can preserve scarcer higher-value capacity;
5. current provider/model inventory is refreshed rather than trusted from stale seed data;
6. deprecated/retired model errors are not misclassified as bad credentials without evidence;
7. Manual pin obeys policy/availability;
8. Local never silently falls back to cloud;
9. provider/model fallback is bounded;
10. streaming never silently splices providers;
11. history stores masked route metadata without prompt/response/key content;
12. model reports remain unverified until objective evidence supports completion;
13. freshness-sensitive routing metadata can be backed by current authoritative sources.

See [NATIVE-INFRASTRUCTURE.md](NATIVE-INFRASTRUCTURE.md), [RUNTIME-FOUNDATIONS.md](RUNTIME-FOUNDATIONS.md), [EPISTEMIC-INTEGRITY.md](EPISTEMIC-INTEGRITY.md), [SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md) and [BUILD-GATES.md](BUILD-GATES.md).
