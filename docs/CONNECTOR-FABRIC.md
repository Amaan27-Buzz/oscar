# Native Connector Fabric

OSCAR prefers official structured authenticated APIs, then official connectors,
reviewed MCP sessions, authorized app automation and computer-use fallback.
`ConnectorFabric` is a capability source for the existing Grid catalog, not another
registry competing with it. Jev selects a capability class; provider manifests
contain service facts. Existing Dispatcher target authorization, action correlation,
idempotency, Runtime and independent Evidence/Verification remain authoritative.

## Implemented boundary

- Typed manifests, instances, capabilities, auth type, opaque CredentialRef,
  connection state, risk, result and event envelopes.
- Bounded HTTPS JSON/media adapter, TLS verification and no redirects; no automatic
  mutation retry. Resource path segments are encoded; query keys are allowlisted.
- Read, write, destructive, financial, security and external-communication scopes
  remain distinct. Writes require explicit confirmation and Personal Policy.
- Environment secret resolver is a platform-supplied reference boundary, not a
  vault. OAuth refresh/revoke and authenticated MCP session are adapter protocols.
  PKCE S256 generation is implemented. Enrollment, token refresh, device flow and
  OS secure storage are **not implemented or live verified**.
- Provider results remain REPORTED. `ConnectorVerifier` independently fetches a
  correlated resource and compares explicit expected fields before verification.
  Gmail sent-recipient/header verification and arbitrary nested/batch-update
  verification remain unimplemented; they must stay PARTIAL.
- Private bodies/results stay in bounded task-scoped transient context. `stage`
  returns an opaque input reference for durable Actions; process restart expires
  that input and BLOCKS execution. Metadata-only receipt/ledger records retain
  evidence IDs/time and policy decision. Callers release completed inputs/results.
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
