# Group 2 baseline privacy and approval audit

Scope: verified Group 1 `dcfd31bca6fbd8080f4c20bebe3d448e4bd8dc2f`,
Desktop discard and Mobile Core session/readback/approval composition. This is
software/reference evidence, not Android, owner consent or acoustic acceptance.

## Confirmed Desktop defect

**P1 cross-session data loss:** discard selected transient tasks using only the
originating node. The voice owner, captured contexts, previews, private response,
private approval and follow-up contracts are already session-scoped. Native callers
say "Discard private drafts and context"; no node-wide privacy operation exists.
The mismatch was unintended rather than an authorized node-wide wipe.

The new regression failed at the untouched baseline in four subcases: another
same-node session's planned and finished payloads were deleted, its active payload
was marked discarded, and missing session provenance was treated as deletion
authority. The fix requires both node and `desktop_task.session_id`. Unknown
provenance fails closed; shared task/ledger state and verification remain intact.
Existing concurrent execution/discard coverage remains applicable.

## Confirmed Mobile defects

**P1 private session isolation:** original Mobile text persisted raw requests in
objectives/plans and model responses in results. `sunday_task` had no session
provenance; same-node replacement sessions could see the request and approve it.

An independent disposable probe executed the exact baseline's `oscar/mobile.py`
from `git show dcfd31b:oscar/mobile.py`, with synthetic owner keys. Its readback was:

```json
{"same_node_replacement_sees_request":true,"same_node_replacement_can_approve":true,"raw_request_durable":true,"exact_review_present":false,"scope_present":false}
```

New Mobile text uses the existing Runtime transient path and private Model Router
mode. Only originating session/node sees requests/results or may approve/retry.
Replacement sessions keep granted shared task metadata and safe denial/cancel,
without private material. Existing durable historical records are not destructively
migrated; their surface readback is sanitized and private approval is unavailable.

Core assembles bounded successful same-session working context, marked reported
data rather than authority. Session-scoped discard removes finished private data;
active execution finishes ordinary verification while presentation stays hidden,
then releases the transient payload. No Android memory database or frontend
reasoning path was introduced. Missing private provider stays blocked/failed rather
than silently sending context through another route.

**P1 incomplete consequential review:** Mobile returned a short description, but
not the full request, exact plan parameters or permission scope. It now returns
`exact_request`, `review` and `scope`. Raw typed text is kept transient even when
Core canonicalizes an arithmetic request. The request and private parameters enter
the signed descriptor digest; changes invalidate the challenge. More than 24,000
combined UTF-8 bytes fail before creating a challenge. Denial/cancel reviews omit
private content. Completion also rechecks currently admitted actions.

Core cannot attest strong confirmation merely from a valid RSA signature. Critical
capabilities fail closed at execution even if a platform signing key exists; the
Group 1 strong-critical-confirmation obligation remains **BLOCKED**.

## Checks and limits

- Desktop-only correction: 79 Desktop/completion/Mobile/Grid tests passed, no skips.
- Mobile privacy correction: 15 Mobile tests passed, plus two focused continuity
  and concurrent-discard checks passed. Final combined Desktop/completion/Mobile/
  Grid/Core run: **118 tests passed, zero failures/skips, 37.450 seconds**.
- Ruff passes for both changed Core files and both regression files; mypy passes
  for `oscar/mobile.py` and `oscar/desktop.py`.
- Fixtures are disposable Core/Grid databases, synthetic keys, bounded arithmetic
  and synthetic private-router adapters. No accounts, recordings, device grants or
  owner data were used.

One attempted command referenced nonexistent `tests.test_runtime`; its loader
error was corrected to the actual `tests.test_core` module. It is not a runtime
defect or a passing test.

No new Desktop redesign, permanent authority, networking client, dependency,
private-history migration or production promotion was performed. Android native
rendering, phone/OEM behavior and platform owner confirmation remain for the
Group 2 implementation and consolidated acceptance. The patch author's reruns
are regression proof, not a substitute for the final fresh adversarial review.
