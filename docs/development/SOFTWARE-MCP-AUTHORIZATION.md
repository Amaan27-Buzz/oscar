# Reviewed MCP resource authorization — local software candidate

OSCAR's existing Desktop and Android **Connections** screens can authorize a
configured remote MCP resource through a registered public OAuth client. The
existing signed owner review, native browser callback, Auth Broker, account
generation, private Vault and MCP transport remain authoritative. No framework,
dependency or automatic tool retry was added.

## Resource access and person identity

An MCP access token proves a grant to a resource; it does not establish a verified
Google, Microsoft or other provider person. The trusted adapter creates a distinct
`mcp-resource` / `resource-grant` record with a random local grant identifier, the
configured authorization issuer and the existing OSCAR owner relationship. Its
service binding records the exact resource audience and granted scopes. Native
surfaces explicitly state that provider person identity was not verified. The
ordinary verified-provider enrollment method cannot create this identity class.

Reauthorization selects the same resource grant by exact issuer and service,
preserves its identifier, replaces its explicitly selected permissions, advances
the generation and deletes the replaced private token references. The token
response must match the requested scope set exactly. An alias, ID-token-shaped
string or tool server annotation cannot promote resource access into a person
identity or action permission.

## Configuration and product path

Add an administered `mcp-resource` entry to the existing `auth_config` provider
file. [The example](../../config/oauth-providers.example.json) contains reserved
example hosts and replacement client IDs; it is not a commissioned registration.
The administrator fixes `id`, public `client_id`, exact numeric-loopback
`redirect_uri`, HTTPS `resource`, exact HTTPS `issuer` and `allowed_scopes` ceiling.
The native client cannot supply issuer endpoints, private credentials or Vault
references. Core's existing encrypted account credential store provides custody
in Cloud composition; local Windows uses its native-key-backed encrypted store.

1. Choose the configured MCP resource in Connections, name its access grant (or
   select the existing matching grant), and select explicit resource permissions.
2. Complete the existing signed connection review. Only then does Core discover
   resource metadata and the selected authorization issuer.
3. The native browser opens the discovered authorization endpoint with PKCE S256,
   exact callback, random state and exact `resource`. Callback code/state/optional
   `iss` remain native and are submitted to Core against the original device,
   owner session and review. They do not pass through the Desktop webview.
4. Core consumes the native continuation before a one-shot code exchange,
   rechecks current owner/session/Personal Policy, then binds only the accepted
   resource token in the Vault. Native readiness follows Core readback.
5. Import a reviewed MCP server registration with the grant's account ID/current
   generation and exactly the granted resource URL. Core resolves its credential
   reference internally. Tool consequence review is separate. A subsequent signed
   **connect** discovers the currently permitted tools through the existing SDK.

Protected Resource Metadata follows RFC 9728: the challenge's `resource_metadata`
URL is preferred, then the SDK's path/root well-known fallbacks. Its `resource`
must exactly match the configured resource and its bounded authorization-server
list must contain the configured issuer. The installed official MCP SDK's RFC
8414 / OpenID discovery URL ordering is reused. Authorization metadata must return
the exact issuer and explicitly support PKCE S256. Advertised public-client,
response-type and grant-type capabilities must permit the selected code flow.
The optional authorization-response issuer flag is typed; when advertised true,
both native and Core callbacks require exact `iss`. Any supplied `iss` must match.

Production metadata/token transport requires public HTTPS destinations, validates
every resolved address, pins the chosen address while retaining Host/TLS SNI, caps
response bytes and timeout, and uses no redirects, environment proxies or retries.
Discovered authorization/token endpoints may belong to a different public HTTPS
host when the exact configured issuer advertises them. Metadata with endpoint
queries is explicitly unsupported; this avoids ambiguous OAuth parameter merging.

## Refresh, interruption and disconnect

Refresh is an explicit signed Connections action. The exact `resource` appears in
authorization, code and refresh requests; bearer tokens appear only in the
authorized resource's HTTP header. The full SDK OAuth provider is deliberately
not attached because its automatic refresh/retry would bypass this reviewed,
one-shot lifecycle. Existing SDK discovery helpers are reused directly.

Before token I/O, Core persists `exchanging` / `refreshing`. Interrupted code or
rotating-refresh exchanges become blocked and require fresh authorization; Core
recovery never retries them. A rejected/ambiguous refresh disables the old grant
and deletes its local token references. Owner, session, configuration, account
generation or policy withdrawal before binding prevents the new grant. A token
response cannot resurrect revoked owner authority. The same code/continuation or
signed review cannot be consumed twice.

Successful refresh/reauthorization closes old MCP sessions, fences old account
generations and records the new internal credential binding. The server remains
disconnected until a new signed connect. The original tool effect is never
automatically retried. Normal MCP dispatch/readback still rechecks account,
generation, exact audience, credential ownership, reviewed consequences and Policy.

Disconnect commits local revocation/generation fencing before credential I/O and
checks local deletion by readback. Provider-side revocation remains `UNKNOWN` for
this bounded adapter; no remote revocation claim is inferred from local deletion.
Already transmitted external effects cannot be recalled by local revocation.

## Bounds and evidence

This implementation supports preregistered public clients, queryless HTTPS
metadata endpoints and exact registered IPv4-loopback native callbacks. Dynamic
client registration, Client ID Metadata Documents, confidential-client auth,
incremental scope challenges during tool execution, automatic refresh and remote
provider revocation are unsupported. Unavailable metadata or unsupported provider
contracts fail closed. Real provider registrations, real account consent, public
TLS deployment and physical phone browser/OEM behavior remain commissioning work.

`tests/test_mcp_auth.py` uses synthetic authorization/resource HTTP servers, real
PKCE verification, existing synthetic RSA signed reviews, private fixture Vault
references and the installed MCP SDK. A trusted test transport maps fixed HTTPS
example aliases onto loopback HTTP; the run does not prove public DNS/TLS or a real
provider consent page. The SDK initializes, discovers and calls a read tool with
the issued bearer token and the test independently observes its resource result.
Failure checks include wrong resource/issuer/PKCE, query endpoints, typed metadata,
scope escalation, wrong node/state/configuration, owner withdrawal, replay,
interrupted code, ambiguous rotating refresh, same-grant reauthorization,
credential-reference injection, generation fencing and deletion.

The [sanitized software receipt](../evidence/software-completion/mcp-authorization-2026-10-23.json)
records exact sources and available check results. Native JVM/Rust checks cover
callback resource/issuer handling; browser consent and physical device acceptance
are not claimed. Desktop component tests cover resource identity language,
permission review and same-grant selection.

Primary contract read on 2026-10-23:
[MCP 2026-07-28 authorization](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/index.mdx),
[authorization server discovery](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/authorization-server-discovery.mdx),
[authorization security considerations](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/security-considerations.mdx).
