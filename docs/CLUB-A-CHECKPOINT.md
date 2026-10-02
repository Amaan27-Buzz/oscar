# Club A — Brain checkpoint

## Final Gate A acceptance — PARTIAL (Tavily credentials absent)

Recorded **2026-10-03 IST** (live observations on 2026-10-02 UTC), continuing remote `work`
`d7caacec37c18d2f62382a9308e4af77967f02fc`. Fetch confirmed that exact head and a
clean checkout. This final pass completes the adapter and closes the routing gap;
it does not redesign Club A, repeat the expensive provider-generation matrix,
merge main or start Slice 05. The earlier PARTIAL checkpoint below and its 69/72
run are preserved as history, not quietly replaced.

### Final decision

**Gate A remains PARTIAL solely because real Tavily/search acceptance is BLOCKED
by absent credentials.** `tavily-1`, `tavily-2` and `tavily-3` are absent from the
execution environment; no key material was printed and no Tavily API traffic,
credits or successful slot results are invented. The credential-location question
was raised during the pass; no credentials became available. The implemented
adapter's loopback/offline contracts do not substitute for actual live acceptance.
No architectural defect was exposed by the focused routing review.

Gate A does not require all providers to work simultaneously. Genuine BLOCKED is
correct when no route satisfies current capability/funding/capacity policy;
temporary rate limits are not defects when reranking/cooldowns are handled
truthfully. Successful generation and a truthful block are distinct observations.

### Focused live routing

| Mode | Latest generation result | Current route / actual backing source | Attempts |
|---|---|---|---:|
| Balanced | VERIFIED bounded JSON contract | `openrouter/free` → `nvidia/nemotron-3.5-lightning:free`, NVIDIA; `openrouter-1` | 1 |
| Heavy Duty | VERIFIED exact text contract | `nvidia/nemotron-3-ultra-550b-a55b:free`, NVIDIA; `openrouter-1` | 1 |
| Free First | VERIFIED bounded JSON contract | `apodex/apodex-1.1-mini:free`, Novita; `openrouter-2` | 1 |

All three use fresh credential-visible inventory and unchanged default funding
policy: no paid or UNKNOWN funding/limits override. Each returned HTTP 200 and was
independently compared against its bounded completion criterion. Model/provider
responses remain REPORTED; this proves generation contracts, not model quality.
Across two focused runs **26 runtime assertions passed**, separate from unit tests.
No full provider generation matrix or Auto/Fast/Manual rerun was needed.

The first Heavy diagnostic required structured output and correctly made **zero
attempts**. Current high-tier free Qwen/Nemotron entries were listed with sufficient
limits, but their current inventories established only text capability; expired
seed metadata could not restore structured support. Offline diagnostics are retained
in the original run. One subsequent text-only Heavy probe used the actually
advertised capability and succeeded; Balanced/Free First were not repeated.

There were **no new 429s or active provider/shared-pool cooldowns** in these focused
runs. Exposed response counters/reset/Retry-After were absent and remain UNKNOWN.
OpenRouter's account endpoint again reported Free tier; account identity/shared
membership is not inferred from slot count. The common conservative pool remains
one capacity pool. Focused offline cases prove a shared 429 blocks sibling keys,
leaves unrelated capacity eligible, and reranks to that unrelated provider. Prior
live rate-limit observations and their original timestamps remain in history.
Z.ai/general balance/product failure 1113 is historical; it was not generation-retested.

### Real freshness objective and search boundary

The exact first objective ran through **Jev → authenticated reference transport →
live inventory retrieval → evidence-qualified answer**. Jev selected live retrieval.
Six real account inventory APIs were read; **zero model-generation calls** were
made. The successful correlated retrieval result stays REPORTED and the task is
PARTIALLY_VERIFIED. Current inventory versus cached/retired conflicts remain explicit.

Sources observed during this pass: Groq `/openai/v1/models`, OpenRouter
`/api/v1/models/user`, NVIDIA `/v1/models`, Google `/v1beta/models` (paginated),
Z.ai general `/api/paas/v4/models`, and Ollama Cloud `/api/tags`. URLs, observation
timestamps, scope and conflicts are preserved in the
[final evidence](evidence/club-a-final-acceptance-2026-10-02.json). Google's applicable
retirement notice remains separately sourced with its prior observation time.
These APIs prove account listing, not successful generation or funding entitlement.

Current official Tavily Search/credits/rate-limit/usage documentation was retrieved
before implementation. Tavily now implements the existing replaceable retrieval
protocol: Bearer HTTPS, explicit basic depth, automatic escalation/answers/raw pages
disabled, bounded calls/results/deadlines, returned credit expenditure, slot health,
shared quota/cooldowns and full Retry-After preservation. Official search results
trigger bounded credential-free page reads. Indexed snippets whose pages cannot
be retrieved remain secondary/UNKNOWN; they cannot count as current official-page
acceptance. No giant page bodies or query text enter retrieval telemetry.

The answer separates account inventories from provider-global evidence and displays
conflicts. Web evidence cannot authorize account routes or override retirement
facts. Factual excerpts remain REPORTED; unsupported or unavailable claims stay
UNKNOWN. The final search verifier requires current-task/correlation evidence, a
successful correlated result, six distinct native inventories, actual objective
Tavily traffic, and six direct official-page sources. Preflights, stale evidence,
index snippets and a failed transport cannot produce PASS.

**Actual live Tavily UNVERIFIED / combined official access-constraint synthesis
BLOCKED**: all three required slots remain absent. Provider-native inventory alone
is not promoted into completion of the full combined-search objective. Canonical
architecture and remaining live acceptance are owned by
[SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md).

### Regression and stop

The full offline suite ran once after focused live acceptance: **209 tests PASS**
in 29.377 seconds. This retains all 161 prior tests and adds 48 focused search,
official-page, source/correlation, mode/capacity and failure contracts. Ruff,
formatting (**39 Python files**) and strict mypy (**25 source files**) PASS.
Repository/link checks, value-silent secret scanning and final diff inspection
are recorded in the final evidence. Missing Tavily credentials are the remaining
live acceptance blocker; account-credit and general factual-verification limits
remain UNKNOWN. **Stop on `work`; no main merge or Slice 05.**


## Historical post-Gate-A correction — 2026-10-02 (preserved)

**Gate A: PARTIAL, downgraded from the previous PASS. Stop for manual review.
Slice 05 is not started.** Core Loop/Jev/reference Transport/Grid proofs remain
verified. The corrected architecture passes automated checks, but the latest
complete live mode rerun did not pass: Auto/Fast generated verified responses;
Balanced encountered a backing failure followed by an unexplained OpenRouter 429;
Heavy Duty and Free First then blocked under the shared-pool cooldown.
Paid/UNKNOWN-cost fallback was not silently used. Earlier successful mode checks
remain historical evidence; they do not turn this latest rerun into PASS.

### Explicit correction to the previous evidence

The checkout was clean and synchronized from remote `work` to `aa791dd` before
editing. Its newer documentation and candidate metadata were read and retained.
Current official provider catalogs/deprecation/limit/product pages were retrieved
before changing metadata, followed by all 17 credential-visible inventories and
bounded current generation probes. Sources and observation times are retained in
[provider research](PROVIDER-RESEARCH.md) and its linked evidence records.

The previous Groq 403 used stale Llama model IDs retired for Free/Developer.
That observation is preserved below and in the unchanged original JSON records.
It was **insufficient to diagnose credential/account health**. All four current
Groq inventories listed GPT OSS/Qwen candidates; all four keys generated with
GPT OSS 20B, and slot 1 also generated with GPT OSS 120B and current Qwen.
These observations supersede the old Groq-health interpretation. A 403 is now
access denial unless more specific evidence identifies retirement or credential failure.

Other corrections are explicit: Google 2.5 is restricted legacy access, not retired;
3.1 Flash-Lite is still listed with a future shutdown. Several officially shut-down
Google previews remain in the API catalog, so official retirement guards override
those listings. Google inventory is now fully paginated. OpenRouter's old Liquid
model still exists but is not a permanent free route. The Ollama versionless
DeepSeek alias was absent, while `:0813` was listed; screenshot-era credit eligibility
is historical. NVIDIA funding remains UNKNOWN despite public free-endpoint labels.
Z.ai general 429 now retains code 1113 rather than guessing temporary rate limits.

### Implemented correction and discovered defects

The manifest is a bootstrap/retirement seed. Fresh, per-slot native inventory with
TTL/source/scope feeds a persistent registry; visibility, generation, retirement,
funding and quota remain separate. Account products and shared quota pools sit
between provider and credentials; four keys do not create four quota budgets.
Jev routes current/latest/live questions toward a replaceable live-source capability,
and unavailable current sources block as UNKNOWN/potentially stale.

The pass also found and fixed concrete runtime defects: rejecting valid
OpenRouter `~...-latest` aliases; blocking the entire aggregator after one backing
model failed; and allowing an empty model-level capacity record to hide an
account-wide cooldown. Regression tests cover each. The latest actual 200-inline
backing failure → alternate current model → 429 sequence shows bounded reranking,
followed by zero attempts for later modes under the common cooldown. There is no
claim that the unknown 429 was daily quota exhaustion or that multiple keys are
confirmed to share one real account.

Final review additionally prevented pricing/limits from one slot's inventory
authorizing another account's route, and prevented a fieldless fresh inventory
from refreshing expired seed limits. These account/fact-scope protections have
focused regression coverage.

### Verification and limits at that historical checkpoint

- **161 automated tests pass**, including all previous contracts and freshness
  A–E, retirement/catalog conflicts, denied generation versus listing, persistence,
  pagination, shared counters/concurrency/reset/cooldown and backing metadata.
- Ruff, format (31 Python files), strict mypy (21 source files), repository/link
  checks, value-silent secret scans and diff checks **PASS**.
- All **17 configured slots** returned current inventories. **15 slots across five
  providers** independently generated matching bounded responses. Both general
  Z.ai slots returned 429/code 1113: insufficient balance or no resource package;
  exact balance/trial/product state remains UNKNOWN.
- An earlier correction run passed **94 live assertions** and all five automatic
  modes. The latest targeted inventory/mode run passed **69 of 72 assertions**;
  three current-mode acceptance assertions failed/blocked as described above.
  These are distinct runs, not cumulative unit tests. Failed intermediate runs and
  the heartbeat-expiry harness error are retained with their causes.
- Groq returned actual request/token limits, remaining counts and reset metadata.
  OpenRouter `/key` returned Free-tier/daily quota information. Other account
  funding/quota gaps remain UNKNOWN; public catalogs are not entitlements.
- Native execution of the intended provider-search objective returned sourced
  inventory and PARTIALLY_VERIFIED status with **zero generation calls**. Official
  web access-constraint synthesis is still unverified. Today's-weather intent with
  no source became BLOCKED/UNKNOWN rather than a fabricated current answer.
- Tavily's provider boundary and three placeholders are prepared. All three keys
  are absent: **actual live Tavily UNVERIFIED**. Z.ai Coding Plan is separately
  modeled and disabled; no legitimate coding credentials/entitlement were established.

Canonical ownership: registry/pool/runtime behavior in [MODEL-ROUTING.md](MODEL-ROUTING.md),
freshness/search/source authority in [SEARCH-FRESHNESS.md](SEARCH-FRESHNESS.md),
dated provider facts in [PROVIDER-RESEARCH.md](PROVIDER-RESEARCH.md), and observations
in [the correction record](evidence/club-a-correction-2026-10-02.json).
Public coordinator deployment, physical nodes, broad web search, model benchmarks
and account-credit forecasting remain outside verified foundation scope.

Gate A can be reconsidered after current eligible free capacity permits a complete
passing mode run. UNKNOWN billing/limits must be resolved with account evidence or
explicit policy; they cannot be reclassified free merely to force acceptance.
**This correction is committed/pushed to `work` only. Do not start Slice 05.**

## Historical pre-correction checkpoint — preserved

The following checkpoint and its linked evidence describe the earlier run. Its
provider-health interpretations and current status are superseded above; the
original failures, assertions and limits are preserved rather than rewritten.

Recorded **2026-10-02**. Overall status: **VERIFIED for the implemented Club A foundation. Gate A: PASS; manual review pending. Slice 05 is not started.**

This verification continues the previously pushed `work` commit **`93ad11a48891035373292fd6a16c39b4340d8684`**. The checkout was fast-forwarded to that implementation before inspection or execution. No Core Loop, Jev, Transport, Grid, provider adapter or router was rebuilt. This continuation adds an opt-in verification script, refreshes four stale model entries using live inventory/generation evidence, and updates durable evidence/status.

## Gate A decision and scope

Gate A passes the foundation criteria authorized for this review:

- Core Loop and Jev are verified by the real HTTP/file/read proof and the complete contract suite.
- Native Transport/Catalog/Grid are coherent reference foundations: authenticated loopback execution, target scope checks, durable objective state, disconnect/reconnect, cancellation and lease expiry are verified.
- **Four real hosted providers and 11 real credential slots** successfully generated independently checked responses.
- Real credential rejection/failover, bounded cross-provider recovery, observed rate-limit reranking, automatic modes and Manual pins have live evidence.
- Executor/provider testimony stays REPORTED; absent objective verification remains partial. Fake success, malformed/empty responses, exhausted retries and Local restrictions have no false-success path in the verified scenarios.

This is acceptance of the implemented developer foundation, **not production Internet transport, physical embodiments, general model quality or complete quota forecasting**. The current review criteria accept the reference Transport/Grid stage; the earlier requirement for a public coordinator deployment is deferred to later Grid integration acceptance. Its implementation and acceptance scenario remain outstanding. Full slice/product capabilities are not silently marked shipped.

**Stop for manual review. Do not start Slice 05.**

## Slice evidence

| Slice | Status in this checkpoint | Evidence / limit |
|---|---|---|
| 01 — Core Loop | VERIFIED for implemented foundation | Real exact-file objective → HTTP execution → REPORTED result → independent read → VERIFIED evidence/task/artifact. Direct filesystem inspection confirmed exact bytes. Fake executor → missing file → FAILED. SQLite restart, cancellation, bounded retries, scope and deduplication tested. |
| 02 — TypeSafe Jev | VERIFIED for implemented foundation | All nine routes are typed and tested; arithmetic/file intents avoid a model. Missing live-source, memory, specialist and Worker capabilities block. Conservative grammar, not general language understanding. |
| 03 — Transport / Catalog / Grid | VERIFIED reference foundation; broader deployment PARTIAL | Authenticated loopback HTTP, scopes, replay rejection, correlated result/control/progress, five availability levels, disconnect/reconnect and durable lease expiry verified. Shared-store reference nodes; public TLS/outbound rendezvous and physical embodiments remain unverified. |
| 04 — Adaptive Model Router | VERIFIED hosted/routing foundation; broader integrations PARTIAL | Four hosted providers, 11 working real slots, all requested live modes/pins, credential failover, cross-provider recovery and actual rate-limit reranking verified. Real quota counters were not exposed. Local runtime integrations, ChatGPT product surfaces and model benchmarks remain later work. |

## Architecture and changed modules

The implementation remains the native Python 3.12/SQLite foundation, without Latch/SwitchRoute runtime dependencies or a new service stack.

| Responsibility | Existing implementation |
|---|---|
| Typed wire/domain/epistemic contracts | [contracts.py](../oscar/contracts.py) |
| Durable task, ledger, replay and idempotency authority | [storage.py](../oscar/storage.py) |
| Objective execution and independent verification | [runtime.py](../oscar/runtime.py), [capabilities.py](../oscar/capabilities.py) |
| Typed execution-class decisions | [jev.py](../oscar/jev.py) |
| Identity, scopes, capabilities, health, availability, leases and revocation | [grid.py](../oscar/grid.py), [transport.py](../oscar/transport.py) |
| Replaceable model/provider metadata and opaque credential pools | [models.py](../oscar/models.py), [registry.py](../oscar/registry.py), [credentials.py](../oscar/credentials.py) |
| Adaptive routing, fallback and content-free history | [router.py](../oscar/router.py) |
| OpenAI-compatible, Google and Ollama HTTPS adapters | [providers.py](../oscar/providers.py), [http_client.py](../oscar/http_client.py) |
| Composition and developer commands | [harness.py](../oscar/harness.py), [cli.py](../oscar/cli.py) |

Verification additions: [live suite](../scripts/verify_club_a_live.py), [refreshed development manifest](../config/development-models.json), and [safe live evidence](evidence/club-a-live-2026-10-02.json). Existing runtime modules are unchanged.

## Automated results

After live integrations, **all 113 tests passed**. Ruff lint passed; formatting passed for all 27 Python files. Strict mypy passed for all 18 checked source files, including the live verification script. Repository required-file, local Markdown-link, removed-reference, whitespace and secret-safety checks pass. GitHub Actions and external URL checks were not run here.

The live suite separately passed **162 checks**. These are explicit live/runtime assertions, not an inflated unit-test count. All ordinary tests remain offline or explicitly synthetic loopback tests; hosted traffic requires the live flag.

## Real hosted evidence

The environment's readiness tool reports UNKNOWN variable/policy readiness, so readiness was not assumed from configuration. The actual HTTPS responses establish operation-level access. Inherited proxy, CA trust and TLS verification were preserved. All 17 configured slots were present; neither presence nor a public model listing proves credential validity.

The [original blocked evidence](evidence/club-a-hosted-2026-10-02.json) is retained as history. The [new live record](evidence/club-a-live-2026-10-02.json) supersedes its hosted-verification status.

| Provider | Returned inventory page | Real generation / masked slots | Outcome |
|---|---:|---|---|
| Groq | HTTP 403 for all four slots | `llama-3.1-8b-instant`; `groq-1` through `groq-4` | UNAVAILABLE: HTTP 403 access rejection. The adapter categorizes it as `credential_failure`; the evidence does not establish whether the cause is the key, account or service access policy. No Groq success claimed. |
| OpenRouter | 464 models per tested slot | `liquid/lfm-2.5-2.6b:free`; `openrouter-1` through `openrouter-4` | VERIFIED generation contract: four HTTP 200 responses independently matched. The live model listing advertises zero prompt/completion pricing; no remaining account quota is inferred. |
| Google AI Studio | 50 models on the returned page per slot | `gemini-3.1-flash-lite`; `google-1` through `google-3` | VERIFIED generation contract: three slots matched. Initial `google-3` HTTP 503 was transient; the subsequent bounded probe succeeded. Listing count is not a complete paginated inventory claim. |
| Ollama Cloud | 17 models per tested slot | `gemma4:31b`; `ollama-cloud-1`, `ollama-cloud-2`; Heavy Duty additionally used `nemotron-3-ultra` | VERIFIED generation contracts and Heavy Duty routing. No remaining credit/request balance is inferred. |
| NVIDIA NIM | 81 models per tested slot | `nvidia/nemotron-3-super-120b-a12b`; `nvidia-1`, `nvidia-2` | VERIFIED generation contract for both slots with bounded 512-token probes. Funding/price remain UNKNOWN; only this explicit diagnostic policy allowed unknown cost. |
| Z.ai | 11 models per tested slot | `glm-4.5-air`; `zai-1`, `zai-2` | UNAVAILABLE: actual HTTP 429. Exact quota/balance and the distinction between temporary rate limiting and account capacity are not exposed by the retained categorical evidence. No Z.ai generation success claimed. |

The refreshed manifest replaces unavailable seeded OpenRouter/NVIDIA models, the Google model that returned 404 for generation, and `gemma3:31b` with observed alternatives. Inventory inclusion alone was insufficient: an advertised NVIDIA Mistral model also returned 404. Quality tiers/context/output limits remain conservative configuration, not benchmarks. `last_verified` is not promoted into a model-quality claim.

An initial NVIDIA 128-token probe and a separate small-budget OpenRouter reasoning probe returned HTTP 200 without usable answer text. OSCAR correctly rejected both as `capability_mismatch` rather than claiming success. Suitable bounded diagnostics then succeeded. The failed reasoning task remained FAILED; its replacement used Google with a 256-token budget and remained PARTIALLY_VERIFIED without a verifier.

NVIDIA/Z.ai diagnostic allowances are opt-in, per-test, and bounded. They do not change default no-paid routing or classify unknown funding as free. No account was deliberately exhausted to manufacture a limit.

## Requested verification matrix

| # | Requirement | Actual evidence / scope |
|---:|---|---|
| 1 | Multiple real provider requests | OpenRouter, Google, Ollama Cloud and NVIDIA NIM returned usable HTTP 200 generations that independently matched the expected response. |
| 2 | Provider/model inventory | All six providers were queried across their configured slots. Five returned model pages; Groq rejected access. Listings are not credential/capacity guarantees. |
| 3 | Multiple credential slots | Four OpenRouter, three Google, two NVIDIA and two Ollama slots independently succeeded. Separate slot metadata does not prove separate billing/quota pools. |
| 4 | Credential failover | A deliberately invalid **test** slot `openrouter-0-invalid-fixture` was rejected by the real endpoint with HTTP 401; `openrouter-1` then returned a matching HTTP 200 in attempt 2. No real credential was corrupted. |
| 5 | Bounded cross-provider fallback | Actual Groq HTTP 403 → OpenRouter HTTP 200 in two attempts. A separate one-attempt policy stopped after Groq rejection and made no alternate call. |
| 6 | Auto | After actual slot-health observations, Auto selected OpenRouter and matched the response. |
| 7 | Free First | Selected the available configured free OpenRouter route and matched; unknown-cost NVIDIA/Z.ai remained outside the default policy. |
| 8 | Scarcity-aware routing | Equal-tier Google/Ollama candidates changed order when explicitly synthetic 2/500 request balances were reversed. The selected Ollama HTTPS call succeeded. These numbers are **test fixtures, not provider quota**. Separately, copied actual Z.ai HTTP 429 cooldown evidence changed a Heavy diagnostic route to OpenRouter, whose real call succeeded. Real numerical quota calibration remains UNVERIFIED. |
| 9 | Fast | Selected OpenRouter using the existing quality floor and observed latency/reliability ranking; real generation matched. This is not a claim that it is globally the fastest model. |
| 10 | Heavy Duty | Quality floor 4 selected the strongest eligible configured tier, Ollama `nemotron-3-ultra`; real generation matched. Model power tiers remain declared metadata. |
| 11 | Manual pins | All 11 successful slot probes used explicit provider/model/slot pins. The real invalid-slot failover retained the provider/model pin. Policy-bypass rejection remains covered by contract tests. |
| 12 | Unknown quota | Successful hosted responses exposed no request/token quota headers. Remaining request/token counters stayed null in real slot state and history. Actual usage tokens are separate from remaining quota. |
| 13 | Secret/content-free history | All live stores' serialized route history was checked against credential material, the sent prompts and response contents. No matches. Only masked IDs, route/usage/timing/failure/verification metadata persist. |
| 14 | Reported until verified | Every usable routed response was REPORTED and objective verification was null before independent comparison. Comparison evidence verified only the generation contract. A real Google reasoning objective stayed PARTIALLY_VERIFIED with a REPORTED result and unknown objective match. |
| 15 | Local refuses silent fallback | The live router produced `route_unavailable` with zero HTTP calls. The actual Local CLI returned exit 2, task BLOCKED and zero route-history entries. |

## Core / Grid proofs and secret safety

The live script re-executed the authenticated HTTP exact-file proof, directly inspected the written bytes, rejected a deliberately lying executor, verified deterministic addition without model use, and observed real-time Grid lease expiry after disconnect while preserving the objective. The full 113-test suite verifies restart/reconnect, correlated evidence, scoped permissions, cancellation, replay/idempotency, bounded fallback, streaming integrity and stale ownership.

Provider secrets were checked value-silently against tracked/non-ignored source/docs, the final patch, and ignored report/log/proof/SQLite artifacts. Common secret-like patterns were also checked. No credential values, prefixes, suffixes, hashes or provider error bodies are included in the evidence. The runtime never reads/writes `.env`.

## Remaining limitations and later acceptance

- Public TLS/outbound rendezvous, configured public coordinator deployment, independent network-node stores/replication and production pairing UX remain unimplemented/unverified. The reference target shares SQLite and is loopback-only. Later Grid integration must supply its own configured-target acceptance scenario.
- Real quota/credit/reset/usage-velocity forecasting needs provider-exposed counters. The existing scarcity heuristic uses confirmed request balances; absent/stale balances remain unknown. No provider balance or model-quality benchmark was invented.
- Groq access and Z.ai rate/account capacity need provider-side resolution. They do not invalidate verified behavior of available routes. UNKNOWN NVIDIA/Z.ai costs remain excluded by default.
- Jev is a conservative grammar. The POSIX verifier proves exact bytes/addition, not arbitrary objectives or Windows behavior. Unsupported verification remains partial/unknown; no automatic file compensation is advertised.
- Cancellation is cooperative; provider reads are bounded and cannot undo committed effects. Crash-ambiguous actions require inspection/reconciliation. Reference transport/control acknowledgements remain REPORTED.
- Local Ollama/LM Studio/vLLM instances, the user's machines/LAN, actual Sunday/Edge hardware, remote wake, Workers, memory, communications and UI are unverified or later slices. No Slice 05 work is included.

## Reproduce the review

From the repository root, provision credentials through the environment without displaying them:

```sh
python -m pip install '.[dev]'
python -m scripts.verify_club_a_live --run-live --allow-unknown-cost-diagnostics --report .oscar/live-review.json
python -m unittest discover -s tests -t . -v
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar scripts/verify_club_a_live.py
python -m scripts.check_repository
python -m oscar proof
python -m oscar grid-proof
python -m oscar reason 'reason about a small architecture tradeoff' --mode local
```

The explicit unknown-cost flag permits only bounded NVIDIA/Z.ai diagnostics; omit it to retain default no-paid discovery-only behavior for those providers. Live outcomes may change with provider/account capacity. The script distinguishes provider UNAVAILABLE operations from failed runtime assertions, retains fresh isolated diagnostic state under ignored `.oscar/`, and reports only safe metadata. Local reasoning should exit **2** and remain BLOCKED. Inspect authoritative task/evidence/files and the live report; API success alone is not objective completion.

**Repository delivery:** commit and push this verification continuation to `work`, then stop for manual review. The final pushed SHA is reported separately; no deployment or Slice 05 advancement is authorized by this checkpoint.
