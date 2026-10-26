# Software communication integration — 2026-10-22

The existing Desktop input and authenticated Cloud Grid Core-target text requests
can compile explicit communication requests into the existing account-bound
Connector Fabric, Runtime, native signed review and independent verifier. This is
a bounded useful Google/Microsoft subset; it does not imply general messaging or
an inferred contact, account, time or body.

## Request forms

`Work` must be an exact unique connected Google/Microsoft account alias or ID.
Text fields use JSON quoting; recipient lists are literal comma-separated email
addresses. An optional leading `please` is accepted.

```text
draft email using Work to person@example.com subject "Subject" body "Text"
send email using Work to person@example.com subject "Subject" body "Text"
list email using Work
read email MESSAGE_ID using Work
create calendar event using Work titled "Title" from 2026-10-23T09:00:00+05:30 to 2026-10-23T10:00:00+05:30 with person@example.com
list task lists using Work
list tasks using Work in list LIST_ID
create task using Work in list LIST_ID titled "Prepare meeting" due 2026-10-25 notes "Read the agenda"
```

Event attendees are optional. Times require an explicit offset; event duration is
bounded to seven days. Requests are bounded to 4096 characters, recipients to 16,
subject/title to 200 and plain text body to 3000. Header injection, ambiguous
accounts, malformed forms and known credential text fail before staging or I/O.
Mail list returns a bounded first page (ten items); pagination tokens remain
explicit provider output, and no complete-inbox claim is made.

### Connected task authoring, 2026-10-24

The same Desktop conversation and authenticated Cloud text entry now compile
Google Tasks and Microsoft To Do requests into existing account-bound capabilities,
exact native signed reviews and independent saved-resource verification. No second
task store, frontend-only task or model-inferred account/list is introduced. The
provider list ID is literal; list discovery and task listing return at most ten
first-page items with provider pagination left explicit. Read results stay
REPORTED, and reading does not create mutation or retention authority.

Task titles are bounded to 200 single-line characters, notes to 3000 characters
with LF line endings, and the request to the existing 4096-character limit. A
literal `YYYY-MM-DD` date is required; relative dates, times, implicit lists and
compound instructions are rejected. This is a due **date**, not a timed reminder
or a promise of provider notification. Google Tasks stores a date; the Microsoft
request uses explicit midnight UTC. Saved-resource readback checks account/list
and returned resource identity, exact title/notes/date, and an uncompleted state.
Deleted/hidden Google tasks cannot verify. Microsoft HTML body conversion or
changed due time cannot silently count as an exact plain-text match.

Google uses a separately authenticated `google.tasks` service with audience
`https://tasks.googleapis.com` and explicit Tasks scopes. Microsoft uses the
existing `microsoft.graph` service with delegated Tasks scopes. The current
Fabric checks literal scopes: configure both Google
`https://www.googleapis.com/auth/tasks.readonly` and
`https://www.googleapis.com/auth/tasks`, or Microsoft `Tasks.Read` and
`Tasks.ReadWrite`, for list/create/readback workflows. Read-only scope permits
listing; write-only scope does not substitute for the verifier's separately
declared read scope. Missing read scope keeps a mutation partially verified.
Existing account grants and OAuth scope ceilings never expand automatically.
Use the existing public app-registration configuration and signed Connections
flow to request the chosen service/scopes; real owner consent remains pending.

The native task request shares the existing session/account-generation fences,
staged-input consumption, independent readback policy and uncertain-write journal.
An HTTP failure is not safe to replay. A saved provider task does not itself grant
canonical retention of the task title/notes or permission to send messages.

Official contracts checked on 2026-10-24:
[Google task insert](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks/insert),
[task GET](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks/get),
[task date semantics](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks),
[Microsoft task creation](https://learn.microsoft.com/en-us/graph/api/todotasklist-post-tasks?view=graph-rest-1.0)
and [GET](https://learn.microsoft.com/en-us/graph/api/todotask-get?view=graph-rest-1.0).
These support the adapter contract, not a claim of real-account acceptance.

The final affected campaign passed **235 tests in 136.826 seconds**, no skips,
with stable runtime/configuration/test hashes. It includes 23 communication/task
cases and real signed synthetic Cloud requests. The initial campaign's stale
35-method expected-count assertion was corrected to 39 and retained as a failed
receipt; the final full affected rerun passed. Ruff, Mypy (100 source files) and
repository link/value-silent credential checks passed. See the
[source-qualified task receipt](../evidence/software-completion/connected-tasks-2026-10-24.json).

### Connected contacts, 2026-10-24

Native Desktop conversation and authenticated Core-target text requests accept:

```text
list contacts using Google
read contact people/c123 using Google
list contacts using Work
read contact AAMk-contact= using Work
```

Select an exact connected account ID or unambiguous alias. Google uses the
separately consented `google.contacts` service at `https://people.googleapis.com`
with `https://www.googleapis.com/auth/contacts.readonly`. Microsoft uses the
existing `microsoft.graph` service with delegated `Contacts.Read`. Mail or task
scopes do not authorize contact access. Existing service bindings and scope
ceilings never expand automatically.

List requests ask for ten first-page contacts. Google requests names, email
addresses and phone numbers; Microsoft requests contact ID/display name,
email addresses and business/home/mobile numbers. Exact contact reads use those
same selected fields. Raw provider pagination stays explicit in the transient
REPORTED response: a first page is not the whole address book. This path does
not follow pagination URLs, search other contact folders, change contacts,
resolve ambiguous recipients or authorize sending messages. Google accepts a
literal `people/ID` resource name or its final ID; Microsoft requires its exact
contact ID. Traversal, URLs, compound commands and ambiguous accounts reject
before staging or provider I/O.

The existing native signed review binds the chosen account generation and typed
request. Disconnect before completion denies the read. Provider responses remain
transient unless a separate retention contract permits storage; ordinary contact
reads do not populate canonical memory or establish current identity facts.
Read results remain PARTIAL/REPORTED rather than verified user assertions.

Official contracts checked on 2026-10-24: [Google connections list](https://developers.google.com/people/api/rest/v1/people.connections/list),
[Google person read](https://developers.google.com/people/api/rest/v1/people/get),
[Microsoft contacts list](https://learn.microsoft.com/en-us/graph/api/user-list-contacts?view=graph-rest-1.0)
and [contact read](https://learn.microsoft.com/en-us/graph/api/contact-get?view=graph-rest-1.0).
Actual synthetic HTTP acceptance covers both account credentials, exact paths and
field/page bounds, native signatures, explicit pagination, private-output
non-retention, missing scope, ambiguous aliases and pre-read disconnect. Real
provider OAuth/contacts and owner physical/native UI acceptance remain separate.
[Source-qualified receipt](../evidence/software-completion/contacts-2026-10-24.json).

## Authority and privacy

The account generation is pinned when preparing the request. Native review binds
the actual typed provider parameters, capability and account identity/generation.
Review drift, staged-body drift, account disconnect/rotation, expired approval and
current operation/consequence Personal Policy denial prevent execution. Current
account, scope, policy and requester authority are rechecked around provider I/O
and independent readback. Successful execution does not authorize retention.

Desktop uses the existing Ask path and canonical independent turn-retention
grants. Cloud native requests retain their original instruction only under the
existing explicit archive grant. Provider parameters, expected private fields and
provider result bodies remain bounded transient task context; plans and durable
results carry metadata/digests. Restart expires private context and blocks pending
work. Responses containing provider data are available only to the originating
live authorized Cloud session. Another session with archive read access does not
receive those transient bodies, and the result-retention path does not copy them
into the Event Archive.

New Cloud invitations must explicitly opt in with `connector_control=True`, or
CLI `--connector-control`, to add connector read/write/external-communication
scopes. Existing invitations/sessions are not upgraded. Provider OAuth scopes,
Core policy, signed owner action authority and retention remain separate. This
change neither authenticates a real provider account nor activates owner Full
Access. Existing signed standing authority remains the authority boundary where
properly activated.

Mutation dispatch consumes the owned staged input once. Uncertain HTTP failure,
revocation during an effect, replayed native approval, duplicate admission and
restart do not automatically replay the mutation. An uncertain external effect
remains uncertain even when the local task is blocked or cancelled.

## Observable completion

| Operation | Independent saved-resource check | Claim limit |
| --- | --- | --- |
| Gmail draft | Returned draft ID GET, raw MIME exact recipients/subject/plain body | Draft resource verified |
| Gmail send | Returned message ID GET, same MIME fields and SENT label | Sent resource verified; delivery unproven |
| Microsoft draft | Returned message ID GET, draft flag and exact text/recipients | Draft resource verified |
| Microsoft sendMail | Empty 202 response has no correlated resource ID | PARTIAL; acceptance is not delivery |
| Google/Microsoft calendar create | Returned event ID GET, exact title/instants/attendees, not cancelled | Event resource verified; invite delivery unproven |
| Mail list/read | Actual bounded provider response through read capability | REPORTED data; no synthetic mutation proof |
| Google Tasks / Microsoft To Do create | Returned task ID GET in the exact selected list; title/plain notes/due date/uncompleted state | Saved task resource verified; no reminder delivery claim |
| Task list discovery / task listing | Bounded first provider page under the selected account | REPORTED data; no complete-account coverage claim |

Readback needs its own admitted provider scope and current Core policy. Missing
read access, changed state, failed GET or a mismatched resource cannot become
VERIFIED. Generic arbitrary nested/batch-update verification remains unavailable.
Readback compares instants across equivalent timezone offsets.

The implementation follows official [Gmail MIME sending](https://developers.google.com/workspace/gmail/api/guides/sending)
and [message GET](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get)
contracts. Microsoft [draft creation](https://learn.microsoft.com/en-us/graph/api/user-post-messages?view=graph-rest-1.0)
returns a message resource; [message GET](https://learn.microsoft.com/en-us/graph/api/message-get?view=graph-rest-1.0)
supports the requested text-body preference. Microsoft
[sendMail](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0)
returns an empty 202 response. These documentation checks do not substitute for
real provider commissioning.

## Local acceptance

`tests/test_communication.py` runs the production connector HTTP adapter against
an actual loopback HTTP server with synthetic provider state. A test-only opener
maps fixed official host requests to that server; no external provider account is
used. Independent GET reads server-side stored state after POST. This proves
executable local HTTP integration, rather than a provider success stub, while
remaining synthetic provider evidence.

Coverage includes Desktop signed exact review, Gmail and Graph mail/calendar,
Cloud actual HTTP enrollment/request/owner proof/approval/verification, isolated
private output, duplicate admission, replay, account generation, requester and
policy revocation, readback mismatch, uncertain mutation without retry, header
injection, body drift, credential rejection and restart fail-closed behavior.

The focused suite passed **155 tests in 97.512 seconds**:

```powershell
python -m unittest tests.test_communication tests.test_connectors tests.test_connector_http tests.test_connector_mount tests.test_desktop tests.test_mobile tests.test_connections tests.test_remote_grid -q
```

See the [source-scoped receipt](../evidence/software-completion/communication-2026-10-22.json).
No real OAuth, real mail/event mutation, recipient delivery, public deployment or
physical-phone acceptance is claimed.

## Google Meet app-created spaces — 2026-10-25

The existing account broker, native conversation admission, signed review,
Fabric and independent verifier now support:

```text
create meet space using ACCOUNT-ALIAS access restricted
read meet space SERVER-GENERATED-SPACE-ID using ACCOUNT-ALIAS
```

Only the selected connected Google account's exact `google.meet` service binding
and `https://www.googleapis.com/auth/meetings.space.created` grant enable these
capabilities. The example OAuth configuration supplies the service and scope
ceiling; it grants nothing by itself. Existing accounts are not upgraded.
Creation is a write operation; reading separately needs Core connector-read
permission. Signed Ask and current account-generation/policy checks apply.

Create posts an explicit `config.accessType: RESTRICTED` to the official v2 API.
The returned `name` must identify one resource under `spaces/`; the independent
GET must return that exact full name, restricted access and a consistent official
Meet join URL/code. No guessed IDs or response-only success can verify the write.
A declared resource-name prefix extends the existing verifier; ordinary providers
retain exact `id` correlation. Read-only responses remain REPORTED. Account
rotation, wrong names, malformed/nested names, wrong access, invalid URLs and
malformed configuration fail closed. A stored effect followed by HTTP failure is
not retried or replayed. Space payloads remain transient and requester-scoped.

Official contracts: [create](https://developers.google.com/workspace/meet/api/reference/rest/v2/spaces/create),
[get](https://developers.google.com/workspace/meet/api/reference/rest/v2/spaces/get),
[space configuration](https://developers.google.com/workspace/meet/api/reference/rest/v2/spaces),
and [user authorization](https://developers.google.com/workspace/meet/api/guides/authenticate-authorize).
RESTRICTED means only invitees join without knocking; it is not a promise that
other users can never request entry. Meeting codes are aliases, not durable
resource identities.

Synthetic acceptance exercises real loopback HTTP with signed Desktop review,
a signed phone/Core request, private output isolation, actual synthetic signed
OIDC/PKCE scope binding, refresh, local revocation and after-effect uncertainty.
The [source-scoped receipt](../evidence/software-completion/meet-2026-10-25.json)
records the final checks. No real Google enrollment, meeting, participant access,
invitation, call, recording or recipient delivery is claimed. Broader meeting
participation and adaptive account/application workflows remain unfinished.

## GitLab.com account-bound issues — 2026-10-25

The configured broker verifies signed OIDC identity with PKCE and binds the
selected account to `gitlab.api`. Native Connections lists configured providers
on Desktop and Android. No personal access token or arbitrary provider endpoint
is inferred. The example configuration grants nothing by itself.

```text
create gitlab issue using ACCOUNT in project NUMERIC-ID titled "TITLE" body "BODY" visibility project
create gitlab issue using ACCOUNT in project NUMERIC-ID titled "TITLE" body "BODY" visibility confidential
read gitlab issue IID using ACCOUNT in project NUMERIC-ID
list gitlab issues using ACCOUNT in project NUMERIC-ID [page N]
list gitlab projects using ACCOUNT [page N]
```

Reads require either `read_api` or `api`; writes require `api` and Core
communication authority. Signed Ask or current standing delegation still applies.
Project visibility is explicit, and an issue may notify project participants.
Creation is independently read back using the exact positive integer project-local
`iid`, never the global issue `id`. Project, title, body, confidential flag and
opened state must match. Wrong identities/types, missing grants and rotated
account generations fail closed. A stored effect followed by an HTTP error is
uncertain and never replayed. Provider bodies remain transient and private.

Each list page is limited to ten items. The explicit next-page header provides
coverage; missing or malformed pagination leaves coverage UNKNOWN. No provider
URL is followed automatically. GitLab revocation's documented empty-object
acknowledgement is recorded as accepted, not independently verified. Local
credential deletion remains independent and remote rejection remains UNKNOWN.

Official contracts: [OIDC discovery](https://gitlab.com/.well-known/openid-configuration),
[OIDC identity](https://docs.gitlab.com/integration/openid_connect_provider/),
[OAuth/PKCE/revocation](https://docs.gitlab.com/api/oauth2/),
[issue identity and fields](https://docs.gitlab.com/api/issues/), and
[API authentication](https://docs.gitlab.com/api/rest/authentication/).

The [source-scoped receipt](../evidence/software-completion/gitlab-2026-10-25.json)
records 120 passing checks with synthetic signed identity and actual loopback HTTP,
including signed Desktop and phone/Core requests. No real enrollment, GitLab
mutation, self-hosted instance, pipeline, merge request or general account-agent
acceptance is claimed.

## Planned task status updates and current readback authority (2026-10-26)

Native account capabilities now include Google Tasks and Microsoft To Do PATCH.
A model-created Worker can complete or reopen an exact Google task, or select a
supported Microsoft status. Only a status-only body gains the private task
verification contract; other PATCH bodies retain generic partial verification.
A separate GET must return the exact task resource and status, with no deleted
or hidden resource. A parent task-list or calendar identifier cannot substitute
for the final resource identifier, even if both mutation and GET agree on it.
Uncertain mutations are never replayed.

Microsoft To Do creation encodes literal notes into escaped HTML, including
line breaks. Independent verification decodes a bounded literal HTML subset;
unknown rich markup remains partially verified. This follows the provider's
[HTML body contract](https://learn.microsoft.com/en-us/graph/api/todotask-update?view=graph-rest-1.0).

Signed Desktop and remote phone/Core communication readbacks now recheck current
owner and executor read scope before, during and after the independent GET.
Removing read authority cannot leave a verified claim. Existing account,
Personal Policy, exact review, cancellation and signed standing authority checks
remain separate. Tests use synthetic owners and provider HTTP fixtures; actual
provider commissioning and rendered native acceptance remain separate.
