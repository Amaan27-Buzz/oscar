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
