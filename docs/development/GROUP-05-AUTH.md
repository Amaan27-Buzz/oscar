# Group 5 C1/C2 identity and shared authentication

Implementation date: 2026-10-20. This is local software/synthetic-provider evidence,
not acceptance of real Google/Microsoft accounts or hosted credential storage.

`oscar/accounts.py` stores OSCAR operational identity and connected-account metadata
in the existing canonical `Store`. It adds no task database, scheduler, capability
registry or policy authority. The operational identity has stable identity/audit IDs,
owner relationship, optional operational email, owned-resource and recovery/revocation
fields. No mailbox or external account is created. Provider accounts refer to this
relationship through an explicit identity class: owner-delegated, OSCAR-owned,
service or workload. OSCAR ownership never grants access to owner accounts.

Provider/tenant/subject IDs establish account identity. Alias and group are display
metadata. Arbitrary aliases may collide; material ambiguity requires an explicit
account choice unless an eligible saved default exists. Explicit account/alias/tenant/
identity-class selection is supported. Provider subject collisions in different
tenants remain different accounts. Account scope/credential changes and local
disconnect advance the generation; rename preserves it. Removed accounts retain
metadata tombstones so stale references cannot resurrect authority. A credential
reference is permanently bound to one account/service, including after replacement.

Each service binding records only opaque credential reference, audience, scopes,
expiry and organization-denied capabilities. Trusted enrollment/broker code owns
creation and binding; frontend-supplied labels, subjects or plugin descriptions do
not establish a verified provider identity. OSCAR Personal Policy remains a separate
check from provider scopes and organizational restrictions.

`ConnectorInstance` optionally carries a trusted account/generation/audience binding.
`ConnectorFabric` rechecks actual account/service/provider/audience/credential/scopes
and organization restrictions when advertising, dispatching and independently reading
back. Account identity/generation appears in metadata-only result audit receipts.
Legacy unbound instances remain supported for the previously accepted Gate B path;
new multi-account callers must use the explicit bound form. In-flight HTTP effects
cannot be recalled by a later revocation; new dispatch/readback is denied.

`oscar/auth_broker.py` uses the existing `Vault`, `CredentialRef`, PKCE generation,
Windows Credential Manager and no-redirect HTTP transport patterns. It supports
Google native desktop and tenant-specific Microsoft identity v2 code flows with
S256 PKCE, one-use hashed state, nonce, exact redirect/configuration binding, bounded
TLS exchanges, RS256/JWKS signature verification, issuer/client audience/authorized
party/expiry checks, provider subject/tenant binding and access-token hash validation
when supplied. Public enrollment returns the authorization URL and metadata; tokens
and verifier stay in the vault. Client secrets, when required by the registered Google
client type, are supplied through an opaque native-vault reference.

Microsoft configuration requires a concrete tenant UUID; a broad `common` tenant
is deliberately unavailable in this adapter. Scope/expiry contract errors, account
switches, revoked generations and provider failures deny enrollment. Scope omission
uses the requested scope set according to OAuth token-response semantics. A refresh
uses the original privately bound refresh grant; when no new ID token is supplied it
retains the originally verified account identity. Supplied identity tokens must still
be signed and valid; unsigned replacement identity claims are never trusted.

Scope upgrades perform a fresh authorization for existing plus requested scopes.
Google explicitly does **not** support native-app incremental authorization, so this
adapter does not send `include_granted_scopes` or claim that feature. Previous refresh
credentials are preserved privately when a successful full reauthorization omits a
replacement. Successful rotation deletes replaced local access/refresh credentials.
Interrupted code/refresh exchange is blocked and requires new authorization, including
after process restart; unknown rotating-token outcomes are never automatically replayed.
Partial native-vault failure cleans new unbound references. Disconnect first fences
account authority, then deletes local service/refresh references. Provider revocation
remains `UNKNOWN_OWNER_ACTION_REQUIRED`; no remote-revocation proof is fabricated.

The existing `GitHubDeviceFlow` implementation and its accepted owner path are
unchanged. Its documented limitations remain: configured registered OAuth App,
supported device scopes only, no borrowed browser/CLI credentials, no new generic
GitHub App installation or service-account enrollment, no remote revocation claim.

## Official specifications checked

Checked from official documentation on 2026-10-20:

- [OAuth 2.0 Security BCP, RFC 9700 / BCP 240 (January 2025)](https://www.rfc-editor.org/info/rfc9700/).
- [PKCE, RFC 7636](https://www.rfc-editor.org/rfc/rfc7636).
- [Google native desktop OAuth / S256 PKCE](https://developers.google.com/identity/protocols/oauth2/native-app).
- [Google OpenID Connect / signed claims and stable subject](https://developers.google.com/identity/openid-connect/openid-connect).
- [Microsoft identity platform v2 code flow / PKCE / refresh](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow).
- [GitHub registered OAuth App device authorization](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).

Local verification runtime: CPython 3.14.2, cryptography 46.0.3. The repository's
existing cryptography dependency is reused; no identity/auth dependency was added.
OIDC cryptographic verification fails closed if the existing optional cryptography
runtime is unavailable. Hosted Linux writable vault and Android account vault
commissioning remain separate; injected server secrets are an administered read-only
adapter, not a claim of a deployed cloud vault.

## Local evidence

`tests/test_accounts.py` executes real per-account synthetic filesystem adapters
through `ConnectorFabric`, checks Ask mutation confirmation and independent readback,
and proves cross-account/provider/audience/organization denial. It covers rename,
default/ambiguous selection, scope withdrawal, expiry, revocation during dispatch,
tenant collisions, operational identity, restart/replacement and immutable credential
ownership. On Windows a dedicated test writes only random OSCAR-owned synthetic
vault references, starts a separate Python process, reloads the registry/vault and
executes both accounts independently. Those test references are deleted in `finally`.

`tests/test_auth_broker.py` starts a real isolated loopback HTTP OAuth fixture with
synthetic RSA-signed OIDC/JWKS responses. The fixture validates PKCE verifier,
redirect/client/code and refresh grants. Tests exercise Google/Microsoft flows,
state/nonce/signature/issuer/audience/expiry rejection, scope upgrades and withdrawal,
account switching, token pairing, native-vault failure, refresh, provider errors,
interrupted exchange, restart and local disconnect. The synthetic transport maps
fixed provider URLs to the fixture; production transport still requires HTTPS.

No owner account, preexisting credential, browser profile, physical Android phone,
external account creation, paid service, Oracle provisioning or CI was used.

Verified locally:

```powershell
python -m unittest tests.test_accounts tests.test_auth_broker -q
# 22 tests, PASS, no skips on this Windows host
python -m unittest tests.test_accounts tests.test_auth_broker tests.test_connectors tests.test_connector_http tests.test_oauth_device tests.test_oauth_acceptance tests.test_windows_capabilities.NativeCredentialTests tests.test_cloud_platform -q
# 95 tests, PASS, 1 skip (POSIX-only owner/mode/symlink enforcement on Windows)
python -m ruff check oscar/accounts.py oscar/auth_broker.py oscar/connectors.py tests/test_accounts.py tests/test_auth_broker.py
python -m ruff format --check oscar/accounts.py oscar/auth_broker.py oscar/connectors.py tests/test_accounts.py tests/test_auth_broker.py
python -m mypy oscar/accounts.py oscar/auth_broker.py oscar/connectors.py
# All PASS; formatting checks 5 files, mypy checks 3 source files
```

The existing HTTP redirect regression emits a Python `ResourceWarning` for its
synthetic `HTTPError 302` cleanup; it does not fail this test run. No live-provider
enrollment, public redirect listener, registered-app consent screen, provider remote
revocation or external organization acceptance was exercised.
