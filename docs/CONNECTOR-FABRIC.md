# Native Connector Fabric

**2026-10-20 local candidate:** [Group 5 C1/C2](development/GROUP-05-CAPABILITY-IDENTITY.md)
adds stable operational/account identities, PKCE/OIDC native-vault brokerage,
account/generation/audience checks and actual official MCP SDK stdio/Streamable
HTTP sessions. [Authentication details](development/GROUP-05-AUTH.md) and
[MCP lifecycle](development/GROUP-05-MCP.md) distinguish synthetic acceptance
from live provider commissioning. The older injected MCP boundary remains a
compatibility adapter; it is not the new session manager. Existing Grid,
Personal Policy, Runtime and Executive remain authoritative. New account-bound
callers must not use the legacy unbound connector compatibility path.

**Current delivery, 2026-10-18:** [verified checklist](CURRENT-STATUS.md), [Group 5 C2 plugin/MCP plan](DELIVERY-PLAN.md). The Connector Fabric, manifests, bounded HTTP/MCP adapters and a narrow owner-verified GitHub OAuth/federation path are **software foundations**, not a deployable general plugin marketplace/client. Real provider/MCP commissioning, easy discovery/install and independent verification remain active capability work after Group 4 authenticated Grid.

OSCAR prefers official structured authenticated APIs, then official connectors,
reviewed MCP sessions, authorized app automation and computer-use fallback.
`ConnectorFabric` is a capability source for the existing Grid catalog, not another
registry competing with it. Controller selects a capability class; provider manifests
contain service facts. Existing Dispatcher target authorization, action correlation,
idempotency, Runtime and independent Evidence/Verification remain authoritative.

## Shared authentication target architecture

GitHub OAuth is only the **first accepted real Gate B authentication proof**.
Owner run `oauth-gate-b-20261004-234817` passed authorization, private reads, restart,
controlled federation and local disconnect; remote revocation remains unknown.
It is not a design for independent OAuth implementations in every plugin.

```text
OSCAR Auth Broker
├── OAuth2 / PKCE
├── Device Flow
├── API Key
├── MCP/session auth
├── refresh / expiry
├── incremental scope upgrades
├── disconnect / revocation state
├── native/server vault abstraction
└── opaque CredentialRef

Reusable provider adapters
├── Google Auth    -> Gmail / Calendar / Drive / Contacts
├── Microsoft Auth -> Outlook / Calendar / OneDrive / Teams
└── GitHub Auth    -> GitHub capabilities
```

Plugins/connectors primarily declare provider, auth type/profile, required scopes,
capabilities, risk and verification/readback. The broker and reusable provider
adapters own enrollment/lifecycle and scope upgrades. Start with the minimum
scopes for the current objective; do not request every future permission during
first authorization. A later upgrade needs owner consent, explicit scope tracking
and permission rechecks; provider consent is not an OSCAR permission grant.

Connectors carry opaque CredentialRef values. Plugins must not receive raw tokens
when an opaque reference suffices. Only trusted broker/provider transport code may
resolve a secret transiently for authenticated protocol I/O. Never place raw tokens
in manifests, task state, logs or SQLite. Reuse provider code across capabilities
while retaining explicit provider/account/tenant/audience/scope identity; one
credential cannot silently authorize another account or provider service.
Native Windows and future server vaults sit behind a replaceable store boundary.

Local credential deletion and remote revocation confirmation remain separate.
Refresh/expiry/revoke support is provider-specific; unsupported remote revocation
stays UNKNOWN/PENDING owner action. The current GitHub registered-client flow
cannot confirm provider revocation without the required provider credentials.

This is target architecture, not a new broker implementation. Existing CredentialRef,
SecretResolver, AuthSession/PKCE, GitHub device enrollment, native vault and durable
recovery are implemented foundations. Broad Google/Microsoft provider enrollment,
server vault deployment, generalized incremental upgrades and every auth profile
are not accepted. Full Auth Broker expansion is later work, not an added Gate B
requirement. Existing trusted HTTP transport resolves raw bytes for requests; this
does not mean an arbitrary plugin is allowed to inspect the native vault.

## Implemented boundary

- Typed manifests, instances, capabilities, auth type, opaque CredentialRef,
  connection state, risk, result and event envelopes.
- Bounded HTTPS JSON/media adapter, TLS verification and no redirects; no automatic
  mutation retry. Resource path segments are encoded; query keys are allowlisted.
- Read, write, destructive, financial, security and external-communication scopes
  remain distinct. Capabilities declare additive consequences; all required grants
  and operation/consequence Personal Policy checks must pass. Writes still require
  explicit confirmation. A deny on `connectors:external-communication` blocks any
  action requiring that consequence, even with a write/destructive grant.
- Environment secret resolver is a platform-supplied reference boundary, not a
  vault. OAuth refresh/revoke and authenticated MCP session are adapter protocols.
  PKCE S256 generation is implemented. GitHub registered-client device enrollment
  and Windows Credential Manager are implemented; native credential lifecycle is exercised.
  Real owner GitHub authorization/private reads/restart/disconnect are accepted.
  This adapter does not implement refresh; acceptance used non-expiring grants.
  Local disconnect does not revoke remotely: UNKNOWN_OWNER_ACTION_REQUIRED.
- Provider results remain REPORTED. `ConnectorVerifier` independently fetches a
  correlated resource and compares explicit expected fields before verification.
  The explicit communication request path verifies Gmail draft/sent saved-resource
  recipients, subject and plain body through an independent raw-message GET;
  sent mail also requires the SENT label. This is saved-resource verification,
  not recipient delivery. Microsoft draft and Google/Microsoft calendar creation
  have corresponding independent resource checks. Microsoft sendMail's empty
  202 response and arbitrary nested/batch-update verification remain PARTIAL.
  See [communication integration](development/SOFTWARE-COMMUNICATION-INTEGRATION.md).
- Private bodies/results stay in bounded task-scoped transient context. `stage`
  returns an opaque input reference for durable Actions; process restart expires
  that input and BLOCKS execution. Metadata-only receipt/ledger records retain
  evidence IDs/time and policy decision. Runtime binds staged references to tasks;
  execution requires an explicit `request_owners` binding to the current task.
  Unbound or other-task references are rejected without consumption; direct executor
  clients must call `bind_task` first. Dispatch consumes owned input before execution,
  including failure/cancellation. The
  verifier releases outcomes in `finally`, after inspecting them. Committed local task
  transitions notify weakly held transient owners: completion, failure, blocked
  execution and cancellation immediately release remaining task context. Admission
  also reaps context of tasks completed by another Store/process, and the active
  Runtime runner rechecks resource ownership on exit to cover cross-process
  cancellation racing with result creation; the
  100-active-item bound is unchanged. Unbound staging is not a task: clients that stage
  without creating one must release that unused reference. Restart drops private
  outcomes too; a durable REPORTED result cannot recreate independent readback proof.
- Event authentication is supplied by the provider/platform boundary. Ingestion
  deduplicates authenticated IDs and keeps metadata only. Polling/incremental cursor
  and webhook interfaces do not claim deployed provider push subscriptions or
  signature verification. Retrieval does not authorize durable retention.

## Concrete adapters

`config/google-connectors.json` contains 39 selected capabilities: 35 official-discovery-backed
capabilities across Gmail (search/read/threads/drafts/send/labels/history), Calendar
(events list/get/create/patch/delete/freebusy), Drive (search/metadata/media/export/
metadata create/patch), Classroom (courses/coursework/submissions/announcements),
Docs (get/create/batchUpdate), Sheets (metadata/ranges get/update/create), and Slides
(get/create/batchUpdate), plus four Google Tasks REST capabilities (list discovery,
task list/get/create, checked 2026-10-24). Bodies are bounded JSON objects; provider validation still
owns full API schemas. Pagination is explicit, caller-driven; a page is not a
complete inbox or course inventory. Drive create/patch currently covers metadata,
not media uploads. Google proprietary documents require explicit MIME export.

Thin Microsoft Graph (mail/calendar/To Do/OneDrive/Teams/SharePoint), GitHub (repository/
issues/PRs/commits/Actions/status), Slack (channels/history/search/post), and Notion
(search/pages/blocks/databases/data sources) use the same HTTP adapter. Scope
requirements are deliberately explicit, not inferred from token presence. GitHub
fine-grained/App installation permissions and Notion integration access remain
provider-side checks; HTTP denial does not diagnose global account health.

MCP maps only owner-reviewed tools into manifests; untrusted annotations cannot
lower risk or grant scope. Current stdio/Streamable HTTP execution uses the installed
SDK and reviewed lifecycle/resource authorization. Actual synthetic SDK and resource
OAuth checks are recorded in [MCP authorization](development/SOFTWARE-MCP-AUTHORIZATION.md);
that is local software acceptance, not a commissioned external provider.

Google Tasks and Microsoft To Do list/create requests reuse native conversation,
exact signed review, account-generation fences and independent saved-resource GET.
The [task integration contract](development/SOFTWARE-COMMUNICATION-INTEGRATION.md)
records exact forms, date semantics and literal OAuth scopes. Existing account
scope ceilings do not expand automatically. Synthetic task HTTP/Cloud integration
passed; real provider accounts and reminder delivery remain uncommissioned.

**Broader live Google/Microsoft/Slack/Notion/MCP account integration: NOT ACCEPTED.** Fixture testing does not establish live private provider access. The separate narrow owner-authorized **GitHub device OAuth/private-read** flow *was* verified for Gate B, with scope `user:email`; it does not imply a deployed general GitHub MCP service, write access, complete Auth Broker or remote provider revocation.

## Official research provenance

Retrieved on **2026-10-03 IST** using TLS through the configured cloud proxy.
Google Discovery returned HTTP 200; selected endpoint methods/paths/scopes were
checked against those current documents. No giant documentation snapshots persist.

- [Gmail Discovery](https://gmail.googleapis.com/$discovery/rest?version=v1)
- [Calendar Discovery](https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest)
- [Drive Discovery](https://www.googleapis.com/discovery/v1/apis/drive/v3/rest)
- [Classroom Discovery](https://classroom.googleapis.com/$discovery/rest?version=v1)
- [Docs Discovery](https://docs.googleapis.com/$discovery/rest?version=v1)
- [Sheets Discovery](https://sheets.googleapis.com/$discovery/rest?version=v4)
- [Slides Discovery](https://slides.googleapis.com/$discovery/rest?version=v1)
- [Google installed-app OAuth/PKCE](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google limited-input device OAuth](https://developers.google.com/identity/protocols/oauth2/limited-input-device)
- [Graph v1.0](https://learn.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0)
- [GitHub repository API](https://docs.github.com/en/rest/repos/repos#get-a-repository)
- [Slack postMessage](https://docs.slack.dev/reference/methods/chat.postMessage)
- [Notion versioning](https://developers.notion.com/reference/versioning)
- [MCP tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [PKCE RFC 7636](https://www.rfc-editor.org/rfc/rfc7636)
- [Device authorization RFC 8628](https://www.rfc-editor.org/rfc/rfc8628)

Notion requires its version header; current documentation shows `2026-03-11`,
selected explicitly. Device grants are not generally interchangeable with desktop
OAuth and their supported scopes are provider-limited. The reference implements
contracts only; it does not pretend to have completed either enrollment flow.

## Additional current-source checks and acceptance

Current method documentation was also retrieved with HTTP 200 for Graph
[mail listing](https://learn.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0),
[sendMail](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0),
[joined Teams](https://learn.microsoft.com/en-us/graph/api/user-list-joinedteams?view=graph-rest-1.0),
[site search](https://learn.microsoft.com/en-us/graph/api/site-search?view=graph-rest-1.0),
Slack [history](https://docs.slack.dev/reference/methods/conversations.history) and
[search](https://docs.slack.dev/reference/methods/search.messages), Notion
[data-source query](https://developers.notion.com/reference/query-a-data-source)
and [page creation](https://developers.notion.com/reference/post-page), and
[MCP 2025-11-25 tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
Slack search requires a user token; public-channel history does not imply private
channels/DM access. Graph `/me` requires delegated identity, not an App-only token.
MCP `isError`/tool annotations remain testimony, never self-granted permission.

The first guessed GitHub versioning-document URL returned an HTTP error. The
successfully retrieved official repository reference explicitly supplies
`latestApiVersion: 2026-03-10` and lists the older `2022-11-28` as another supported
version. The adapter now explicitly selects **2026-03-10** based on that source.
This corrects the initially selected older version, preserving the initial public
read as a dated older-version observation rather than silently relabeling it.

`tests.test_connector_http` routes the actual bounded adapter to an explicitly
synthetic loopback HTTP service for all 35 Google methods, including media/export
and redirect refusal. This verifies local HTTP/contract behavior, not Google
account access. `scripts.verify_connector_public --run-public` performs only a
real unauthenticated public GitHub response-contract check with source/time/ID.

The [2026-10-23 reviewed resource-authorization candidate](development/SOFTWARE-MCP-AUTHORIZATION.md)
adds native Connections consent for administered MCP resources. Its distinct
`resource-grant` identity class records resource access without asserting a
verified provider person. Explicit signed refresh, exact resource audience,
generation fencing and local credential-deletion readback remain separate from
tool action authority and unknown provider-side revocation. Synthetic HTTP/SDK
acceptance does not commission a real provider account.

MCP has an SDK session HTTP-interface adapter through Fabric permission/policy
checks. Session readiness must be supplied by trusted composition. Destructive
MCP tool calls require both reviewed risk scope and confirmation even if the server
claims a read-only annotation. No live MCP service has been authenticated/tested.
Read-back also requires explicitly granted OSCAR read permission and the same
connector instance/account; a write grant cannot borrow read access for verification.

## PR #10 pre-merge corrections

Readback is selected from the **executed mutation's installed manifest**, not the
objective. Legacy `read_capability` may only agree with that declaration; omission
is preferred. Verification checks the original Result identity/correlation/executor,
the exact installed instance/account, granted read scope and read policy, original
parent/resource path and mutation response ID, then an independent GET and expected
fields. A manifest without declared GET readback remains PARTIAL. A verification
attempt consumes its transient outcome; repeated attempts cannot reuse private data.

Composite review of current mutations:

| Mutation | Required consequences |
| --- | --- |
| Google Calendar create | write; communication if attendees or `sendUpdates` other than `none` |
| Google Calendar update/delete | write/destructive + communication conservatively, including `none` |
| Microsoft calendar create | write; communication when attendees are supplied |
| Gmail send / Microsoft mail send / Slack post | write + communication |
| GitHub issue creation | write + communication (publishing/notifications) |
| Gmail draft; Drive metadata; Docs/Sheets/Slides; Notion pages | write; no explicit outbound notification option in the current admitted contract |
| MCP | owner-reviewed primary risk plus optional additive consequences; server annotations confer no authority |

Grid advertises the maximum permission set for conditional capabilities because it
authenticates the caller before private input resolution. The Fabric then evaluates
the parameter-specific consequences. This deliberately requires a communication-capable
Grid session even for a calendar-create action that ends up having only a write effect.
A capability-specific allow never overrides a consequence-specific deny.

Official sources retrieved over TLS on 2026-10-03 UTC: Google Calendar
[insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert),
[update](https://developers.google.com/workspace/calendar/api/v3/reference/events/update),
[delete](https://developers.google.com/workspace/calendar/api/v3/reference/events/delete),
and Microsoft [create event](https://learn.microsoft.com/en-us/graph/api/user-post-events?view=graph-rest-1.0).
Google warns some emails may still be sent with notifications suppressed; update/delete
can affect pre-existing attendees unknown to the request. Microsoft attendee invitations
cannot be disabled. These are reference contract tests, not live private-account tests.

## Gate B local completion candidate — 2026-10-04

`python -m oscar.oauth_cli --state <local.sqlite> --owner-authorized --begin <registered-client-id>` starts only the official GitHub device flow. One `--poll <transaction-id>` reads its nonce from stdin; no polling loop or token output. Tokens/device credentials live in OSCAR-owned native Credential Manager references. Interrupted exchange is ambiguous and blocked rather than replayed. A registered client was used in the owner acceptance run; no client secret was needed. Provider revocation needs the legitimate provider settings/app boundary; local disconnect is explicitly pending remote revocation. No CLI/browser tokens are borrowed. Verified acceptance includes native Windows/Codex work, typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j, local embedding/reranking, memory evaluation and owner-reviewed policy candidates. The owner completed physical machine acceptance and registered GitHub device OAuth with exactly `user:email`, real private reads, new-process restart, controlled private/public federation and local credential deletion/absence checks. Slice 05 and Slice 06 are COMPLETE for the documented local-alpha scope; Gate B is PASS. Remote provider revocation remains `UNKNOWN_OWNER_ACTION_REQUIRED`; private writes were not authorized and are optional. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).


The owner's final physical/manual machine acceptance PASSED in run
`manual-gate-b-20261004-200734`; desktop/local/public browser phases are VERIFIED.
The [accepted GitHub OAuth/federation path](GATE-B-OAUTH-ACCEPTANCE.md) uses
the existing native vault, opaque references and Connector Fabric; private email
addresses remain transient. The controlled synthetic past count remains RECALLED;
current provider count facts remain REPORTED, with separate source/temporal provenance.
Owner run `oauth-gate-b-20261004-234817` passed real private OAuth and controlled
federation. Slice 06 COMPLETE; Gate B PASS. Remote revocation remains
`UNKNOWN_OWNER_ACTION_REQUIRED`. See [final acceptance](GATE-B-COMPLETION.md).


## Model-authored MCP execution

Installed, connected, owner-reviewed account-bound MCP tools can participate in
conversation-created temporary Workers. Planning descriptors expose the exact
executor/capability/account identity and the reviewed argument schema. Tool names
and schemas are untrusted metadata, not instructions or additional authority.
The configured model proposes literal `parameters.arguments` only. Native schema,
capability, account generation, session, policy and standing-authority checks remain
authoritative. A changed tool schema needs installation review before new planning.

Before the model result is persisted, arguments move into the existing transient
Connector Fabric. Durable results, goals and actions contain opaque `request_ref`
values, fixed server-authored account criteria and provenance. Request guards bind
the input digest and current connector contract through dispatch/cancellation.
Inputs expire after 120 seconds and are consumed before RPC. Core restart loses
them; a new draft is required. A later invalid step releases preceding staged
arguments. The existing 100-input Fabric bound remains enforced.

Ask displays the exact arguments in a signed plan review. That review payload is
held transiently for its 30-second lifetime; only its digest is durable. Ordinary
consequential-action confirmation remains required by policy after plan acceptance.
Desktop and Android expose a pending action through `confirm_task` in the existing
signed native review. It shows the current private arguments, account and executor;
the signed completion rechecks input digest, schema/account generation, task/policy
digest, expiry and current owner scope before recording the existing one-attempt
Executive confirmation. Pending readback contains IDs only. Standing-delegation
tasks cannot fall back to this Ask path when their account coverage is missing.
Synthetic Full Access uses the existing signed owner/account/capability ceiling
without per-action prompts. Neither mode adds an account, installs a server,
refreshes authorization or bypasses external mandatory approval.

Connector plans run once immediately. Recurrence, delayed execution, argument
substitution from other steps and MCP observation continuation are rejected.
Generic tool success is REPORTED/PARTIALLY_VERIFIED, never independent objective
verification. Core integration, native contract tests and builds do not establish
rendered native MCP action-confirmation acceptance or general model accuracy.
