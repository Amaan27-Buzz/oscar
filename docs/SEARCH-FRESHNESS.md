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

Jev should classify whether an objective is:

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

If current lookup is unavailable, OSCAR should say that the answer may be stale rather than presenting old knowledge as current fact.

## Search capability

Search is a first-class OSCAR capability exposed through the Capability Catalog. Tavily is the initial planned web-search provider, not the architectural boundary.

Initial development credential pool after Club A:

```text
TAVILY_API_KEY_1
TAVILY_API_KEY_2
TAVILY_API_KEY_3
```

Keys are independent credential slots with the same health/rate/quota/cooldown/secrecy rules as model-provider credentials.

The search adapter must remain replaceable so OSCAR can later use other search/research providers or native provider search without redesigning Jev/Core.

Tavily currently exposes Search, Extract, Crawl, Map and Research APIs. The first implementation only needs the smallest useful search/retrieval contract; do not overbuild the integration.

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

## Freshness metadata

Retrieved claims should retain, where available:

- source URL / source ID;
- publication/update time;
- retrieval time;
- source authority/type;
- requested freshness horizon;
- whether the source actually satisfies that horizon;
- conflicts between sources.

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

The first end-to-end search objective should be OSCAR-related and deliberately freshness-sensitive:

> `What are the currently supported models and relevant free/developer access constraints for OSCAR's configured intelligence providers right now?`

Expected behavior:

```text
Jev detects freshness-sensitive objective
→ live search/provider inventory
→ authoritative current sources
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
8. Search keys use independent credential-pool/failover semantics.
9. Search is invoked when freshness matters, not on every stable fact.
10. The first search acceptance objective is explicitly about OSCAR's own current provider/model state.
