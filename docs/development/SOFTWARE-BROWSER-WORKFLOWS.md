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

Fill/click/submit/select/navigate objectives enter the existing conversation
planning path after Controller memory/current-evidence preflight. The first signed
review authorizes only selected model input. The second signed review binds the
exact proposed effects, target and capability. Existing session, lease, account,
policy and local Worker checks still own execution. Preparing a candidate does not
grant authority, and uncertain mutations are not automatically replayed.

The intended native surface is conversation and its existing exact signed review.
The direct-operation dropdown continues to expose inspection only because it has
no workflow composer. No raw JSON editor or design change was introduced.

The browser Worker reports its observations. The canonical browser task remains
`partially_verified`; a reported DOM or successful click is not promoted to
independently verified objective completion. A workflow can partially mutate a
site before a later step fails; there is no transaction or rollback promise.

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
