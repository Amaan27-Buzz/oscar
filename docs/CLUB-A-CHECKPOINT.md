# Club A — Brain checkpoint

Recorded **2026-10-02**. Overall status: **PARTIAL**. Gate A has not passed. **Slice 05 is not started.**

## Slice evidence

| Slice | Status in this checkpoint | Evidence / limit |
|---|---|---|
| 01 — Core Loop | VERIFIED for implemented foundation | Real exact-file objective → HTTP execution → REPORTED result → independent read → VERIFIED evidence/task/artifact. Fake executor → missing file → FAILED. SQLite restart, cancellation, retry budgets, scope and deduplication tested. |
| 02 — TypeSafe Jev | VERIFIED for implemented foundation | All nine routes are typed; arithmetic/file intents avoid a model. Live-source, memory, specialist and Worker intents block without advertised capabilities. Conservative routing grammar, not general language understanding. |
| 03 — Transport / Catalog / Grid | PARTIAL | Real authenticated loopback HTTP, scope rechecks, replay rejection, correlated result/control/progress, node state, availability, disconnect/reconnect and durable lease expiry verified. Shared-store reference nodes; no public TLS/outbound rendezvous or physical embodiments verified. |
| 04 — Adaptive Model Router | PARTIAL / hosted integration BLOCKED | Ten modes, capability/quality/context filters, credential pools, task fit, scarcity, bounded fallback, decaying observations, history and native HTTP adapter contracts tested. All real hosted attempts were denied by environment policy. |

These statuses describe the implemented Club A scope. They are not acceptance of later architecture or a completed Gate A.

## Architecture and changed modules

There are no Latch/SwitchRoute runtime dependencies and no Kafka/Redis/Kubernetes stack. Python 3.12 and SQLite provide the native foundation without third-party runtime dependencies.

| Responsibility | Files |
|---|---|
| Typed domain / wire / epistemic states | [contracts.py](../oscar/contracts.py) |
| Durable task, ledger, replay and idempotency authority | [storage.py](../oscar/storage.py) |
| Objective planning, execution lifecycle and verification handoff | [runtime.py](../oscar/runtime.py) |
| Deterministic scoped executors and independent verifier | [capabilities.py](../oscar/capabilities.py) |
| Fast typed path decisions | [jev.py](../oscar/jev.py) |
| Node identity, pairing/scope, health, availability, leases and revocation | [grid.py](../oscar/grid.py) |
| Target-side dispatch and real loopback HTTP reference transport/control | [transport.py](../oscar/transport.py) |
| Model/task/policy contracts and replaceable metadata | [models.py](../oscar/models.py), [registry.py](../oscar/registry.py), [development-models.json](../config/development-models.json), [local-template.json](../config/local-template.json) |
| Opaque credential material and independent slot metadata | [credentials.py](../oscar/credentials.py) |
| Adaptive mode ranking, reservation, fallback and content-free history | [router.py](../oscar/router.py) |
| Native OpenAI-compatible, Google and Ollama adapters / redirect security | [providers.py](../oscar/providers.py), [http_client.py](../oscar/http_client.py) |
| Composition and manual developer commands | [harness.py](../oscar/harness.py), [cli.py](../oscar/cli.py), [pyproject.toml](../pyproject.toml) |
| Contract/failure/real-loopback verification and CI | [tests](../tests/), [repository checker](../scripts/check_repository.py), [Brain checks](../.github/workflows/brain-checks.yml) |

README, ROADMAP, BUILD-GATES, MODEL-ROUTING, NATIVE-INFRASTRUCTURE, ADR-059, DEVELOPMENT and CHANGELOG now describe this checkpoint.

## Automated results

**113 tests passed**, covering all 28 requested matrix cases. Ruff lint/format checks and strict mypy checks pass. Offline repository required-file, local Markdown-link, removed-reference and secret-safety checks pass. External link checking and GitHub Actions were not run here.

| Matrix cases | Proof |
|---|---|
| 1–4 | Exact-file core flow; mandatory missing-file fake-success rejection; deterministic addition; all typed Jev classes/routes. |
| 5–8 | Value-silent credential presence; 17 independent masked slots; invalid/rate-limited key failover; bounded cross-provider reranking. |
| 9–17 | Explainable Auto; Free First capability/quality floor and scarcity preservation; hard-task escalation; Fast/Balanced/Heavy; Local/Private restrictions; Manual pins and Specialist affinity. |
| 18–20 | Unknown/stale quota and unknown price retain uncertainty; replaceable six-model Ollama metadata; history contains route/timing/fallback but no prompt/response/key material. |
| 21–24 | Reference advertisement, durable objective/task across disconnect/restart, dead lease expiry, blocked/reclaimable state instead of false Working/Done. |
| 25–28 | Provider/executor success stays REPORTED; model objectives without a verifier are partial; independent outcome learning is separate; interrupted streaming never splices; cooperative cancellation and authenticated HTTP cancel; idempotency/replay/crash ambiguity guards; concurrent runners and stale leases cannot alter newer ownership. |

The provider contract tests execute actual HTTP requests against explicitly synthetic loopback servers for all three adapter protocols, structured output, SSE/NDJSON, 401/429/503, policy denial, redirects and malformed/empty 200 responses. End-to-end router HTTP tests prove credential failover and cross-provider fallback. These are **fault-injection/reference proofs, not hosted-provider integrations**.

## Real hosted operations

All **17 expected credential variables were present** in the safe presence check. Presence does not prove validity, account capacity or provider access. Credential values, lengths, prefixes, suffixes and hashes were never printed.

The [safe hosted evidence record](evidence/club-a-hosted-2026-10-02.json) records these actual attempts:

| Provider | Operation / configured model attempted | Masked slot | Required HTTPS hostname | Outcome |
|---|---|---|---|---|
| GroqCloud | Generation POST; `llama-3.1-8b-instant` | `groq-1` | `api.groq.com` | BLOCKED |
| OpenRouter | Generation POST; `meta-llama/llama-3.3-70b-instruct:free` | `openrouter-1` | `openrouter.ai` | BLOCKED |
| Google AI Studio | Generation POST; `gemini-2.5-flash-lite` | `google-1` | `generativelanguage.googleapis.com` | BLOCKED |
| Ollama Cloud | Generation POST; `gemma3:31b` | `ollama-cloud-1` | `ollama.com` | BLOCKED |
| NVIDIA NIM | Read-only model inventory GET; no generation/model called | `nvidia-1` | `integrate.api.nvidia.com` | BLOCKED |
| Z.ai | Read-only model inventory GET; no generation/model called | `zai-1` | `api.z.ai` | BLOCKED |

**No hosted model was successfully called. No provider HTTP success, live credential failover or live quota/quality adaptation is verified.** The proxy denied access before a provider response. NVIDIA/Z.ai generation was also excluded because its funding/price was unknown under the default no-paid policy. The relevant discovery denial was rechecked after correcting discovery error classification.

Required environment change: allow HTTPS egress to the six listed hostnames through the supported environment configuration workflow, preserving inherited proxy/CA/TLS settings. Credential readiness should then be rechecked. No network controls were bypassed or changed.

## Routing and fallback observations

Observed in explicit synthetic contract fixtures:

- Auto / Free First extraction selected `plentiful / small / plentiful-1`: required capability and quality tier 2 satisfied, known remaining requests 1000, low fixture latency; the stronger route had only 2 remaining requests.
- A difficult reasoning task requiring quality tier 4 selected `scarce / strong / scarce-1`; the small tier-2 model was ineligible. Heavy Duty selected the strongest eligible tier; Specialist prioritized task affinity.
- An invalid or rate-limited `plentiful-1` failed over to `plentiful-2`. A provider failure reranked to `scarce / strong`; retries were bounded. The same provider/slot policy and actual HTTP adapters were also exercised against the reference servers.
- Unknown quota remained null. Old balances became unknown after reset/staleness or successful consumption without a fresh header. Unknown monetary cost was not treated as free. Known paid fallback cost budgets were cumulative.
- Manual pins, Local/Private restrictions and cancellation remained authoritative during fallback. Interrupted meaningful streaming failed with provenance instead of appending another provider.

No synthetic remaining balances or latency figures above describe the real hosted accounts.

## Manual proofs actually run

1. `python -m oscar --state .oscar/final-proof.sqlite proof` passed. A real loopback node wrote exact bytes. The verifier read them independently; the resulting artifact was also inspected directly from the filesystem. Result status remained REPORTED while evidence/task/artifact became VERIFIED. Artifact promotion is bound to the exact inspected resource; unrelated reported artifacts cannot inherit objective verification.
2. The same command invoked a deliberate fake executor for a unique absent path. Its success claim stayed REPORTED; independent evidence reported the missing file and task state became FAILED.
3. Deterministic `2 + 2` became VERIFIED using a separate decimal-column calculation; no model route history was created for it.
4. `python -m oscar --state .oscar/final-grid.sqlite grid-proof` observed real-time lease expiry after disconnect. The objective remained present, the lease became inactive, and the task stayed BLOCKED. Reconnect/readvertisement/reclaim are separately covered by contract tests.
5. `python -m oscar --state .oscar/final-local.sqlite reason 'reason about this architecture' --mode local` returned expected exit code 2 and BLOCKED / `route_unavailable`; it made no hosted fallback.
6. `live-providers` attempted the operations listed above using environment credentials and saved categorical blocked results. Runtime SQLite/report artifacts were also scanned against credential material without printing it.

These traces are retained locally under ignored `.oscar/`. Reference Grid roles do not establish the presence of a real phone, laptop or Edge device.

## Secret safety and repository state

- No `.env` was read or written by the runtime; the existing ignored file was left alone.
- Provider material is held only in the opaque environment-backed pool. Slot persistence/route history contain metadata and masked IDs. Session handles are non-serializable; authentication token digests are stored only for generated Grid sessions, not provider keys.
- Provider error bodies and exception diagnostics are excluded from persistent errors. Redirects are rejected. Response/stream secret redaction includes keys spanning chunks.
- Actual credential material and common secret-like patterns were checked in tracked/non-ignored source and documentation. Ignored proof/report/SQLite files were separately scanned. No credential material was found in those artifacts.
- Work is local on branch `work`. No commit or push was made; GitHub/main was not changed.

## Limits and technical debt

- Public coordinator deployment, encrypted Internet transport, outbound private-node rendezvous, independent network-node state replication and a production pairing UX remain unverified/unimplemented. The HTTP reference target shares SQLite with the coordinator and is loopback-only.
- The POSIX file verifier proves exact bytes, not every possible objective. Unsupported verifiers remain partial/unknown. No automatic compensation/undo is advertised for overwritten files.
- Jev uses a conservative grammar; typed callers supply model task class and quality floor. Initial model quality/context/funding metadata needs live calibration and benchmarks. No hosted result establishes task quality yet.
- Scarcity is a small confirmed-request-quota heuristic, not complete credit/reset/usage-velocity forecasting. Telemetry/session/nonce retention and large-history indexing require later work.
- Cancellation is cooperative and cannot undo committed effects. Blocking provider I/O may complete a bounded read before noticing cancellation. Reference cancellation acknowledgements are REPORTED. Crash-ambiguous actions require explicit inspection/reconciliation before replay. Retry/reconnect scheduling is exposed as bounded foundations, not an autonomous distributed scheduler.
- Local Ollama/LM Studio/vLLM interfaces are configured only by explicit manifests and disabled in the template. The user's laptop/LAN, Windows runtime, ESP32/Pico, Wake-on-LAN and actual Sunday mobile runtime are unavailable here and remain UNVERIFIED.
- Coding Workers, memory, communication, hardware safety implementations, UI and ChatGPT product-surface connectors were not started in Club A.

## Exact Gate A review commands

Run from the repository root; provision credentials through the environment without displaying them:

```sh
python -m pip install '.[dev]'
python -m ruff check oscar tests scripts
python -m ruff format --check oscar tests scripts
python -m mypy oscar
python -m unittest discover -s tests -t . -v
python -m scripts.check_repository
python -m oscar proof
python -m oscar grid-proof
python -m oscar ask 'what is 2 + 2?'
python -m oscar write --path gate-a/review.txt --content 'Gate A exact bytes' --http-reference
python -m oscar reason 'reason about this architecture' --mode local
python -m oscar credentials
python -m oscar routes --mode auto
python -m oscar routes --mode fast
python -m oscar routes --mode balanced
python -m oscar routes --mode heavy --quality 4
python -m oscar routes --mode free_first
python -m oscar routes --mode manual --provider groq --model llama-3.1-8b-instant --slot groq-1
python -m oscar history
```

The Local reasoning command should exit **2** with BLOCKED, and never call cloud. Inspect the `proof`/`grid-proof` output and authoritative files/SQLite records, not just command exit codes. Use `python -m oscar inspect TASK_ID`, `cancel TASK_ID`, and `resume TASK_ID` with IDs returned by the commands; completed/ambiguous tasks must not replay consequential work.

After the egress policy permits the hostnames and current model/funding metadata is reviewed:

```sh
python -m oscar --state .oscar/live-review.sqlite live-providers --report .oscar/live-review.json
python -m oscar --state .oscar/live-review.sqlite history
python -m oscar reason 'reason about a small architecture tradeoff' --mode free_first --quality 2
```

Use a fresh diagnostic state path for a new live review so a prior temporary circuit does not obscure the test. The live harness independently compares a sentinel response; even a match verifies only the generation contract. General reasoning objectives remain partially verified without an independent objective check. Real credential/provider failover must be exercised only through an explicitly authorized scenario; do not exhaust accounts to manufacture rate limits. A public coordinator deployment still needs its own configured-target acceptance scenario before Gate A can pass.
