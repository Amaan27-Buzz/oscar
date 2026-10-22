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
```

Event attendees are optional. Times require an explicit offset; event duration is
bounded to seven days. Requests are bounded to 4096 characters, recipients to 16,
subject/title to 200 and plain text body to 3000. Header injection, ambiguous
accounts, malformed forms and known credential text fail before staging or I/O.
Mail list returns a bounded first page (ten items); pagination tokens remain
explicit provider output, and no complete-inbox claim is made.

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
