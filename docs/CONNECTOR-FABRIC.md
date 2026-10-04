# Native Connector Fabric

OSCAR prefers official structured authenticated APIs, then official connectors,
reviewed MCP sessions, authorized app automation and computer-use fallback.
`ConnectorFabric` is a capability source for the existing Grid catalog, not another
registry competing with it. Controller selects a capability class; provider manifests
contain service facts. Existing Dispatcher target authorization, action correlation,
idempotency, Runtime and independent Evidence/Verification remain authoritative.

## Shared authentication target architecture

GitHub OAuth is only the **first intended real Gate B authentication proof**.
Owner authorization has NOT STARTED, and private acceptance remains unverified.
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
  Real owner OAuth authorization/private reads/provider revocation remain unverified.
  GitHub OAuth App device grants do not support refresh; local disconnect does not revoke remotely.
- Provider results remain REPORTED. `ConnectorVerifier` independently fetches a
  correlated resource and compares explicit expected fields before verification.
  Gmail sent-recipient/header verification and arbitrary nested/batch-update
  verification remain unimplemented; they must stay PARTIAL.
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

`config/google-connectors.json` contains 35 selected official-discovery-backed
capabilities across Gmail (search/read/threads/drafts/send/labels/history), Calendar
(events list/get/create/patch/delete/freebusy), Drive (search/metadata/media/export/
metadata create/patch), Classroom (courses/coursework/submissions/announcements),
Docs (get/create/batchUpdate), Sheets (metadata/ranges get/update/create), and Slides
(get/create/batchUpdate). Bodies are bounded JSON objects; provider validation still
owns full API schemas. Pagination is explicit, caller-driven; a page is not a
complete inbox or course inventory. Drive create/patch currently covers metadata,
not media uploads. Google proprietary documents require explicit MIME export.

Thin Microsoft Graph (mail/calendar/OneDrive/Teams/SharePoint), GitHub (repository/
issues/PRs/commits/Actions/status), Slack (channels/history/search/post), and Notion
(search/pages/blocks/databases/data sources) use the same HTTP adapter. Scope
requirements are deliberately explicit, not inferred from token presence. GitHub
fine-grained/App installation permissions and Notion integration access remain
provider-side checks; HTTP denial does not diagnose global account health.

MCP maps only owner-reviewed tools into manifests; untrusted annotations cannot
lower risk or grant scope. An authenticated external SDK session is required.
The current MCP boundary is manifest/session plumbing, not a deployed MCP client.

**Private Google/Microsoft/GitHub/Slack/Notion/MCP account access: UNVERIFIED.**
Fixture tests are synthetic. A separate opt-in public GitHub acceptance does not
verify private authenticated GitHub operations.

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

`python -m oscar.oauth_cli --state <local.sqlite> --owner-authorized --begin <registered-client-id>` starts only the official GitHub device flow. One `--poll <transaction-id>` reads its nonce from stdin; no polling loop or token output. Tokens/device credentials live in OSCAR-owned native Credential Manager references. Interrupted exchange is ambiguous and blocked rather than replayed. A registered client is currently absent. Provider revocation needs the legitimate provider settings/app boundary; local disconnect is explicitly pending remote revocation. No CLI/browser tokens are borrowed. Verified local acceptance now includes typed PowerShell, registered Notepad/UIA, isolated browser, separate owner control, native credentials, canonical WAL/FTS5, real Qdrant/Graphiti/Neo4j with local embedding/reranking, memory evaluation and owner-reviewed model policy candidates. Slice 05 is COMPLETE for this Windows local-alpha scope; Slice 06 and Gate B remain PARTIAL. Real private OAuth, provider revocation and private-source/live-memory federation require owner authorization. General conversational recall integration remains a composition boundary, not a proven autonomous product. See [Gate B completion ledger](GATE-B-COMPLETION.md).
