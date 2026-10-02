# Search + Freshness

OSCAR must not answer freshness-sensitive questions from stale memory, old provider manifests or model priors when an authoritative live source can reasonably be checked.

This is an epistemic-integrity rule, not an optional research feature.

## Core rule

> If the answer can materially change with time, OSCAR should prefer a current authoritative source over recalled/model knowledge.

Examples include:

- latest/current/today/recent news or events;
- model/provider availability, deprecations, pricing, quotas and rate limits;
- software/API/framework documentation and releases;
- product inventory, prices and availability;
- schedules, reservations, outages and service status;
- laws/policies/requirements that may have changed;
- live device/app/account state;
- any claim whose staleness could change the user's decision or OSCAR's execution path.

`RECALLED` or model-prior information must never silently become `VERIFIED CURRENT`.

## Freshness decision

Jev now classifies whether an objective is:

```text
stable
freshness-sensitive
live-state
unknown-freshness
```

A freshness-sensitive/live-state objective should normally route through one or more of:

```text
authoritative API / connector
provider-specific inventory/status endpoint
live World Model source
web/search capability
specialist research capability
```

Only after retrieval should reasoning/synthesis occur.

If current lookup is unavailable, OSCAR returns **UNKNOWN / potentially stale**
and blocks the current-fact objective. It does not fall through to model prior,
including when the caller forces a reasoning path. Static deterministic file/addition
paths run first; `what is 2+2?` makes no search/model call. Recognition remains a
conservative grammar, not a claim of general intent understanding.

## Search capability

Search is a first-class OSCAR capability exposed through the Capability Catalog. Tavily is the first implemented web-search adapter, not the architectural boundary.

Initial development credential pool after Club A:

```text
TAVILY_API_KEY_1
TAVILY_API_KEY_2
TAVILY_API_KEY_3
```

Keys are separate credential slots; they may share an account quota pool.
Three keys do not imply three times the credits. Provider identity, product/pool,
slot health, rate/quota/cooldown and secrecy remain separate concerns.

The search adapter must remain replaceable so OSCAR can later use other search/research providers or native provider search without redesigning Jev/Core.

Tavily currently exposes Search, Extract, Crawl, Map and Research APIs. The first implementation only needs the smallest useful search/retrieval contract; do not overbuild the integration.

## Implemented boundary and limits

[freshness.py](../oscar/freshness.py) owns typed freshness and source authority.
[retrieval.py](../oscar/retrieval.py) owns `RetrievalRequest`, `RetrievedFact`,
`RetrievalResult`, the replaceable `RetrievalProvider` protocol and executor.
Requests bound result count/depth and allow domain/time constraints. Query/source
text is task data; retrieval telemetry retains references, timestamps, scope and
conflicts without prompt/answer content. Domain restrictions match hostnames.

The real `live_source` capability uses provider-native inventories for configured
provider-model questions. Current-fact requests actively retrieve even when a
short routing TTL would otherwise permit a cache. Complete inventories preserve
URL/identity, observation time, scope and retirement/cache contradictions. Listed
models do not imply generation or funding. Officially retired entries remain
excluded even when the API lists them.

[search.py](../oscar/search.py) now implements Tavily through that same protocol.
Harness composes native inventory and web retrieval without changing Jev. Search
uses the current official Bearer-authenticated `POST /search` contract: explicit
basic depth, automatic cost escalation/answers/raw pages disabled, usage enabled,
15-second calls and a 30-second total search budget. Domain restrictions are checked
again against returned HTTPS URLs; query/credential-bearing references are omitted.
Official results trigger a bounded, credential-free read of the actual trusted
official page. Only those reads receive `official_page` evidence. Index excerpts
whose pages cannot be read remain secondary discovery hints marked UNKNOWN /
potentially stale; they cannot satisfy current official-page acceptance.
The configured-provider objective searches each of the six official domain groups
with one result per group, within the requested result budget. Other objectives
use a bounded ordinary search when keys are present.

Tavily slots have their own conservatively shared account-product/quota pool,
separate from model providers. A 401 invalidates only its slot; 429/432/433 preserve
rate/usage-limit semantics and shared cooldowns, including explicit Retry-After.
Returned numeric `usage.credits` is observed expenditure, not an inferred remaining
balance or three independent free allotments. No account product is inferred from
a public Free offer. Missing/unusable keys produce UNKNOWN, never a fabricated result.

Evidence synthesis separates account-visible inventories from provider-wide source
excerpts and displays conflicts, source authority and observation times. Web excerpts
cannot update routing availability/funding or override applicable retirement guards.
Search publication/update dates are estimates, distinct from retrieval time; the
answer explicitly qualifies excerpt recency and unresolved account entitlements.
Source material stays REPORTED; unsupported factual verification remains PARTIAL.
Persisted retrieval/search telemetry stores references, retrieval method, timestamps,
conflicts, masked slots, categorical status and numeric credits, not queries or webpage dumps.

The final acceptance environment still exposes **none of the three Tavily slots**.
The adapter and loopback contracts are implemented/tested, but **actual live Tavily
UNVERIFIED; combined public-web acceptance BLOCKED**. The real Jev objective did
retrieve six current native inventories, with zero generation calls. It does not
claim current public access constraints from those listings alone. See the dated
[checkpoint](CLUB-A-CHECKPOINT.md) for live observations and credential blockers.

## Search request contract

A search request should preserve at least:

```text
objective/query
freshness requirement
requested time range when applicable
source/domain constraints when applicable
result limit
search depth / cost class
credential slot
request timestamp
source URLs
retrieval timestamp
provider usage/credits when exposed
```

Search results are `REPORTED` source material until the claim is evaluated against the returned sources. Search ranking is not truth.

## Source authority

Prefer source authority appropriate to the claim.

Examples:

```text
provider model availability
→ provider's official model/inventory/deprecation docs or live API

API behavior
→ current official API docs + observed endpoint behavior

repository state
→ repository itself

account quota
→ account/provider usage endpoint, not a blog post

news/current event
→ current primary/credible reporting with dates
```

Search is not permission to replace an authoritative source with an easier secondary source.

For provider/model facts, preserve ordered source authority rather than flattening
it into one confidence number:

1. live account/provider API;
2. current official documentation;
3. current official announcements/deprecations;
4. reputable secondary source;
5. cached OSCAR metadata;
6. model prior.

The ordering is claim-specific: account availability prefers account APIs over
generic pages; provider/product retirement prefers the applicable official notice
over an API catalog/cache that still lists the ID. Observation time, product scope
and contradictions remain separate fields. `prefer_source` encodes this comparison;
the registry enforces account absence and explicit retirement guards. Evidence
synthesis retains conflicting native/retirement observations and separates
account claims from generic web claims. Arbitrary prose contradictions are not
automatically verified or resolved; unresolved source statements stay explicit.

## Freshness metadata

Retrieved claims should retain, where available:

- source URL / source ID;
- publication/update time;
- retrieval time;
- source authority/type;
- requested freshness horizon;
- whether the source actually satisfies that horizon;
- conflicts between sources.
- account-specific vs provider-global scope;
- refreshability and TTL (hosted inventory defaults to 300 seconds).

If freshness cannot be established, preserve `UNKNOWN` rather than inventing recency.

## Search-first provider/model maintenance

Provider/model metadata is volatile. Before using seeded model IDs as current truth, OSCAR should prefer live inventory/deprecation evidence.

Expected flow:

```text
need provider/model route
→ check cached metadata freshness
→ if stale/unknown: query live provider inventory and/or current official docs
→ remove/deprioritize deprecated/unavailable IDs
→ test candidate with bounded probe when appropriate
→ record observed capability/availability
→ route task
```

A historical successful model call does not prove that model is still available today.

## First search objective

The first combined-search acceptance objective, still pending real Tavily
credentials, is OSCAR-related and deliberately freshness-sensitive:

> `What are the currently supported models and relevant free/developer access constraints for OSCAR's configured intelligence providers right now?`

Expected behavior:

```text
Jev detects freshness-sensitive objective
→ live search/provider inventory
→ authoritative current sources
→ prefer official pages; reconcile conflicting evidence by claim scope
→ source-backed synthesis
→ no stale manifest/model-prior claim presented as current
→ evidence + retrieval timestamps recorded
```

This objective should specifically catch the failure mode where OSCAR attempts retired provider model IDs from an old manifest.

## Tavily handling

For the first Tavily integration:

- use the official Search endpoint;
- use time ranges/date filters when the objective requires them;
- keep `include_answer` optional because OSCAR should reason over cited results itself;
- preserve result URLs and retrieval metadata;
- use usage/credit information when the API exposes it;
- treat 401/429/plan-limit responses as credential/capacity state, not fabricated search results;
- bounded credential failover across the three slots;
- never print or persist raw API keys.

## Relationship to memory

Memory answers `what did I know/observe before?`

Search/live retrieval answers `what is true now?`

When the user asks for current truth, live authoritative evidence outranks memory unless the live source itself is known stale or inappropriate.

## Invariants

1. Freshness-sensitive questions do not silently rely on model training knowledge.
2. Old manifests/caches are hints, not current authority.
3. Search results retain sources and retrieval time.
4. Search ranking does not equal verification.
5. Current authoritative sources outrank recalled/model-prior information.
6. If OSCAR cannot obtain current evidence, it says so.
7. Tavily is the first adapter, not a permanent dependency.
8. Search keys retain slot health/failover and shared account quota-pool semantics.
9. Search is invoked when freshness matters, not on every stable fact.
10. The first search acceptance objective is explicitly about OSCAR's own current provider/model state.
