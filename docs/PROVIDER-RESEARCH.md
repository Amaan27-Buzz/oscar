# Provider research — Post-Gate-A correction

Observed **2026-10-02**. This is a dated evidence record, not a permanent catalog.
Official pages were retrieved before changing the registry. The
[source ledger](evidence/provider-sources-2026-10-02.json) records exact URLs,
HTTP outcomes and observation times; the
[live correction record](evidence/club-a-correction-2026-10-02.json) records
credential-slot inventories, bounded generation probes and safe quota metadata.
Page bodies, account labels and credentials are not retained.

Public support, listing through a credential, and successful generation are three
different claims. A successful diagnostic does not prove free funding, current
balance, model quality or entitlement to every listed model. All six inventories
are dynamic. Re-query them at runtime; cached counts below are historical after
their observation window expires.

## Endpoints and discovery

| Provider / account product | API base | Native inventory / account metadata | Latest complete inventory in this pass |
|---|---|---|---|
| GroqCloud developer API | `https://api.groq.com/openai/v1` | `GET /models`; rate headers on generation | 11 per slot, all four slots |
| OpenRouter API | `https://openrouter.ai/api/v1` | Public `GET /models`; account-filtered `GET /models/user`; `GET /key` | 464 public; 461 account-filtered per slot, all four slots; 18 zero-priced routes at observation |
| NVIDIA hosted NIM API | `https://integrate.api.nvidia.com/v1` | `GET /models`; model-specific official API catalog | 81 per slot, both slots |
| Google Gemini Developer API / AI Studio | `https://generativelanguage.googleapis.com/v1beta` | Paginated `GET /models`; `generateContent` supported methods and token limits | 61 over two pages per slot, all three slots |
| Z.ai general API | `https://api.z.ai/api/paas/v4` | `GET /models`; documented business error codes | 11 per slot, both slots |
| Z.ai Coding Plan | `https://api.z.ai/api/coding/paas/v4` | Separate product endpoint and console quota | UNVERIFIED; disabled, no coding credentials/entitlement established |
| Ollama Cloud API | `https://ollama.com/api` | `GET /tags`; model details where supported | 17 per slot, both slots |

An authenticated catalog may still include models the credential cannot generate
with. The runtime labels these **listed via credential; generation entitlement
not implied**. It separately retains generation observations and refusals.

## GroqCloud

Sources: [supported models](https://console.groq.com/docs/models),
[deprecations](https://console.groq.com/docs/deprecations),
[rate limits](https://console.groq.com/docs/rate-limits),
[structured output](https://console.groq.com/docs/structured-outputs), and
[tools](https://console.groq.com/docs/tool-use/overview), plus all four live inventories.

- Current account-listed and generation-tested text/reasoning candidates:
  `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`.
  All four slots generated with GPT OSS 20B; slot 1 also generated with the other two.
- Official retirement applies to **Free/Developer**, with a committed-spend
  Enterprise exception: `llama-3.1-8b-instant` and `llama-3.3-70b-versatile`
  shut down 2026-08-16; `qwen/qwen3.6-27b` on 2026-09-14;
  `qwen/qwen3-32b` and Llama 4 Scout on 2026-07-17. Compound/Compound Mini
  shut down 2026-09-21. The generic models page retaining Enterprise Llama entries
  does not override product-specific deprecation or account absence.
- Documented context: 131,072; GPT OSS output: 65,536; Qwen output: 16,384.
  Strict JSON and tool support are documented for the current candidates.
  OSCAR's runtime does not implement tool-call execution.
- Public Free and paid Developer offerings exist. Account billing/product identity
  is **UNKNOWN** from the retained APIs; the observed limits are consistent with
  the published Free rows, which is not proof of the account plan.
- Limits are organization-level and model-specific, not per key. Generation
  returned request cap **1,000/day**, token cap **8,000/minute**, request remaining
  **999** and token remaining **7,596 / 7,575 / 7,541 / 7,596** for slots 1–4.
  Separate request/token reset durations were captured as absolute observation-time
  horizons. `Retry-After` was absent. These counters are already historical.
- No organization identifier was exposed. Actual shared organization membership
  is **UNKNOWN**; matching limits do not prove it. OSCAR conservatively groups the
  four keys into one capacity pool and does not multiply capacity by four.

The old 403 against retired Llama choices is preserved in the original checkpoint.
It was insufficient to diagnose credential/account health. Current inventory and
successful GPT OSS probes supersede that interpretation.

## OpenRouter

Sources: [free variant](https://openrouter.ai/docs/guides/routing/model-variants/free),
[free router](https://openrouter.ai/docs/guides/routing/routers/free-router.md),
[limits](https://openrouter.ai/docs/api_reference/limits), and
[account-filtered model API](https://openrouter.ai/docs/api/api-reference/models/list-models-filtered-by-user-provider-preferences-privacy-settings-and-guardrails.md).

- `openrouter/free` dynamically selects among currently available zero-priced
  models according to requested features. It is not one permanent backing model.
  All four slots generated through it. Actual backing observations included
  Dots Note / AtlasCloud, Liquid LFM / Liquid, and Nemotron Lightning / Nvidia;
  additional routing used Apodex / Novita and Nemotron Ultra / Nvidia.
- The runtime checks every returned pricing component before classifying a route
  free. A `:free` name alone is insufficient. Missing/nonzero fee components remain
  UNKNOWN for default routing. Context, output limits and supported parameters are
  model-specific catalog fields; valid `~...-latest` aliases are accepted.
- `/key` reported `is_free_tier=true`, **50 free requests/day** and actual remaining
  daily request counts. The account API is authoritative for this account's current
  numeric constraint; changing public credit/deposit policies are not inferred from
  a templated documentation placeholder. A null key credit cap is not unlimited
  daily free capacity. The latest per-slot counts and reset times are in the record.
- Successful inference responses exposed no quota headers. Generic request limit,
  remaining/reset and `Retry-After` headers are supported when returned on failures.
  Rate limits/account balances and upstream provider capacity are separate.
- Account identity across keys is not exposed; conservative common grouping is
  configurable when distinct accounts are established. It does not sum counters.
  A backing-model failure re-ranks other OpenRouter models; a network failure can
  still block the aggregator. The failed intermediate rerun is retained explicitly.

The previous fixed Liquid route remains listed at this observation; it was not
retired. Its existence does not justify permanently choosing it as OSCAR's free model.

## Google AI Studio

Sources: [models](https://ai.google.dev/gemini-api/docs/models),
[models API](https://ai.google.dev/api/models),
[deprecations](https://ai.google.dev/gemini-api/docs/deprecations),
[pricing](https://ai.google.dev/gemini-api/docs/pricing),
[limits](https://ai.google.dev/gemini-api/docs/rate-limits), and model pages for
[3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
and [3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).

- All three slots listed and generated with `gemini-3.5-flash-lite`; slot 1 also
  generated with `gemini-3.8-flash` after bounded retries of earlier HTTP 503s.
  Lite is the declared low-latency/cost candidate; Flash the declared stronger
  reasoning candidate. These are task-fit choices, not measured comparative benchmarks.
- Both expose input limit **1,048,576**, output limit **65,536**. Official model
  pages document thinking, structured output and function calling. Tool execution
  remains outside OSCAR's implemented adapter contract.
- Current docs advertise standard Free-tier availability. The model list does not
  establish this account's billing tier, project identity, quota or entitlement;
  funding and numerical remaining quota therefore remain **UNKNOWN**.
- Limits are **per project, not per API key**. AI Studio exposes current account
  limits; daily counters reset at midnight Pacific. Batch/priority configurations
  have their own rules; Vertex is a distinct product, not this configured endpoint.
- `gemini-2.5-flash` is legacy access restricted to previous users, **not deprecated**.
  `gemini-3.1-flash-lite` is still listed, with shutdown scheduled 2027-05-07.
  The API still listed officially shut-down Flash-Lite Preview, Flash Image Preview,
  Pro Image Preview and Computer Use Preview. Retirement guards preserve the official
  notices and exclude these despite listing. No retired preview was generation-tested.

The original 50-entry page was not a complete inventory. The correction follows
pagination before asserting account absence; the complete observation was 61.

## NVIDIA NIM

Sources: [current API catalog](https://build.nvidia.com/models) and
[Nemotron Super API documentation](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-super-120b-a12b),
plus both authenticated inventories.

- Both slots generated with `nvidia/nemotron-3.5-lightning-30b-a3b`.
  Slot 1 generated with `nvidia/nemotron-3-super-120b-a12b` and
  `nvidia/nemotron-3-ultra-550b-a55b`; Ultra initially returned 503, later succeeded.
- Lightning/Super/Ultra are declared increasing task-fit candidates. Super documents
  up to a 1M-token context; the public catalog also describes Ultra's long context.
  Exact limits absent from the relevant retained API remain UNKNOWN. Capabilities
  such as JSON/tools vary by model; catalog listing alone is not capability proof.
- The public catalog shows free endpoints, but no authoritative account credit,
  billing, rate/reset or plan metadata was exposed in these responses.
  **Funding = UNKNOWN**. Only bounded diagnostics explicitly permitted unknown cost.
- Hosted developer API trials, self-hosted NIM deployments and enterprise products
  have different licensing/funding arrangements. They are not interchangeable quota
  pools. No account-specific retirement conclusion is inferred for unrelated catalog
  models; the old advertised Mistral 404 remains historical non-callability evidence.

## Z.ai general API and Coding Plan

Sources: [HTTP API](https://docs.z.ai/guides/develop/http/introduction.md),
[general pricing](https://docs.z.ai/guides/overview/pricing.md),
[error codes](https://docs.z.ai/api-reference/api-code.md),
[Coding Plan FAQ](https://docs.z.ai/devpack/faq.md),
[quick start](https://docs.z.ai/devpack/quick-start.md),
[usage policy](https://docs.z.ai/devpack/usage-policy.md),
[release notes](https://docs.z.ai/release-notes/new-released.md), and current
[GLM-5.3](https://docs.z.ai/guides/llm/glm-5.3.md) /
[GLM-5.3-Flash](https://docs.z.ai/guides/vlm/glm-5.3-flash.md) pages.

- General inventories listed `glm-4.5`, `glm-4.5-air`, `glm-4.6`, `glm-4.7`,
  `glm-5`, `glm-5-turbo`, `glm-5.1`, `glm-5.2`, `glm-5.3`, `glm-5.3-flash`,
  `glm-5.3-flashx`. Both general slots called current `glm-5.3-flash` and returned
  **HTTP 429, code 1113**: insufficient balance or no resource package.
  This is quota/funding evidence, not proof of temporary request-rate limiting or
  invalid credentials. Exact balance, package and trial entitlement remain UNKNOWN.
- GLM-5.3 / Flash docs describe 1M context, 128K output, structured/tool capabilities.
  Public general API pricing is paid per token. Runtime account funding remains
  UNKNOWN because trial, prepaid balance and resource-package state were not exposed.
  No new provider-wide retirement is inferred merely from an older model's existence.
- Coding Plan uses the separate `/api/coding/paas/v4` endpoint and subscription/trial
  quota. General API calls consume general balance rather than subscription quota.
  Coding Plan is restricted to officially supported coding tools/products; it is not
  a generic OSCAR reasoning fallback. Team/product credentials may not interchange.
- No legitimate coding-product credentials were configured. Its optional registry
  entry is disabled, coding-task restricted, and has a distinct quota pool.
  **Coding product status, models and remaining quota: UNVERIFIED / UNKNOWN.**
- Numeric plan/account concurrency is dynamic/console-dependent. The API error-code
  boundary distinguishes 1302 rate limiting, 1305 temporary capacity, documented
  product errors and quota exhaustion. Unclassified 429 remains cause UNKNOWN.

## Ollama Cloud

Sources: [cloud API](https://docs.ollama.com/cloud.md),
[API usage](https://docs.ollama.com/api/usage.md),
[tags](https://docs.ollama.com/api/tags.md),
[current cloud catalog](https://ollama.com/search?c=cloud),
[pricing](https://ollama.com/pricing),
[structured outputs](https://docs.ollama.com/capabilities/structured-outputs.md), and
[tools](https://docs.ollama.com/capabilities/tool-calling.md).

Both account observations listed:

```text
mistral-large-3:675b      kimi-k2.6                minimax-m2.7
nemotron-3-super         nemotron-3-ultra         kimi-k2.7-code
nemotron-3-nano:30b      glm-5.3-flash            deepseek-v4.1-flash
gpt-oss:120b             gpt-oss:20b              minimax-m3
gemma4:31b               deepseek-v4-pro:0813     glm-5.2
glm-5.3                 kimi-k3
```

- Both slots generated with `gemma4:31b`. `glm-5.3-flash` returned 402 on both;
  `glm-5.3` returned 402 on slot 1. Funding/entitlement for those models is unknown;
  the model-specific refusal does not make the whole account or all starter models
  unavailable. The seed alias `deepseek-v4-pro` was absent; `:0813` was observed.
  This is an alias/account-inventory correction, not proof of global retirement.
- Free plans include starter credits and starter-model access. Adding credits
  unlocks all models; paid Pro/Max and Team offerings have separate credit/concurrency
  terms. Team credits are shared. Current plan, remaining credits and per-model
  free-credit eligibility were **not exposed** by `/tags` or these generation headers.
  Funding remains UNKNOWN even for successful Gemma generation.
- **Cloud structured outputs are currently unsupported** according to official docs;
  local Ollama support must not be transferred to cloud. Tool support is model-specific.
  The tags response does not expose authoritative context/output limits. Missing
  cloud limits stay UNKNOWN; bounded diagnostics explicitly acknowledge that gap.
- The old screenshot/free-credit list is historical account evidence. It does not
  establish today's eligibility or capacity. No account balance endpoint is invented.

## Outstanding acceptance

Public support/current listing/generation/funding are preserved separately in the
registry. Numerical shared-pool membership, account credits and most provider quota
totals remain UNKNOWN. Tool execution, broad web retrieval and quality benchmarking
are not claimed by these probes. Tavily's provider boundary and three placeholders
are prepared, but keys are absent and live Tavily integration is UNVERIFIED.

The intended first combined native-inventory/search acceptance objective is owned by
[SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md). This correction remains Club A;
**Slice 05 is not started**.
