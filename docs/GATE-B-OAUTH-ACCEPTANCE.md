# Owner GitHub OAuth and federation acceptance

GitHub is the first real Auth Broker/provider proof, not OAuth independently owned
by every plugin. This harness reuses `GitHubDeviceFlow`, the Windows native vault,
opaque `CredentialRef`, `ConnectorFabric` and the existing GitHub manifests.
**Real owner acceptance PASSED in `oauth-gate-b-20261004-234817`.**
Slice 05/06 COMPLETE; Gate B PASS for the documented local-alpha scope. No Slice 07, Sunday/Android,
deployment, private write or merge is authorized by this acceptance recording.

## Registered OAuth App setup

Official GitHub documentation checked on 2026-10-04:
[create an OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app),
[device flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow)
and [authenticated email reads](https://docs.github.com/en/rest/users/emails).

Under **GitHub Settings → Developer settings → OAuth Apps → New OAuth App**:

| Field | Value for this acceptance |
|---|---|
| Application name | `OSCAR Gate B Local Acceptance` |
| Homepage URL | `https://github.com/amaansyed27/oscar` |
| Application description | `Owner-operated OSCAR read-only device-flow acceptance` |
| Authorization callback URL | `http://127.0.0.1:8765/oauth/callback` |
| Enable Device Flow | Checked |
| Expire user access tokens | Unchecked for this adapter's bounded acceptance |

The callback is a registration placeholder unused by device flow; the harness
does not start a callback server or deploy anything. GitHub now supports expiring
OAuth App tokens/refresh, with expiration enabled by default in current creation
documentation. OSCAR's current device adapter does not implement refresh. Do not
request `offline_access`; future refresh support remains separate work.

After registration, supply only the app's **Client ID** (the value labeled Client
ID on that OAuth App page). Do not generate, supply or store a client secret.
Do not supply a PAT, `gh` token, Git Credential Manager secret or browser cookie.
Scopes are chosen by the harness: exactly `user:email`, never `gist` or `repo`.
Use a dedicated app without previous broader grants; unexpected scopes block.

## Owner command and interaction

From the repository root, in an interactive Windows terminal:

```powershell
$root = ".oscar\oauth-gate-b-" + (Get-Date -Format "yyyyMMdd-HHmmss")
& .\.oscar\gate-b-venv\Scripts\python.exe -m scripts.verify_gate_b_oauth --root $root --client-id YOUR_REGISTERED_OAUTH_APP_CLIENT_ID --owner-authorized
```

The interpreter uses standard-library HTTP and the native Windows vault; browser
automation and external credentials are not involved. Existing roots are refused.
The terminal prints the evidence root and, from the authorization challenge, only
`https://github.com/login/device` and the short user code. Visit that URL yourself,
enter the code, verify the app identity and the email-read scope, and authorize.
Then type **AUTHORIZED** in the terminal. No polling occurs before this explicit
interaction. Owner codes/nonces are not written into evidence. Do not record the
authorization screen or redirect the interactive challenge to persistent logs.

Polling follows GitHub's minimum interval, increases it on `slow_down`, and stops
at expiry or a bounded iteration limit. Ambiguous exchanges block without replay.
Device credentials and access tokens live only in native Credential Manager;
SQLite holds opaque references, client/scope metadata and recovery state.

## Read, restart and disconnect evidence

The harness performs real authenticated `/user` and `/user/emails` reads through
the Connector Fabric. It validates response shape, hashes the account ID with the
unique fixture ID, and retains only bounded metadata. Email evidence is the count
of records returned on **page 1, per_page=100**, not a claim about an unpaginated
total. Actual addresses, login/profile names, raw tokens, cookies and private bodies
are never saved. Existing HTTPS response limits, fixed origins and no-redirect
behavior apply; provider errors produce named checks without raw exception text.

Read-contract checks are VERIFIED; provider facts remain REPORTED. Success is not
arbitrary independent proof of every statement in the GitHub payload.

The coordinator closes its Store and launches a bounded new Python process. That
process reopens SQLite and the native vault, recovers the existing connection,
repeats both private reads, and checks the salted identity matches. No token is
passed in argv or environment. Changed counts do not falsely imply account change.
The parent then reopens storage and exercises federation before disconnecting.

Local disconnect deletes the owned credential and independently checks it is
absent. Failure cleanup attempts deletion of only references in this fresh run's
enrollment database, retaining failure metadata for review. Cleanup failure blocks
acceptance. This is local logout only: remote provider revocation remains
**UNKNOWN_OWNER_ACTION_REQUIRED**. Review/revoke the app in GitHub's **Settings →
Applications → Authorized OAuth Apps** afterward; the harness does not claim it
revoked provider authorization. No private write/gist acceptance is performed.

## Controlled current-versus-history federation

After authorization and restart readback, a unique relationship/project in the
canonical Event Archive retains a deliberately synthetic prior count `-1`, with
source/event/memory IDs and a past timestamp. This is test history, not an invented
fact about the owner's actual past email count.

The existing Memory Writer/Fabric, archive FTS5, FabricBackend, ConnectorContextSource
and LiveContextFederation compose:

- NOW: fresh authenticated `/user/emails` page-one count, source GitHub, REPORTED;
- HISTORY: time-qualified retrieval of the synthetic event, source archive, RECALLED;
- public context: anonymous current `python/cpython` repository contract;
- conflict: explicit source identity and temporal interpretation for each value.

The claim verifier checks the historical event/memory support. History is checked
unchanged after the live read; live data does not rewrite it. Missing private/public
sources fail this acceptance rather than passing with stale memory or model guesses.
Only synthetic history and count/provenance metadata are retained. This is a bounded
composition proof, not a general conversational entailment or retrieval-quality claim.

Evidence includes `initial.json`, `checkpoint.json`, `restart.json`, synthetic
`archive.sqlite`, opaque enrollment metadata and `report.json`, or named `failure.json`
and restart failure metadata. Prior failed roots are never erased or reused.
An unexpected process crash may leave owned enrollment state: review that root and
native-vault references; existing recovery never blindly repeats the exchange.

The owner completed this path and the independent final B1–B8 review accepted it.
See [the final Gate B checklist](GATE-B-COMPLETION.md) and
[redacted machine-readable record](evidence/gate-b-final-acceptance-2026-10-05.json).
The original report conservatively says Gate B PARTIAL because the harness cannot
automatically decide overall gate status; it remains unchanged. This separate review
records PASS. Remote revocation remains UNKNOWN_OWNER_ACTION_REQUIRED.
