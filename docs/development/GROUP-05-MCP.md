# Group 5 C2 — MCP sessions and plugin lifecycle

Local implementation, 2026-10-20 IST. Depends on the unmerged D2 candidate;
no push, CI trigger, external account enrollment or hosted MCP acceptance.

## Architecture inventory

The existing `MCPBoundary` and `MCPConnectorHTTP` already projected reviewed tools
through Connector Fabric and its Grid capabilities, but accepted an injected
session. They did not launch, negotiate or maintain a general MCP connection.
`oscar/mcp_client.py` supplies those sessions with the official SDK. There is no
new capability catalog, policy engine, task database or event archive.

`MCPPlugins` persists installation metadata in canonical `Store` records. Harness
owns one instance alongside its existing Connector Fabric. Only connected,
enabled, account-valid installations appear as executable Grid capabilities.
Process loss and account revocation withdraw eligibility; restart loads metadata
without automatically launching a process. Connect is an explicit operation.
Native management consumes the same snapshot and lifecycle operations.

Each installation binds an exact account ID/generation and reviewed tool risks.
Changing the account disconnects the old process first. HTTP credentials must
belong to the bound account/service and exact MCP resource URL audience in the
Auth Fabric. Raw secrets resolve privately inside the trusted transport; they
are absent from installation records and native snapshots. Anonymous trusted
stdio fixtures do not invent credentials to simulate provider authorization.

## Current official specification and SDK

Research checked the [2026-07-28 MCP changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog),
the [official SDK release v2.3.0](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0)
and [SDK client implementation](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/src/mcp/client/client.py).
The optional dependency is `mcp==2.3.0`. Imports stay lazy so an ordinary Core
without this optional dependency can list disconnected installation metadata.

The SDK's `Client(mode="auto")` probes current `server/discover` and falls back
to the legacy initialization handshake when needed. Its negotiated version is
reported, rather than hardcoded. The real stdio and Streamable HTTP fixtures
negotiated **2026-07-28**. Modern HTTP is stateless; OSCAR does not assume the old
session/GET handshake is still the current protocol. Legacy fallback is supplied
by the SDK; interoperability with an independent older SDK server is not accepted
by these local receipts.

The [official SDK transports](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/src/mcp/client/streamable_http.py)
and [MCP transport specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
own framing, discovery, request metadata, notification parsing and cancellation.
OSCAR supplies reviewed destination/identity, policy, schemas and lifecycle.

## Enforcement and lifecycle

- Registration needs explicit trusted-owner review of command/arguments, reviewed
  executable/script hashes, account identity and per-tool risk. Server annotations
  cannot grant authority. Initial discovery records schema hashes; changed schemas
  reject subsequent invocation/reconnect until an explicit fresh review.
- Stdio uses an absolute executable, rechecks reviewed file hashes at each launch,
  overrides SDK environment inheritance, omits provider keys and discards server
  stderr. Runtime and connection deadlines, list cardinality, schema depth and
  response size are bounded. SDK teardown owns subprocess cleanup.
- HTTP rejects userinfo, query secrets, fragments, non-HTTPS public endpoints,
  private/reserved destinations and mixed public/private DNS results. A deliberately
  approved **exact loopback fixture origin** is the only local HTTP exception.
  Resolved addresses are pinned for network I/O while TLS SNI/Host remain bound to
  the reviewed host. Redirects, environment proxies and destination changes reject.
- Up to 16 installations, 200 discovered tools, bounded pagination, 100 KB tool
  metadata and 16 KB server metadata. Remote JSON Schema references in input and
  output schemas reject before the SDK can use them. Input validation precedes I/O;
  case-sensitive MCP tool names get stable lowercase Grid IDs when necessary.
- Tool discovery refreshes before every invocation. Notifications are accepted by
  the SDK and counted without storing their content. Fresh lists also cover modern
  subscription/cache invalidation without treating cached manifests as authority.
- Resources and prompts are discovered explicitly. Their content access uses
  separately reviewed `oscar.resources.read` / `oscar.prompts.get` capabilities
  through Fabric policy. Resource/prompt contents remain untrusted data.
- Fabric `Cancellation` is checked while awaiting the SDK. Timeout, owner cancel
  and account revocation cancel the request; no mutation is automatically retried.
  A cancelled or timed-out mutation may need readback before another attempt.
- Disconnect/disable removes the Fabric instance and closes its process/session.
  Enable only changes metadata; connect remains explicit. Removal deletes the live
  installation record. It does not claim secure erasure of WAL/backups or remote
  provider token revocation. Activity retains only bounded event/time metadata.

## Trusted local management and immediate test path

Install optional support and run the real separate-process contracts:

```powershell
python -m pip install -e '.[mcp]'
python -m unittest tests.test_mcp_client tests.test_connectors -v
python -m oscar.mcp_cli --state .oscar/core.sqlite list
```

The trusted local CLI supports register/inspect/connect/disconnect/enable/disable/
remove. Registration reads a bounded JSON object with `config` (the exact
`MCPServerConfig` fields) and `reviewed` (tool names to explicit risk lists).
An initial run prints the candidate and its SHA-256 digest without installing.
Repeating with `--approve-digest <exact digest>` records that reviewed candidate.
Its account ID/generation must already exist in the Auth Fabric. The CLI's connect
is a diagnostic session that closes on process exit; persistent live sessions
belong to the running Core. Native signed owner control uses the Core instance.

## Local verification evidence

`tests/fixtures/mcp_knowledge.py` is a real independent SDK server process exposing
typed tools, a synthetic resource and a prompt. `mcp_workspace.py` is another real
SDK server using existing `ScopedFiles` in a temporary workspace; it returns a
receipt and never declares objective verification. `mcp_changing.py` exercises
actual discovery drift after restart.

Focused tests cover real stdio and Streamable HTTP negotiation, resources/prompts,
two accounts executing the same tool in distinct processes, case-sensitive names,
malformed arguments, Ask denial with an absent artifact, approved write and direct
filesystem readback, per-server capability isolation, reconnect, enable/disable,
revoked account withdrawal, schema drift, fresh-process Core metadata recovery
without autolaunch, trusted CLI review, timeout/cancellation and removal. Hostile
schema references, private destinations and mixed DNS answers reject. Secret
environment inheritance is checked in the child process. Exact current command
results are recorded by the integration run; successful tool receipts stay REPORTED.

The integrated Harness test mounts Fabric executors on a distinct scoped Grid
node. A reviewed Executive goal performs the second-account MCP write and a
dependent native file export after research from the first account. The MCP write
does not consume its staged request or call the server before exact Ask approval.
Both resulting file effects are independently VERIFIED, and canonical connector
audit entries retain the stable account ID and generation, tool and correlation.
Disconnect withdraws the catalog entry; explicit reconnect restores it. The
normal-deadline timeout test uses a 30-second delay against the unchanged
15-second default, then requires lookup, cancellation and reconnect to succeed.

## Boundaries

This is **local synthetic software interoperability**, not real owner/provider or
Internet-host acceptance. Public HTTPS MCP authorization enrollment, OAuth challenge
discovery/refresh interoperability, bearer rotation across a live session and remote
revocation remain commissioning work. No raw owner credentials were used.

Launching arbitrary MCP code is **not an OS sandbox**. Reviewed trusted local
servers run with the user's OS rights. RPC deadlines/cardinality/output bounds
are implemented; hostile-code CPU/RAM quotas, a hardened process container and a
preparse cap inside SDK stdio framing are not verified or claimed. Only trusted
fixture servers were launched. There is no Secure/Full Access activation, hosted
deployment, physical-device acceptance or formal Gate C/D/E promotion here.
