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
