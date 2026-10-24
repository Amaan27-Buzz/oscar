# Reviewed browser workflows — local software candidate

Conversation planning now includes the existing bounded browser workflow contract,
rather than only page inspection. `browser_workflow` is an owner action form whose
single `workflow` field encodes the existing remote browser parameters as bounded
JSON text. The authoritative Core validates that envelope through
`validate_remote_machine`; the existing browser validator admits only explicit
origins and typed steps. No JavaScript/evaluate executor was added.

The planner's example passes through the same form validation as admission. It
shows navigate, fill, submit, wait and inspect; existing select, upload, artifact
and tab operations remain available within their existing bounds. Explicit account
use requires both immutable account ID and current generation. No personal browser
profile path or inferred account selection is accepted. File transfer remains
confined to the Worker artifact workspace, with the existing basename and size
checks. Network redirects and subresources remain checked against exact origins.

## Authenticated HTTP anchor downloads

Same-origin HTTP anchor downloads now stream through a fixed browser-internal
fetch in the selected isolated profile. Cookies and authentication stay inside
Chromium; OSCAR does not export cookies or accept caller-supplied authorization
headers. The existing account ID/generation, selected origin, owner review and
Worker permissions continue to govern the plan. This adds no raw JavaScript
operation or browser-profile import. Other explicitly granted origins retain
the anonymous bounded HTTP path.

The reader aborts on non-success HTTP status, redirect, deadline or more than the
explicit byte limit (maximum one million bytes). Browser cache reuse and service
workers are disabled for this path. Bytes are base64-transported inside the owned
Worker process, checked again in Python, and written by the existing exclusive,
scoped artifact writer. Existing files are preserved. No complete temporary
browser download is accepted before enforcing the size limit.

This supports ordinary same-origin authenticated HTTP links. Blob links,
JavaScript-generated downloads, cross-origin authenticated transfers, external
download-manager flows and arbitrary sites remain unsupported or unaccepted.
It does not bypass browser CORS/CSP/OS restrictions or grant login consent.
HTTP GET is attempted once; no download retry or overwrite is introduced.

The implementation follows the browser's
[credential and response streaming contracts](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
and [bounded stream reads](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStreamDefaultReader/read).
The actual Chromium fixture requires a synthetic HttpOnly cookie before returning
the file and records which isolated account requested it. Negative acceptance
checks missing authentication, an oversized streamed body, redirect refusal and
preservation of an existing artifact. A binary payload is compared byte for byte.
The final source-stable browser/native/Grid campaign passed **48 tests in
72.271 seconds**, no skips; Ruff and strict Mypy (100 source modules) passed.
An initial blind exception assertion was replaced by explicit Playwright error
categories before the final campaign. See the
[sanitized receipt](../evidence/software-completion/browser-auth-download-2026-10-24.json).

Fill/click/submit/select/navigate objectives enter the existing conversation
planning path after Controller memory/current-evidence preflight. The first signed
review authorizes only selected model input. The second signed review binds the
exact proposed effects, target and capability. Existing session, lease, account,
policy and local Worker checks still own execution. Preparing a candidate does not
grant authority, and uncertain mutations are not automatically replayed.

The intended native surface is conversation and its existing exact signed review.
The direct-operation dropdown continues to expose inspection only because it has
no workflow composer. No raw JSON editor or design change was introduced.

Without an explicit objective readback, the canonical browser task remains
`partially_verified`. A reported DOM or successful click does not establish the
objective. A workflow can partially mutate a site before a later step fails;
there is no transaction or rollback promise.

## Exact browser text verification

An optional sibling of `request` in the reviewed workflow parameters declares
one exact postcondition:

```json
"verification": {
  "url": "https://example.com/receipt",
  "selector": "#receipt",
  "text": "The exact expected receipt"
}
```

The URL must stay inside the already reviewed origins. Only those three members
are accepted; expected text is bounded by 8,192 characters and the original DOM
read limit. The planner receives the contract and must omit verification when
the URL, selector or expected text is unknown. Inventing a receipt is not evidence.

Core derives a separate readback containing only navigation and `read_text`,
with the same immutable account ID/generation when present. The outbound Worker
opens a fresh Chromium process/context, using that account's isolated profile,
and reads exactly one matching element. It bounds text and visited text nodes;
duplicates, missing elements, overflow and truncated Unicode prefixes reject.
No submission, click, upload, download or original effect is replayed by readback.
Current lease, policy, account and owner authority checks remain in force.

Core compares both the final URL and complete element text. A matching exact DOM
postcondition can become `VERIFIED`; wrong text or a redirected final URL fails.
This proves only that explicit DOM postcondition, not delivery, financial success,
server truth or arbitrary page semantics. Missing/unavailable readback remains
unverified; it never authorizes a dependent step. No browser rollback is promised.

The signed HTTPS synthetic workflow submits once, verifies its exact receipt
through the independent browser read and then creates a dependent scoped local
confirmation file with separate byte readback. Wrong-text and redirected-URL
campaigns leave that file absent and do not repeat the submission. The ordinary
unverified browser path retains its earlier partial status. Runtime/source-qualified
regression evidence is recorded in the [source-qualified receipt](../evidence/software-completion/browser-readback-2026-10-24.json).
The authenticated campaign persists only the selected synthetic profile: fresh
readback succeeds, while an anonymous browser receives a denial.

Run the focused acceptance with:

```powershell
python -m unittest tests.test_browser_workflow -v
```

The actual acceptance uses signed requests over disposable loopback HTTPS, a synthetic HTTP model
candidate, two synthetic owner signatures and the outbound native Worker running
Chromium. It fills and selects a disposable local form, submits exactly once,
checks the independent server file and opens a separate read-only Chromium context
to inspect the resulting receipt. Core and Worker execute in the test process;
Chromium executes in child processes. This does not claim independent Core/Worker
process-lifecycle acceptance. Repeated follow-up/Worker polling does not
resubmit. Contract cases reject wrong navigation origins, injected profile paths,
missing/invalid account generations, upload traversal, hidden step fields and
nonfinite timeouts. Existing profile tests separately exercise current-generation
revocation and isolated persistence. Optional missing Playwright is an explicit
skip; an installed but unusable Chromium is a failure.

This is synthetic local browser acceptance. Real provider accounts, arbitrary
external websites, native visual approval and production owner commissioning are
not verified by this campaign.

## Signed two-account confirmation transfer, 2026-10-24

The same production conversation/Executive path now has actual integrated
acceptance for an explicitly reviewed cross-account workflow: submit a synthetic
registration under account A, independently verify its exact receipt, save and
independently read back the scoped confirmation file, then upload those exact
bytes under account B and independently verify the destination receipt. The
owner objective supplies both immutable account IDs; the native signature review
contains both IDs/generations and all three exact effect plans. A synthetic HTTP
model proposes those already explicit details; this is not installed-model
account discovery or arbitrary step-output substitution.

Chromium opens fresh child processes for each effect and observer. Two distinct
private profiles persist only their respective synthetic sessions. The archive
page rejects any source cookie, and its receipt requires the destination cookie.
Independent server state checks the uploaded filename and exact bytes. Repeated
owner follow-up and Worker polls leave one source submission and one upload.
All 15 browser workflow/profile cases passed together in 111.284 seconds with
stable source hashes, including existing wrong-text/redirect/overflow negatives.
[Receipt](../evidence/software-completion/browser-cross-account-2026-10-24.json).

This establishes the explicit browser/file/browser subset. General cross-account
reasoning, arbitrary installed application workflows, real provider consent,
remote Core/Worker process-lifecycle and production usability remain separate.
