# Model-assisted responsibility planning — local software candidate

Desktop and connected Android Automations offer **Propose a plan** using the
existing Executive, Model Router and signed Assistance review. This adds no
assistant, scheduler or model-provider dependency.

The owner enters a bounded goal and responsibility name, chooses private or
configured routing, and selects one Core model route plus one to fifteen action
capabilities. Private means the existing Router's configured private/local
eligibility rules. Configured routing can include cloud sources. Private does
not assert that an uncommissioned provider has been independently audited.

The first review displays the exact model prompt, selected capability contracts,
executor sessions, candidate provider endpoints/privacy labels and configured
routing policy. The prompt includes only the entered goal and selected action
descriptors. Files, memories, conversation history and ambient context are not
implicitly attached. An ineligible or unavailable configured route stays
unavailable; review construction does no network discovery or inference.

Only a valid signature creates a scoped Executive Worker and a model-only draft
goal. Existing Runtime/Policy/Grid enforcement still applies. At execution the
ModelExecutor checks the reviewed provider configurations and routing settings,
then restricts the Router to the reviewed providers. Configuration or provider
drift fails closed before provider I/O. Credentials stay in the existing pool.

The returned model task remains reported/partially verified. A separate
**Review suggested actions** command retrieves its exact result and passes it
through the same production Executive step validator used during registration.
Only selected capability contracts may appear; another model invocation is
rejected. The second review includes every normalized step and dependency,
original scoped Worker/owner, result digest, observed routing evidence, current
account generations/status, executor sessions and current policy. Completion
recomputes all this material. Changed output, source configuration, account,
owner/session, capability or policy requires another valid review or fresh
planning. Model output never grants authority.

Only the second signature calls the existing `propose_from_result`, accepts the
exact plan and binds current native owner authority. Both native controls
currently propose a one-time run. Existing per-action policy, access mode,
independent verification, cancellation and no-replay rules remain in force.
Declining either review does not enable its effects. Reusing a consumed review
or accepting the same draft twice is rejected.

The model-only draft intentionally does not become a verified responsibility:
model output is a proposal. Its reported task and the separately approved effect
goal remain distinct canonical records. Malformed/unsupported output can show
reported state while the action-review command rejects it; it is not completion.

## Local verification

`tests.test_planner_authoring` uses a real disposable loopback HTTP provider,
the production HTTP adapter, configured Router, ModelExecutor, Executive and
synthetic RSA native signatures. It observes zero HTTP calls and zero Workers
before the first signature; one reported model task before the second; and an
independently verified arithmetic effect after the second. It exercises private
source exclusion, unavailable routes, provider/routing drift before and after
approval, source/result/owner-scope changes, malformed output, escalation and
signature replay. The ordinary Executive/Assistance suite remains relevant.

Desktop tests exercise explicit capability/privacy selection and the distinct
second-review command. Android contract tests validate finite scope, privacy,
bounded draft projection and reuse of the generic signed owner review.

No hosted provider, real owner account, production secret, physical phone,
microphone or camera is used. Automated acceptance does not establish owner
visual approval, production model quality or general-purpose task reliability.

## Conversation requests

Desktop Ask and authenticated remote text submission now offer this same reviewed
planner for ordinary actionable objectives after the existing exact operation,
schedule and communication routes. The Controller still owns memory preflight
and current-evidence routes. Recognized historical/current-context requests do
not enter this planner with unreviewed memory or ambient inputs.

The initial response is an unsigned `plan_draft` proposal. Review construction
performs no inference; its signed completion creates the model-only draft. A
follow-up such as **Review the plan** or **Proceed with the plan** locates one
unaccepted draft belonging to the same relationship, owner node, exact session
and approval scope, and opens the separate action review. Those words do not
approve effects. Multiple drafts require `Review plan PLAN-ID`. Multiple devices
with the same action kind require `On device DEVICE-ID: objective`. Revoked
sessions, stale capabilities, changed contracts and consumed reviews fail closed.

Only currently scoped, implemented typed action contracts are sent as examples.
These include exact workspace file writes, arithmetic, bounded file inspection,
directory/search operations, Git operations, selected PowerShell operations,
page inspection and application/tool catalog inspection when advertised. This
path does not yet provide generic Android actions, arbitrary computer use,
connector account selection, coding-agent orchestration, registered application
launch selection or terminal program selection. A dependency orders literal
steps; it does not substitute earlier outputs into later steps. Plans cannot
invent account IDs, device IDs, retrieved facts, credentials or output bindings.
Missing information can produce a bounded clarification instead of an executable
plan. Unsupported output remains blocked.

`tests.test_conversation_planning` exercises both signatures through Desktop and
actual authenticated remote TLS/HTTP submission, a disposable loopback synthetic
model, real file effects and independent byte readback. It also checks decline,
consumed-review replay, exact-session continuity, multiple drafts/devices,
revocation, private history exclusion, missing routes, malformed model field
types, unselected capabilities and untrusted authority escalation. These fixtures
prove the integration and enforcement, not general model quality.

The [23 October local inference receipt](../evidence/software-completion/conversation-planning-2026-10-23.json)
records an actual installed `qwen3.5:4b` run through conversation, both synthetic
RSA owner signatures, the production Model Router/HTTP adapter/Executive, a real
workspace file write and independent exact-byte verification. The immutable
source campaign passed in 77.964 seconds; the planner/conversation regression
passed 19 tests. No model output was replaced with fixture steps.

This campaign explicitly configured the local Ollama server with cloud disabled
and a 16,384-token context, and used an 8,192-token output budget. The configured
model's advertised context alone does not change Ollama's runtime context.
Earlier malformed and empty model outputs were rejected without file effects;
the default 4,096-token server context truncated one later attempt. Another
earlier fixture omitted normal Core services and consequently lost capability
freshness during inference. The successful campaign ran the normal independent
execution-session heartbeat. These failed receipts remain separately recorded;
one successful objective does not establish general-purpose planning reliability.

## Structured local Executive decoding (24 October)

When the existing model configuration explicitly requires `structured` output,
native Executive model tasks carry an internal `executive_plan` marker. The local
Ollama adapter then sends a JSON Schema for exactly one `steps` array or one
`clarification`, with typed Intent fields, bounded dependency names and at most
16 steps. It uses temperature zero. The marker is internal and rejected by the
owner configuration parser. Generic structured requests still use ordinary JSON
mode; text-only routes remain text-only. Other provider adapters retain their
existing JSON modes. No arbitrary schemas, image inputs or dependencies were added.

Schema decoding is not authority or semantic verification. Executive still checks
capability pins, actual node/account/session state, topological order, typed
operations, policy and current owner authority. Ask still requires the two native
reviews, while signed synthetic Full uses its current delegation. Malformed output
is rejected; no repair, replacement output or automatic uncertain-effect retry was
introduced. Existing pending reviews bind model configuration and may need renewal
after configuration/source drift.

[The local receipt](../evidence/software-completion/planning-schema-2026-10-24.json)
records 159 passed regressions and three actual installed-Qwen runs on the final
source, with independently verified file bytes. An earlier schema-only source
failed with `structured_output_failure`; its raw failing response was not captured,
so the exact cause remains unknown. Later success does not establish a universal
model reliability fix. The trace only wraps the actual HTTP read to retain exact
synthetic request/response bytes; it never repairs or substitutes model output.
[Ollama's official contract](https://docs.ollama.com/capabilities/structured-outputs)
specifies the schema format and recommends lower temperature for deterministic
completions. No real owner account, microphone/camera or production Full activation
was used.

**2026-10-24 two-step local model acceptance:** compound Calculate/then
requests now reach the reviewed planner; simple arithmetic keeps its existing
path. Capability instructions state the existing exact arithmetic-expression
contract. Actual installed Qwen passed arithmetic → dependent verified file in
Ask (4.772 s, both signatures) and synthetic Full (4.905 s). All 71 affected
checks passed (52.335 s). The initial routing failure and rejected prose
arithmetic output remain recorded. These are literal steps with no output
substitution or broad model-reliability claim.
[Receipt](../evidence/software-completion/multistep-model-2026-10-24.json).

**2026-10-28 bounded native draft correction:** reviewed structured planning can
correct one native-invalid draft on known free/subscription/local-funded routes,
within the existing total route-attempt ceiling. The correction pins the original
provider/model, prohibits paid/unknown-cost fallback and repeats provider-contract,
context, cancellation, observation/memory and account checks. Rejected staged
connector inputs are discarded; raw rejected output is not appended to the prompt.
The same graph parser and local file-path validator are reused without executing
proposed steps. Clarification stays a question; another invalid draft fails.

All 38 final catalog cases pass (50.593s), including synthetic signed Ask/Full,
free OpenAI-format HTTP, path-alias rejection without normalization, private-input
cleanup, cancellation, source withdrawal, changed provider origin and route/context
budget denial. A preceding 180-case integration passed before the final funding
eligibility/provider-guard follow-up. A command typo produced a retained loader
error; it is not represented as a passing aggregate.

The current actual-model campaign passes six of eight cases. Granite passes five
file/arithmetic/handoff cases but Ask loses exact text and stops at effect review.
Qwen 9B Full corrects its native-invalid draft and independently verifies the task
in the requested synthetic Google account; Ask chooses the wrong account and
fails external acceptance. This is mixed model reliability, not general semantic
verification. A separate installed-runtime native Worker run passes signed TLS
file execution/readback/stop/withdrawal (9.711s). Recorded model/native source hashes
were independently matched. Whole-suite regression completed on frozen sources: 1,397 total, 1,386 passed, ten skipped and one native foreground failure (1,116.212s). All manifest source hashes independently match. The older visual fixture HWND was not foreground at its assertion; cause remains unproven. No guard was relaxed.
[Correction evidence](../evidence/software-completion/draft-correction-2026-10-28.json).


**2026-10-28 explicit planning constraints:** conversation catalogs now honor
JSON-quoted Google/Microsoft account-alias clauses through the existing account
registry. Only named providers/aliases are offered for connector work; native
capabilities remain available. Exact alias case, service availability and duplicate
alias ambiguity remain enforced. Effect admission rechecks the account choice.
Multiple named accounts are supported without assigning semantic roles to steps.
Quoted goal data does not become an account selector. Existing exact-file-text
validation also runs before draft persistence so altered text can trigger the
bounded correction path.

All 179 affected integration cases pass (234.420s), including wrong-account draft
correction before provider effects and canonical selected-account verification.
Final installed-model acceptance passes 8/8: Qwen 9B Ask/Full selected synthetic
Google task creation plus independent saved-resource GET, and Granite Ask/Full
file, arithmetic and value-handoff workflows. Qwen Ask rejects an initial draft
and corrects it within the route budget. The Ask harness was updated to assert
that the narrowed catalog contains exactly the selected account; its obsolete
large-catalog assertion failure is retained. A fresh installed-runtime TLS native
Worker check passes (8.979s). All model/native source hashes independently match.
Ruff, 290-file formatting and 107-file mypy pass. The preceding full regression
predates this follow-up and remains a failed aggregate (1,386 pass, ten skip,
one native foreground failure); no new full PASS or general model reliability
is claimed. Resource/field/operation semantics, arbitrary account wording and
multi-account step roles remain partial. No real account or activation occurred.
[Evidence](../evidence/software-completion/explicit-goals-2026-10-28.json).


## 2026-10-28 cross-service preflight and native input checks

Initial live-read planning now explains its current stage before the larger goal;
clarification concerns missing reader inputs rather than future effects or facts
that can be retrieved. Deferred operation names remain informational; the decoder
and native admission still accept only selected readers in preflight.

Microsoft task creation advertises nested `body.contentType` / `body.content`
and `dueDateTime.dateTime` / `dueDateTime.timeZone` fields. Malformed objects,
unsupported note types and empty date values are rejected before staging/effects;
no date means omit the field. Additional provider fields keep generic partial
verification. Action-review discovery excludes automatically allowed readers but
still exposes a reader when explicit Personal Policy requires confirmation.

All 88 final focused tests pass (133.902s), including same-route malformed-body
correction before any provider effect, extended-field partial outcomes and
policy-aware read review. The earlier 185-case pass predates the final two guards.
Final installed Qwen Ask/Full cross-service trials both fail the owner objective:
Ask selected Google creation with an unsupported status; Full verified a Google
creation instead of the requested Microsoft destination. Independent substep
verification does not establish owner-goal correctness. Earlier intermediate Ask
success and every failed trial remain recorded. Broader account/operation/resource
roles and field semantics remain active software gaps. No real account or owner
activation occurred. Frozen full Python regression has 1,400 PASS, ten SKIP and one native foreground FAIL (1,411 total, 1,080.220s); all source hashes independently match. The fixture expected PID 12804 but observed foreground PID 10072; cause remains unresolved and the guard stays enforced. The newest-source restart soak passes 98 signed effects and independent readbacks in 603.74s. Neither closes the failed general cross-service owner objective.
[Evidence](../evidence/software-completion/cross-service-preflight-2026-10-28.json).
